# 🎓 Certification Architecte en Intelligence Artificielle — RNCP 41993 (Bloc 3)

Dépôt principal hébergeant l'architecture hybride **Détection de Fraude Bancaire Temps Réel & Batch Medallion (Bloc 3 — Concevoir et mettre en œuvre des pipelines de données pour l'IA)**, combinant conteneurs **Docker locaux** et services managés **Neon PostgreSQL (`eu-central-1`) + AWS S3 (`eu-west-3`) + Gmail SMTP TLS**.

## 📂 Organisation du Dépôt

* [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/`](03_BLOC_3_PIPELINE_FRAUD_DETECTION/README.md) — **Code applicatif complet, Docker Compose, scripts Python, DAG Airflow et livrables officiels** :
  * `01_train/` : Feature engineering partagé (`features.py`), benchmark multi-modèles MLflow (`train_model.py`, notebook) connecté à **Neon `fraud_mlflow_db`** + **AWS S3 (`eu-west-3`)** sur `555 719` transactions (`HistGradientBoosting` `@champion` ROC-AUC `0.9876`, `RandomForest` `@challenger` ROC-AUC `0.9836`).
  * `02_api/` : Microservice **FastAPI** + Pydantic strict (`POST /predict`, `/predict-raw`, `/reload-model`, latence médiane `19.4 ms`, p95 `28.9 ms`).
  * `03_pipeline_streaming/` : Producteur/Consommateur **confluent-kafka**, **Pandera Quality Gate**, quarantaine **DLQ**, et alerting réel **`smtplib`** (**Gmail SMTP TLS** / fallback **Mailpit**).
  * `04_batch_airflow/` : DAG **Apache Airflow 2.11** à 3 tâches (`etl_bronze_to_silver >> gold_audit_and_drift >> check_retrain_trigger`), rapports Markdown quotidiens et événements **OpenLineage**.
  * `05_database/` : Schéma **PostgreSQL** déployé sur **Neon Serverless SSL (`fraud_db`)**, masquage PCI-DSS `**** **** **** 1234`, pseudonymisation RGPD **SHA-256 salé** (`SECRET_SALT` via `.env`) et couche **Data Lake Medallion Parquet** (`bronze/`, `silver/`, `gold/`, `rejected/`, `lineage/`).
  * `LIVRABLES/` : Schéma PNG, présentation PPTX/PDF, rapport d'architecture PDF, guide vidéo PDF et archive ZIP prête au dépôt (`Fraud_Detection_Livrables_Bloc3.zip`).
* [`02_PREPARATION_ORAL/`](02_PREPARATION_ORAL/FICHE_REVISION_MASTER_BLOC3_ORAL.md) — Supports et fiches de révision pour la soutenance Bloc 3 (5 min pitch + 15 min Q&A).

---

👉 **Guide complet d'installation, architecture, Data Lineage, FinOps et commandes :** consulter [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/README.md`](03_BLOC_3_PIPELINE_FRAUD_DETECTION/README.md).
