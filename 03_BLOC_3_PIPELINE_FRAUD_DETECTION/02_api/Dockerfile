# Lightweight Python Dockerfile pour Microservice FastAPI + MLflow Model Registry
FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY 02_api/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY 01_train/features.py /app/01_train/features.py
COPY 01_train/fraud_model.joblib /app/01_train/fraud_model.joblib
COPY 01_train/model_metadata.json /app/01_train/model_metadata.json
COPY 02_api/app.py /app/02_api/app.py

EXPOSE 8080

CMD ["uvicorn", "02_api.app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
