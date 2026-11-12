# Architecture Data & Cloud Souveraine — Stripe

Conception d'une infrastructure cloud souveraine (AWS Paris `eu-west-3` & enclave CCPA `us-west-2`) pour le traitement des paiements, les abonnements récurrents, la recommandation contextuelle et l'évaluation du risque de fraude en temps réel (< 100 ms).

---

## 1. Contexte et Contraintes du Système

Le projet consiste à concevoir l'architecture technique complète de la plateforme de traitement de paiements pour Stripe, soumise à quatre contraintes majeures :

1. **Souveraineté des données et conformité multi-juridictions :** Implantation souveraine sur AWS Paris (`eu-west-3`), isolation physique conforme **PCI-DSS v4.0 Level 1**, respect strict du **RGPD** (Droit à l'oubli Art. 17 sous 30j) et du **CCPA** (*Opt-Out* `do_not_sell_or_share`), avec audit continu via AWS Security Hub et Amazon Macie.
2. **SLA d'inférence temps réel :** Budget temps total strictement inférieur à **100 millisecondes (95 ms p99)** pour évaluer le risque de fraude (`Stripe Radar`) et personnaliser le checkout (`Adaptive Checkout`) avant validation du paiement.
3. **Haute résilience opérationnelle :** Disponibilité de 99,999 %, objectif de perte de données nulle (**RPO = 0**), basculement automatique Intra-AZ (< 30s) et réplication Disaster Recovery inter-région (**RTO < 60s** / DRP < 5 min).
4. **Optimisation FinOps & GreenOps :** Architecture élastique favorisant les services managés, Savings Plans 3 ans (-38 %), instances GPU Spot (-70 %) et hébergement bas-carbone (~50 g CO₂e/kWh).

---

## 2. Découpage Fonctionnel de l'Architecture

L'architecture sépare strictement le chemin critique de traitement en ligne des flux analytiques asynchrones :

* **Sas d'ingestion et sécurité périmétrique :**
  * Routage DNS par Amazon Route 53, filtrage anti-DDoS par AWS WAF et AWS Shield.
  * Répartition de charge via Application Load Balancer (ALB, TLS 1.3).
  * Chiffrement immédiat du numéro de carte bancaire (PAN) via un **Tokenization Vault** isolé exploitant des puces matérielles **AWS CloudHSM** (FIPS 140-2 Level 3). Zéro PAN ne circule dans l'infrastructure Data.
* **Cœur transactionnel OLTP :**
  * Base de données **Amazon Aurora PostgreSQL** modélisée en **3e Forme Normale (3NF)** (12 tables incluant paiements, abonnements `Subscription`, remboursements, litiges et données de référence `CountryReference`, `CurrencyExchangeRate`, `ProductCatalog`) pour garantir l'intégrité **ACID**.
  * Réplication synchrone sur 3 zones de disponibilité (Multi-AZ avec Quorum 4/6) et DR cross-région.
* **Monde documentaire NoSQL :**
  * Base **Amazon DocumentDB** (compatible MongoDB) gérant les formats JSON/BSON, XML bancaire ISO 20022 normalisé et références binaires à travers 5 collections (`device_fingerprints`, `clickstream_events`, `webhook_delivery_logs` avec TTL 90j, `customer_feedback` NLP et `ml_feature_vectors`).
* **Streaming, découplage et résolution de conflits :**
  * Ingestion en temps réel sans impact sur la production via **Debezium CDC** lisant le journal binaire (**WAL** + numéro de séquence `LSN`) + Connecteur Change Streams DocumentDB vers **Amazon MSK (Kafka)**.
  * Calcul de fenêtres glissantes via Apache Flink vers Feast/Redis et résolution déterministe des conflits par ordre LSN, machine à états monotone et `MERGE` idempotent.
* **Modèles IA (Fraude < 100 ms, Personnalisation & Analyse Prédictive) :**
  * **Stripe Radar (< 100 ms) :** 15 ms réseau + 20 ms Feast Redis + 15 ms OpenSearch k-NN + 30 ms XGBoost ONNX Runtime (CPU `c6i`) + 15 ms règles métiers = **95 ms p99**.
  * **Adaptive Checkout :** Recommandation contextuelle en ligne des méthodes de paiement depuis le clickstream NoSQL.
  * **Smart Retries & Churn :** Modèles prédictifs entraînés en batch GPU sur SageMaker et surveillés par Evidently AI (drift PSI > 0.20).
* **Entrepôt analytique OLAP et Data Lake :**
  * Entrepôt **Amazon Redshift Serverless** modélisé en **Schéma en Étoile** (4 tables de faits incluant `FactComplianceAudits`, 1 table de synthèse mensuelle `AggMonthlyProductPerformance` et 7 dimensions dont `DimProduct` et `DimCustomer` RFM), optimisé par `DISTKEY(merchant_key)`, `SORTKEY` temporel et Vues Matérialisées auto-rafraîchies.
  * Stockage Data Lake sur Amazon S3 (Bronze / Silver / Gold Parquet Snappy) avec archivage légal S3 Glacier (10 ans).

---

## 3. Inventaire des Livrables

Tous les livrables d'ingénierie sont regroupés au format PDF, DBML/PNG et PPTX dans [`LIVRABLES/`](./LIVRABLES/) (l'archive `Stripe_Dossier_Livrables_Bloc2.zip` ne contient aucun doublon `.md`) :

