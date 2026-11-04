# Architecture Data & Cloud Souveraine — Stripe

Conception d'une infrastructure cloud souveraine (AWS Paris eu-west-3) pour le traitement des paiements et l'évaluation du risque de fraude en temps réel (< 100 ms).  

---

## 1. Contexte et Contraintes du Système

Le projet consiste à concevoir l'architecture technique complète de la plateforme de traitement de paiements pour l'expansion européenne de Stripe, soumise à quatre contraintes majeures :

1. **Souveraineté des données et conformité bancaire :** Implantation exclusive sur la région AWS Paris (`eu-west-3`), isolation physique conforme PCI-DSS Level 1 et conformité stricte au RGPD.
2. **SLA d'inférence temps réel :** Budget temps total strictement inférieur à **100 millisecondes (95 ms p99)** pour évaluer le risque de fraude avant validation du paiement.
3. **Haute résilience opérationnelle :** Disponibilité de 99,999 %, avec un objectif de perte de données nulle (**RPO = 0**) et reprise d'activité en moins d'une minute (**RTO < 60s**).
4. **Optimisation FinOps :** Architecture élastique favorisant les services managés et serverless afin de minimiser les coûts d'infrastructure hors périodes de pic.

---

## 2. Découpage Fonctionnel de l'Architecture

L'architecture sépare strictement le chemin critique de traitement en ligne des flux analytiques asynchrones :

* **Sas d'ingestion et sécurité périmétrique :**
  * Routage DNS par Amazon Route 53, filtrage d'attaques volumétriques par AWS WAF et AWS Shield.
  * Répartition de charge via Application Load Balancer (ALB).
  * Chiffrement immédiat du numéro de carte bancaire (PAN) via un **Card Vault** isolé exploitant des puces matérielles **AWS CloudHSM** (norme FIPS 140-2 Level 3). Génération d'un jeton opaque (*Tokenization*) ; aucun numéro en clair ne circule dans l'infrastructure.
* **Cœur transactionnel OLTP :**
  * Base de données **Amazon Aurora PostgreSQL** modélisée en **3e Forme Normale (3NF)** pour garantir une intégrité transactionnelle ACID absolue.
  * Réplication synchrone sur 3 zones de disponibilité (Multi-AZ avec Quorum 4/6).
* **Streaming et découplage événementiel :**
  * Ingestion en temps réel sans impact sur la base de production via **Debezium CDC (Change Data Capture)** lisant de manière non-bloquante les journaux d'écriture (**WAL** - *Write-Ahead Log*).
  * Distribution des événements dans un cluster **Kafka MSK**.
  * Calcul de compteurs glissants en streaming avec Apache Flink pour mise à jour continue de l'historique chaud.
* **Inférence d'IA sous 100 ms :**
  * Décomposition du budget temps : 15 ms réseau + 20 ms interrogation du Feature Store Feast (Redis) + 15 ms recherche de similarité vectorielle OpenSearch k-NN + 30 ms inférence XGBoost sous ONNX Runtime (CPU instances c6i) + 15 ms acquittement = **95 ms**.
* **Entrepôt analytique OLAP et Data Lake :**
  * Entrepôt **Amazon Redshift Serverless** avec modélisation décisionnelle en **Schéma en Étoile** (3 tables de faits : transactions, remboursements, frais ; 6 dimensions : temps, marchand, client, carte, géographie, devise).
  * Stockage persistant Data Lake sur Amazon S3 (partitionnement Bronze / Silver / Gold au format Parquet Snappy).
  * Cycle de vie FinOps avec archivage légal des pièces comptables sur S3 Glacier (rétention légale de 10 ans).

---

## 3. Inventaire des Livrables

Tous les livrables d'ingénierie sont regroupés au format PDF et schémas exécutifs dans [`LIVRABLES/`](./LIVRABLES/) :

| Fichier | Type | Description technique |
| :--- | :---: | :--- |
| `00_Executive_Summary.pdf` | PDF | Synthèse exécutive du projet, contraintes de souveraineté et dimensionnement. |
| `01_Data_Architecture_Diagram.pdf` | PDF | Architecture physique AWS Multi-AZ détaillée, réseau VPC et sécurité. |
| `02_OLTP_ERD.pdf` | PDF | Modèle conceptuel et logique relationnel normalisé en 3e Forme Normale (3NF). |
| `03_OLAP_Schema.pdf` | PDF | Modèle dimensionnel en Schéma en Étoile pour Redshift Serverless. |
| `04_NoSQL_Model.pdf` | PDF | Modélisation des documents semi-structurés JSON sous Amazon DocumentDB. |
| `05_Data_Pipeline_Architecture.pdf` | PDF | Architecture des flux streaming CDC Debezium, Kafka MSK et Apache Flink. |
| `06_Security_Compliance_Plan.pdf` | PDF | Stratégie de chiffrement KMS, tokenisation CloudHSM et conformité PCI-DSS. |
| `07_ML_Integration_Strategy.pdf` | PDF | Budget de latence p99 (< 100 ms), Feature Store Feast Redis et inférence ONNX. |
| `08_SQL_NoSQL_Queries.pdf` | PDF | Requêtes d'analyse décisionnelle et opérations NoSQL documentées. |
| `PRESENTATION_STRIPE_BLOC2.pptx` | PPTX | Support officiel de soutenance orale (6 slides avec notes d'orateur). |
| `stripe_oltp.dbml` & `stripe_olap.dbml` | DBML | Code source de la modélisation des bases de données relationnelle et analytique. |
| `stripe_oltp_erd.png` & `stripe_olap_schema.png` | PNG | Diagrammes graphiques haute résolution des schémas de données. |
| `Stripe_Dossier_Livrables_Bloc2.zip` | ZIP | Archive officielle consolidée déposée sur Julie LMS. |

