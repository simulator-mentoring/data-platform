"""
DAG: Daily event activity report
Analyzes user event activity from the shared mentoring database,
identifies top active users and event type distribution.
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


def report_event_distribution(**context):
    """Print event type distribution for the last 7 days."""
    hook = PostgresHook(postgres_conn_id="mentoring_db")
    records = hook.get_records("""
        SELECT
            event_type,
            COUNT(*) AS event_count,
            COUNT(DISTINCT user_id) AS unique_users,
            ROUND(COUNT(*)::numeric / GREATEST(COUNT(DISTINCT user_id), 1), 1)
                AS events_per_user
        FROM shared_data.events
        WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY event_type
        ORDER BY event_count DESC;
    """)
    print("=" * 65)
    print("EVENT DISTRIBUTION (last 7 days)")
    print("=" * 65)
    print(f"{'Event Type':<20} {'Events':>8} {'Users':>8} {'Avg/User':>10}")
    print("-" * 50)
    for row in records:
        print(f"{row[0]:<20} {row[1]:>8} {row[2]:>8} {row[3]:>10}")
    print("=" * 65)


def report_top_active_users(**context):
    """Print top 10 most active users over the last 7 days."""
    hook = PostgresHook(postgres_conn_id="mentoring_db")
    records = hook.get_records("""
        SELECT
            u.username,
            u.country,
            COUNT(*) AS total_events,
            COUNT(DISTINCT e.event_type) AS event_types_used
        FROM shared_data.events e
        JOIN shared_data.users u ON u.id = e.user_id
        WHERE e.event_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY u.username, u.country
        ORDER BY total_events DESC
        LIMIT 10;
    """)
    print("=" * 65)
    print("TOP 10 ACTIVE USERS (last 7 days)")
    print("=" * 65)
    print(f"{'Username':<18} {'Country':<10} {'Events':>8} {'Types':>8}")
    print("-" * 48)
    for row in records:
        print(f"{row[0]:<18} {row[1]:<10} {row[2]:>8} {row[3]:>8}")
    print("=" * 65)


with DAG(
    dag_id="daily_event_activity_report",
    default_args=default_args,
    description="Daily report on user event activity and engagement",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["mentoring", "analytics"],
) as dag:

    check_db = PostgresOperator(
        task_id="check_database_connection",
        postgres_conn_id="mentoring_db",
        sql="SELECT 1;",
    )

    event_distribution = PythonOperator(
        task_id="report_event_distribution",
        python_callable=report_event_distribution,
    )

    top_users = PythonOperator(
        task_id="report_top_active_users",
        python_callable=report_top_active_users,
    )

    check_db >> [event_distribution, top_users]