| Fichier | Type | Description technique |
| :--- | :---: | :--- |
| `00_Executive_Summary.pdf` | PDF | Synthèse exécutive du projet, contraintes multi-réglementaires et dimensionnement. |
| `01_Data_Architecture_Diagram.pdf` | PDF | Architecture logique & physique AWS Multi-AZ détaillée, flux temps réel/batch et gouvernance. |
| `02_OLTP_ERD.pdf` | PDF | Modèle relationnel 3NF ACID complet (transactions, abonnements, référentiels, réplication & DRP). |
| `03_OLAP_Schema.pdf` | PDF | Modèle dimensionnel en Étoile Redshift, `DISTKEY`/`SORTKEY` et Vues Matérialisées. |
| `04_NoSQL_Model.pdf` | PDF | Modélisation multi-formats DocumentDB (JSON, XML ISO 20022, binaire), 5 collections et pont polyglotte. |
| `05_Data_Pipeline_Architecture.pdf` | PDF | Pipelines CDC Debezium, Kafka MSK, Flink, Airflow/dbt, cohérence éventuelle et résolution de conflits. |
| `06_Security_Compliance_Plan.pdf` | PDF | Tokenisation CloudHSM, conformité PCI-DSS/RGPD/CCPA, audit automatisé Security Hub/Macie et FinOps. |
| `07_ML_Integration_Strategy.pdf` | PDF | Intégration ML↔NoSQL, budget < 100 ms Radar, personnalisation Adaptive Checkout et prédictif Smart Retries. |
| `08_SQL_NoSQL_Queries.pdf` | PDF | 6 requêtes SQL OLAP (GPV, échecs, chargebacks, cohortes, RFM CCPA, produit) et 5 pipelines NoSQL. |
| `PRESENTATION_STRIPE_BLOC2.pptx` | PPTX | Support officiel de soutenance orale (6 slides avec notes d'orateur). |
| `stripe_oltp.dbml` & `stripe_olap.dbml` | DBML | Code source DBML des modèles relationnel (OLTP) et décisionnel (OLAP). |
| `stripe_oltp_erd.png` & `stripe_olap_schema.png` | PNG | Diagrammes graphiques haute résolution des schémas de données. |
| `Stripe_Dossier_Livrables_Bloc2.zip` | ZIP | Archive officielle consolidée sans doublons `.md` pour dépôt Julie LMS. |
