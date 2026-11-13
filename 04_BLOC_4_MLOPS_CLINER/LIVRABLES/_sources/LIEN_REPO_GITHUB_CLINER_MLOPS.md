# 🚀 LIENS OFFICIELS & CODE SOURCE — BLOC 4 `CliNER-MLOps` (RNCP 41993)

*Accès direct au dépôt GitHub applicatif complet, à l'infrastructure Terraform (IaC), aux workflows CI/CD GitHub Actions et aux services déployés en production.*

---

## 1. Liens Officiels du Projet (`CliNER-MLOps`)

* **Dépôt GitHub du Code Source Complet :**
  [https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)
* **Pipelines CI/CD (GitHub Actions — Lint, PyTest, Drift Dry-Run, Docker, Auto-Kill) :**
  [https://github.com/Elkristobal59/cliner-mlops/actions](https://github.com/Elkristobal59/cliner-mlops/actions)
* **Application Web Streamlit (Production Render CPU — 0 €) :**
  [https://cliner-mlops.onrender.com/](https://cliner-mlops.onrender.com/)
* **Serveur MLflow & Model Registry (Google Cloud Run Scale-to-Zero) :**
  [https://mlflow-cliner-mlops-1054740171053.europe-west9.run.app](https://mlflow-cliner-mlops-1054740171053.europe-west9.run.app)
* **Dépôt RNCP 41993 Global (Support & Livrables Bloc 4) :**
  [https://github.com/Elkristobal59/CERTIFICATION_AIA/tree/main/04_BLOC_4_MLOPS_CLINER](https://github.com/Elkristobal59/CERTIFICATION_AIA/tree/main/04_BLOC_4_MLOPS_CLINER)

---

## 2. Contenu Technique Hébergé dans `Elkristobal59/cliner-mlops`

* **`api/main.py` & `app/streamlit_app.py` :** API FastAPI (7 endpoints Swagger `/docs`) + interface Streamlit à 4 onglets (API ClinicalTrials v2, Summary Table, Extraction NER Qwen2.5-7B QLoRA, Chatbot RAG).
* **`mlops_reentrainement/` :** Détection non supervisée de dérive par distance de **Wasserstein (`W₁ > 0.08`)** sur embeddings **BioBERT**, rapports **Evidently AI**, réentraînement **QLoRA 4-bit (~84 Mo)**, suivi **MLflow**, versionnage/rollback **AWS S3** et protocole **Auto-Kill EC2 (`g4dn.xlarge`)**.
* **`terraform/` :** Provisioning *Infrastructure as Code* (`main.tf`, `variables.tf`, `outputs.tf`, `schema.sql` — AWS S3 & PostgreSQL Supabase `pgvector`).
* **`.github/workflows/` :** Automatisation CI/CD (`ci_mlops.yml`), pipeline hebdomadaire (`weekly_mlops_pipeline.yml`) et orchestration EC2 FinOps (`deploy_ec2_autokill.yml`).
* **`tests/test_mlops_pipeline.py` :** Suite automatisée **PyTest** (11 tests unitaires et d'intégration).
