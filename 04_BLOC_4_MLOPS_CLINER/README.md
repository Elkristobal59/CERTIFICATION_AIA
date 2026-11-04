# Bloc 4 — Industrialisation, Déploiement & MLOps

> **Projet :** CliNER-MLOps (Clinical Named Entity Recognition & Continuous Training)  
> **Dépôt GitHub de l'Application & CI/CD :** 👉 [https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)

---

## 1. Dépôt de Code Source & CI/CD de Production

Le code source complet de la solution d'IA médicale, les conteneurs Docker et les pipelines d'intégration continue sont hébergés sur le dépôt dédié :

🔗 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**

Ce dépôt comprend notamment :
* **Workflows CI/CD GitHub Actions :**
  * `ci_mlops.yml` : Validation de la qualité de code (Flake8), tests unitaires (Pytest) et construction des images Docker.
  * `deploy_frontend.yml` : Déploiement continu de l'interface Streamlit sur Render.
  * `deploy_backend_aws.yml` : Orchestration du déploiement de l'API d'inférence vLLM sur AWS EC2 GPU.
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

Le code source complet, les Dockerfiles et les workflows GitHub Actions sont directement consultables sur le dépôt applicatif :  
👉 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**
