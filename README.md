# Certification Architecte en Intelligence Artificielle (RNCP 41993 - Niveau 7)

Dépôt officiel des livrables et projets techniques présentés dans le cadre de la certification professionnelle d'**Architecte en Intelligence Artificielle (RNCP 41993 — Niveau 7 / Bac+5)** délivrée par **Jedha Bootcamp** (France Compétences).

* **Candidat :** Christopher GILLERON

---

## Vue d'ensemble des 4 Blocs de Compétences

Ce dépôt centralise les travaux d'ingénierie, architectures, codes sources et livrables officiels répartis selon les **4 blocs du référentiel RNCP 41993** :

| Bloc | Intitulé officiel | Cas d'étude / Projet | Format Soutenance | Emplacement / Dépôt |
| :---: | :--- | :--- | :---: | :--- |
| **Bloc 1** | Concevoir et piloter la gouvernance des données et des systèmes d'IA | **Spotify** (Gouvernance Data & IA, DMBOK, RGPD/AI Act) | 15 min + 15 min Q&A | [`01_BLOC_1_GOUVERNANCE_SPOTIFY/`](./01_BLOC_1_GOUVERNANCE_SPOTIFY/) |
| **Bloc 2** | Concevoir et déployer l'infrastructure de données et de calcul pour l'IA | **Stripe** (Architecture Cloud Souveraine AWS `< 100 ms`) | 5 min + 15 min Q&A | [`02_BLOC_2_ARCHITECTURE_STRIPE/`](./02_BLOC_2_ARCHITECTURE_STRIPE/) |
| **Bloc 3** | Concevoir et mettre en œuvre des pipelines de données pour l'IA | **Fraud Detection** (Streaming Kafka KRaft, FastAPI & Batch Airflow) | 5 min + 15 min Q&A | [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/`](./03_BLOC_3_PIPELINE_FRAUD_DETECTION/) |
| **Bloc 4** | Concevoir et piloter l'industrialisation et le déploiement de solutions d'IA | **CliNER-MLOps** (RAG BioBERT, Qwen2.5-7B QLoRA, Drift & FinOps) | 5 min + 10 min Q&A | [`04_BLOC_4_MLOPS_CLINER/`](./04_BLOC_4_MLOPS_CLINER/) & [Dépôt `cliner-mlops`](https://github.com/Elkristobal59/cliner-mlops) |

---

## 1. Bloc 1 — Gouvernance des Données et des Systèmes d'IA (Spotify)

* **Objectif :** Définir et piloter une stratégie globale de gouvernance des données et des systèmes d'IA ainsi que la conformité réglementaire multi-juridictionnelle (**RGPD, CCPA, PCI-DSS v4.0, EU AI Act**) pour une plateforme mondiale de streaming musical (180 pays).
* **Composants clés :**
  * **Audit de maturité Gartner & DAMA-DMBOK2 sur les 10 dimensions :** Niveau global initial **2 / 5 ("Réactive")** (moyenne **2,2 / 5**, avec *Data Architecture* et *Analytics & BI* au niveau 3, *Usage & Accessibilité* à 2,5, et *Metadata Management* à 1,5) vers une cible **Niveau 4 / 5 ("Managed")** (pilote 6 mois → généralisation Groupe 12 mois).
  * **10 Politiques de gouvernance DMBOK & Écosystème d'outillage intégré :** *OpenMetadata / Collibra* (Data Catalog & Lineage), *Talend Data Quality* (profiling & standard ISO-8601), *OneTrust* (automatisation SARs & Droit à l'Oubli < 30 jours), *Splunk SIEM* (sécurité PCI-DSS & alerte brèche < 72h), *DVC / MLflow* (traçabilité IA *Discover Weekly*).
  * **Organisation en CoE Hybride (Hub & Spoke) & Matrice RACI :** Définition des rôles (`CDO`, `DPO`, `Data Owners`, `Data Stewards`, `Data Custodians`) et matrice RACI détaillée sur **33 tâches opérationnelles** (strictement `1 A` et `≥ 1 R` par tâche).
  * **Acculturation, conduite du changement & Inclusion du Handicap (C3) :** Programme Data Literacy accessible au standard **WCAG 2.1 Niveau AA**, lecteurs d'écran **NVDA / JAWS**, sous-titrage VTT et fiches **FALC** (*Facile à Lire et à Comprendre*).
