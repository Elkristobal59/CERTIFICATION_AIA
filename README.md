# 💳 Bloc 3 — Concevoir & Mettre en Œuvre un Pipeline de Données pour l'IA (Real-Time Fraud Detection) ⚡

> **Titre Officiel :** Architecte en Intelligence Artificielle (Niveau 7 - Bac+5, RNCP 41993)  
> **Bloc de Compétence :** Bloc 3 — Déploiement de Pipelines de Transformation & Streaming pour l'IA  
> **Étude de Cas Officielle :** Automatic Fraud Detection 🥷  
> **Auteur & Candidat :** Chris GILLERON  
> **Dépôt GitHub Officiel :** [https://github.com/Elkristobal59/CERTIFICATION_AIA](https://github.com/Elkristobal59/CERTIFICATION_AIA)  
> **Présentation d'Architecture (Livrable 1) :** [ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pptx](file:///d:/AIL-FT-02/CERTIF%20AIL/FRAUD_DETECTION_BLOC_3/ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pptx)  

---

## 🧭 1. Synthèse des 5 Compétences Évaluées par le Jury (RNCP 41993 - Bloc 3)

| Compétence RNCP | Intitulé Officiel | Implémentation Industrielle dans ce Projet |
| :--- | :--- | :--- |
| **C1** | **Système temps réel (vélocité, volume)** | Broker **Apache Kafka KRaft** (3 partitions) traitant les flux continus de l'API live HuggingFace avec débit garanti et tolérance aux pannes. |
| **C2** | **ETL/ELT entre différentes bases** | Double flux de stockage : Ingestion brute partitionnée en **Apache Parquet dans le Data Lake Bronze** (`data_lake/bronze/year=YYYY/...`) + persistance transactionnelle ACID en base SQL. |
| **C3** | **Automatisation des flux** | Inférence automatisée via microservice **FastAPI conteneurisé (Docker / GCP Cloud Run)** + batch matinal quotidien d'audit planifié par **Apache Airflow DAG** (06h00 UTC). |
| **C4** | **Surveillance, gouvernance & sécurité** | **Conformité stricte PCI-DSS v4.0** : troncature des cartes bancaires (6 premiers + 4 derniers chiffres : `453288******9812`) et pseudonymisation RGPD des identités. Alertes flash temps réel immédiates (< 15 ms). |
| **C5** | **Contrôle qualité & résilience** | Data Quality Gate avec validation de schéma Pydantic, rejet des anomalies (montants négatifs, corruptions) et routage automatique vers la **Dead Letter Queue (DLQ `fraud-dlq`)**. |

---

## 🏗️ 2. Architecture Technique Globale de Bout en Bout

```text
┌───────────────────────────────────────────────────────────────────────────────────────────────────┐
│                          ARCHITECTURE TECHNIQUE HYBRIDE DU PIPELINE IA                            │
│                                                                                                   │
│  [SOURCE API LIVE]                                                                               │
│  API HuggingFace Stream ────────┐                                                                 │
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
│                │ (Flux valide)                   │ (Payload corrompu / anomalie)                  │
│                ▼                                 ▼                                                │
│   ┌─────────────────────────┐       ┌─────────────────────────┐                                   │
│   │ CONSUMER & SCORING ML   │       │ DEAD LETTER QUEUE (DLQ) │                                   │
│   │ • Contrôle Schéma       │       │ • Topic 'fraud-dlq'     │                                   │
│   │ • API FastAPI Cloud Run │       │ • Table SQL DLQ         │                                   │
│   └────────────┬────────────┘       └─────────────────────────┘                                   │
│                │                                                                                  │
│        ┌───────┴───────────────────────┐                                                          │
│        ▼                               ▼                                                          │
│ ┌──────────────┐             ┌─────────────────────┐                                              │
│ │  ALERTE 🚨   │             │   DUAL PERSISTENCE  │                                              │
│ │ Console & Log│             │ 1. Data Lake Bronze │ ➔ Parquet horodaté partitionné               │
│ │ Immédiate    │             │ 2. BDD SQL          │ ➔ Transactions enrichies & masquées          │
│ └──────────────┘             └──────────┬──────────┘                                              │
│                                         │                                                         │
│                                         ▼                                                         │
│                              ┌─────────────────────┐                                              │
│                              │  DAG APACHE AIRFLOW │ (Batch Matinal Quotidien 06h00 UTC)          │
│                              │  Rapport d'Audit    │ ➔ KPI Fraudes, Drift, Taux & Volume Sauvé    │
│                              └─────────────────────┘                                              │
└───────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ☁️ 3. Déploiement Serverless sur Google Cloud Run (GCP)

L'API d'inférence est conçue selon le paradigme **Serverless / Scale-to-Zero** conformément aux cours de Mehdi Semar :
* **Zéro coût hors charge (`min-instances: 0`)** : le conteneur s'éteint complètement quand aucun trafic n'est reçu.
* **Auto-scaling instantané** : passage à 1, 2 ou 5 instances dès qu'un pic de transactions survient.
* **Latence d'inférence** : < 15 millisecondes par requête.

### Déploiement via le script fourni :
```bash
# Avec Google Cloud SDK
bash 02_api/deploy_cloud_run.sh
```
Ou avec PowerShell sur Windows :
```powershell
.\02_api\deploy_cloud_run.ps1 -ProjectId "votre-projet-gcp"
```

### Exécution locale avec Docker Desktop (Réplique exacte de Cloud Run) :
```bash
# 1. Build du conteneur API
docker build -t fraud-scoring-api:latest -f 02_api/Dockerfile .

# 2. Lancement sur le port 8080 (port standard Cloud Run)
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest

# 3. Test du Healthcheck
curl http://localhost:8080/health
```

---

## 🛡️ 4. Sécurité, PCI-DSS & Contrôle Qualité (C4 & C5)

### Troncature & Masquage PCI-DSS v4.0 :
Les numéros de carte de crédit ne sont **jamais stockés ni loggués en clair** :
```python
# db_manager.py & alert_service.py
def mask_credit_card(cc_num):
    # Conserve les 6 premiers (BIN) et les 4 derniers chiffres
    return f"{s[:6]}{'*' * (len(s) - 10)}{s[-4:]}" # Ex: 453288******9812
```

### Dead Letter Queue (DLQ) & Isolation des Erreurs :
Toute transaction malformée (ex: montant négatif, payload non JSON, attributs manquants) est interceptée par la couche de validation et redirigée vers la DLQ :
* **Topic Kafka :** `fraud-dlq`
* **Table SQL :** `dead_letter_queue`
* Permet aux flux sains de continuer à circuler sans interruption de service.

---

## 🚀 5. Guide de Lancement Pas-à-Pas pour la Démonstration & Vidéo

### Prérequis :
1. **Docker Desktop** démarré.
2. Lancer le cluster Kafka KRaft :
```bash
docker compose -f 03_pipeline_streaming/docker-compose.kafka.yml up -d
```
> 💡 *Accédez à l'interface web de supervision des topics Kafka : [http://localhost:8085](http://localhost:8085)*

3. Lancer l'API conteneurisée :
```bash
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest
```

### Lancement du Pipeline de Streaming :

1. **Démarrer le Consommateur de streaming Kafka (Terminal 1) :**
```bash
python 03_pipeline_streaming/consumer.py
```
*Écoute les transactions, appelle l'API d'inférence HTTP, filtre les anomalies vers la DLQ, masque les numéros de carte (PCI-DSS) et persiste dans le Data Lake Parquet et la base SQL.*

2. **Démarrer le Producteur de flux en temps réel (Terminal 2) :**
```bash
python 03_pipeline_streaming/producer.py
```
*Interroge en continu l'API live HuggingFace et diffuse les événements dans le topic Kafka 'raw-transactions'.*

3. **Exécuter l'Audit Matinal Quotidien (Batch DAG Apache Airflow) :**
```bash
python 04_batch_airflow/run_daily_audit.py
```
*Agrège les flux des dernières 24h et produit le rapport officiel pour les équipes Risque et Conformité.*

---

## 🎬 6. Consignes d'Enregistrement Vidéo pour l'Évaluation Julie LMS

1. **Outil d'enregistrement recommandé :** Vidyard, OBS Studio, Loom ou la barre de jeu Windows (`Win + G`).
2. **Durée de la vidéo :** 3 à 5 minutes.
3. **Contenu à filmer :**
   * L'interface Docker Desktop avec les conteneurs actifs (`kafka-fraud-broker`, `kafka-fraud-ui`, `fraud-scoring-api`).
   * L'interface web Kafka UI sur [http://localhost:8085](http://localhost:8085) montrant les topics `raw-transactions` et `fraud-dlq`.
   * Le terminal montrant la consommation en direct et les alertes de fraude.
   * L'ouverture du rapport d'audit matinal généré dans `04_batch_airflow/RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md`.
4. **Hébergement :** Déposer la vidéo sur Vidyard, Google Drive (lien public) ou YouTube (Non répertorié), et inscrire l'URL dans le document de soumission.

