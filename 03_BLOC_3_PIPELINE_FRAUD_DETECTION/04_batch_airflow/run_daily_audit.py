import os
import sys
import json
import uuid
import datetime
import importlib
import urllib.request
from typing import Any, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.getenv("FRAUD_PROJECT_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(BASE_DIR, "01_train")) and os.path.exists("/opt/project/01_train"):
    BASE_DIR = "/opt/project"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

features_mod = importlib.import_module("01_train.features")
db_mod = importlib.import_module("05_database.db_manager")

features_mod.load_project_env()
init_db = db_mod.init_db
transform_bronze_to_silver = db_mod.transform_bronze_to_silver
compute_daily_audit = db_mod.compute_daily_audit
BRONZE_DIR = db_mod.BRONZE_DIR
SILVER_DIR = db_mod.SILVER_DIR
GOLD_DIR = db_mod.GOLD_DIR
REJECTED_DIR = db_mod.REJECTED_DIR

LINEAGE_DIR = os.path.join(os.path.dirname(BRONZE_DIR), "lineage")
REPORTS_DIR = os.path.join(BASE_DIR, "04_batch_airflow")


def emit_openlineage_event(job_name: str, target_date: str, audit_metrics: Dict[str, Any]) -> str:
    """Enregistre un événement OpenLineage v1 traçant Bronze -> Silver -> Gold -> PostgreSQL."""
    os.makedirs(LINEAGE_DIR, exist_ok=True)
    lineage_file = os.path.join(LINEAGE_DIR, "openlineage_events.jsonl")
    event = {
        "eventType": "COMPLETE",
        "eventTime": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "run": {
            "runId": str(uuid.uuid4()),
            "facets": {
                "dataQualityMetrics": {
                    "audit_date": target_date,
                    "total_transactions": audit_metrics.get("total_transactions", 0),
                    "dlq_rejected_count": audit_metrics.get("dlq_rejected_count", 0),
                    "data_drift_status": audit_metrics.get("data_drift_status", "OK"),
                }
            },
        },
        "job": {"namespace": "rncp41993-bloc3-fraud-pipeline", "name": job_name},
        "inputs": [
            {"namespace": "local-datalake", "name": f"bronze/year={target_date[:4]}/raw_transactions_stream.parquet"},
            {"namespace": "local-datalake", "name": f"silver/year={target_date[:4]}/clean_transactions_silver.parquet"},
        ],
        "outputs": [
            {"namespace": "local-datalake", "name": f"gold/year={target_date[:4]}/fraud_features_gold.parquet"},
            {"namespace": "postgresql", "name": "fraud_db.daily_audit_summary"},
        ],
        "producer": "https://github.com/Elkristobal59/CERTIFICATION_AIA/04_batch_airflow",
    }
    with open(lineage_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
    return lineage_file


def run_etl_bronze_to_silver(target_date: Optional[str] = None) -> Dict[str, Any]:
    """Tâche 1 Airflow : ETL Bronze -> Silver (Pandera, Quarantaine rejected/, SHA-256 salé, Drop PII)."""
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    res = transform_bronze_to_silver(target)
    print(f"🧹 [ETL Bronze -> Silver | {target}] {res}")
    return res


def run_gold_audit_and_drift(target_date: Optional[str] = None) -> Dict[str, Any]:
    """Tâche 2 Airflow : Gold Parquet + Data Drift + Agrégation PostgreSQL + Rapport Markdown + OpenLineage."""
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    metrics = compute_daily_audit(target)
    lineage_file = emit_openlineage_event("daily_fraud_audit_pipeline", target, metrics)

    md_content = "\n".join([
        f"# 🛡️ RAPPORT D'AUDIT MATINAL QUOTIDIEN — {target}",
        "",
        f"*Généré automatiquement le {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} — Pipeline Batch Airflow / PostgreSQL*",
        "",
        "| Indicateur | Valeur Mesurée |",
        "| :--- | :--- |",
        f"| **Volume Transactions Analysées** | `{metrics['total_transactions']}` |",
        f"| **Volume Financier Traité** | `{metrics['total_volume_eur']:.2f} €` |",
        f"| **Alertes Fraude Confirmées** | `{metrics['frauds_detected']}` ({metrics['fraud_rate_pct']:.2f} %) |",
        f"| **Montant Fraude Bloquée / Monitorée** | `{metrics['fraud_volume_eur']:.2f} €` |",
        f"| **Catégorie la Plus Ciblée** | `{metrics['top_fraud_category']}` |",
        f"| **Rejets Pandera / DLQ (`rejected/`)** | `{metrics['dlq_rejected_count']}` |",
        f"| **Statut Data Drift (Gold)** | `{metrics['data_drift_status']}` |",
        "",
        f"- **Stockage Data Lake Medallion** : `bronze/` -> `silver/` -> `gold/` & `rejected/`",
        f"- **Traçabilité OpenLineage** : `{os.path.relpath(lineage_file, BASE_DIR)}`",
        "",
    ])

    for report_name in ("RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md", f"audit_report_{target}.md"):
        with open(os.path.join(REPORTS_DIR, report_name), "w", encoding="utf-8") as f:
            f.write(md_content)

    print(f"📊 [Gold & Audit Matinal | {target}] {metrics}")
    return metrics


def check_retrain_trigger(target_date: Optional[str] = None) -> Dict[str, Any]:
    """Tâche 3 Airflow : Évalue la dérive et l'état du modèle `@champion` dans MLflow Model Registry."""
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    audit = compute_daily_audit(target)
    mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000").rstrip("/")
    model_name = os.getenv("MLFLOW_MODEL_NAME", "fraud_detection_model")
    model_alias = os.getenv("MLFLOW_MODEL_ALIAS", "champion")

    champion_version = None
    try:
        url = f"{mlflow_uri}/api/2.0/mlflow/registered-models/alias?name={model_name}&alias={model_alias}"
        with urllib.request.urlopen(url, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        champion_version = data.get("model_version", {}).get("version")
    except Exception as exc:
        print(f"ℹ️ Vérification alias MLflow ignorée ({exc}).")

    needs_retrain = audit.get("data_drift_status") == "DRIFT_ALERT" or audit.get("fraud_rate_pct", 0.0) > 25.0
    decision = {
        "audit_date": target,
        "data_drift_status": audit.get("data_drift_status"),
        "mlflow_champion_version": champion_version,
        "action": "TRIGGER_RETRAIN_RECOMMENDED" if needs_retrain else "KEEP_CURRENT_CHAMPION",
    }
    print(f"🤖 [Contrôle MLOps & Drift | {target}] {decision}")
    return decision


def generate_daily_audit(target_date: Optional[str] = None) -> Dict[str, Any]:
    """Point d'entrée complet pour exécution locale/CI (équivalent strict du DAG Airflow)."""
    init_db()
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    silver_res = run_etl_bronze_to_silver(target)
    audit_res = run_gold_audit_and_drift(target)
    mlops_res = check_retrain_trigger(target)
    return {"silver": silver_res, "audit": audit_res, "mlops": mlops_res}


if __name__ == "__main__":
    summary = generate_daily_audit()
    print(json.dumps(summary, indent=2, ensure_ascii=False))