* **Livrables :** Dossier maître et rapports Word (`.docx`), grilles d'audit Gartner (10 dimensions), RACI (33 tâches) et Checklist conformité (17 contrôles RGPD/CCPA/PCI-DSS/EU AI Act) sous Excel (`.xlsx`), schéma RACI et présentation exécutive 16:9 (11 slides `.pptx`).
* **Accès :** [`01_BLOC_1_GOUVERNANCE_SPOTIFY/LIVRABLES/`](./01_BLOC_1_GOUVERNANCE_SPOTIFY/LIVRABLES/) (synthèse : [`01_BLOC_1_GOUVERNANCE_SPOTIFY/README.md`](./01_BLOC_1_GOUVERNANCE_SPOTIFY/README.md))

---

## 2. Bloc 2 — Infrastructure de Données et de Calcul pour l'IA (Stripe)

* **Objectif :** Concevoir une architecture Cloud souveraine sur **AWS Paris (`eu-west-3`)** capable d'absorber **15 millions de transactions/jour** en réconciliant trois mondes de données (**OLTP, OLAP, NoSQL**) sous une contrainte d'inférence IA **Stripe Radar `< 100 ms` (`95 ms p99`)**.
* **Composants clés :**
  * **Cœur transactionnel OLTP en 3e Forme Normale (3NF ACID) :** **Amazon Aurora PostgreSQL Multi-AZ** (Quorum 4/6 sur 3 AZs, **RPO = 0**, **RTO < 60s**) structuré autour de **12 tables** (montants en entiers `BIGINT` en centimes, clé `idempotency_key` anti-double débit, abonnements `Subscription` et tables de référence).
  * **Entrepôt analytique OLAP en Schéma en Étoile (*Star Schema*) :** **Amazon Redshift Serverless** comprenant **4 tables de faits**, **1 table de synthèse pré-agrégée (`AggMonthlyProductPerformance`)** et **7 dimensions** avec clés de substitution (*Surrogate Keys*), historisation **SCD Type 2** et optimisations `DISTKEY` / `SORTKEY`.
  * **Monde documentaire NoSQL multi-formats :** **Amazon DocumentDB** (compatible MongoDB) modélisé en **5 collections** (`device_fingerprints`, `clickstream_events`, `webhook_delivery_logs`, `customer_feedback`, `ml_feature_vectors`) absorbant JSON, XML ISO 20022 et références binaires avec purge automatique **TTL à 90 jours**.
  * **Pipelines CDC & Chemin critique IA (`95 ms p99`) :** Capture **Debezium CDC** sur le journal binaire WAL d'Aurora → **Amazon MSK (Kafka)** → **Apache Flink** & Data Lake **S3 Medallion** (`Bronze / Silver / Gold` Parquet) orchestré par **Airflow / dbt / Great Expectations**. Inférence en ligne combinant **Feast Online (Redis `< 5 ms`)**, **OpenSearch k-NN (`15 ms`)** et **XGBoost compilé sous ONNX Runtime CPU `c6i` (`30 ms`)**, complétée par *Adaptive Checkout*, *Smart Retries* et monitoring de dérive **Evidently AI (`PSI > 0.20`)**.
  * **Sécurité PCI-DSS v4.0 Level 1, RGPD/CCPA, FinOps & GreenOps :** Isolation **Tokenization Vault sur AWS CloudHSM**, chiffrement **AES-256 (KMS CMK)** et **TLS 1.3**, hachage **SHA-256 salé**, validation métier par **6 requêtes SQL OLAP et 5 pipelines NoSQL**, budget **~25 000 $/mois** (Savings Plans -38 %, Spot GPU -70 %) et empreinte bas-carbone Paris (`~50 g CO₂e/kWh`).
