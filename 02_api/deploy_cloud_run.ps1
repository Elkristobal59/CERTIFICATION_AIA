# =============================================================================
# SCRIPT POWERSHELL DE DÉPLOIEMENT SERVERLESS SUR GCP CLOUD RUN (BLOC 3)
# =============================================================================
param (
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = "europe-west9"
)

if (-not $ProjectId) {
    $ProjectId = "jedha-aia-certification"
}

$ServiceName = "fraud-scoring-api"
$ImageTag = "gcr.io/$ProjectId/$ServiceName`:latest"

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "☁️ DEPLOIEMENT DE L'API SUR GOOGLE CLOUD RUN (SERVERLESS)" -ForegroundColor Cyan
Write-Host "   Projet GCP : $ProjectId | Region : $Region" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan

# 1. Vérification gcloud
if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ La commande 'gcloud' n'est pas installée sur ce poste Windows." -ForegroundColor Red
    Write-Host "ℹ️ Vous pouvez exécuter ce déploiement depuis Google Cloud Shell ou déployer via Docker local." -ForegroundColor Yellow
    exit 1
}

# 2. Build Cloud Build
Write-Host "🔨 Construction de l'image Docker avec Cloud Build..." -ForegroundColor Cyan
gcloud builds submit --tag $ImageTag --file 02_api/Dockerfile .

# 3. Déploiement Cloud Run
Write-Host "🚀 Déploiement sur Google Cloud Run..." -ForegroundColor Cyan
gcloud run deploy $ServiceName `
  --image $ImageTag `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --port 8080 `
  --min-instances 0 `
  --max-instances 5 `
  --memory 1Gi `
  --cpu 1

$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format 'value(status.url)'
Write-Host "✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !" -ForegroundColor Green
Write-Host "👉 URL Cloud Run : $ServiceUrl" -ForegroundColor Green
