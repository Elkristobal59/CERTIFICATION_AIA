# 🎥 DÉMONSTRATION VIDÉO — BLOC 3 FRAUDE (RNCP 41993)

*Démonstration vidéo de bout en bout (3 min 54 s) du pipeline hybride déployé : Docker local (`MLflow`, `Kafka KRaft`, `Pandera DLQ`, `FastAPI`, `Mailpit/Gmail TLS`, `Apache Airflow 2.11`) et Cloud managé (`Neon PostgreSQL` & `AWS S3 eu-west-3`).*

---

## 1. Accès à la Démonstration Vidéo

* **Lien vidéo public (Google Drive) :** [https://drive.google.com/file/d/1nUORFhIksV191HoE_yuvA1I3GrJLSQNe/view?usp=sharing](https://drive.google.com/file/d/1nUORFhIksV191HoE_yuvA1I3GrJLSQNe/view?usp=sharing)
* **Fichier source local :** `demo fraud detection christopher gilleron.mp4` (`3 min 54 s`, `110,20 Mo`, `2112 × 1022` px, non inclus dans Git/.zip pour respecter la limite GitHub de 100 Mo).
* **Infrastructure démontrée :**
  * **MLflow + Neon PostgreSQL (`fraud_mlflow_db`) + AWS S3 (`eu-west-3`, `fraud-bloc3-mlflow-rncp41993-chris`)** avec registres `@champion` (v3 `HistGradientBoosting_Balanced`) et `@challenger` (v2).
  * **Kafka KRaft + Validation Pandera + Quarantaine (`fraud-dlq` / `data_lake/rejected/`)** avec anonymisation PII systématique (masquage PAN `**** **** **** 1234` et hachage SHA-256 salé).
  * **FastAPI (`:8080`) + Neon PostgreSQL (`fraud_db`) + Alerting SMTP Gmail TLS (`smtp.gmail.com:587`)** *(avec fallback local Mailpit sous Docker)*.
  * **Apache Airflow 2.11 (`:8088`) + Architecture Medallion (`bronze/`, `silver/`, `gold/`)** et audit matinal automatisé.

---

## 2. Déroulé Chapitré de la Vidéo (`00:00` → `03:54`)

* **`00:00 – 01:00` | Lancement du Pipeline Temps Réel (`run_full_pipeline_demo.py`)** — Vérification de la stack Docker (`Kafka`, `MLflow`, `FastAPI`, `Airflow`, `Mailpit`), puis envoi et traitement en streaming de transactions légitimes, frauduleuses et corrompues (rejet Pandera).
* **`01:00 – 02:00` | Gouvernance ML & Quarantaine Kafka** — Modèle `@champion` dans **MLflow UI (`http://localhost:5000`)** avec artefacts sur AWS S3, puis inspection dans **Kafka UI (`http://localhost:8085`)** des topics actifs et des messages rejetés dans `fraud-dlq` (données sensibles masquées).
* **`02:00 – 03:10` | Alerting, Persistance Cloud & Orchestration** — Réception en direct de l'e-mail d'alerte critique sur **Gmail TLS**, vérification de la table anonymisée `transactions` dans **Neon PostgreSQL (`fraud_db`)**, et DAG `daily_fraud_audit_pipeline` au vert dans **Apache Airflow UI (`http://localhost:8088`)**.
* **`03:10 – 03:54` | Data Lake Medallion & Rapport d'Audit** — Exploration des couches `data_lake/bronze/`, `silver/`, `gold/` et `rejected/`, puis ouverture du rapport synthétique généré (`04_batch_airflow/RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md`).
