# Démonstration Opérationnelle & Liens du Projet

> **Projet :** Pipeline de Détection de Fraude en Temps Réel (Kafka & IA — RNCP 41993 Bloc 3)  
> **Candidat :** Christopher GILLERON  
> **Organisme :** Jedha Bootcamp  

---

## 🎥 1. Vidéo de Démonstration (1 min 51s)

La vidéo montre le fonctionnement de l'infrastructure de streaming et d'inférence en direct :
* Lancement du pipeline et ingestion des transactions dans Kafka.
* Inférence du modèle et déclenchement instantané de l'alerte sur transaction suspecte.
* Isolation des anomalies et exécution du batch de réconciliation quotidienne.

👉 **Lien de visionnage :** [https://drive.google.com/file/d/1sPFnorGQee8DDsr_ij2umzWRrIFj6gAe/view?usp=sharing](https://drive.google.com/file/d/1sPFnorGQee8DDsr_ij2umzWRrIFj6gAe/view?usp=sharing)

---

## 💻 2. Dépôt GitHub

Le code source complet, les Dockerfiles et les scripts sont disponibles sur :  
👉 **[https://github.com/Elkristobal59/CERTIFICATION_AIA](https://github.com/Elkristobal59/CERTIFICATION_AIA)**

---

## 🚀 3. Reproduction Locale

Pour exécuter la démonstration en local :

```bash
# 1. Démarrer Kafka KRaft et Kafka UI
docker compose -f 03_pipeline_streaming/docker-compose.kafka.yml up -d

# 2. Démarrer l'API de scoring FastAPI
docker run -d --name fraud-scoring-api -p 8080:8080 fraud-scoring-api:latest

# 3. Lancer le flux streaming de démonstration
python run_full_pipeline_demo.py
```

