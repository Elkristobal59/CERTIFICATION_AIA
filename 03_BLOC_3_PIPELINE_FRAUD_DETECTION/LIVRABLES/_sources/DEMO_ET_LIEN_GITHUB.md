# Fiche Officielle : Démonstration Vidéo & Dépôt GitHub

> **Projet :** Pipeline de Détection de Fraude en Temps Réel (Kafka & IA — RNCP 41993 Bloc 3)  
> **Candidat :** Christopher GILLERON  
> **Organisme :** Jedha Bootcamp  
> **Dépôt GitHub Officiel :** [https://github.com/Elkristobal59/CERTIFICATION_AIA](https://github.com/Elkristobal59/CERTIFICATION_AIA)  
> **Lien Direct Vidéo Démonstrateur (Google Drive) :** [https://drive.google.com/file/d/1sPFnorGQee8DDsr_ij2umzWRrIFj6gAe/view?usp=sharing](https://drive.google.com/file/d/1sPFnorGQee8DDsr_ij2umzWRrIFj6gAe/view?usp=sharing)  
> **Fichier Local :** `fraud_detectionApp_chris_gilleron.mp4` (Durée : 1 min 51 sec — Full HD 1080p)

---

## 1. Accès à la Vidéo de Démonstration

La vidéo de démonstration opérationnelle du pipeline complet est accessible via le lien cloud permanent suivant :

👉 **[Visionner la démonstration sur Google Drive](https://drive.google.com/file/d/1sPFnorGQee8DDsr_ij2umzWRrIFj6gAe/view?usp=sharing)**

*(Ce lien permet une lecture immédiate en streaming sans téléchargement préalable requis).*

---

## 2. Déroulement Chronométré de la Démonstration (1 min 51s)

La séquence vidéo démontre en conditions réelles l'ensemble des modules d'infrastructure requis par le référentiel Jedha / RNCP 41993 :

1. **Environnement Conteneurisé (0:00 - 0:25) :**
   * Validation des services Docker Desktop actifs : Broker Apache Kafka en mode KRaft, interface d'administration Kafka UI et conteneur FastAPI.
2. **Exécution du Pipeline de bout en bout (`run_full_pipeline_demo.py`) (0:25 - 1:05) :**
   * Connexion au cluster Kafka et émission des transactions dans le topic `raw-transactions`.
   * Inférence prédictive sub-15ms via le microservice FastAPI et déclenchement d'alertes instantanées `BLOCK_IMMEDIATE` sur les transactions frauduleuses.
   * Démonstration du contrôle qualité et de la résilience (Compétence C5) : détection d'une anomalie de schéma (montant négatif) et routage immédiat vers la Dead Letter Queue (`fraud-dlq`).
   * Sauvegarde synchrone dans le Data Lake partitionné (`data_lake/bronze/year=2026/`).
   * Déclenchement du DAG Apache Airflow et génération du rapport matinal de réconciliation.
3. **Supervision Temps Réel dans Kafka UI (1:05 - 1:30) :**
   * Visualisation sur `http://localhost:8085` des flux ingérés, des partitions et des messages isolés dans la Dead Letter Queue.
4. **Validation de l'API REST (1:30 - 1:51) :**
   * Documentation interactive OpenAPI / Swagger sur `http://localhost:8080/docs` avec exécution d'un test d'inférence direct sous code 200 OK.

---

## 3. Commandes de Reproduction Locale

Pour reproduire la démonstration sur un poste local :

```bash
# 1. Démarrer le cluster Kafka KRaft
docker compose -f 03_pipeline_streaming/docker-compose.kafka.yml up -d

# 2. Démarrer le microservice de scoring
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest

# 3. Lancer la chaîne complète
python run_full_pipeline_demo.py
```
