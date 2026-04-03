from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook


default_args = {
    "owner": "student",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def validate_results():
    hook = PostgresHook(postgres_conn_id="mentoring_db")

    query = """
        SELECT COUNT(*)
        FROM sandbox.daily_metrics
        WHERE report_date = (CURRENT_DATE - INTERVAL '1 day')::date
    """

    result = hook.get_first(query)

    if not result or result[0] == 0:
        raise ValueError("Строка за вчерашний день не найдена в sandbox.daily_metrics")


with DAG(
    dag_id="dag_daily_metrics",
    default_args=default_args,
    description="Calculate daily metrics and load into sandbox.daily_metrics",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["mentoring", "daily_metrics"],
) as dag:

    create_table = PostgresOperator(
        task_id="create_table",
        postgres_conn_id="mentoring_db",
        sql="""
        CREATE SCHEMA IF NOT EXISTS sandbox;

        CREATE TABLE IF NOT EXISTS sandbox.daily_metrics (
            report_date DATE PRIMARY KEY,
            total_users INTEGER,
            new_users INTEGER,
            total_events INTEGER,
            total_orders INTEGER,
            total_revenue DECIMAL(12,2),
            avg_order_amount DECIMAL(10,2),
            created_at TIMESTAMP
        );
        """,
    )

    calculate_metrics = PostgresOperator(
        task_id="calculate_metrics",
        postgres_conn_id="mentoring_db",
        sql="""
        INSERT INTO sandbox.daily_metrics (
            report_date,
            total_users,
            new_users,
            total_events,
            total_orders,
            total_revenue,
            avg_order_amount,
            created_at
        )
        WITH target_date AS (
            SELECT (CURRENT_DATE - INTERVAL '1 day')::date AS report_date
        ),
        total_users AS (
            SELECT
                td.report_date,
                COUNT(u.user_id) AS total_users
            FROM target_date td
            LEFT JOIN shared_data.users u
                ON u.signup_date <= td.report_date
            GROUP BY td.report_date
        ),
        new_users AS (
            SELECT
                signup_date AS report_date,
                COUNT(*) AS new_users
            FROM shared_data.users
            WHERE signup_date = (CURRENT_DATE - INTERVAL '1 day')::date
            GROUP BY signup_date
        ),
        events_daily AS (
            SELECT
                event_date::date AS report_date,
                COUNT(*) AS total_events
            FROM shared_data.events
            WHERE event_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
            GROUP BY event_date::date
        ),
        orders_daily AS (
            SELECT
                order_date::date AS report_date,
                COUNT(*) AS total_orders
            FROM shared_data.orders
            WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
            GROUP BY order_date::date
        ),
        revenue_daily AS (
            SELECT
                order_date::date AS report_date,
                SUM(amount)::DECIMAL(12,2) AS total_revenue,
                AVG(amount)::DECIMAL(10,2) AS avg_order_amount
            FROM shared_data.orders
            WHERE status = 'completed'
              AND order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
            GROUP BY order_date::date
        )
        SELECT
            td.report_date,
            COALESCE(tu.total_users, 0) AS total_users,
            COALESCE(nu.new_users, 0) AS new_users,
            COALESCE(ed.total_events, 0) AS total_events,
            COALESCE(od.total_orders, 0) AS total_orders,
            COALESCE(rd.total_revenue, 0)::DECIMAL(12,2) AS total_revenue,
            COALESCE(rd.avg_order_amount, 0)::DECIMAL(10,2) AS avg_order_amount,
            CURRENT_TIMESTAMP AS created_at
        FROM target_date td
        LEFT JOIN total_users tu
            ON td.report_date = tu.report_date
        LEFT JOIN new_users nu
            ON td.report_date = nu.report_date
        LEFT JOIN events_daily ed
            ON td.report_date = ed.report_date
        LEFT JOIN orders_daily od
            ON td.report_date = od.report_date
        LEFT JOIN revenue_daily rd
            ON td.report_date = rd.report_date
        ON CONFLICT (report_date) DO UPDATE
        SET
            total_users = EXCLUDED.total_users,
            new_users = EXCLUDED.new_users,
            total_events = EXCLUDED.total_events,
            total_orders = EXCLUDED.total_orders,
            total_revenue = EXCLUDED.total_revenue,
            avg_order_amount = EXCLUDED.avg_order_amount,
            created_at = EXCLUDED.created_at;
        """,
    )

    validate_results_task = PythonOperator(
        task_id="validate_results",
        python_callable=validate_results,
    )

    create_table >> calculate_metrics >> validate_results_task
