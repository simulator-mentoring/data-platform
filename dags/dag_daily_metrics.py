"""
DAG: Daily Metrics Pipeline
Считает ежедневные метрики и загружает в sandbox.daily_metrics.
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
            with users_stat as (
                select
                    (current_date - interval '1 day')::date as yesterday,
                    count(distinct user_id) filter (
                    where signup_date::date <= (current_date - interval '1 day')) as total_users,
                    count(distinct user_id) filter (
                    where signup_date::date = (current_date - interval '1 day')) as new_users
                from shared_data.users),
            events_stat as (
                select
                    (current_date - interval '1 day')::date as yesterday,
                    count(distinct event_id) as total_events
                from shared_data.events
                where event_date::date = (current_date - interval '1 day')::date),
            orders_stat as (
                select
                    (current_date - interval '1 day')::date as yesterday,
                    count(distinct order_id) as total_orders,
                    coalesce(sum(case when status = 'completed' then amount end), 0) as total_revenue,
                    coalesce(avg(case when status = 'completed' then amount end), 0) as avg_order_amount
                from shared_data.orders
                where order_date::date = (current_date - interval '1 day')::date
            )
            insert into sandbox.daily_metrics (
                 report_date, total_users, new_users,
                 total_events, total_orders, total_revenue, avg_order_amount
            )
             select
                 (current_date - interval '1 day')::date,
                 u.total_users,
                 u.new_users,
                 e.total_events,
                 o.total_orders,
                 o.total_revenue,
                 o.avg_order_amount
            from users_stat u
            join events_stat e on u.yesterday = e.yesterday
            join orders_stat o on o.yesterday = u.yesterday
                 
            on conflict (report_date) do update set
                 total_users = excluded.total_users,
                 new_users = excluded.new_users,
                 total_events = excluded.total_events,
                 total_orders = excluded.total_orders,
                 total_revenue = excluded.total_revenue,
                 avg_order_amount = excluded.avg_order_amount;

        """,
    )

    validate = PythonOperator(
        task_id="validate_results",
        python_callable=validate_metrics,
    )

create_table >> calculate_metrics >> validate
