"""
hello_pipeline.py
A practice DAG with two simple steps that run in order.
"""

from datetime import datetime

from airflow.sdk import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="hello_pipeline",
    start_date=datetime(2026, 11, 1),
    schedule=None,
    catchup=False,
) as dag:

    say_hello = BashOperator(
        task_id="say_hello",
        bash_command="echo 'Hello from Airflow'",
    )

    show_date = BashOperator(
        task_id="show_date",
        bash_command="date",
    )

    say_hello >> show_date