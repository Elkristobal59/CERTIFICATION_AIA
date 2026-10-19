# 🎙️ Script Oral de Soutenance — Détection de Fraude (Bloc 3)
> **Titre Visé :** Architecte en Intelligence Artificielle (RNCP 41993 - Niveau 7 / Bac+5)  
> **Bloc 3 :** Déploiement de Pipelines de Données pour l'IA  
> **Durée Officielle :** 5 minutes chrono (suivi de 15 minutes de Q&A)  
> **Auditoire :** Jury de Certification RNCP 41993  

---

## ⏱️ Chronomètre & Découpage Minute par Minute

```
[00:00 - 01:00]  1. Contexte Métier, Enjeu Financier & Les 2 Exigences Clés
[01:00 - 02:15]  2. L'Architecture Temps Réel : Source API, Kafka & Scoring FastAPI
[02:15 - 03:15]  3. L'Arbitrage Clé d'Architecte : Pourquoi Kafka ET Airflow ?
[03:15 - 04:15]  4. Le Modèle d'Inférence, la Distance Haversine & la Persistance
[04:15 - 05:00]  5. Démonstration du Pipeline & Conclusion FinOps
```

---

## 🗣️ Discours Intégral à Prononcer à l'Oral

### 1. Contexte Métier & Les Deux Exigences Clés (00:00 - 01:00)
> *"Bonjour à tous. En tant que Data Architecte pour ce troisième bloc de compétences, je vais vous présenter la conception et la mise en œuvre de notre pipeline de données pour la détection automatisée des fraudes aux cartes bancaires.*
>
> *Dans l'Union Européenne, la fraude financière représente plus d'un milliard d'euros de préjudice annuel. Le département métier de notre banque nous a mandatés pour répondre à deux exigences opérationnelles très concrètes :*
> *1. **Premièrement, une alerte immédiate :** dès qu'un paiement suspect survient, une notification instantanée doit être émise pour bloquer la carte ou déclencher une vérification forte.*
> *2. **Deuxièmement, un audit quotidien chaque matin :** vérifier l'ensemble des paiements et des fraudes survenus au cours de la journée précédente pour alimenter les tableaux de bord de la direction des risques.*
>
> *Face à ces deux besoins radicalement différents en termes de latence, mon rôle a été de concevoir une infrastructure hybride conciliant streaming temps réel et traitement par lots."*

---

### 2. L'Architecture Temps Réel & Le Flux Événementiel (01:00 - 02:15)
> *"Pour satisfaire la première exigence de détection instantanée, nous avons banni toute logique de batch périodique au profit d'une **architecture événementielle en streaming** :*
>
> *1. **La Source de Données :** Nous ingérons les transactions en flux continu depuis une API de paiement en temps réel hébergée sur HuggingFace Spaces.*
> *2. **Le Bus de Messages Apache Kafka :** Dès qu'une transaction est reçue, notre `Producer` la publie instantanément dans un topic Kafka nommé `raw-transactions`. Kafka joue ici le rôle de tampon haute cadence, garantissant l'élasticité face aux pics de paiements sans jamais saturer notre système aval.*
> *3. **Le Microservice d'Inférence FastAPI :** Notre `Consumer` Kafka dépile chaque événement et interroge notre microservice de scoring conteneurisé. Ce service extrait les caractéristiques à la volée et calcule la probabilité de fraude en moins de **3 millisecondes**.*
> *4. **L'Alerte Flash :** Dès que la probabilité dépasse le seuil critique de 50%, notre service d'alerte déclenche une notification immédiate avec le détail de la transaction, le marchand et le porteur de carte, permettant le blocage du paiement avant son règlement définitif."*

---

### 3. L'Arbitrage Clé : Pourquoi Kafka ET Airflow ? (02:15 - 03:15)
> *"Une question fondamentale se posait : pourquoi ne pas avoir tout implémenté sous Apache Airflow, comme suggéré dans l'intitulé initial du cours ?*
>
> *La réponse réside dans le **compromis de latence** :*
> *- **Airflow** est un orchestrateur de batchs planifiés. Même avec un cron toutes les 5 minutes, une fraude de 1 000 euros serait détectée avec 5 minutes de retard : la marchandise serait déjà expédiée et le préjudice irréversible.*
> *- **Kafka**, à l'inverse, est conçu pour l'événementiel à la milliseconde. C'est l'outil indispensable pour l'interception de fraude en temps réel.*
>
> *En revanche, **Airflow retrouve toute sa légitimité pour la deuxième exigence métier** : notre DAG `daily_fraud_audit_pipeline` s'exécute chaque matin à 06h00 UTC. Il extrait l'historique des 24 dernières heures depuis notre base opérationnelle, consolide le taux de fraude, identifie les catégories de marchands les plus attaquées et génère le rapport matinal pour la direction financière.*
>
> *Nous avons donc l'alliance idéale : **Kafka pour la protection instantanée, Airflow pour la gouvernance et l'audit**."*

---

### 4. Le Modèle de Scoring, la Géolocalisation & la Persistance (03:15 - 04:15)
> *"Sur le plan de l'IA et de la donnée :*
> *- Nous avons entraîné un algorithme **HistGradientBoosting** sur les 550 000 transactions réelles du jeu de données `fraudTest.csv` avec rééquilibrage de classe.*
> *- Au-delà du montant de la transaction, notre feature la plus discriminante est la **distance orthodromique de Haversine**, calculée en temps réel entre les coordonnées GPS du client et celles du terminal de paiement. Un paiement physique à 500 kilomètres du domicile du client est un signal immédiat d'anomalie.*
> *- Notre modèle atteint un **ROC-AUC de 0.9866** et intercepte plus de **92 % des fraudes réelles**.*
> *- Enfin, chaque transaction enrichie de son score et de sa décision est persistée avec garanties ACID dans notre base de données relationnelle, garantissant une traçabilité intégrale pour les audits bancaires et la conformité PCI-DSS."*

---

### 5. Démonstration & Conclusion Stratégique (04:15 - 05:00)
> *"Le code source de l'ensemble de cette infrastructure est entièrement modulaire et opérationnel dans notre repository : de l'entraînement ML à l'API conteneurisée, jusqu'au cluster Kafka et au DAG Airflow.*
>
> *Comme vous allez le voir dans notre démonstration live, le pipeline ingère les flux de transactions, discrimine les opérations légitimes en vert et fait retentir l'alerte dès qu'une anomalie critique est détectée, avant de compiler le rapport quotidien.*
>
> *Ce pipeline illustre parfaitement le rôle de l'Architecte IA : concevoir une chaîne de bout en bout résiliente, scalable et directement alignée sur la rentabilité de l'entreprise.*
>
> *Je vous remercie pour votre attention et je suis à votre disposition pour vos questions."*
