# Bloc 1 — Gouvernance des Données & des Systèmes d'IA

> **Cas d'étude :** Stratégie de Gouvernance et Conformité Réglementaire pour Spotify Europe  
> **Certification :** Architecte en Intelligence Artificielle (RNCP 41993)  
> **Candidat :** Christopher Gilleron  
> **Format d'évaluation :** Soutenance orale de 30 minutes (15 min pitch + 15 min Q&A)

---

## 1. Contexte et Problématique

Spotify opère dans un environnement distribué caractérisé par une forte autonomie des équipes produit (Squads et Tribes). Cette décentralisation a favorisé une innovation rapide mais a généré une dette importante en matière de gouvernance :
* **Hétérogénéité sémantique :** Absence de glossaire d'entreprise unifié (divergence sur la définition d'un stream écouté ou d'un utilisateur actif).
* **Risque de conformité réglementaire :** Amende réelle de 5 millions d'euros infligée par l'autorité suédoise (IMY) en juin 2023 pour non-respect de l'Article 15 du RGPD (défaut d'information claire lors des demandes de droit d'accès / SARs).
* **Entraînement des modèles d'IA :** Manque de traçabilité sur les jeux de données alimentant les moteurs de recommandation (*Discover Weekly*).

---

## 2. Démarche et Cadre Méthodologique

Le projet s'appuie sur le référentiel international **DAMA-DMBOK2** et le modèle de maturité **Gartner** :

1. **Audit de maturité initiale (Score : 1.8 / 5) :** Identification des lacunes critiques sur la qualité des données, la sécurité et la traçabilité des métadonnées.
2. **Organisation cible en CoE Hybride (Hub & Spoke) :**
   * **Hub central (Gouvernance d'Entreprise) :** Sous l'autorité du Chief Data Officer (CDO), définit les standards, les politiques globales et administre le catalogue de données.
   * **Spokes distribués (Tribes produit) :** Chaque domaine dispose d'un **Data Owner** (décideur métier responsable légalement de son périmètre) et d'un **Data Steward** (garant opérationnel de la qualité et du glossaire sémantique).
3. **Matrice RACI opérationnelle :** Définition précise des responsabilités sur 33 processus clés (minimisation, gestion des accès, détection des incidents de sécurité, validation des données d'entraînement).
4. **Projet Pilote Recommandation & Abonnés :**
   * Standardisation des définitions métier dans un Semantic Layer.
   * Traçabilité complète du lignage des données d'entraînement des modèles d'IA via DVC et MLflow.
   * Procédure de réponse aux notifications de fuite de données sous 72 heures (Article 33 du RGPD).

---

## 3. Inventaire des Livrables

Tous les livrables finaux sont réunis dans le répertoire [`LIVRABLES/`](./LIVRABLES/) :

| Livrable | Format | Description |
| :--- | :---: | :--- |
| `00_Dossier_Maitre_Gouvernance_Donnees_et_IA_Spotify.docx` | Word | Rapport complet de cadrage, politiques et méthodologie (80+ pages). |
| `01_Rapport_Evaluation_Maturite_Donnees_Spotify.docx` | Word | Synthèse de l'audit de maturité Gartner par domaine de données. |
| `01_Annexe_Grille_Audit_Maturite_Gartner_DMBOK.xlsx` | Excel | Grille d'évaluation détaillée des 10 fonctions DMBOK. |
| `02_Politique_Gouvernance_Donnees_et_IA_Spotify.docx` | Word | Règles de gouvernance, sécurité, qualité et conformité IA. |
| `02_Annexe_Matrice_RACI_Detaillee_33_Taches.xlsx` | Excel | Matrice RACI complète par fonction et rôle organisationnel. |
| `02_Annexe_Checklist_Conformite_RGPD_CCPA_PCIDSS.xlsx` | Excel | Grille de contrôle de conformité multi-juridictionnelle. |
| `02_Schema_Roles_et_Responsabilites_RACI_Spotify.pptx` | PPTX | Schéma visuel de l'organisation Hub & Spoke. |
| `03_Plan_Mise_en_Oeuvre_et_Projet_Pilote_Spotify.docx` | Word | Feuille de route du projet pilote sur la recommandation musicale. |
| `04_Presentation_Executive_Gouvernance_Spotify.pptx` | PPTX | Support officiel de soutenance orale (15 minutes). |
| `Spotify_Dossier_Livrables_Bloc1.zip` | ZIP | Archive officielle consolidée déposée sur Julie LMS. |

