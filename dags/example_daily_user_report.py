"""
Example DAG: Daily user signup report
Pulls data from the shared mentoring database and prints a summary.

This is your first DAG! Modify it, add new ones, commit to GitHub.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator
from airflow.hooks.postgres_hook import PostgresHook


default_args = {
    "owner": "student",
    "depends_on_past": False,
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def print_user_stats(**context):
    """Pull user signup stats and print them."""
    hook = PostgresHook(postgres_conn_id="mentoring_db")
    records = hook.get_records("""
        SELECT
            country,
            COUNT(*) as total_users,
            SUM(CASE WHEN is_premium THEN 1 ELSE 0 END) as premium_users,
            ROUND(AVG(CASE WHEN is_premium THEN 1.0 ELSE 0.0 END) * 100, 1) as premium_pct
        FROM shared_data.users
        GROUP BY country
        ORDER BY total_users DESC
        LIMIT 10;
    """)
    print("=" * 60)
    print("TOP 10 COUNTRIES BY SIGNUPS")
    print("=" * 60)
    print(f"{'Country':<10} {'Total':>8} {'Premium':>8} {'Premium%':>10}")
    print("-" * 40)
    for row in records:
        print(f"{row[0]:<10} {row[1]:>8} {row[2]:>8} {row[3]:>9}%")
    print("=" * 60)


with DAG(
    dag_id="example_daily_user_report",
    default_args=default_args,
    description="Daily user signup report from shared database",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["mentoring", "example"],
) as dag:

    # Task 1: Check database connection
    check_db = PostgresOperator(
        task_id="check_database_connection",
        postgres_conn_id="mentoring_db",
        sql="SELECT 1;",
    )

    # Task 2: Count events from yesterday
    count_events = PostgresOperator(
        task_id="count_yesterday_events",
        postgres_conn_id="mentoring_db",
        sql="""
            SELECT event_type, COUNT(*)
            FROM shared_data.events
            WHERE event_date >= CURRENT_DATE - INTERVAL '1 day'
              AND event_date < CURRENT_DATE
            GROUP BY event_type
            ORDER BY COUNT(*) DESC;
        """,
    )

    # Task 3: Print user stats using Python
    print_stats = PythonOperator(
        task_id="print_user_stats",
        python_callable=print_user_stats,
    )

    # Pipeline: check -> count -> print
    check_db >> count_events >> print_stats
