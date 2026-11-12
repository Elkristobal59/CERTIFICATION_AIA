import os
import sys
import time
import json
import importlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

features_mod = importlib.import_module("01_train.features")
load_project_env = features_mod.load_project_env
prepare_features = features_mod.prepare_features
FEATURE_COLUMNS = features_mod.FEATURE_COLUMNS

load_project_env()

try:
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

PARENT_CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "fraudTest.csv")
LOCAL_CSV_PATH = os.path.join(BASE_DIR, "fraudTest.csv")
SAMPLE_CSV_PATH = os.path.join(BASE_DIR, "sample_fraud_data.csv")
MODEL_DIR = os.path.join(BASE_DIR, "01_train")
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.joblib")
META_PATH = os.path.join(MODEL_DIR, "model_metadata.json")


def resolve_dataset_path() -> str:
    for candidate in (LOCAL_CSV_PATH, PARENT_CSV_PATH, SAMPLE_CSV_PATH):
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("Aucun fichier d'entraînement trouvé (fraudTest.csv ou sample_fraud_data.csv).")


def build_candidate_models():
    """Retourne les pipelines candidats intégrant StandardScaler + classifieur."""
    return [
        (
            "LogisticRegression_Balanced",
            Pipeline([
                ("scaler", StandardScaler()),
                ("classifier", LogisticRegression(class_weight="balanced", max_iter=500, random_state=42)),
            ]),
            {"algorithm": "LogisticRegression", "class_weight": "balanced", "max_iter": 500, "scaler": "StandardScaler"},
        ),
        (
            "RandomForest_Balanced",
            Pipeline([
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=80, max_depth=12, class_weight="balanced", n_jobs=-1, random_state=42
                    ),
                ),
            ]),
            {
                "algorithm": "RandomForestClassifier",
                "n_estimators": 80,
                "max_depth": 12,
                "class_weight": "balanced",
                "scaler": "StandardScaler",
            },
        ),
        (
            "HistGradientBoosting_Balanced",
            Pipeline([
                ("scaler", StandardScaler()),
                (
                    "classifier",
                    HistGradientBoostingClassifier(
                        class_weight="balanced", max_iter=150, learning_rate=0.08, max_depth=6, random_state=42
                    ),
                ),
            ]),
            {
                "algorithm": "HistGradientBoostingClassifier",
                "class_weight": "balanced",
                "max_iter": 150,
                "learning_rate": 0.08,
                "max_depth": 6,
                "scaler": "StandardScaler",
            },
        ),
    ]


