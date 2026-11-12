import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(BASE_DIR, "schema_architecture_infrastructure_fraud.png")


def draw_box(ax, x, y, w, h, title, lines, edge_color, fill_color="#0F172A", title_color="#F8FAFC", badge=None):
    box = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.004,rounding_size=0.014",
        linewidth=1.9,
        edgecolor=edge_color,
        facecolor=fill_color,
        zorder=3,
    )
    ax.add_patch(box)

    if badge:
        bw = min(w * 0.56, 0.125)
        b_patch = FancyBboxPatch(
            (x + w - bw - 0.008, y + h - 0.028), bw, 0.024,
            boxstyle="round,pad=0.002,rounding_size=0.006",
            linewidth=0,
            facecolor=edge_color,
            zorder=4,
        )
        ax.add_patch(b_patch)
        ax.text(
            x + w - bw / 2 - 0.008, y + h - 0.016, badge,
            ha="center", va="center", fontsize=7.0, fontweight="bold", color="#090D16", zorder=5
        )

    ax.text(
        x + 0.010, y + h - 0.036, title,
        ha="left", va="top", fontsize=9.8, fontweight="bold", color=title_color, zorder=5
    )

    body = "\n".join(lines)
    ax.text(
        x + 0.010, y + h - 0.070, body,
        ha="left", va="top", fontsize=8.0, linespacing=1.40, color="#CBD5E1", zorder=5
    )


def draw_arrow(ax, x1, y1, x2, y2, label="", color="#38BDF8", rad=0.0, lx_off=0.0, ly_off=0.0):
    arrow = mpatches.FancyArrowPatch(
        (x1, y1), (x2, y2),
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>,head_length=7,head_width=4.5",
        linewidth=1.9,
        color=color,
        zorder=2,
    )
    ax.add_patch(arrow)
    if label:
        mx = (x1 + x2) / 2 + lx_off
        my = (y1 + y2) / 2 + ly_off
        ax.text(
            mx, my, label,
            ha="center", va="center", fontsize=7.8, fontweight="bold", color=color,
            bbox=dict(boxstyle="round,pad=0.22", facecolor="#090D16", edgecolor=color, linewidth=0.9),
            zorder=6,
        )


