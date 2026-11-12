from datetime import datetime, timedelta
import importlib
import os
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_ROOT = os.getenv("FRAUD_PROJECT_ROOT", "/opt/project")
if os.path.exists(PROJECT_ROOT) and PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
elif os.path.dirname(os.path.dirname(os.path.abspath(__file__))) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

audit_mod = importlib.import_module("04_batch_airflow.run_daily_audit")
check_retrain_trigger = audit_mod.check_retrain_trigger
run_etl_bronze_to_silver = audit_mod.run_etl_bronze_to_silver
run_gold_audit_and_drift = audit_mod.run_gold_audit_and_drift

default_args = {
    "owner": "data-architecture-rncp41993",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="daily_fraud_audit_pipeline",
    default_args=default_args,
    description="ETL Bronze->Silver (Pandera & RGPD) >> Gold Audit/Drift & OpenLineage >> Contrôle MLflow @champion",
    schedule="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["fraud", "medallion", "pandera", "rncp41993", "bloc3"],
) as dag:

    task_etl_bronze_to_silver = PythonOperator(
        task_id="etl_bronze_to_silver",
        python_callable=run_etl_bronze_to_silver,
    )

    task_gold_audit_and_drift = PythonOperator(
        task_id="gold_audit_and_drift",
        python_callable=run_gold_audit_and_drift,
    )

    task_check_retrain_trigger = PythonOperator(
        task_id="check_retrain_trigger",
        python_callable=check_retrain_trigger,
    )

    task_etl_bronze_to_silver >> task_gold_audit_and_drift >> task_check_retrain_trigger
