from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook



default_args = {
    "owner": "student",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def validate_metrics(**context):
    """Check that yesterday's metrics were calculated."""
    hook = PostgresHook(postgres_conn_id="mentoring_db")
    result = hook.get_first("""
        SELECT report_date, total_orders, total_revenue
        FROM sandbox.daily_metrics
        WHERE report_date = CURRENT_DATE - INTERVAL '1 day'
    """)
    if result is None:
        raise ValueError("No metrics found for yesterday! Check calculate_metrics task.")

    print("Validation passed!")
    print(f"  Date:     {result[0]}")
    print(f"  Orders:   {result[1]}")
    print(f"  Revenue:  {result[2]}")


with DAG(
    dag_id="dag_daily_metrics",
    default_args=default_args,
    description="Calculate daily metrics and load into sandbox.daily_metrics",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["mentoring", "daily_metrics"],
) as dag:

    create_table = PostgresOperator(
        task_id="create_table",
        postgres_conn_id="mentoring_db",
        sql="""
            CREATE TABLE IF NOT EXISTS sandbox.daily_metrics (
                report_date      DATE PRIMARY KEY,
                total_users      INTEGER NOT NULL DEFAULT 0,
                new_users        INTEGER NOT NULL DEFAULT 0,
                total_events     INTEGER NOT NULL DEFAULT 0,
                total_orders     INTEGER NOT NULL DEFAULT 0,
                total_revenue    DECIMAL(12, 2) NOT NULL DEFAULT 0,
                avg_order_amount DECIMAL(10, 2) NOT NULL DEFAULT 0,
                created_at       TIMESTAMP DEFAULT NOW()
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
                avg_order_amount
            )
            SELECT
                (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,

                (
                    SELECT COUNT(*)
                    FROM shared_data.users
                    WHERE signup_date::date <= (CURRENT_DATE - INTERVAL '1 day')::date
                ) AS total_users,

                (
                    SELECT COUNT(*)
                    FROM shared_data.users
                    WHERE signup_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                ) AS new_users,

                (
                    SELECT COUNT(*)
                    FROM shared_data.events
                    WHERE event_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                ) AS total_events,

                (
                    SELECT COUNT(*)
                    FROM shared_data.orders
                    WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                ) AS total_orders,

                (
                    SELECT COALESCE(SUM(amount), 0)
                    FROM shared_data.orders
                    WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                      AND status = 'completed'
                ) AS total_revenue,

                (
                    SELECT COALESCE(AVG(amount), 0)
                    FROM shared_data.orders
                    WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                ) AS avg_order_amount

            ON CONFLICT (report_date) DO UPDATE SET
                total_users = EXCLUDED.total_users,
                new_users = EXCLUDED.new_users,
                total_events = EXCLUDED.total_events,
                total_orders = EXCLUDED.total_orders,
                total_revenue = EXCLUDED.total_revenue,
                avg_order_amount = EXCLUDED.avg_order_amount,
                created_at = NOW();
        """,
    )

    validate = PythonOperator(
        task_id="validate_results",
        python_callable=validate_metrics,
    )

    create_table >> calculate_metrics >> validate
