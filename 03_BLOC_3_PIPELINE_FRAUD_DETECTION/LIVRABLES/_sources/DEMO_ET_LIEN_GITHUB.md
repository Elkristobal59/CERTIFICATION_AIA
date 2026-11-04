# Démonstration & Dépôt Officiel du Projet

> **Projet :** Pipeline de Détection de Fraude en Temps Réel (Kafka & IA - RNCP 41993 Bloc 3)  
> **Auteur :** Chris Gilleron  
> **Lien du Dépôt GitHub :** [https://github.com/Elkristobal59/CERTIFICATION_AIA](https://github.com/Elkristobal59/CERTIFICATION_AIA)  
> **Vidéo Démonstrateur :** `fraud_detectionApp_chris_gilleron.mp4` (Durée : 1 min 51 sec - Full HD 1080p)  

---

## 🎬 Contenu de la Démonstration Vidéo (1 min 51s)

La vidéo `fraud_detectionApp_chris_gilleron.mp4` démontre en direct l'infrastructure complète :
1. **Conteneurisation Docker Desktop :** Broker Kafka KRaft, Kafka UI et microservice FastAPI actifs.
2. **Exécution du Pipeline Streaming de bout en bout (`run_full_pipeline_demo.py`) :**
   * Ingestion continue et publication dans le topic `raw-transactions`.
   * Scoring ML ultra-rapide (< 4 ms) et déclenchement instantané des alertes `BLOCK_IMMEDIATE`.
   * Test de résilience & Contrôle Qualité (C5) : routage immédiat de la charge corrompue vers la Dead Letter Queue (`fraud-dlq`).
   * Persistance synchrone dans le Data Lake Parquet partitionné (`data_lake/bronze/`).
   * Exécution du DAG matinal Apache Airflow et génération du rapport financier de réconciliation.
3. **Supervision en direct dans Kafka UI (`http://localhost:8085`) :** Visualisation des messages temps réel dans les partitions du topic.
4. **Validation de l'API REST sous OpenAPI / Swagger (`http://localhost:8080/docs`) :** Inférence HTTP en direct avec code 200 OK.

---

## 🚀 Guide Rapide de Lancement de la Démonstration

### 1. Démarrer les Services Conteneurisés
```bash
# 1. Démarrer le cluster Kafka KRaft et l'interface Web Kafka UI
docker compose -f 03_pipeline_streaming/docker-compose.kafka.yml up -d

# 2. Démarrer l'API de scoring FastAPI
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest
```
* **Supervision Kafka UI :** [http://localhost:8085](http://localhost:8085)
* **Documentation OpenAPI / Swagger :** [http://localhost:8080/docs](http://localhost:8080/docs)

### 2. Exécuter la Démonstration Complète en 1 Commande
```bash
python run_full_pipeline_demo.py
```

Le script exécute automatiquement :
1. Connexion et flux streaming depuis l'API et les transactions d'exemple.
2. Inférence temps réel via l'API HTTP (< 15 ms).
3. Déclenchement d'alertes flash immédiates en cas de fraude suspectée.
4. Test d'injection d'anomalie avec routage automatique vers la Dead Letter Queue (DLQ).
5. Persistance synchrone dans le Data Lake Parquet partitionné.
6. Exécution du DAG d'audit matinal Airflow et génération du rapport de réconciliation.
