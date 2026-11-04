# Bloc 4 — Industrialisation, Déploiement & MLOps

> **Projet :** CliNER-MLOps (Clinical Named Entity Recognition & Continuous Training)  
> **Certification :** Architecte en Intelligence Artificielle (RNCP 41993)  
> **Candidat :** Christopher Gilleron  
> **Format d'évaluation :** Soutenance orale de 15 minutes (5 min pitch + 10 min Q&A)  
> **Dépôt GitHub de code source :** [https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)

---

## 1. Contexte et Objectifs

CliNER-MLOps est une solution d'intelligence artificielle dédiée au traitement automatique du langage médical (NLP clinique). Elle extrait automatiquement les critères d'inclusion et d'exclusion (pathologies, dosages, contre-indications) à partir de protocoles d'essais cliniques non structurés pour accélérer le recrutement des patients.

L'objectif de ce bloc est de concevoir et piloter l'ensemble de la chaîne MLOps : de l'entraînement ciblé à la surveillance en production et au réentraînement automatisé sous contraintes FinOps strictes.

---

## 2. Piliers d'Architecture MLOps

1. **Architecture Modèle Bicéphale (Fine-Tuning LoRA vs Embedder Figé) :**
   * **Modèle d'embedding :** `BioBERT` (figé en inférence, optimisé pour la vectorisation sémantique des termes biomédicaux).
   * **LLM Génératif :** `Qwen-7B` fine-tuné par adaptateur de bas rang **LoRA (PEFT)**. Seuls les poids de l'adaptateur (~84 Mo) sont réentraînés, évitant de recharger et de recalculer les 7 milliards de paramètres complets du modèle de base.
2. **Surveillance Continue de la Dérive (Drift Monitoring) :**
   * Calcul de la distance statistique de **Wasserstein** sur les embeddings BioBERT des protocoles cliniques récents (seuil critique : $\Delta > 0.15$).
   * Déclenchement automatique d'un pipeline de réentraînement dès que la distribution lexicale des nouveaux essais s'écarte de la base d'apprentissage.
3. **Protocole FinOps d'Auto-Arrêt AWS EC2 (`ec2_manager.py`) :**
   * Pour maîtriser les coûts de calcul, l'instance GPU AWS (`g4dn.xlarge` avec GPU Nvidia T4) n'est allumée à la demande via le SDK `boto3` que pendant l'exécution du script de réentraînement.
   * Extinction et résiliation automatiques dès la fin de l'opération, garantissant une facturation limitée au strict temps de calcul effectif.
4. **Registry et Traçabilité des Modèles (MLflow) :**
   * Suivi des métriques d'évaluation (F1-score par type d'entité, perte de validation).
   * Promotion automatique du nouvel adaptateur LoRA en `Production` uniquement si le F1-score dépasse la version courante sur un jeu de test de référence.

---

## 3. Livrables de Soutenance

Les supports de présentation et synthèses techniques sont réunis dans [`LIVRABLES/`](./LIVRABLES/) :

| Fichier | Format | Description |
| :--- | :---: | :--- |
| `PRESENTATION_cliner-mlops.pdf` | PDF | Support officiel de soutenance orale (6 slides avec notes). |
| `FICHE_REVISION_MASTER_CLINER_MLOPS_ORAL.pdf` | PDF | Fiche de synthèse MLOps complète (architecture, LoRA, FinOps, questions/réponses). |
| `SPEECH_ORAL_BLOC_4_CLINER_MLOPS_5MIN.pdf` | PDF | Déroulé chronométré de l'épreuve orale (5 minutes chrono). |

Le code source complet, les Dockerfiles, les configurations CI/CD et les scripts de déploiement sont consultables sur le dépôt public dédié :  
👉 **[https://github.com/Elkristobal59/cliner-mlops](https://github.com/Elkristobal59/cliner-mlops)**