* **Livrables :** **9 rapports techniques PDF** (`00` à `08`), modèles sources **DBML** (`stripe_oltp.dbml`, `stripe_olap.dbml`), diagrammes haute définition **PNG** et présentation de soutenance (6 slides `.pptx`).
* **Accès :** [`02_BLOC_2_ARCHITECTURE_STRIPE/LIVRABLES/`](./02_BLOC_2_ARCHITECTURE_STRIPE/LIVRABLES/) (synthèse : [`02_BLOC_2_ARCHITECTURE_STRIPE/README.md`](./02_BLOC_2_ARCHITECTURE_STRIPE/README.md))

---

## 3. Bloc 3 — Pipelines de Données Temps Réel & Batch pour l'IA (Fraud Detection)

* **Objectif :** Concevoir et mettre en œuvre une architecture hybride déployée de détection de fraude bancaire conciliant **streaming temps réel sub-100 ms** (**Docker Local : Kafka KRaft, Pandera, FastAPI, MLflow, Airflow 2.11**) et **services Cloud managés** (**Neon PostgreSQL SSL `fraud_db` & `fraud_mlflow_db`, Amazon S3 `eu-west-3`, Alerting SMTP `smtplib` Mailpit / Gmail TLS**).
* **Composants clés :**
  * **Ingestion Streaming & Contrôle Qualité Pandera (C2, C3, C5) :** Producteur/Consommateur `confluent-kafka` sur broker **Apache Kafka KRaft** (`raw-transactions`). Validation stricte en entrée via **Pandera (`DataFrameSchema`)** bloquant les anomalies (ex : `amt = -150.0 €`, GPS hors bornes) et les dérivant sans interrompre le flux vers le topic **`fraud-dlq`** (après sanitisation PII via `_sanitize_payload_pii()`), la table SQL **`dead_letter_queue`** et la zone Parquet `data_lake/rejected/`.
  * **MLOps, Registry MLflow Cloud & Inférence FastAPI (C1, C2) :** Feature engineering partagé (`01_train/features.py` : montant, distance géodésique de **Haversine**, densité urbaine, heure UTC, âge) et Pipeline Scikit-Learn anti-fuite entraîné sur **555 719 transactions réelles (`fraudTest.csv`)**. Promotion automatique de **`HistGradientBoosting_Balanced` en `@champion`** (**ROC-AUC `0.9876`**, **Recall `91.61 %`**) face à `RandomForest_Balanced` en **`@challenger`** (**ROC-AUC `0.9836`**, **Recall `82.05 %`**) et `LogisticRegression` (`0.8236`, Recall `74.13 %`), tracés sur **Neon `fraud_mlflow_db`** + **AWS S3 (`eu-west-3`)**. Microservice **FastAPI** (`/predict`, `/predict-raw`, `/reload-model`) répondant en **`19.4 ms` médiane (`28.9 ms` p95)**.
  * **Sécurité PCI-DSS v4.0, RGPD Privacy-by-Design & Alerting SMTP (C4) :** Masquage PAN systématique au format **`**** **** **** 1234`**, pseudonymisation irréversible **SHA-256 salé** (`SECRET_SALT` injecté par `.env`), notification e-mail temps réel via `smtplib` dès `FRAUD_THRESHOLD = 0.50` (`BLOCK_IMMEDIATE` à `>= 0.75`) et persistance dans **Neon PostgreSQL (`fraud_db`)**.
  * **Data Lake Medallion & Orchestration Batch Apache Airflow 2.11 (C3, C5) :** Stockage Parquet Snappy partitionné `year=/month=/day=` (`bronze/`, `silver/` expurgé des 7 colonnes PII directes, `gold/`, `rejected/`), DAG matinal **`daily_fraud_audit_pipeline`** (06h00 UTC, 3 tâches validées en conteneur) et traçabilité bout-en-bout **OpenLineage v1** (`openlineage_events.jsonl`).
