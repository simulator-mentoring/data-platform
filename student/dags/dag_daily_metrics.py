"""
DAG: Daily Metrics Pipeline
Считает ежедневные метрики и загружает в sandbox.daily_metrics.

TODO: Заполните все пропуски (отмечены TODO) и скопируйте в dags/
      cp templates/dag_daily_metrics.py dags/dag_daily_metrics.py
"""

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

    print(f"Validation passed!")
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

    # Task 1: Create table if not exists
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

    # Task 2: Calculate metrics for yesterday
    # TODO: Напишите SQL, который вставляет метрики за вчерашний день
    #
    # Подсказки:
    # - Используйте CURRENT_DATE - INTERVAL '1 day' для вчерашней даты
    # - total_users: COUNT пользователей с signup_date <= вчера
    # - new_users: COUNT пользователей с signup_date = вчера
    # - total_events: COUNT событий с event_date::date = вчера
    # - total_orders: COUNT заказов с order_date::date = вчера
    # - total_revenue: SUM(amount) заказов со статусом 'completed' за вчера
    # - avg_order_amount: AVG(amount) заказов за вчера
    # - Используйте ON CONFLICT для идемпотентности (повторный запуск обновляет данные)

    calculate_metrics = PostgresOperator(
        task_id="calculate_metrics",
        postgres_conn_id="mentoring_db",
        sql="""
            -- TODO: Замените этот запрос на INSERT...SELECT
            -- Пример структуры:
            --
            -- INSERT INTO sandbox.daily_metrics (
            --     report_date, total_users, new_users,
            --     total_events, total_orders, total_revenue, avg_order_amount
            -- )
            -- SELECT
            --     (CURRENT_DATE - INTERVAL '1 day')::date,
            --     ... ваши подзапросы ...
            -- ON CONFLICT (report_date) DO UPDATE SET
            --     total_users = EXCLUDED.total_users,
            --     ...
            INSERT INTO sandbox.daily_metrics (
                report_date,
                total_users,
                new_users,
                total_events,
                total_orders,
                total_revenue,
                avg_order_amount
            )
            WITH target_date AS (
                SELECT (CURRENT_DATE - INTERVAL '1 day')::date AS report_date
            ),
            total_users AS (
                SELECT
                    (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,
                    COUNT(user_id) AS total_users
                FROM shared_data.users
                WHERE signup_date::date <= (CURRENT_DATE - INTERVAL '1 day')::date
            ),
            new_users AS (
                SELECT
                    (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,
                    COUNT(user_id) AS new_users
                FROM shared_data.users
                WHERE signup_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
            ),
            total_events AS (
                SELECT
                    (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,
                    COUNT(event_id) AS total_events
                FROM shared_data.events
                WHERE event_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
            ),
            total_orders AS (
                SELECT
                    (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,
                    COUNT(order_id) AS total_orders
                FROM shared_data.orders
                WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                AND status = 'completed'
            ),
            total_revenue AS (
                SELECT
                    (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,
                    SUM(amount) AS total_revenue
                FROM shared_data.orders
                WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                AND status = 'completed'
            ),
            avg_order_amount AS (
                SELECT
                    (CURRENT_DATE - INTERVAL '1 day')::date AS report_date,
                    ROUND(AVG(amount), 2) AS avg_order_amount
                FROM shared_data.orders
                WHERE order_date::date = (CURRENT_DATE - INTERVAL '1 day')::date
                AND status = 'completed'
            )
            SELECT
                dt.report_date,
                COALESCE(tu.total_users, 0)                       AS total_users,
                COALESCE(nu.new_users, 0)                         AS new_users,
                COALESCE(te.total_events, 0)                      AS total_events,
                COALESCE(ord.total_orders, 0)                     AS total_orders,
                COALESCE(tr.total_revenue, 0)::DECIMAL(12,2)      AS total_revenue,
                COALESCE(aoa.avg_order_amount, 0)::DECIMAL(10,2)  AS avg_order_amount
            FROM target_date dt
            LEFT JOIN total_users tu       ON dt.report_date = tu.report_date
            LEFT JOIN new_users nu         ON dt.report_date = nu.report_date
            LEFT JOIN total_events te      ON dt.report_date = te.report_date
            LEFT JOIN total_orders ord     ON dt.report_date = ord.report_date
            LEFT JOIN total_revenue tr     ON dt.report_date = tr.report_date
            LEFT JOIN avg_order_amount aoa ON dt.report_date = aoa.report_date
            ON CONFLICT (report_date) DO UPDATE SET
                total_users      = EXCLUDED.total_users,
                new_users        = EXCLUDED.new_users,
                total_events     = EXCLUDED.total_events,
                total_orders     = EXCLUDED.total_orders,
                total_revenue    = EXCLUDED.total_revenue,
                avg_order_amount = EXCLUDED.avg_order_amount,
                created_at       = NOW();
        """,
    )

    # Task 3: Validate results
    validate = PythonOperator(
        task_id="validate_results",
        python_callable=validate_metrics,
    )

    # TODO: Задайте порядок выполнения задач
    # Подсказка: create_table >> calculate_metrics >> validate
    create_table >> calculate_metrics >> validate