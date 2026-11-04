import os
import sys
import time
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Chemins
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "01_train", "fraud_model.joblib")
META_PATH = os.path.join(BASE_DIR, "01_train", "model_metadata.json")

app = FastAPI(
    title="Real-Time Fraud Detection Scoring API",
    description="Microservice d'inférence temps réel pour la détection de fraudes bancaires (Bloc 3 - RNCP 41993)",
    version="1.0.0"
)

# Chargement du modèle au démarrage
model = None
metadata = {}

def haversine_np(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0)**2
    return 6367 * 2 * np.arcsin(np.sqrt(a))

@app.on_event("startup")
def load_model():
    global model, metadata
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Modèle introuvable à {MODEL_PATH}. Exécutez d'abord 01_train/train_model.py")
    model = joblib.load(MODEL_PATH)
    if os.path.exists(META_PATH):
        with open(META_PATH, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    print(f"✅ Modèle de scoring de fraude chargé avec succès depuis {MODEL_PATH}")

class TransactionPayload(BaseModel):
    cc_num: Optional[Any] = None
    merchant: Optional[str] = "Unknown"
    category: Optional[str] = "general"
    amt: float
    first: Optional[str] = ""
    last: Optional[str] = ""
    gender: Optional[str] = "M"
    street: Optional[str] = ""
    city: Optional[str] = ""
    state: Optional[str] = ""
    zip: Optional[Any] = 0
    lat: float
    long: float
    city_pop: Optional[float] = 1000.0
    job: Optional[str] = ""
    dob: Optional[str] = "1980-01-01"
    trans_num: Optional[str] = "txn_demo"
    unix_time: Optional[int] = None
    merch_lat: float
    merch_long: float
    current_time: Optional[str] = None
    trans_date_trans_time: Optional[str] = None

class PredictionResponse(BaseModel):
    trans_num: str
    amt: float
    distance_km: float
    is_fraud: bool
    fraud_probability: float
    risk_level: str
    decision: str
    latency_ms: float


@app.get("/health")
def healthcheck():
    return {
        "status": "HEALTHY",
        "service": "Fraud Scoring API",
        "model_loaded": model is not None,
        "metrics": metadata.get("metrics", {})
    }

@app.get("/model-info")
def model_info():
    return metadata

def process_single(tx_dict: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.time()
    amt = float(tx_dict.get("amt", 0.0))
    city_pop = float(tx_dict.get("city_pop", 1000.0))
    
    lat = float(tx_dict.get("lat", 0.0))
    lon = float(tx_dict.get("long", 0.0))
    m_lat = float(tx_dict.get("merch_lat", 0.0))
    m_lon = float(tx_dict.get("merch_long", 0.0))
    distance_km = haversine_np(lon, lat, m_lon, m_lat)
    
    # Extraction heure
    time_val = tx_dict.get("current_time") or tx_dict.get("trans_date_trans_time")
    hour = 12
    if time_val:
        try:
            hour = pd.to_datetime(time_val).hour
        except Exception:
            hour = 12
            
    # Extraction âge
    dob_val = tx_dict.get("dob")
    age = 40
    if dob_val:
        try:
            age = 2026 - pd.to_datetime(dob_val).year
        except Exception:
            age = 40

    X_row = pd.DataFrame([{
        "amt": amt,
        "distance_km": distance_km,
        "city_pop": city_pop,
        "hour": hour,
        "age": age
    }])
    
    prob = float(model.predict_proba(X_row)[0, 1])
    is_fraud = prob >= 0.50
    
    if prob >= 0.75:
        risk_level = "CRITICAL"
        decision = "BLOCK_IMMEDIATE"
    elif prob >= 0.50:
        risk_level = "HIGH"
        decision = "CHALLENGE_3DS"
    elif prob >= 0.25:
        risk_level = "MEDIUM"
        decision = "ALLOW_WITH_MONITORING"
    else:
        risk_level = "LOW"
        decision = "ALLOW"

    latency_ms = round((time.time() - t0) * 1000, 2)

    return {
        "trans_num": str(tx_dict.get("trans_num", "unknown")),
        "amt": amt,
        "distance_km": round(float(distance_km), 2),
        "is_fraud": is_fraud,
        "fraud_probability": round(prob, 4),
        "risk_level": risk_level,
        "decision": decision,
        "latency_ms": latency_ms
    }


@app.post("/predict", response_model=PredictionResponse)
def predict_transaction(payload: TransactionPayload):
    if model is None:
        raise HTTPException(status_code=500, detail="Modèle non initialisé")
    res = process_single(payload.dict())
    return PredictionResponse(**res)

@app.post("/predict-raw")
def predict_raw_dict(payload: Dict[str, Any]):
    """Accepte n'importe quel dictionnaire JSON brut issu de l'API HuggingFace."""
    if model is None:
        raise HTTPException(status_code=500, detail="Modèle non initialisé")
    return process_single(payload)
