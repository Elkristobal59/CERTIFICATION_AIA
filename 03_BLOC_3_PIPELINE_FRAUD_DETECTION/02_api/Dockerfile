# Multi-stage lightweight Python Dockerfile pour GCP Cloud Run / AWS ECS
FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des dépendances
COPY 02_api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copie du modèle entraîné et du code API
COPY 01_train/fraud_model.joblib /app/01_train/fraud_model.joblib
COPY 01_train/model_metadata.json /app/01_train/model_metadata.json
COPY 02_api/app.py /app/02_api/app.py

EXPOSE 8080

# Démarrage avec Uvicorn haute performance
CMD ["uvicorn", "02_api.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