def train():
    print("=" * 72)
    print("🚀 BENCHMARK & ENTRAÎNEMENT MULTI-MODÈLES MLFLOW — BLOC 3 (RNCP 41993)")
    print("=" * 72)

    csv_path = resolve_dataset_path()
    print(f"📖 Chargement intégral du dataset : {csv_path}")
    df = pd.read_csv(csv_path)
    frauds_total = int(df["is_fraud"].sum())
    print(f"✅ Dataset chargé : {len(df):,} transactions ({frauds_total:,} fraudes | {frauds_total / len(df) * 100:.2f} %)")

    print("⚙️ Feature Engineering partagé (Distance Haversine, Heure, Âge, Densité)...")
    X = prepare_features(df)
    y = df["is_fraud"].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "RealTime_Fraud_Detection_AIA_Bloc3")
    registered_model_name = os.getenv("MLFLOW_MODEL_NAME", "fraud_detection_model")

    mlflow_ready = False
    if MLFLOW_AVAILABLE:
        try:
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment(experiment_name)
            mlflow_ready = True
            print(f"📡 Connecté au serveur MLflow : {tracking_uri}")
        except Exception as exc:
            print(f"⚠️ Serveur MLflow injoignable ({exc}). Entraînement poursuivi en local.")

    results = []
    signature = infer_signature(X_train.head(50), pd.Series([0, 1] * 25)[:50]) if mlflow_ready else None

    for run_name, pipeline, params in build_candidate_models():
        t0 = time.time()
        print(f"\n🧠 Entraînement : {run_name} ...")
        pipeline.fit(X_train, y_train)
        train_sec = round(time.time() - t0, 2)

        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1]

        metrics = {
            "roc_auc": round(float(roc_auc_score(y_test, y_prob)), 4),
            "pr_auc": round(float(average_precision_score(y_test, y_prob)), 4),
            "recall": round(float(recall_score(y_test, y_pred)), 4),
            "precision": round(float(precision_score(y_test, y_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_test, y_pred, zero_division=0)), 4),
            "training_duration_sec": train_sec,
        }
        print(
            f"   ➔ ROC-AUC={metrics['roc_auc']:.4f} | PR-AUC={metrics['pr_auc']:.4f} "
            f"| Recall={metrics['recall']*100:.1f}% | F1={metrics['f1']:.4f} ({train_sec}s)"
        )

        model_version = None
        run_id = None
        if mlflow_ready:
            try:
                with mlflow.start_run(run_name=run_name) as run:
                    run_id = run.info.run_id
                    mlflow.log_params(params)
                    mlflow.log_param("sample_size", len(df))
                    mlflow.log_param("train_size", len(X_train))
                    mlflow.log_param("test_size", len(X_test))
                    mlflow.log_param("features", ",".join(FEATURE_COLUMNS))
                    mlflow.log_metrics(metrics)
                    model_info = mlflow.sklearn.log_model(
                        sk_model=pipeline,
                        name="model",
                        signature=signature,
                        input_example=X_train.head(5),
                        serialization_format="cloudpickle",
                        pip_requirements=[
                            "scikit-learn==1.7.2",
                            "pandas",
                            "numpy",
                            "joblib",
                        ],
                        registered_model_name=registered_model_name,
                    )
                    model_version = model_info.registered_model_version
            except Exception as exc:
                print(f"   ⚠️ Erreur enregistrement MLflow pour {run_name} : {exc}")

        results.append({
            "run_name": run_name,
            "pipeline": pipeline,
            "params": params,
            "metrics": metrics,
            "run_id": run_id,
            "model_version": model_version,
        })

    # Sélection objective du meilleur modèle sur ROC-AUC puis PR-AUC
    ranked = sorted(results, key=lambda r: (r["metrics"]["roc_auc"], r["metrics"]["pr_auc"]), reverse=True)
    champion = ranked[0]
    challenger = ranked[1] if len(ranked) > 1 else None

    print("\n" + "-" * 72)
    print(f"🏆 MODÈLE CHAMPION SÉLECTIONNÉ : {champion['run_name']} (ROC-AUC={champion['metrics']['roc_auc']})")

    if mlflow_ready and champion["model_version"] is not None:
        try:
            client = MlflowClient(tracking_uri=tracking_uri)
            client.set_registered_model_alias(registered_model_name, "champion", str(champion["model_version"]))
            print(f"   🔖 Alias MLflow '@champion' attribué à {registered_model_name} v{champion['model_version']}")
            if challenger and challenger["model_version"] is not None:
                client.set_registered_model_alias(registered_model_name, "challenger", str(challenger["model_version"]))
                print(f"   🥈 Alias MLflow '@challenger' attribué à {registered_model_name} v{challenger['model_version']}")
        except Exception as exc:
            print(f"   ⚠️ Impossible d'assigner les alias MLflow : {exc}")

    # Sauvegarde locale de secours (pour conteneur autonome si MLflow hors ligne)
    joblib.dump(champion["pipeline"], MODEL_PATH)
    size_bytes = os.path.getsize(MODEL_PATH)

    metadata = {
        "model_name": registered_model_name,
        "alias": "champion",
        "champion_run_name": champion["run_name"],
        "model_type": champion["params"]["algorithm"],
        "preprocessing": "StandardScaler + Haversine Feature Engineering",
        "features": list(FEATURE_COLUMNS),
        "parameters": champion["params"],
        "sample_size": len(df),
        "fraud_count_dataset": frauds_total,
        "metrics": champion["metrics"],
        "mlflow_run_id": champion["run_id"],
        "mlflow_version": champion["model_version"],
        "artifact_size_bytes": size_bytes,
        "benchmark": [
            {"run_name": r["run_name"], "metrics": r["metrics"], "mlflow_version": r["model_version"]}
            for r in ranked
        ],
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"💾 Modèle sérialisé : {MODEL_PATH} ({size_bytes / 1024:.1f} Ko)")
    print(f"✅ Métadonnées enregistrées : {META_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    train()
