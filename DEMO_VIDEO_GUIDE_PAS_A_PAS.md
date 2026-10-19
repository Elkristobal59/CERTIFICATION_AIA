# 🎬 Guide Pas-à-Pas pour Enregistrer Votre Vidéo de Démonstration (Vidyard / OBS)

> **Titre Visé :** Architecte en Intelligence Artificielle (RNCP 41993 - Bloc 3)  
> **Exigence du Cahier des Charges :** *"Une vidéo de votre infrastructure en fonctionnement sur un exemple. Vous pouvez utiliser Vidyard pour ce faire."*  
> **Durée Recommandée :** **2 minutes 30 à 3 minutes maximum**  

---

## 🛠️ 1. Préparation Technique Avant d'Enregistrer (1 minute)

1. **Outil d'enregistrement au choix :**
   * **Option 1 (Recommandée par Jedha) :** Extension Chrome gratuite [Vidyard](https://www.vidyard.com/) (enregistrement d'écran en 1 clic avec export de lien direct).
   * **Option 2 :** [OBS Studio](https://obsproject.com/) ou l'outil Capture d'écran Windows (Touche `Windows + Alt + R`).
2. **Disposition de votre écran :**
   * Ouvrez **VS Code** sur le dossier `d:\AIL-FT-02\CERTIF AIL\FRAUD_DETECTION_BLOC_3\`.
   * Affichez le terminal intégré en bas ou sur la droite, avec une police lisible.
   * Ayez sous la main le fichier [`run_full_pipeline_demo.py`](file:///d:/AIL-FT-02/CERTIF%20AIL/FRAUD_DETECTION_BLOC_3/run_full_pipeline_demo.py).

---

## ⏱️ 2. Trame Minute par Minute de Votre Vidéo

### 🔹 [00:00 - 00:35] : Introduction & Présentation de l'Architecture
* **À l'écran :** Montrez l'arborescence des dossiers dans VS Code (`01_train`, `02_api`, `03_pipeline_streaming`, `04_batch_airflow`, `05_database`).
* **Ce que vous dites :**  
  > *"Bonjour. Dans cette vidéo, je vous présente notre pipeline de détection de fraudes bancaires en production pour le Bloc 3.  
  > Notre architecture est découpée en composants modulaires : un modèle entraîné sur 550 000 transactions, une API de scoring conteneurisée, une tuyauterie de streaming Kafka ingérant les flux en temps réel, un système d'alerte immédiate, et un DAG Airflow pour l'audit matinal quotidien demandé par le métier."*

---

### 🔹 [00:35 - 01:50] : Démonstration du Streaming & Alerte Immédiate Live
* **À l'écran :** Dans votre terminal, lancez la commande :
  ```powershell
  python run_full_pipeline_demo.py
  ```
* **Ce qui se passe :**
  1. L'initialisation de l'infrastructure s'affiche.
  2. Les transactions commencent à défiler en direct depuis l'API HuggingFace (`🟢 [VALIDE]`).
  3. **L'encadré d'alerte rouge apparaît en direct avec la sonnerie d'alerte :**
     ```
     ╔══════════════════════════════════════════════════════════════╗
     ║ 🚨 ALERTE FRAUDE EN TEMPS RÉEL INTERCEPTÉE ! 🚨             ║
     ║ Probabilité : 75.4% | Décision : BLOCK_IMMEDIATE             ║
     ╚══════════════════════════════════════════════════════════════╝
     ```
* **Ce que vous dites :**  
  > *"Je lance le pipeline en direct. Le Producer interroge l'API temps réel de transactions et publie dans le topic Kafka.  
  > Le Consumer interroge notre modèle d'inférence : les transactions légitimes sont validées en moins de 3 millisecondes.  
  > Et voici l'événement critique : dès qu'une anomalie majeure est détectée — ici une transaction suspecte avec un risque de plus de 75% —, notre service d'alerte flash est déclenché instantanément pour bloquer la carte, répondant ainsi à la première exigence du métier."*

---

### 🔹 [01:50 - 02:40] : L'Audit Matinal Quotidien (Airflow Batch)
* **À l'écran :**
  1. La console affiche l'Étape 4 : exécution de l'audit des 24h.
  2. Ouvrez dans VS Code le fichier généré :  
     [`04_batch_airflow/RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md`](file:///d:/AIL-FT-02/CERTIF%20AIL/FRAUD_DETECTION_BLOC_3/04_batch_airflow/RAPPORT_AUDIT_MATINAL_QUOTIDIEN.md).
* **Ce que vous dites :**  
  > *"À la fin du flux, notre DAG Apache Airflow s'exécute pour accomplir la seconde exigence métier : compiler chaque matin l'audit complet des 24 dernières heures.  
  > Comme vous pouvez le constater dans ce rapport markdown consolidé, la direction des risques dispose du volume total traité, du montant des fraudes neutralisées et du taux de sinistralité, assurant une conformité parfaite pour les régulateurs."*

---

### 🔹 [02:40 - 03:00] : Conclusion
* **Ce que vous dites :**  
  > *"Ce pipeline concilie avec succès la réactivité de Kafka pour la protection immédiate et la rigueur d'Airflow pour la gouvernance des données.  
  > Je vous remercie pour votre attention."*

---

## ✅ 3. Vérifications Finales Après Enregistrement
1. Copiez le lien vidéo généré par Vidyard (ou enregistrez votre fichier MP4).
2. Ajoutez le lien tout en haut de votre dossier pour le jury.
3. Vous êtes prêt pour obtenir la note maximale sur ce bloc technique ! 🚀
