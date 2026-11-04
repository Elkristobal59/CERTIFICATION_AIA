"""
=============================================================================
DAG APACHE AIRFLOW : DAILY FRAUD AUDIT & REPORTING PIPELINE (BLOC 3)
=============================================================================
Objectif Métier : Chaque matin à 06h00 UTC, agréger l'ensemble des paiements
et des fraudes détectées au cours des dernières 24h et produire le rapport
exécutif pour les équipes Conformité et Risque Financier.
=============================================================================
"""

import os
import sys
from datetime import datetime, timedelta

# Airflow imports conditionnels
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    from airflow.operators.bash import BashOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import importlib
db_mod = importlib.import_module("05_database.db_manager")
compute_daily_audit = db_mod.compute_daily_audit

default_args = {
    'owner': 'data-engineering-lead',
    'depends_on_past': False,
    'email': ['risk-fraud-alerts@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def task_extract_and_compute_audit(**context):
    """Étape 1 : Extraction et calcul des KPIs de fraude sur les dernières 24 heures."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    audit_data = compute_daily_audit(yesterday)
    print(f"📊 Audit calculé pour le {yesterday} : {audit_data}")
    return audit_data

def task_publish_executive_digest(**context):
    """Étape 2 : Formatage et publication de la synthèse matinale."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    audit_data = compute_daily_audit(yesterday)
    
    report_file = os.path.join(BASE_DIR, "04_batch_airflow", f"audit_report_{yesterday}.md")
    report_content = f"""# 📑 Rapport Matinal Quotidien d'Audit des Fraudes ({yesterday})
> **Généré par le DAG Apache Airflow :** `daily_fraud_audit_pipeline`  
> **Exécution :** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  

## 📌 Synthèse Exécutive des Dernières 24 Heures :
* **Nombre Total de Transactions Traitées :** {audit_data['total_transactions']}
* **Volume Financier Total Traité         :** {audit_data['total_volume_eur']:,.2f} €
* **Nombre de Fraudes Détectées           :** {audit_data['frauds_detected']}
* **Volume Financier des Fraudes Bloquées  :** {audit_data['fraud_volume_eur']:,.2f} €
* **Taux de Fraude                        :** {audit_data['fraud_rate_pct']} %
* **Catégorie la plus Ciblée              :** {audit_data['top_fraud_category']}

---
*Ce rapport est archivé automatiquement dans le Data Lake d'Audit pour conformité PCI-DSS.*
"""
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"✅ Rapport matinal exporté : {report_file}")

if AIRFLOW_AVAILABLE:
    with DAG(
        dag_id="daily_fraud_audit_pipeline",
        default_args=default_args,
        description="Pipeline batch Airflow pour l'audit matinal des fraudes bancaires",
        schedule_interval="0 6 * * *",  # Tous les matins à 06h00 UTC
        start_date=datetime(2026, 1, 1),
        catchup=False,
        tags=['fraud', 'compliance', 'rncp41993', 'bloc3'],
    ) as dag:

        t1_compute = PythonOperator(
            task_id="compute_24h_fraud_kpis",
            python_callable=task_extract_and_compute_audit,
        )

        t2_publish = PythonOperator(
            task_id="publish_executive_digest",
            python_callable=task_publish_executive_digest,
        )

        t1_compute >> t2_publish
