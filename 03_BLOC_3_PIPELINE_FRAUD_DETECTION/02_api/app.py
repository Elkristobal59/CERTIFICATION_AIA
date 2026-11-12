import os
import sys
import time
import json
import importlib
from typing import Any, Dict, Optional

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

features_mod = importlib.import_module("01_train.features")
load_project_env = features_mod.load_project_env
prepare_features = features_mod.prepare_features

load_project_env()

MODEL_PATH = os.path.join(BASE_DIR, "01_train", "fraud_model.joblib")
META_PATH = os.path.join(BASE_DIR, "01_train", "model_metadata.json")

try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

app = FastAPI(
    title="Real-Time Fraud Detection Scoring API",
    description="Microservice d'inférence temps réel connecté au Model Registry MLflow (@champion) — RNCP 41993 Bloc 3",
    version="2.0.0",
)

model = None
metadata: Dict[str, Any] = {}
model_source: str = "uninitialized"


@app.on_event("startup")
def load_model():
    """Charge le modèle `@champion` depuis MLflow Registry (avec fallback local .joblib)."""
    global model, metadata, model_source

    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "").strip()
    model_name = os.getenv("MLFLOW_MODEL_NAME", "fraud_detection_model")
    model_alias = os.getenv("MLFLOW_MODEL_ALIAS", "champion")

    if MLFLOW_AVAILABLE and tracking_uri:
        registry_uri = f"models:/{model_name}@{model_alias}"
        try:
            mlflow.set_tracking_uri(tracking_uri)
            model = mlflow.sklearn.load_model(registry_uri)
            model_source = f"mlflow://{model_name}@{model_alias} ({tracking_uri})"
            print(f"✅ Modèle chargé depuis MLflow Registry : {model_source}")
            return
        except Exception as exc:
            print(f"ℹ️ Registry MLflow indisponible au démarrage ({exc}). Bascule sur artefact local.")

    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Aucun modèle disponible (ni MLflow ni {MODEL_PATH}). Exécutez 01_train/train_model.py")

    model = joblib.load(MODEL_PATH)
    model_source = f"local_joblib://{MODEL_PATH}"
    print(f"✅ Modèle chargé depuis le fallback local : {model_source}")


class TransactionPayload(BaseModel):
    cc_num: Optional[Any] = None
    merchant: Optional[str] = "Unknown"
    category: Optional[str] = "general"
    amt: float = Field(..., ge=0.0, description="Montant strictement non négatif")
    first: Optional[str] = ""
    last: Optional[str] = ""
    gender: Optional[str] = "M"
    street: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    zip: Optional[Any] = 0
    lat: float = Field(..., ge=-90.0, le=90.0)
    long: float = Field(..., ge=-180.0, le=180.0)
    city_pop: Optional[float] = Field(1000.0, ge=0.0)
    job: Optional[str] = ""
    dob: Optional[str] = "1980-01-01"
    trans_num: Optional[str] = "txn_demo"
    unix_time: Optional[int] = None
    merch_lat: float = Field(..., ge=-90.0, le=90.0)
    merch_long: float = Field(..., ge=-180.0, le=180.0)
    current_time: Optional[Any] = None
    trans_date_trans_time: Optional[Any] = None


class PredictionResponse(BaseModel):
    trans_num: str
    amt: float
    distance_km: float
    is_fraud: bool
    fraud_probability: float
    risk_level: str
    decision: str
    model_source: str
    latency_ms: float


def classify_risk(prob: float) -> tuple[bool, str, str]:
    is_fraud = prob >= 0.50
    if prob >= 0.75:
        return is_fraud, "CRITICAL", "BLOCK_IMMEDIATE"
    if prob >= 0.50:
        return is_fraud, "HIGH", "CHALLENGE_3DS"
    if prob >= 0.25:
        return is_fraud, "MEDIUM", "ALLOW_WITH_MONITORING"
    return is_fraud, "LOW", "ALLOW"


def process_single(tx_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Calcule les variables via le module partagé et exécute l'inférence."""
    if model is None:
        load_model()

    t0 = time.time()
    df_row = pd.DataFrame([tx_dict])
    X_row = prepare_features(df_row)
    distance_km = float(X_row["distance_km"].iloc[0])

    prob = float(model.predict_proba(X_row)[0, 1])
    is_fraud, risk_level, decision = classify_risk(prob)
    latency_ms = round((time.time() - t0) * 1000.0, 2)

    return {
        "trans_num": str(tx_dict.get("trans_num", "unknown")),
        "amt": float(X_row["amt"].iloc[0]),
        "distance_km": round(distance_km, 2),
        "is_fraud": is_fraud,
        "fraud_probability": round(prob, 4),
        "risk_level": risk_level,
        "decision": decision,
        "model_source": model_source,
        "latency_ms": latency_ms,
    }


@app.get("/health")
def healthcheck():
    return {
        "status": "HEALTHY",
        "service": "Fraud Scoring API",
        "model_loaded": model is not None,
        "model_source": model_source,
        "metrics": metadata.get("metrics", {}),
    }


@app.get("/model-info")
def model_info():
    return {"model_source": model_source, **metadata}


@app.post("/reload-model")
def reload_model():
    """Recharge dynamiquement le modèle `@champion` depuis MLflow Model Registry."""
    load_model()
    return {"status": "RELOADED", "model_source": model_source}


@app.post("/predict", response_model=PredictionResponse)
def predict_transaction(payload: TransactionPayload):
    res = process_single(payload.model_dump())
    return PredictionResponse(**res)


@app.post("/predict-raw", response_model=PredictionResponse)
def predict_raw_validated(payload: Dict[str, Any]):
    """Valide strictement tout payload brut via Pydantic avant scoring."""
    try:
        validated = TransactionPayload(**payload)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    res = process_single(validated.model_dump())
    return PredictionResponse(**res)