* **Livrables & Code :** Code source complet (`01_train/`, `02_api/`, `03_pipeline_streaming/`, `04_batch_airflow/`, `05_database/`, `docker-compose.yml`), schéma d'architecture PNG, rapport d'architecture PDF, présentation de soutenance (7 slides `.pptx` / `.pdf`) et guide de démonstration vidéo PDF.
* **Démo vidéo publique (3 min 54 s — Google Drive) :** https://drive.google.com/file/d/1nUORFhIksV191HoE_yuvA1I3GrJLSQNe/view?usp=sharing
* **Accès :** [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/`](./03_BLOC_3_PIPELINE_FRAUD_DETECTION/) (guide complet : [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/README.md`](./03_BLOC_3_PIPELINE_FRAUD_DETECTION/README.md))

---

## 4. Bloc 4 — Industrialisation, Déploiement & MLOps (CliNER-MLOps)

* **Objectif :** Industrialiser en production une plateforme Cloud hybride d'extraction automatique de critères d'éligibilité d'essais cliniques (**Clinical NER & RAG**) avec détection de dérive non supervisée, réentraînement continu **QLoRA** et gouvernance **FinOps Auto-Kill**.
* **Dépôt GitHub dédié (Code applicatif, Terraform & CI/CD) :** 👉 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**
* **Composants clés :**
  * **Jeu de données CHIA & Architecture RAG Hybride :** Benchmark médical **CHIA** (*Nature 2020*, `1 000` études, `12 409` critères, `41 000+` entités, **9 classes** cibles, split hermétique sans fuite `800` train / `200` test). Découplage entre l'encodeur **BioBERT figé (768d)** indexé sous **Supabase `pgvector` HNSW** (`12 ms`, Top-5 chunks NER / Top-15 Chatbot RAG) et le génératif **Qwen2.5-7B fine-tuné en QLoRA 4-bit NF4** (`r=16, α=32`, adaptateur de **84 Mo** vs 15 Go, Loss `1.450 → 0.284`, **F1 Exact Match `58,3 %`**, inférence **vLLM `< 3 s`** et cache SQL `clinical_ner_cache` en `0,01 s`).
  * **Déploiement Cloud Hybride, IaC Terraform & CI/CD GitHub Actions :** Frontend Streamlit à 4 onglets sur **Render (`0 €`)**, API FastAPI (7 endpoints documentés sous Swagger `/docs`) & moteur GPU sur **AWS EC2 `g4dn.xlarge` (Tesla T4)**, Data Lake & Registry LoRA sur **AWS S3 (`cliner-mlops`)**, **MLflow sur Google Cloud Run (`Scale-to-Zero 0 €`)**, provisionnés par **Terraform** (`terraform/main.tf`). Pipeline CI/CD (`ci_mlops.yml`, `weekly_mlops_pipeline.yml`, `deploy_ec2_autokill.yml`) exécutant `flake8`, **11 tests PyTest** et les builds Docker.
  * **Monitoring de Dérive Wasserstein, Rollback S3 & FinOps Auto-Kill :** Surveillance non supervisée par **distance de Wasserstein (`W₁ > 0.08`)** sur embeddings BioBERT (`drift_detection.py`, dérive mesurée à `0.0949`), rapport HTML/JSON **Evidently AI** (`monitoring_evidently.py`), journaux d'audit **XML ISO 13485 & RGPD** (`/logs/xml`), **Rollback Zero-Downtime `vN-1`** sur S3 et **double ceinture Auto-Kill EC2** (`finally:` Python + `if: always()` CI/CD = **`0,18 $` par session** au lieu de `400 $/mois`).
