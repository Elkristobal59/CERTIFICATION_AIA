# Certification Architecte en Intelligence Artificielle (RNCP 41993 - Niveau 7)

Dépôt officiel des livrables et projets techniques présentés dans le cadre de la certification professionnelle d'Architecte en Intelligence Artificielle (Jedha Bootcamp / France Compétences).

---

## Vue d'ensemble des 4 Blocs de Compétences

Ce dépôt centralise les travaux d'ingénierie, architectures, codes sources et livrables officiels répartis selon les 4 blocs du référentiel RNCP 41993 :

| Bloc | Intitulé officiel | Cas d'étude / Projet | Nature de l'épreuve | Statut | Emplacement / Dépôt |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **Bloc 1** | Concevoir et piloter la gouvernance des données et des systèmes d'IA | **Spotify** (Gouvernance & RGPD) | Dossier écrit & Soutenance (15 min pitch + 15 min Q&A) | Prêt | [`01_BLOC_1_GOUVERNANCE_SPOTIFY/`](./01_BLOC_1_GOUVERNANCE_SPOTIFY/) |
| **Bloc 2** | Concevoir et déployer l'infrastructure de données et de calcul pour l'IA | **Stripe** (Architecture Cloud Souveraine) | Dossier de conception (5 min pitch + 15 min Q&A) | Prêt | [`02_BLOC_2_ARCHITECTURE_STRIPE/`](./02_BLOC_2_ARCHITECTURE_STRIPE/) |
| **Bloc 3** | Concevoir et mettre en œuvre des pipelines de données pour l'IA | **Fraud Detection** (Streaming Kafka & Batch) | Infrastructure déployée & Démo (5 min pitch + 15 min Q&A) | Prêt | [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/`](./03_BLOC_3_PIPELINE_FRAUD_DETECTION/) |
| **Bloc 4** | Concevoir et piloter l'industrialisation et le déploiement de solutions d'IA | **CliNER-MLOps** (LLM LoRA & Drift) | Application en production & MLOps (5 min pitch + 10 min Q&A) | Prêt | [Dépôt dédié `cliner-mlops`](https://github.com/Elkristobal59/cliner-mlops) |

---

## 1. Bloc 1 — Gouvernance des Données et Systèmes d'IA (Spotify)

* **Objectif :** Définir et piloter une stratégie globale de gouvernance des données et de conformité réglementaire (RGPD, CCPA, AI Act) pour un service de streaming musical à grande échelle.
* **Composants clés :**
  * Évaluation de maturité selon le framework Gartner & DAMA-DMBOK2 (score initial 1.8/5 cible 3.8/5).
  * Matrice RACI opérationnelle sur 33 tâches critiques et organisation en CoE Hybride (Hub & Spoke).
  * Traitement des demandes d'accès (SARs Article 15 RGPD) et politique de minimisation des données.
  * Projet pilote sur le système de recommandation musicale et traçabilité des modèles (DVC / MLflow).
* **Livrables :** Rapport maître au format Word/PDF, support de soutenance 16:9 (`.pptx`), annexes d'audit Excel.
* **Accès :** [`01_BLOC_1_GOUVERNANCE_SPOTIFY/LIVRABLES/`](./01_BLOC_1_GOUVERNANCE_SPOTIFY/LIVRABLES/)

---

## 2. Bloc 2 — Architecture Data & Calcul pour l'IA (Stripe)

* **Objectif :** Concevoir une architecture cloud souveraine sur AWS (Région Paris `eu-west-3`) pour l'évaluation du risque de transaction en temps réel avec un SLA inférieur à 100 ms.
* **Composants clés :**
  * Cœur transactionnel OLTP en 3e Forme Normale (Aurora PostgreSQL, réplication Multi-AZ).
  * Isolation bancaire conforme PCI-DSS Level 1 (Card Vault CloudHSM, chiffrement AES-256 CMK).
  * Streaming asynchrone via Debezium CDC et Kafka MSK pour découpler la production de l'analytique.
  * Entrepôt décisionnel Redshift Serverless modélisé en Schéma en Étoile (3 faits, 6 dimensions).
  * Inférence d'IA sous 30 ms via FastAPI et ONNX Runtime sur CPU optimisés (c6i), couplé au Feature Store Feast (Redis).
* **Livrables :** 9 rapports techniques d'architecture au format PDF, schémas relationnels et dimensionnels (DBML et PNG), présentation de soutenance (`.pptx`).
* **Accès :** [`02_BLOC_2_ARCHITECTURE_STRIPE/LIVRABLES/`](./02_BLOC_2_ARCHITECTURE_STRIPE/LIVRABLES/)

---

## 3. Bloc 3 — Pipeline de Streaming & Détection de Fraude (Kafka)

* **Objectif :** Déployer une chaîne complète de traitement de données temps réel et batch pour intercepter les transactions frauduleuses avant débit bancaire.
* **Composants clés :**
  * Ingestion streaming via cluster Apache Kafka en mode KRaft (3 partitions).
  * Modèle de Machine Learning (`HistGradientBoostingClassifier`, Scikit-Learn) entraîné sur 555 719 transactions réelles (ROC-AUC : 0.986, inférence unitaire < 4 ms).
  * API de scoring REST FastAPI conteneurisée (Docker).
  * Résilience par Dead Letter Queue (`fraud-dlq`) pour l'isolation des messages corrompus.
  * Double persistance : stockage colonne partitionné (Data Lake Parquet Snappy) et base relationnelle d'audit.
  * Réconciliation quotidienne par batch ordonnancé via Apache Airflow.
* **Livrables & Code :** Code source complet (`01_train`, `02_api`, `03_pipeline_streaming`, `04_batch_airflow`, `05_database`), rapport technique PDF, présentation PPTX/PDF, fiche de démonstration vidéo.
* **Accès :** [`03_BLOC_3_PIPELINE_FRAUD_DETECTION/`](./03_BLOC_3_PIPELINE_FRAUD_DETECTION/)

---

## 4. Bloc 4 — Industrialisation, Déploiement & MLOps (CliNER-MLOps)

* **Objectif :** Industrialiser en environnement de production une solution d'IA médicale pour l'extraction d'entités cliniques (Clinical NER) avec monitoring continu et réentraînement automatisé.
* **Dépôt GitHub de l'application & CI/CD :** 👉 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**
* **Composants clés :**
  * Architecture bicéphale : Embedder figé (BioBERT) et LLM génératif fine-tuné par adaptateur LoRA (Qwen-7B / PEFT).
  * Détection de dérive (Data & Concept Drift) basée sur la distance de Wasserstein sur les embeddings de protocoles cliniques récents.
  * Déclenchement automatique de réentraînement sur instance GPU AWS EC2 (`g4dn.xlarge`) avec protocole FinOps d'auto-arrêt.
  * Workflows CI/CD GitHub Actions (`ci_mlops.yml`, `deploy_frontend.yml`, `deploy_backend_aws.yml`) et Model Registry MLflow.
* **Livrables de soutenance :** Support de présentation officiel (`.pdf` et `.pptx`) dans [`04_BLOC_4_MLOPS_CLINER/LIVRABLES/`](./04_BLOC_4_MLOPS_CLINER/LIVRABLES/).

---

## Structure du Dépôt

```text
CERTIFICATION_AIA/
├── 01_BLOC_1_GOUVERNANCE_SPOTIFY/
│   ├── LIVRABLES/         # Dossier maître Word/PDF, politiques DMBOK, RACI, présentation PPTX
│   └── README.md          # Synthèse du projet et cadre méthodologique
├── 02_BLOC_2_ARCHITECTURE_STRIPE/
│   ├── LIVRABLES/         # 9 rapports techniques PDF, présentation PPTX, modèles DBML/PNG
│   └── README.md          # Synthèse d'architecture cloud et SLA de latence
├── 03_BLOC_3_PIPELINE_FRAUD_DETECTION/
│   ├── LIVRABLES/         # Rapport technique PDF, support PPTX/PDF, fiche démo vidéo
│   ├── 01_train/          # Scripts et modèle de scoring entraîné
│   ├── 02_api/            # Microservice FastAPI Dockerisé
│   ├── 03_pipeline_streaming/ # Broker Kafka, Consumer, Alerting, DLQ
│   ├── 04_batch_airflow/  # DAG d'audit matinal et réconciliation
│   ├── 05_database/       # Gestionnaire de base de données relationnelle
│   ├── run_full_pipeline_demo.py # Script d'exécution de la démonstration
│   └── README.md          # Guide technique de reproduction pas à pas
├── 04_BLOC_4_MLOPS_CLINER/
│   ├── LIVRABLES/         # Support de présentation PPTX et PDF
│   └── README.md          # Architecture MLOps et renvoi vers https://github.com/Elkristobal59/cliner-mlops
└── README.md              # Ce document
```

---
