import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def create_architecture_diagram():
    output_dir = r"D:\AIL-FT-02\CERTIF AIL\FRAUD_DETECTION_BLOC_3\03_BLOC_3_PIPELINE_FRAUD_DETECTION\LIVRABLES"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "schema_architecture_infrastructure_fraud.png")

    fig, ax = plt.subplots(figsize=(18, 12), dpi=300)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')
    ax.set_xlim(0, 18)
    ax.set_ylim(0, 12)
    ax.axis('off')

    # ==========================================
    # HEADER / TITRE
    # ==========================================
    ax.text(9, 11.45, "Data Infrastructure Architecture — Real-Time Fraud Detection", 
            ha='center', va='center', fontsize=23, fontweight='bold', color='#0F172A', family='sans-serif')
    ax.text(9, 11.05, "Architecture Industrielle Conforme au Modèle Pédagogique Jedha (RNCP 41993 - Bloc 3)", 
            ha='center', va='center', fontsize=11.5, color='#475569', style='italic', family='sans-serif')

    # Helper pour boîtes principales avec bandeau de titre
    def draw_box(x, y, w, h, bg_color, border_color, title, lw=2.2):
        # Boîte extérieure
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06,rounding_size=0.25",
                                     facecolor=bg_color, edgecolor=border_color, linewidth=lw, zorder=2)
        ax.add_patch(box)
        # Bandeau de titre en haut
        title_box = patches.FancyBboxPatch((x + 0.1, y + h - 0.55), w - 0.2, 0.45, 
                                           boxstyle="round,pad=0.03,rounding_size=0.12",
                                           facecolor=border_color, edgecolor='none', zorder=3)
        ax.add_patch(title_box)
        ax.text(x + w/2, y + h - 0.32, title, ha='center', va='center', 
                fontsize=12.5, fontweight='bold', color='#FFFFFF', family='sans-serif', zorder=4)

    # Helper pour sous-cartes blanches
    def draw_subcard(x, y, w, h, title, items, badge=None, badge_color="#3B82F6"):
        card = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.15",
                                      facecolor='#FFFFFF', edgecolor='#CBD5E1', linewidth=1.2, zorder=3)
        ax.add_patch(card)
        if badge:
            badge_w = len(badge) * 0.12 + 0.35
            b_patch = patches.FancyBboxPatch((x + 0.15, y + h - 0.34), badge_w, 0.22, 
                                             boxstyle="round,pad=0.02,rounding_size=0.06",
                                             facecolor=badge_color, edgecolor='none', zorder=4)
            ax.add_patch(b_patch)
            ax.text(x + 0.15 + badge_w/2, y + h - 0.23, badge, fontsize=7.2, fontweight='bold', color='#FFFFFF', 
                    ha='center', va='center', family='sans-serif', zorder=5)
            ax.text(x + 0.25 + badge_w, y + h - 0.23, title, fontsize=9.2, fontweight='bold', color='#1E293B', 
                    va='center', family='sans-serif', zorder=5)
        else:
            ax.text(x + 0.2, y + h - 0.23, title, fontsize=9.2, fontweight='bold', color='#1E293B', 
                    va='center', family='sans-serif', zorder=4)
            
        y_cursor = y + h - 0.52
        for item in items:
            ax.text(x + 0.25, y_cursor, f"• {item}", fontsize=8.0, color='#334155', family='sans-serif', zorder=4)
            y_cursor -= 0.25

    # ==========================================
    # 1. BLOC GAUCHE : BUILD ALGORITHM
    # ==========================================
    draw_box(0.6, 5.7, 5.2, 4.9, '#F3E8FF', '#7E22CE', "1. Build Algorithm")
    
    draw_subcard(0.85, 8.85, 4.7, 1.0, "Data Source (Historique)", 
                 ["Fichier fraudTest.csv (555 719 transactions)", "Labels supervisés : is_fraud (0: sain, 1: fraude)"],
                 badge="SOURCE", badge_color="#7E22CE")

    draw_subcard(0.85, 7.35, 4.7, 1.35, "Preprocessing & Feature Eng.", 
                 ["Distance Haversine (distance porteur - commerçant)", "Extraction temporelle (heure) & Âge du porteur", "StandardScaler + Gestion du déséquilibre de classes"],
                 badge="PIPELINE", badge_color="#9333EA")

    draw_subcard(0.85, 5.85, 4.7, 1.35, "Model Training (Scikit-Learn)", 
                 ["HistGradientBoostingClassifier optimisé", "Performance : ROC-AUC > 0.98, Rappel > 91%", "Sérialisation : fraud_model.joblib (1.2 Mo)"],
                 badge="MODÈLE", badge_color="#A855F7")

    # ==========================================
    # 2. BLOC CENTRE : MLFLOW & SERVING
    # ==========================================
    draw_box(6.4, 5.7, 5.2, 4.9, '#DCFCE7', '#15803D', "2. MLflow & Serving")

    draw_subcard(6.65, 8.85, 4.7, 1.0, "MLflow Model Registry", 
                 ["Tracking des runs, hyperparamètres et métriques", "Artefacts : Signatures I/O, modèle & métadonnées", "Statut du modèle : Passage en Stage 'Production'"],
                 badge="TRACKING", badge_color="#16A34A")

    draw_subcard(6.65, 7.20, 4.7, 1.5, "FastAPI Microservice (REST)", 
                 ["Conteneur Dockerisé (Image : fraud-scoring-api:latest)", "Compatible Serverless Cloud Run (Port 8080)", "Latence d'inférence ultra-faible : < 4 ms", "Documentation interactive : /predict & /docs"],
                 badge="SERVING", badge_color="#22C55E")

    draw_subcard(6.65, 5.85, 4.7, 1.2, "Règles Décisionnelles Métier", 
                 ["p >= 75% ➔ BLOCK_IMMEDIATE (Alerte instantanée)", "p >= 50% ➔ CHALLENGE_3DS (Authentification forte)", "p < 50% ➔ ALLOW (Transaction validée)"],
                 badge="DÉCISION", badge_color="#15803D")

    # ==========================================
    # 3. BLOC DROITE : CONSUME DATA (KAFKA STREAMING)
    # ==========================================
    draw_box(12.2, 5.7, 5.2, 4.9, '#FEF3C7', '#B45309', "3. Consume Data")

    draw_subcard(12.45, 8.85, 4.7, 1.0, "Real-Time Producer", 
                 ["API Live HuggingFace : /current-transactions", "Fallback Replay haute fidélité (Générateur local)"],
                 badge="INGESTION", badge_color="#D97706")

    draw_subcard(12.45, 7.20, 4.7, 1.5, "Apache Kafka KRaft (Broker)", 
                 ["Topic Source : 'raw-transactions' (3 partitions)", "Architecture moderne KRaft (zéro dépendance ZooKeeper)", "Rétention disque 7 jours & Commit d'offsets fiables", "Supervision Web Kafka UI sur port 8085"],
                 badge="KAFKA", badge_color="#B45309")

    draw_subcard(12.45, 5.85, 4.7, 1.2, "Dead Letter Queue & Alertes", 
                 ["Topic 'fraud-dlq' : Isolation des anomalies (-150 €)", "Moteur d'alerte instantanée PCI-DSS (< 15 ms)", "Validation stricte du schéma Pydantic avant scoring"],
                 badge="RÉSILIENCE", badge_color="#DC2626")

    # ==========================================
    # 4. BLOC BAS-DROITE (MILIEU) : STORE DATA
    # ==========================================
    draw_box(12.2, 2.9, 5.2, 2.3, '#E0F2FE', '#0369A1', "4. Store Data")

    draw_subcard(12.45, 4.05, 4.7, 0.95, "Data Lake Bronze (Apache Parquet)", 
                 ["Format compressé Snappy, partitionné par date (Y/M/D)", "Réduction stockage 75% vs JSON brut, Column Pruning"],
                 badge="LAKEHOUSE", badge_color="#0284C7")

    draw_subcard(12.45, 3.05, 4.7, 0.85, "Base SQL Opérationnelle (SQLite / Postgres)", 
                 ["Tables : transactions, dead_letter_queue, daily_audit", "Piste d'audit immuable et conformité financière"],
                 badge="SQL BDD", badge_color="#0369A1")

    # ==========================================
    # 5. BLOC BAS-DROITE (BAS) : LEVERAGE DATA
    # ==========================================
    draw_box(12.2, 0.35, 5.2, 2.1, '#F1F5F9', '#334155', "5. Leverage Data")

    draw_subcard(12.45, 1.35, 4.7, 0.95, "Apache Airflow DAG (Daily Audit)", 
                 ["Déclenchement automatisé quotidien à 06h00 UTC", "Rapprochement bancaire sur 24h & Calcul des taux"],
                 badge="AIRFLOW", badge_color="#475569")

    draw_subcard(12.45, 0.48, 4.7, 0.75, "Livrables Métier & Rapports", 
                 ["Rapport exécutif Markdown généré (`RAPPORT_AUDIT...`)", "Notification Webhooks & Synthèse des fraudes arrêtées"],
                 badge="AUDIT", badge_color="#0F172A")

    # ==========================================
    # FLÈCHES DE FLUX DIRECTIONNELLES AVEC LABELS
    # ==========================================
    # Flèche 1: Build -> MLflow
    ax.annotate('', xy=(6.4, 7.95), xytext=(5.8, 7.95),
                arrowprops=dict(facecolor='#7E22CE', edgecolor='#7E22CE', width=2.5, headwidth=9, headlength=10), zorder=6)
    ax.text(6.1, 8.25, "Log Model\n& Weights", ha='center', va='center', fontsize=8.2, fontweight='bold', color='#7E22CE', zorder=6)

    # Flèche 2: MLflow -> Consume Data (Interrogation Inférence)
    ax.annotate('', xy=(12.2, 7.95), xytext=(11.6, 7.95),
                arrowprops=dict(facecolor='#15803D', edgecolor='#15803D', width=2.5, headwidth=9, headlength=10), zorder=6)
    ax.text(11.9, 8.25, "Inférence HTTP\n< 4ms REST", ha='center', va='center', fontsize=8.2, fontweight='bold', color='#15803D', zorder=6)

    # Flèche 3: Consume Data -> Store Data (Flèche vers le bas)
    ax.annotate('', xy=(14.8, 5.2), xytext=(14.8, 5.7),
                arrowprops=dict(facecolor='#0369A1', edgecolor='#0369A1', width=2.5, headwidth=9, headlength=10), zorder=6)
    ax.text(15.0, 5.45, "Persistance\nSynchrone", ha='left', va='center', fontsize=8.2, fontweight='bold', color='#0369A1', zorder=6)

    # Flèche 4: Store Data -> Leverage Data (Flèche vers le bas)
    ax.annotate('', xy=(14.8, 2.45), xytext=(14.8, 2.9),
                arrowprops=dict(facecolor='#334155', edgecolor='#334155', width=2.5, headwidth=9, headlength=10), zorder=6)
    ax.text(15.0, 2.68, "Batch Audit\n(06h00 UTC)", ha='left', va='center', fontsize=8.2, fontweight='bold', color='#334155', zorder=6)

    # ==========================================
    # CARTOUCHE DE VALIDATION RNCP EN BAS À GAUCHE
    # ==========================================
    cartouche = patches.FancyBboxPatch((0.6, 0.35), 11.0, 4.85, boxstyle="round,pad=0.06,rounding_size=0.25",
                                       facecolor='#FFFFFF', edgecolor='#0EA5E9', linewidth=1.8, zorder=2)
    ax.add_patch(cartouche)
    
    # Titre du cartouche
    t_box = patches.FancyBboxPatch((0.9, 4.65), 10.4, 0.42, boxstyle="round,pad=0.02,rounding_size=0.08",
                                   facecolor='#0284C7', edgecolor='none', zorder=3)
    ax.add_patch(t_box)
    ax.text(6.1, 4.86, "CORRESPONDANCE INTÉGRALE AVEC LE RÉFÉRENTIEL RNCP 41993 - BLOC 3", 
            ha='center', va='center', fontsize=11, fontweight='bold', color='#FFFFFF', family='sans-serif', zorder=4)
    
    rncp_items = [
        ("C1 - Conception Pipeline Streaming", "Apache Kafka KRaft avec cluster partitionné (haute vélocité, zéro perte de message)."),
        ("C2 - ETL / ELT & Stockage Hybride", "Ingestion continue -> Transformation et stockage Parquet partitionné + Base SQL opérationnelle."),
        ("C3 - Automatisation & Industrialisation", "Microservice FastAPI conteneurisé (Scale-to-Zero Cloud Run) + Orchestration batch Airflow."),
        ("C4 - Sécurité & Masquage PCI-DSS", "Numéros de carte tronqués (6+4), hachage SHA-256 des identités et alertes flash < 15ms."),
        ("C5 - Data Quality & Dead Letter Queue", "Validation Pydantic des schémas, rejet montants négatifs et topic d'isolement 'fraud-dlq'.")
    ]
    
    y_rncp = 4.22
    for code, desc in rncp_items:
        # Badge code
        b = patches.FancyBboxPatch((0.9, y_rncp - 0.16), 3.4, 0.32, boxstyle="round,pad=0.02,rounding_size=0.08",
                                   facecolor='#E0F2FE', edgecolor='#0284C7', linewidth=1, zorder=3)
        ax.add_patch(b)
        ax.text(1.0, y_rncp, code, fontsize=8.5, fontweight='bold', color='#0369A1', va='center', family='sans-serif', zorder=4)
        ax.text(4.5, y_rncp, desc, fontsize=8.5, color='#334155', va='center', family='sans-serif', zorder=4)
        y_rncp -= 0.62

    # Signature auteur
    ax.text(6.1, 0.70, "Candidat : Christopher GILLERON  |  Certification Architecte IA  |  Dépôt Officiel : github.com/Elkristobal59/CERTIFICATION_AIA", 
            ha='center', va='center', fontsize=8.5, color='#64748B', style='italic', family='sans-serif', zorder=3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Diagram successfully polished at: {output_path}")

if __name__ == '__main__':
    create_architecture_diagram()
