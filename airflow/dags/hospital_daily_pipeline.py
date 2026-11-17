"""
hospital_daily_pipeline.py
Runs the daily claims pipeline: make -> clean -> load -> check.
"""

from datetime import datetime, timedelta

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJECT_DIR = "/Users/rupamanchikalapudi/Documents/hospital-pipeline"
PYTHON = PROJECT_DIR + "/.venv/bin/python"

default_args = {
    "retries": 2,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    dag_id="hospital_daily_pipeline",
    start_date=datetime(2026, 11, 1),
    schedule="30 1 * * *",
    catchup=False,
    default_args=default_args,
    tags=["hospital"],
) as dag:

    make_file = BashOperator(
        task_id="make_daily_file",
        bash_command=PYTHON + " scripts/make_daily_file.py {{ ds }}",
        cwd=PROJECT_DIR,
    )

    clean_file = BashOperator(
        task_id="clean_daily_file",
        bash_command=PYTHON + " scripts/clean_daily_file.py {{ ds }}",
        cwd=PROJECT_DIR,
    )

    load_file = BashOperator(
        task_id="load_to_bigquery",
        bash_command=PYTHON + " scripts/load_to_bigquery.py {{ ds }}",
        cwd=PROJECT_DIR,
    )

    check = BashOperator(
        task_id="check_quality",
        bash_command=PYTHON + " scripts/check_quality.py {{ ds }}",
        cwd=PROJECT_DIR,
    )

    make_file >> clean_file >> load_file >> check