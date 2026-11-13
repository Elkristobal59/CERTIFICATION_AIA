# 🎥 SUPPORT & SCÉNARIO DE DÉMONSTRATION VIDÉO — BLOC 3 FRAUDE (RNCP 41993)

*Guide de démonstration opérationnelle (2 min 30 s) aligné sur l'architecture hybride Session 3 déployée (`Docker Local` : `MLflow`, `Kafka KRaft`, `Pandera DLQ`, `FastAPI`, `Mailpit/Gmail SMTP`, `Apache Airflow 2.11` + `Cloud Managé` : `Neon PostgreSQL` & `AWS S3 eu-west-3`).*

---

## 1. Livrable Vidéo & État Actuel

* **Fichier vidéo présent dans `LIVRABLES/` :** `fraud_detectionApp_chris_gilleron.mp4` (`123.1 Mo`, capture originale ; mise à jour vidéo planifiée post-refonte).
* **Mise à niveau de l'infrastructure :** Depuis la capture initiale, le pipeline a été aligné sur les exigences complètes Session 3 + RNCP 41993 : serveur **MLflow + Neon PostgreSQL (`fraud_mlflow_db`) + AWS S3 (`eu-west-3`, `fraud-bloc3-mlflow-rncp41993-chris`)** avec alias `@champion` / `@challenger`, base opérationnelle **Neon PostgreSQL (`fraud_db`)**, validation **Pandera + quarantaine `fraud-dlq` / `rejected/` anonymisée**, masquage PAN `**** **** **** 1234` + **SHA-256 salé**, alerting **e-mail SMTP réel (`Mailpit` / `Gmail TLS`)** et DAG **Apache Airflow 2.11** vérifié en conteneur.
* **Déroulé opérationnel couvert :** La séquence ci-dessous décrit les étapes de démonstration de bout en bout sur les interfaces web `MLflow`, `AWS S3` / `Neon`, `Mailpit` / `Gmail`, `Kafka UI` et `Airflow`.

---

## 2. Séquence Recommandée de Démonstration Live (2 min 30 s)

### ⏱️ 00:00 – 00:30 | Stack Hybride Docker + Neon PostgreSQL + AWS S3 (`@champion`)
* Commande présentée : `docker compose ps` montrant les services locaux (`mlflow`, `kafka`, `kafka-ui`, `mailpit`, `fraud-scoring-api`, `airflow`, `postgres` scheduler) connectés à **Neon Cloud SSL** et **AWS S3 (`eu-west-3`)**.
* Ouverture de `http://localhost:5000` (MLflow UI) : présentation du benchmark complet sur **555 719 transactions**, avec promotion **`@champion`** sur `HistGradientBoosting_Balanced` (`ROC-AUC 0.9876`, `Recall 91.61 %`) et **`@challenger`** sur `RandomForest_Balanced` (`ROC-AUC 0.9836`), artefacts stockés réellement sur `s3://fraud-bloc3-mlflow-rncp41993-chris/`.

### ⏱️ 00:30 – 01:25 | Streaming Kafka, Validation Pandera, Scoring API & Alerte SMTP
* Exécution directe : `python run_full_pipeline_demo.py`.
* Points clés observés en sortie console :
  1. Récupération d'une transaction live Hugging Face + replay dataset + injection volontaire d'un payload invalide (`amt = -150.0 €`).
  2. Validation **Pandera** bloquant `-150.0 €` vers le topic Kafka `fraud-dlq`, **Neon `dead_letter_queue`** et `data_lake/rejected/`.
  3. Appel HTTP `POST /predict` (`http://localhost:8080/health` affichant `mlflow://fraud_detection_model@champion`, latence médiane **19.4 ms**, p95 **28.9 ms**).
  4. Déclenchement d'une alerte fraude `CRITICAL` (`99.77 %` -> `BLOCK_IMMEDIATE` sur `955.16 €`) avec PAN masqué `**** **** **** 0820` et identité pseudonymisée `D*** W*** (ID:64698E)`.
* Bascule sur **Mailpit Web UI** (`http://localhost:8025`) ou boîte **Gmail** (selon `.env`) : ouverture de l'e-mail d'alerte reçu instantanément via `smtplib`.

### ⏱️ 01:25 – 02:10 | Data Lake Medallion, Conformité RGPD & Neon PostgreSQL
* Vérification de la double persistance :
  * Tables `transactions`, `fraud_alerts` et `dead_letter_queue` sur **Neon PostgreSQL (`fraud_db`)** (aucun PAN ni nom complet en clair).
  * Data Lake Parquet partitionné `year=/month=/day=` : `bronze/` (PAN masqué), `silver/` (**7 colonnes PII directes supprimées** + hash SHA-256 salé), `gold/`, `rejected/` et journal **OpenLineage** (`data_lake/lineage/openlineage_events.jsonl`).

### ⏱️ 02:10 – 02:30 | Orchestration Batch Apache Airflow & FinOps
* Ouverture de `http://localhost:8088` (Airflow) ou commande `docker exec fraud-airflow airflow dags test daily_fraud_audit_pipeline 2026-11-12` validant le DAG à 3 tâches (`etl_bronze_to_silver >> gold_audit_and_drift >> check_retrain_trigger`) vers **Neon `fraud_db`** et la génération automatique de `RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md`.
