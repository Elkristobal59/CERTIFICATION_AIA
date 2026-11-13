# Bloc 4 — Industrialisation, Déploiement & MLOps

> **Projet :** CliNER-MLOps (Clinical Named Entity Recognition & Continuous Training)  
> **Dépôt GitHub de l'Application & CI/CD :** 👉 [https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)

---

## 1. Dépôt de Code Source & CI/CD de Production

Le code source complet de la solution d'IA médicale, les conteneurs Docker et les pipelines d'intégration continue sont hébergés sur le dépôt dédié :

🔗 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**

Ce dépôt comprend notamment :
* **Workflows CI/CD GitHub Actions :**
  * `ci_mlops.yml` : Validation de la qualité de code (Flake8), 11 tests unitaires/intégration (PyTest), simulation Continuous Training LoRA sur MLflow et construction des images Docker (`cliner-frontend`, `cliner-mlops-worker`).
  * `weekly_mlops_pipeline.yml` : Cron hebdomadaire (Lundi 02h00 UTC) mesurant la dérive Wasserstein + rapport Evidently AI et déclenchant le réentraînement LoRA si $W > 0.08$.
  * `deploy_ec2_autokill.yml` : Déclenchement manuel à la demande de l'instance AWS EC2 GPU avec minuteur et Auto-Kill FinOps garanti (`if: always()`).
* **Architecture applicative :**
  * Frontend Streamlit conteneurisé.
  * Backend d'inférence LoRA optimisé vLLM.
  * Base vectorielle Supabase `pgvector` pour l'indexation sémantique BioBERT et le cache d'inférence.
* **Pipeline MLOps de réentraînement :**
  * Scripts de détection de dérive statistique (`drift_detection.py` via distance de Wasserstein).
  * Gestionnaire d'infrastructure FinOps (`ec2_manager.py` avec démarrage/coupure automatique d'instance AWS EC2 `g4dn.xlarge`).
  * Fine-tuning LoRA PEFT (`finetune_lora.py`) avec tracking MLflow.

---

## 2. Piliers d'Architecture MLOps

1. **Architecture Modèle Bicéphale (LoRA vs Embedder Figé) :**
   * **Modèle d'embedding :** `BioBERT` (figé en inférence, optimisé pour la vectorisation sémantique des termes biomédicaux).
   * **LLM Génératif :** `Qwen-7B` fine-tuné par adaptateur de bas rang **LoRA (PEFT)**. Seuls les poids de l'adaptateur (~84 Mo) sont réentraînés, évitant de recharger et de recalculer les 7 milliards de paramètres complets du modèle de base.
2. **Surveillance Continue de la Dérive (Drift Monitoring) :**
   * Mesure de dérive non supervisée par distance de **Wasserstein** sur les vecteurs BioBERT des protocoles cliniques récents (seuil critique : $\Delta > 0.08$).
   * Déclenchement automatique du pipeline de réentraînement dès détection d'une dérive lexicale.
3. **Protocole FinOps d'Auto-Arrêt AWS EC2 :**
   * L'instance GPU AWS (`g4dn.xlarge`, Nvidia T4) est allumée à la demande via `boto3` pour le réentraînement, puis arrêtée automatiquement à la fin du run, limitant la dépense au strict temps de calcul effectif.
4. **Registry et Traçabilité des Modèles (MLflow) :**
   * Suivi des métriques (F1-score par entité clinique, perte de validation).
   * Promotion en `Production` conditionnée au dépassement des performances du modèle en place sur un jeu de référence Gold Standard.

---

## 3. Livrables de Soutenance (Dossier `LIVRABLES/`)

| Fichier | Format | Description |
| :--- | :---: | :--- |
| `PRESENTATION_cliner-mlops.pdf` | PDF | Support officiel de soutenance orale (6 slides avec notes). |
| `PRESENTATION_cliner-mlops.pptx` | PPTX | Support modifiable de présentation (16:9). |
| `LIEN_REPO_GITHUB_CLINER_MLOPS.pdf` | PDF | Fiche officielle des liens GitHub, CI/CD, Terraform & URLs Cloud. |
| `LIENS_GITHUB_ET_DEMO.txt` | TXT | Fichier texte des liens officiels pour dépôt Julie LMS (`CliNER_MLOps_Livrables_Bloc4.zip`). |

Le code source complet, les Dockerfiles et les workflows GitHub Actions sont directement consultables sur le dépôt applicatif :  
👉 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**
* **Workflows CI/CD GitHub Actions :** https://github.com/Elkristobal59/cliner-mlops/actions
* **Application Web Streamlit (Render) :** https://cliner-mlops.onrender.com/
* **Serveur MLflow & Model Registry (Cloud Run) :** https://mlflow-cliner-mlops-1054740171053.europe-west9.run.app
