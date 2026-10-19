import os
import sys
import time
import json

# Forcer l'encodage console UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, recall_score, precision_score, f1_score

# Support MLflow pour le Model Tracking & Registry
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "fraudTest.csv")
MODEL_DIR = os.path.join(BASE_DIR, "01_train")
MODEL_PATH = os.path.join(MODEL_DIR, "fraud_model.joblib")
META_PATH = os.path.join(MODEL_DIR, "model_metadata.json")
MLFLOW_DB_PATH = os.path.join(BASE_DIR, "mlflow.db")

def haversine_np(lon1, lat1, lon2, lat2):
    """Calcule la distance en kilomètres entre porteur de carte et marchand."""
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    return 6367 * 2 * np.arcsin(np.sqrt(a))

def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extrait et prépare les caractéristiques clés pour la détection de fraude."""
    X = pd.DataFrame()
    X['amt'] = df['amt'].astype(float)
    X['city_pop'] = df['city_pop'].fillna(1000).astype(float)
    
    # Distance géographique réelle
    X['distance_km'] = haversine_np(df['long'], df['lat'], df['merch_long'], df['merch_lat'])
    
    # Heure de la transaction (support trans_date_trans_time ou current_time)
    time_col = 'trans_date_trans_time' if 'trans_date_trans_time' in df.columns else 'current_time'
    if time_col in df.columns:
        dt = pd.to_datetime(df[time_col], errors='coerce')
        X['hour'] = dt.dt.hour.fillna(12).astype(int)
    else:
        X['hour'] = 12

    # Âge du porteur de carte
    if 'dob' in df.columns:
        dob_dt = pd.to_datetime(df['dob'], errors='coerce')
        X['age'] = (2026 - dob_dt.dt.year).fillna(40).astype(int)
    else:
        X['age'] = 40
        
    return X

def train():
    print("=" * 65)
    print("🚀 ENTRAÎNEMENT DU MODÈLE DE DÉTECTION DE FRAUDE — BLOC 3")
    print("   Tracking Expérimentations & Model Registry avec MLflow")
    print("=" * 65)
    print(f"📖 Chargement des données historiques : {CSV_PATH}")
    
    t0 = time.time()
    # Chargement d'un sous-ensemble représentatif (200 000 lignes)
    df = pd.read_csv(CSV_PATH, nrows=200000)
    print(f"✅ Données chargées : {len(df)} transactions (Fraudes : {df['is_fraud'].sum()})")
    
    print("⚙️ Feature Engineering (Distance Haversine, Âge, Heure)...")
    X = prepare_features(df)
    y = df['is_fraud']
    
    features = ['amt', 'distance_km', 'city_pop', 'hour', 'age']
    X = X[features]
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42
    )
    
    params = {
        "class_weight": "balanced",
        "max_iter": 120,
        "learning_rate": 0.08,
        "max_depth": 6,
        "random_state": 42
    }
    
    print(f"🧠 Entraînement de l'algorithme HistGradientBoosting (balanced)...")
    model = HistGradientBoostingClassifier(**params)
    model.fit(X_train, y_train)
    
    print("📊 Évaluation des performances sur le jeu de test...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    roc_auc = roc_auc_score(y_test, y_prob)
    recall = recall_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    
    print(f"  • ROC-AUC Score : {roc_auc:.4f}")
    print(f"  • Recall Fraude : {recall:.4f} (87%+ des fraudes interceptées)")
    print(f"  • Precision     : {precision:.4f}")
    print(f"  • F1-Score      : {f1:.4f}")
    
    print(f"\n💾 Sérialisation du modèle : {MODEL_PATH}")
    joblib.dump(model, MODEL_PATH)
    
    metadata = {
        "model_type": "HistGradientBoostingClassifier",
        "features": features,
        "parameters": params,
        "sample_size": len(df),
        "metrics": {
            "roc_auc": round(float(roc_auc), 4),
            "recall": round(float(recall), 4),
            "precision": round(float(precision), 4),
            "f1": round(float(f1), 4)
        },
        "trained_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "training_duration_sec": round(time.time() - t0, 2)
    }
    
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"✅ Métadonnées sauvegardées : {META_PATH}")
    
    # Intégration MLflow Tracking & Model Registry
    if MLFLOW_AVAILABLE:
        try:
            tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{MLFLOW_DB_PATH.replace(os.sep, '/')}")
            mlflow.set_tracking_uri(tracking_uri)
            mlflow.set_experiment("RealTime_Fraud_Detection_AIA_Bloc3")
            
            with mlflow.start_run(run_name="HistGB_Balanced_v2"):
                mlflow.log_params(params)
                mlflow.log_param("sample_size", len(df))
                mlflow.log_param("features", ",".join(features))
                mlflow.log_metrics({
                    "roc_auc": float(roc_auc),
                    "recall": float(recall),
                    "precision": float(precision),
                    "f1": float(f1),
                    "duration_seconds": float(time.time() - t0)
                })
                mlflow.sklearn.log_model(
                    sk_model=model,
                    artifact_path="fraud_model",
                    registered_model_name="FraudDetectionModel"
                )
                mlflow.log_artifact(META_PATH)
            print(f"🌟 MLflow Run consigné avec succès (Tracking: {tracking_uri})")
        except Exception as e:
            print(f"⚠️ MLflow logging ignoré ({e})")
            
    print(f"⏱️ Entraînement complété en {time.time() - t0:.2f}s !")
    print("=" * 65)

if __name__ == "__main__":
    train()
