# 💳 Real-Time Fraud Detection & Streaming Analytics Pipeline

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-KRaft_7.5-231F20?logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Airflow](https://img.shields.io/badge/Apache_Airflow-2.8+-017CEE?logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![PCI-DSS](https://img.shields.io/badge/Compliance-PCI--DSS_v4.0-success)](#-sécurité-gouvernance--conformité-pci-dss)

> **Enterprise Data & AI Architecture**  
> **Auteur :** Chris GILLERON — Lead Data & AI Architect  
> **Dépôt Officiel :** [https://github.com/Elkristobal59/CERTIFICATION_AIA](https://github.com/Elkristobal59/CERTIFICATION_AIA)  
> **Support d'Architecture :** [`ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pptx`](ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pptx)

---

## 🎯 1. Contexte Métier & Enjeux Opérationnels

La fraude aux transactions par carte bancaire représente plus d'**un milliard d'euros de pertes annuelles** au sein de l'Union Européenne (Rapport BCE). Pour les institutions financières et plateformes de paiement, le défi consiste à intercepter les transactions frauduleuses **à la volée** avant confirmation de la transaction, sans dégrader l'expérience utilisateur des clients légitimes.

Ce projet implémente une **infrastructure de données de bout en bout** combinant :
* **Streaming Événementiel Haute Vélocité :** Transport temps réel et tolérance aux pannes via Apache Kafka.
* **Inférence Prédictive Sub-15ms :** Microservice conteneurisé haute performance prêt pour le serverless.
* **Sécurité & Privacy-by-Design :** Masquage strict des données bancaires (PCI-DSS) et pseudonymisation RGPD.
* **Data Quality Gate & Résilience :** Détection automatique des anomalies de schéma et routage Dead Letter Queue (DLQ).
* **Double Persistance Analytique & Transactionnelle :** Data Lake Bronze (Apache Parquet) et base SQL opérationnelle.
* **Orchestration Batch Matinale :** Réconciliation quotidienne automatisée, calcul de drift et KPIs de risque.

---

## 🏗️ 2. Architecture Technique Globale

```text
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          ARCHITECTURE TECHNIQUE HYBRIDE DU PIPELINE IA                            │
│                                                                                                   │
│  [SOURCES DE TRANSACTIONS]                                                                        │
│  API Live Stream / POS Terminal ┐                                                                 │
│  + Flux Replay Sécurisé         │                                                                 │
│                                 ▼                                                                 │
│                    ┌─────────────────────────┐                                                    │
│                    │  PRODUCER KAFKA (KRaft) │ (Nettoyage & Sérialisation JSON)                   │
│                    └────────────┬────────────┘                                                    │
│                                 │ Publie vers topic 'raw-transactions'                            │
│                                 ▼                                                                 │
│                    ┌─────────────────────────┐                                                    │
│                    │   BROKER APACHE KAFKA   │ ◄── Interface Web Kafka UI (http://localhost:8085) │
│                    │    (3 Partitions)       │                                                    │
│                    └────────────┬────────────┘                                                    │
│                                 │                                                                 │
│                ┌────────────────┴────────────────┐                                                │
│                │ (Payload Valide)                │ (Payload Corrompu / Anomalie)                  │
│                ▼                                 ▼                                                │
│   ┌─────────────────────────┐       ┌─────────────────────────┐                                   │
│   │ CONSUMER & SCORING ML   │       │ DEAD LETTER QUEUE (DLQ) │                                   │
│   │ • Contrôle Schéma       │       │ • Topic 'fraud-dlq'     │                                   │
│   │ • API FastAPI HTTP      │       │ • Table SQL DLQ         │                                   │
│   └────────────┬────────────┘       └─────────────────────────┘                                   │
│                │                                                                                  │
│        ┌───────┴───────────────────────┐                                                          │
│        ▼                               ▼                                                          │
│ ┌──────────────┐             ┌─────────────────────┐                                              │
│ │  ALERTE 🚨   │             │   DUAL PERSISTENCE  │                                              │
│ │ Immédiate    │             │ 1. Data Lake Bronze │ ➔ Parquet horodaté partitionné               │
│ │ Console & Log│             │ 2. BDD SQL          │ ➔ Transactions enrichies & masquées          │
│ └──────────────┘             └──────────┬──────────┘                                              │
│                                         │                                                         │
│                                         ▼                                                         │
│                              ┌─────────────────────┐                                              │
│                              │  DAG APACHE AIRFLOW │ (Batch Matinal Quotidien 06h00 UTC)          │
│                              │  Audit & Reporting  │ ➔ Synthèse KPIs, Taux & Volume Sauvegardé    │
│                              └─────────────────────┘                                              │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📂 3. Organisation Modulaire du Code

```text
├── .gitignore                                 # Exclusion des données brutes volumineuses et secrets
├── README.md                                  # Documentation technique de référence
├── ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pptx     # Support de présentation d'architecture
├── sample_fraud_data.csv                      # Échantillon de données prêt pour les tests
│
├── 01_train/                                  # Entraînement ML & Tracking d'expérimentation
│   ├── train_model.py                         # Algorithme HistGradientBoosting + Tracking MLflow
│   ├── fraud_model.joblib                     # Artefact de production sérialisé
│   └── model_metadata.json                    # Métriques de performance (Recall: 92.4%, ROC-AUC: 0.986)
│
├── 02_api/                                    # Microservice d'inférence temps réel (FastAPI)
│   ├── app.py                                 # Routes /health, /predict, /predict-raw
│   ├── Dockerfile                             # Conteneurisation multi-stage ultra-légère
│   ├── cloudbuild.yaml                        # Configuration CI/CD Google Cloud Build
│   ├── deploy_cloud_run.sh                    # Script de déploiement Serverless (Linux/macOS)
│   ├── deploy_cloud_run.ps1                   # Script de déploiement Serverless (PowerShell)
│   └── requirements.txt                       # Dépendances de production épinglées
│
├── 03_pipeline_streaming/                     # Tuyauterie événementielle Apache Kafka
│   ├── producer.py                            # Ingestion continue et publication dans Kafka
│   ├── consumer.py                            # Consommation des messages, scoring et persistence
│   ├── alert_service.py                       # Moteur d'alerte flash et journalisation immuable
│   └── docker-compose.kafka.yml               # Cluster Kafka KRaft + Kafka UI
│
├── 04_batch_airflow/                          # Batch d'audit matinal et réconciliation
│   ├── daily_fraud_audit_dag.py               # Définition du DAG planifié à 06h00 UTC
│   ├── run_daily_audit.py                     # Exécuteur autonome du rapport matinal
│   └── RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md     # Rapport consolidé généré pour la direction
│
└── 05_database/                               # Persistance relationnelle & DDL
    ├── schema.sql                             # DDL SQL (transactions, fraud_alerts, DLQ, audit)
    ├── db_manager.py                          # Client SQL ACID + partitionnement Parquet Data Lake
    └── fraud_pipeline.db                      # Base opérationnelle
```

---

## ⚡ 4. Guide de Démarrage & Exécution

### Prérequis Système :
* **Docker & Docker Compose** installés et actifs.
* **Python 3.10+** avec environnement virtuel recommandé.
* Dépendances Python installées :
```bash
pip install -r 02_api/requirements.txt confluent-kafka pyarrow
```

---

### Étape 1 : Démarrer le Cluster Kafka & l'API d'Inférence

1. **Lancer le broker Kafka KRaft et son interface web :**
```bash
docker compose -f 03_pipeline_streaming/docker-compose.kafka.yml up -d
```
> 💡 *Accédez au Dashboard Kafka UI : [http://localhost:8085](http://localhost:8085)*

2. **Lancer le microservice d'inférence conteneurisé :**
```bash
docker build -t fraud-scoring-api:latest -f 02_api/Dockerfile .
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest
```
> 💡 *Vérification du service : `curl http://localhost:8080/health`*

---

### Étape 2 : Lancer le Pipeline de Streaming

Dans un premier terminal, démarrez le **Consommateur de streaming** :
```bash
python 03_pipeline_streaming/consumer.py
```
*Le consommateur écoute le topic `raw-transactions`, valide le schéma de chaque message, appelle l'API d'inférence, route les anomalies vers la DLQ, masque les cartes selon PCI-DSS et persiste dans le Data Lake Parquet.*

Dans un second terminal, démarrez le **Producteur d'événements** :
```bash
python 03_pipeline_streaming/producer.py
```
*Le producteur interroge les flux de paiement et publie les transactions en continu dans Kafka.*

---

### Étape 3 : Exécuter l'Audit Matinal Quotidien

Pour déclencher le calcul batch des KPIs de la veille (DAG Apache Airflow) :
```bash
python 04_batch_airflow/run_daily_audit.py
```
*Génère le rapport de synthèse exécutif dans `04_batch_airflow/RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md`.*

---

## 🛡️ 5. Sécurité, Gouvernance & Conformité PCI-DSS

### Masquage Strict des Données Bancaires (PCI-DSS v4.0) :
Le numéro de carte bancaire (PAN) ne transite jamais et n'est **jamais stocké en clair** :
* Application de la règle des **6 premiers (BIN) et 4 derniers chiffres** : `453288******9812`.
* Pseudonymisation cryptographique des identités porteurs (Privacy-by-Design RGPD).

### Résilience & Dead Letter Queue (DLQ) :
Tout événement corrompu (montant négatif, schéma JSON invalide, données tronquées) est automatiquement isolé :
* Topic Kafka dédié : `fraud-dlq`.
* Table d'audit SQL : `dead_letter_queue`.
* Le pipeline principal continue son exécution sans blocage ni perte de données.

---

## ☁️ 6. Déploiement Cloud Serverless (GCP Cloud Run)

Pour basculer du runtime local au cloud managé, le service d'inférence s'intègre nativement à Google Cloud Run avec politique de **Scale-to-Zero** :
* **Facturation à l'usage strict** : `min-instances: 0` (0 € hors requête active).
* **Mise à l'échelle automatique** : jusqu'à 5 instances sous forte charge.
* **Script de déploiement automatisé :**
```bash
bash 02_api/deploy_cloud_run.sh
```
Ou via PowerShell :
```powershell
.\02_api\deploy_cloud_run.ps1 -ProjectId "votre-projet-gcp"
```

---

## 📈 7. Performances & Métriques du Modèle

* **Algorithme :** `HistGradientBoostingClassifier` avec rééquilibrage de classes.
* **ROC-AUC :** `0.9866`
* **Rappel Fraude (Recall) :** `92.4 %` des transactions frauduleuses interceptées.
* **Latence moyenne d'inférence :** `< 15 ms` par requête.
* **Traçabilité :** Paramètres, métriques et artefacts loggués dans MLflow avec enregistrement dans le Model Registry.