* **Livrables de soutenance :** Support officiel de soutenance (6 slides `.pptx` et `.pdf`), fiche liens [`LIEN_REPO_GITHUB_CLINER_MLOPS.pdf`](./04_BLOC_4_MLOPS_CLINER/LIVRABLES/LIEN_REPO_GITHUB_CLINER_MLOPS.pdf) et [`LIENS_GITHUB_ET_DEMO.txt`](./04_BLOC_4_MLOPS_CLINER/LIVRABLES/LIENS_GITHUB_ET_DEMO.txt) dans [`04_BLOC_4_MLOPS_CLINER/LIVRABLES/`](./04_BLOC_4_MLOPS_CLINER/LIVRABLES/) (synthèse : [`04_BLOC_4_MLOPS_CLINER/README.md`](./04_BLOC_4_MLOPS_CLINER/README.md)).
* **Application & MLflow en production :** `https://cliner-mlops.onrender.com/` | `https://mlflow-cliner-mlops-1054740171053.europe-west9.run.app`

---

## Structure du Dépôt

```text
CERTIFICATION_AIA/
├── 01_BLOC_1_GOUVERNANCE_SPOTIFY/
│   ├── LIVRABLES/         # Dossier maître Word, politiques DMBOK, grilles Gartner/RACI/Checklist Excel, slides PPTX
│   └── README.md          # Synthèse du projet de gouvernance et cadre méthodologique
├── 02_BLOC_2_ARCHITECTURE_STRIPE/
│   ├── LIVRABLES/         # 9 rapports techniques PDF (00 à 08), modèles DBML/PNG et présentation PPTX
│   └── README.md          # Synthèse de l'architecture Cloud AWS souveraine et du SLA < 100 ms
├── 03_BLOC_3_PIPELINE_FRAUD_DETECTION/
│   ├── LIVRABLES/         # Schéma PNG, rapport technique PDF, support PPTX/PDF, guide démo vidéo PDF
│   ├── 01_train/          # Feature engineering partagé (features.py) et entraînement MLflow (train_model.py)
│   ├── 02_api/            # Microservice FastAPI conteneurisé (/predict, /predict-raw, /reload-model)
│   ├── 03_pipeline_streaming/ # Producteur/Consommateur Kafka KRaft, Pandera Quality Gate, DLQ & Alerting SMTP
│   ├── 04_batch_airflow/  # DAG Apache Airflow 2.11 (daily_fraud_audit_pipeline) et traçabilité OpenLineage
│   ├── 05_database/       # Schéma PostgreSQL Neon, masquage PCI-DSS, SHA-256 salé & Data Lake Medallion Parquet
│   ├── docker-compose.yml # Orchestration multi-conteneurs (Kafka, MLflow, FastAPI, Airflow, Mailpit)
│   ├── run_full_pipeline_demo.py # Démonstrateur de bout en bout du pipeline
│   └── README.md          # Documentation technique complète du Bloc 3
├── 04_BLOC_4_MLOPS_CLINER/
│   ├── LIVRABLES/         # Support de présentation officiel PPTX et PDF (6 slides)
│   └── README.md          # Synthèse de l'architecture MLOps et lien vers https://github.com/Elkristobal59/cliner-mlops
└── README.md              # Ce document (Présentation générale des 4 Blocs RNCP 41993)
```

---

## Format de l'Épreuve Orale (RNCP 41993 — 1h25 Séquentiel)

L'examen final se déroule sous la forme d'une soutenance orale séquentielle continue de **85 minutes (1h25)** couvrant les 4 blocs de compétences :
* **Bloc 1 (Gouvernance — Spotify) :** 15 min de présentation + 15 min de questions/réponses *(30 min)*
* **Bloc 2 (Architecture — Stripe) :** 5 min de présentation + 15 min de questions/réponses *(20 min — 100 % conception)*
* **Bloc 3 (Pipelines — Fraud Detection) :** 5 min de présentation + 15 min de questions/réponses *(20 min — pipeline déployé)*
* **Bloc 4 (MLOps — CliNER-MLOps) :** 5 min de présentation + 10 min de questions/réponses *(15 min — application & MLOps en production)*
