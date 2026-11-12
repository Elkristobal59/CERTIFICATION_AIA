import os
from typing import Iterable
import numpy as np
import pandas as pd

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATURE_COLUMNS = ["amt", "distance_km", "city_pop", "hour", "age"]


def load_project_env() -> None:
    """Charge les variables d'environnement depuis `.env` à la racine du projet."""
    if load_dotenv is not None:
        env_path = os.path.join(BASE_DIR, ".env")
        if os.path.exists(env_path):
            load_dotenv(env_path, override=False)
    if not os.environ.get("MLFLOW_S3_ENDPOINT_URL", "").strip():
        os.environ.pop("MLFLOW_S3_ENDPOINT_URL", None)


def haversine_np(lon1, lat1, lon2, lat2):
    """Calcule la distance orthodromique en kilomètres entre porteur et commerçant."""
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2.0) ** 2
    return 6367.0 * 2.0 * np.arcsin(np.sqrt(a))


def parse_hour_series(series: pd.Series) -> pd.Series:
    """Extrait l'heure UTC [0-23] depuis un timestamp ISO ou epoch millisecondes (API HF)."""
    numeric_vals = pd.to_numeric(series, errors="coerce")
    is_epoch_ms = numeric_vals.notna() & (numeric_vals > 1e11)

    hours = pd.Series(12, index=series.index, dtype=int)
    if is_epoch_ms.any():
        dt_ms = pd.to_datetime(numeric_vals[is_epoch_ms], unit="ms", errors="coerce")
        hours.loc[is_epoch_ms] = dt_ms.dt.hour.fillna(12).astype(int)

    remaining = ~is_epoch_ms
    if remaining.any():
        dt_str = pd.to_datetime(series[remaining], errors="coerce")
        hours.loc[remaining] = dt_str.dt.hour.fillna(12).astype(int)
    return hours


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extrait la matrice ordonnée des variables prédictives du modèle de fraude."""
    features = pd.DataFrame(index=df.index)
    features["amt"] = pd.to_numeric(df["amt"], errors="coerce").fillna(0.0).astype(float)
    features["distance_km"] = haversine_np(
        pd.to_numeric(df["long"], errors="coerce").fillna(0.0),
        pd.to_numeric(df["lat"], errors="coerce").fillna(0.0),
        pd.to_numeric(df["merch_long"], errors="coerce").fillna(0.0),
        pd.to_numeric(df["merch_lat"], errors="coerce").fillna(0.0),
    ).astype(float)
    features["city_pop"] = (
        pd.to_numeric(df.get("city_pop", 1000.0), errors="coerce").fillna(1000.0).astype(float)
    )

    if "trans_date_trans_time" in df.columns and df["trans_date_trans_time"].notna().any():
        features["hour"] = parse_hour_series(df["trans_date_trans_time"])
    elif "current_time" in df.columns and df["current_time"].notna().any():
        features["hour"] = parse_hour_series(df["current_time"])
    else:
        features["hour"] = 12

    if "dob" in df.columns and df["dob"].notna().any():
        dob_dt = pd.to_datetime(df["dob"], errors="coerce")
        features["age"] = (2026 - dob_dt.dt.year).fillna(40).clip(lower=18, upper=100).astype(int)
    else:
        features["age"] = 40

    return features[FEATURE_COLUMNS]


def resolve_feature_columns() -> Iterable[str]:
    return tuple(FEATURE_COLUMNS)

