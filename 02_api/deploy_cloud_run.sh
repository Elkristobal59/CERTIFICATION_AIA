#!/bin/bash
# =============================================================================
# SCRIPT DE DÉPLOIEMENT SERVERLESS SUR GCP CLOUD RUN (BLOC 3 - RNCP 41993)
# =============================================================================
set -e

# Configuration du Projet GCP
PROJECT_ID=${GCP_PROJECT_ID:-"jedha-aia-certification"}
REGION="europe-west9" # Paris
SERVICE_NAME="fraud-scoring-api"
IMAGE_TAG="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "================================================================="
echo "☁️ DÉPLOIEMENT DE L'API DE SCORING FRAUDE SUR GOOGLE CLOUD RUN"
echo "   Projet GCP : ${PROJECT_ID} | Région : ${REGION}"
echo "================================================================="

# 1. Vérification de l'authentification GCP
echo "🔐 Vérification des identifiants gcloud..."
gcloud config set project ${PROJECT_ID}

# 2. Build de l'image Docker avec Cloud Build ou Docker local
echo "🔨 Construction et envoi de l'image conteneurisée..."
gcloud builds submit --tag ${IMAGE_TAG} --file 02_api/Dockerfile .

# 3. Déploiement sur Cloud Run avec Scale-to-Zero FinOps
echo "🚀 Déploiement du service Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_TAG} \
  --region ${REGION} \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --min-instances 0 \
  --max-instances 5 \
  --memory 1Gi \
  --cpu 1 \
  --set-env-vars ENVIRONMENT=production

# 4. Affichage de l'URL publique HTTPS générée
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
echo "================================================================="
echo "✅ SERVICE DÉPLOYÉ AVEC SUCCÈS SUR CLOUD RUN !"
echo "👉 URL HTTPS Publique : ${SERVICE_URL}"
echo "👉 Healthcheck        : ${SERVICE_URL}/health"
echo "👉 Documentation API  : ${SERVICE_URL}/docs"
echo "================================================================="
