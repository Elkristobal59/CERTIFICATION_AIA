# Bloc 3 — Pipeline de Streaming & Détection de Fraude en Temps Réel

> **Cas d'étude :** Détection de Fraude Bancaire en Temps Réel (Apache Kafka & Scikit-Learn)  
> **Certification :** Architecte en Intelligence Artificielle (RNCP 41993)  
> **Candidat :** Christopher Gilleron  
> **Format d'évaluation :** Soutenance orale de 20 minutes (5 min pitch + 15 min Q&A avec démonstration)

---

## 1. Contexte Métier et Objectifs

Dans le secteur bancaire et du commerce en ligne, la fraude aux cartes de paiement impose d'intercepter les comportements suspects à la volée avant confirmation de la transaction, tout en évitant les faux positifs qui bloqueraient les clients légitimes.

Ce projet implémente une architecture de données complète combinant :
* **Streaming événementiel temps réel :** Ingestion continue et amortissement de charge via Apache Kafka en mode KRaft.
* **Inférence prédictive sub-15ms :** Microservice conteneurisé FastAPI avec modèle Scikit-Learn compilé.
* **Résilience et qualité des données :** Détection d'anomalies de schéma et routage automatique vers une Dead Letter Queue (`fraud-dlq`).
* **Double persistance :** Stockage colonne partitionné au format Parquet (Data Lake Bronze) et base relationnelle pour l'audit opérationnel.
* **Orchestration batch matinale :** DAG Apache Airflow pour la réconciliation quotidienne et le suivi des métriques de risque.

---

## 2. Architecture Technique

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE DU PIPELINE DE FRAUDE                              │
│                                                                                        │
│  [SOURCE TRANSACTIONS]                                                                 │
│  Flux streaming continu ──► PRODUCER KAFKA ──► TOPIC 'raw-transactions'                │
│                                                (3 Partitions, Commit synchrone)        │
│                                                            │                           │
│                                                            ▼                           │
│                                                CONSUMER & QUALITÉ DONNÉES              │
│                                                 ├── Erreur schéma ──► TOPIC 'fraud-dlq'│
│                                                 │                     (Rejets isolés)  │
│                                                 ▼                                      │
│                                        API SCORING FASTAPI (Port 8080)                 │
│                                        HistGradientBoosting (Inférence < 4ms)          │
│                                                 │                                      │
│                                                 ├── Score >= 0.70 ──► ALERTE FLASH     │
│                                                 │                                      │
│                                                 ▼                                      │
│                                        DOUBLE PERSISTANCE                              │
│                                        • Data Lake Bronze (Parquet partitionné)        │
│                                        • Base SQL d'audit (Transactions scorées)       │
│                                                            │                           │
│                                                            ▼                           │
│                                                BATCH AIRFLOW QUOTIDIEN (06h00 UTC)     │
│                                                ➔ Rapport Matinal de Réconciliation     │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Guide d'Exécution de la Démonstration

### Prérequis
* Python 3.10 ou supérieur
* Docker Desktop installé et démarré

### Étape 1 : Démarrer le cluster Kafka KRaft
```bash
docker compose -f 03_pipeline_streaming/docker-compose.kafka.yml up -d
```
* Interface Web Kafka UI accessible sur : `http://localhost:8085`

### Étape 2 : Démarrer le microservice de scoring FastAPI
```bash
docker build -t fraud-scoring-api:latest 02_api/
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest
```
* Documentation interactive OpenAPI / Swagger : `http://localhost:8080/docs`

### Étape 3 : Lancer la démonstration de bout en bout
```bash
python run_full_pipeline_demo.py
```

Le script exécute successivement :
1. Connexion au broker Kafka et vérification de la disponibilité de l'API.
2. Ingestion et scoring en continu d'un échantillon de transactions réelles (`sample_fraud_data.csv`).
3. Déclenchement d'alertes immédiates sur les transactions frauduleuses détectées.
4. Test de résilience : injection volontaire d'une charge corrompue et déroutement immédiat vers la Dead Letter Queue.
5. Sauvegarde synchrone dans le Data Lake Parquet partitionné (`data_lake/bronze/`).
6. Exécution du job d'audit Airflow et génération du rapport matinal de réconciliation.

---

## 4. Modèle de Machine Learning

* **Algorithme :** `HistGradientBoostingClassifier` (Scikit-Learn).
* **Jeu d'entraînement :** 555 719 transactions réelles (`fraudTest.csv`).
* **Variables d'entrée :** Montant (`amt`), distance Haversine client-commerçant (`distance_km`), heure de la transaction (`hour`), âge du titulaire (`age`), population de la commune (`city_pop`).
* **Performances :** ROC-AUC : 0.9866 | Rappel Fraude : 92.4 % | Temps de calcul unitaire : < 3 ms CPU.

---

## 5. Livrables Officiels

Tous les documents d'évaluation sont réunis dans [`LIVRABLES/`](./LIVRABLES/) :

| Fichier | Format | Description |
| :--- | :---: | :--- |
| `ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pdf` | PDF | Support officiel de soutenance (7 slides, 5 minutes). |
| `ARCHITECTURE_PIPELINE_FRAUD_BLOC3.pptx` | PPTX | Slides modifiables avec notes d'orateur complètes. |
| `RAPPORT_ARCHITECTURE_TECHNIQUE_PIPELINE.pdf` | PDF | Rapport technique d'ingénierie et justifications de conception. |
| `LIEN_DEMO_VIDEO.pdf` | PDF | Fiche officielle récapitulative des liens et scénario de démo. |
| `SPEECH_ORAL_BLOC_3_FRAUD_KAFKA_5MIN.pdf` | PDF | Déroulé chronométré de l'épreuve orale. |
| `schema_architecture_infrastructure_fraud.png` | PNG | Diagramme haute résolution de l'architecture. |
| `Fraud_Detection_Livrables_Bloc3.zip` | ZIP | Archive officielle consolidée déposée sur Julie LMS. |