def build_diagram():
    fig, ax = plt.subplots(figsize=(18.5, 10.6), dpi=240)
    fig.patch.set_facecolor("#090D16")
    ax.set_facecolor("#090D16")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    # Header
    ax.text(
        0.5, 0.968,
        "ARCHITECTURE HYBRIDE STREAMING & BATCH — DÉTECTION DE FRAUDE BANCAIRE (RNCP 41993 - BLOC 3)",
        ha="center", va="top", fontsize=14.5, fontweight="bold", color="#F8FAFC"
    )
    ax.text(
        0.5, 0.935,
        "Docker Local (Kafka • FastAPI 19.4 ms • MLflow • Airflow)  +  Cloud Managé (Neon PostgreSQL • AWS S3 eu-west-3 • SMTP TLS)",
        ha="center", va="top", fontsize=9.8, color="#94A3B8"
    )

    # Background Lane Bands
    lanes = [
        (0.015, 0.455, 0.97, 0.450, "#0F1B2E", "#1E3A5F", "VOIE RAPIDE TEMPS RÉEL (KAFKA STREAMING & SCORING < 40 ms)"),
        (0.015, 0.045, 0.97, 0.375, "#111A26", "#1F3B2D", "GOVERNANCE MLOPS, DATA LAKE MEDALLION & ORCHESTRATION BATCH AIRFLOW"),
    ]
    for lx, ly, lw, lh, fc, ec, ltitle in lanes:
        panel = FancyBboxPatch(
            (lx, ly), lw, lh,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            linewidth=1.3, linestyle="--", edgecolor=ec, facecolor=fc, alpha=0.55, zorder=1
        )
        ax.add_patch(panel)
        ax.text(lx + 0.012, ly + lh - 0.010, ltitle, ha="left", va="top", fontsize=8.8, fontweight="bold", color="#93C5FD", zorder=2)

    # ROW 1: Streaming Lane (y ~ 0.62..0.85 and 0.48..0.60)
    draw_box(
        ax, 0.030, 0.650, 0.165, 0.215,
        "1. Source & Producer",
        [
            "• API Hugging Face Live",
            "  (ou replay dataset contrôlé)",
            "• confluent-kafka Producer",
            "• Timeout 10s & retries sûrs",
            "• Publication topic JSON",
        ],
        edge_color="#38BDF8", badge="INGESTION"
    )

    draw_box(
        ax, 0.230, 0.650, 0.175, 0.215,
        "2. Apache Kafka KRaft",
        [
            "• Broker confluentinc/7.5.0",
            "• Topic : raw-transactions",
            "• Topic DLQ : fraud-dlq",
            "• Tampon anti-rafales disque",
            "• Supervision Kafka UI :8085",
        ],
        edge_color="#A855F7", badge="BROKER EVENT"
    )

    draw_box(
        ax, 0.440, 0.650, 0.180, 0.215,
        "3. Consumer & Pandera",
        [
            "• Validation Pandera Schema",
            "  (amt >= 0, coords GPS valides)",
            "• Rejet auto vers fraud-dlq",
            "  & zone rejected/ (Quarantaine)",
            "• Conformité PCI-DSS / RGPD",
        ],
        edge_color="#F59E0B", badge="QUALITY GATE"
    )

    draw_box(
        ax, 0.655, 0.650, 0.155, 0.215,
        "4. FastAPI Scoring",
        [
            "• Microservice Python 3.11",
            "• Endpoint POST /predict",
            "• Validation stricte Pydantic",
            "• Médiane HTTP : 19.4 ms",
            "• p95 : 28.9 ms (CPU)",
        ],
        edge_color="#10B981", badge="INFÉRENCE"
    )

    draw_box(
        ax, 0.840, 0.625, 0.135, 0.240,
        "5. Alertes & Neon SQL",
        [
            "• Neon PostgreSQL",
            "  (fraud_db : txns,",
            "   fraud_alerts, dlq)",
            "• PAN **** 1234",
            "• SHA-256 + SALT",
            "• Gmail TLS / Mailpit",
        ],
        edge_color="#EF4444", badge="ALERTE & SINK"
    )

    # DLQ Quarantine Box (bottom of lane 1, cleanly separated)
    draw_box(
        ax, 0.385, 0.475, 0.255, 0.120,
        "Quarantaine DLQ & Sécurité (.env)",
        [
            "• Rejets amt < 0 / JSON -> fraud-dlq + rejected/",
            "• PII supprimés/pseudonymisés avant stockage DLQ",
        ],
        edge_color="#F97316"
    )

    # ROW 2: MLOps & Batch Medallion (y ~ 0.08..0.37)
    draw_box(
        ax, 0.028, 0.078, 0.228, 0.295,
        "6. MLflow + Neon + AWS S3",
        [
            "• Dataset : 555 719 tx (2 145 fraudes)",
            "• 3 Modèles + StandardScaler + Haversine :",
            "  - HistGradientBoosting : 0.9876 AUC (91.6% Rec)",
            "  - RandomForest : 0.9836 AUC (@challenger)",
            "  - LogisticRegression : 0.8236 AUC",
            "• Backend Neon SSL (fraud_mlflow_db)",
            "• AWS S3 eu-west-3 -> @champion",
        ],
        edge_color="#EC4899", badge="MLOPS REGISTRY"
    )

    draw_box(
        ax, 0.288, 0.078, 0.285, 0.295,
        "7. Data Lake Medallion Parquet",
        [
            "• Zone BRONZE : Parquet partitionné Y/M/D",
            "  (PAN déjà masqué **** **** **** 1234)",
            "• Zone REJECTED : quarantaine Pandera DLQ",
            "• Zone SILVER : validation batch + Hash SHA-256 salé",
            "  + DROP strict PII (first, last, street, dob, zip)",
            "• Zone GOLD : features modélisation & KPIs Drift",
            "• Traçabilité OpenLineage JSONL complète",
        ],
        edge_color="#22D3EE", badge="MEDALLION"
    )

    draw_box(
        ax, 0.605, 0.078, 0.205, 0.295,
        "8. Apache Airflow DAG",
        [
            "• Conteneur Apache Airflow 2.11",
            "• DAG : daily_fraud_audit_pipeline",
            "• Planifié @ 06h00 UTC :",
            "  1. etl_bronze_to_silver",
            "  2. gold_audit_and_drift",
            "  3. check_retrain_trigger",
            "• Exports Markdown & daily_audit",
        ],
        edge_color="#3B82F6", badge="ORCHESTRATION"
    )

    draw_box(
        ax, 0.840, 0.078, 0.133, 0.295,
        "9. Cloud & FinOps",
        [
            "• Hybride Actif (~0 €) :",
            "  - Docker Local Compute",
            "  - Neon Serverless SSL",
            "  - AWS S3 (eu-west-3)",
            "• Full-Cloud Prêt (.env) :",
            "  - EC2 / App Runner",
            "  - Pricing vs Cost Expl.",
        ],
        edge_color="#84CC16", badge="FINOPS / CLOUD"
    )

    # Arrows Streaming
    draw_arrow(ax, 0.197, 0.758, 0.226, 0.758, "produce()", "#38BDF8")
    draw_arrow(ax, 0.407, 0.758, 0.436, 0.758, "poll()", "#A855F7")
    draw_arrow(ax, 0.622, 0.758, 0.651, 0.758, "HTTP /predict", "#10B981")
    draw_arrow(ax, 0.812, 0.758, 0.836, 0.758, "score", "#EF4444")

    # DLQ arrow & Quarantaine -> Rejected Parquet
    draw_arrow(ax, 0.515, 0.646, 0.515, 0.599, "amt < 0 -> REJET", "#F97316")
    draw_arrow(ax, 0.470, 0.471, 0.455, 0.379, "Parquet rejected/", "#F97316")

    # MLflow -> FastAPI (@champion) routed orthogonally along the inter-lane corridor
    from matplotlib.path import Path
    verts = [(0.145, 0.378), (0.145, 0.422), (0.730, 0.422), (0.730, 0.645)]
    codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO]
    champ_arrow = mpatches.FancyArrowPatch(
        path=Path(verts, codes),
        arrowstyle="-|>,head_length=7,head_width=4.5",
        linewidth=2.0,
        color="#EC4899",
        zorder=2,
    )
    ax.add_patch(champ_arrow)
    ax.text(
        0.655, 0.422,
        "load_model('models:/fraud_detection_model@champion')",
        ha="center", va="center", fontsize=7.8, fontweight="bold", color="#EC4899",
        bbox=dict(boxstyle="round,pad=0.22", facecolor="#090D16", edgecolor="#EC4899", linewidth=0.9),
        zorder=6,
    )

    # Consumer / Postgres -> Bronze Lake
    draw_arrow(ax, 0.905, 0.620, 0.550, 0.378, "Bronze Parquet + Audit", "#22D3EE", rad=-0.07, lx_off=0.05, ly_off=0.01)

    # Airflow orchestrates Medallion & checks FinOps/Cloud
    draw_arrow(ax, 0.602, 0.225, 0.576, 0.225, "ETL", "#3B82F6")
    draw_arrow(ax, 0.812, 0.225, 0.837, 0.225, "Audit", "#84CC16")

    # Footer
    ax.text(
        0.5, 0.015,
        "Certification Architecte en Intelligence Artificielle (RNCP 41993 - Bloc 3)  •  Stack 100 % reproductible via Docker Compose & .env sans secrets en clair",
        ha="center", va="bottom", fontsize=8.8, color="#64748B"
    )

    plt.tight_layout(pad=0.4)
    plt.savefig(OUT_PATH, dpi=240, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"✅ Schéma généré : {OUT_PATH}")


if __name__ == "__main__":
    build_diagram()
