import os
import json
import datetime
import hashlib
import importlib
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
features_mod = importlib.import_module("01_train.features")
quality_mod = importlib.import_module("03_pipeline_streaming.quality_gate")

features_mod.load_project_env()
prepare_features = features_mod.prepare_features
validate_transactions_dataframe = quality_mod.validate_transactions_dataframe

SCHEMA_PATH = os.path.join(BASE_DIR, "05_database", "schema.sql")
BRONZE_DIR = os.path.join(BASE_DIR, "data_lake", "bronze")
SILVER_DIR = os.path.join(BASE_DIR, "data_lake", "silver")
GOLD_DIR = os.path.join(BASE_DIR, "data_lake", "gold")
REJECTED_DIR = os.path.join(BASE_DIR, "data_lake", "rejected")
META_PATH = os.path.join(BASE_DIR, "01_train", "model_metadata.json")
FALLBACK_SQLITE_PATH = os.path.join(BASE_DIR, "05_database", "fraud_pipeline.db")

PII_DIRECT_COLUMNS = ["cc_num", "first", "last", "street", "dob", "job", "zip"]
_ENGINE = None


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", f"sqlite:///{FALLBACK_SQLITE_PATH.replace(os.sep, '/')}").strip()


def is_postgres() -> bool:
    return get_database_url().startswith("postgresql")


def get_engine():
    global _ENGINE
    url = get_database_url()
    if _ENGINE is None or str(_ENGINE.url) != url:
        _ENGINE = create_engine(url, pool_pre_ping=True, future=True)
    return _ENGINE


def _init_sqlite_fallback(conn) -> None:
    statements = [
        """CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trans_num VARCHAR(64) UNIQUE NOT NULL,
            cc_num VARCHAR(32) NOT NULL, merchant VARCHAR(128) NOT NULL, category VARCHAR(64) NOT NULL,
            amt REAL NOT NULL, customer_name VARCHAR(128) NOT NULL, customer_pseudo_hash VARCHAR(64) NOT NULL,
            city VARCHAR(64), state VARCHAR(16), city_pop INTEGER, distance_km REAL NOT NULL DEFAULT 0,
            trans_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_fraud_predicted INTEGER NOT NULL DEFAULT 0,
            fraud_probability REAL NOT NULL, risk_level VARCHAR(16) NOT NULL, decision VARCHAR(32) NOT NULL,
            model_version VARCHAR(64) DEFAULT 'champion', scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS fraud_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trans_num VARCHAR(64) NOT NULL, amt REAL NOT NULL,
            merchant VARCHAR(128), fraud_probability REAL NOT NULL, risk_level VARCHAR(16) NOT NULL,
            alert_channel VARCHAR(64) NOT NULL DEFAULT 'SMTP_EMAIL_AND_LOG', alert_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS daily_audit_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT, audit_date DATE UNIQUE NOT NULL, total_transactions INTEGER NOT NULL,
            total_volume_eur REAL NOT NULL, frauds_detected INTEGER NOT NULL, fraud_volume_eur REAL NOT NULL,
            fraud_rate_pct REAL NOT NULL, top_fraud_category VARCHAR(64), dlq_rejected_count INTEGER NOT NULL DEFAULT 0,
            data_drift_status VARCHAR(32) NOT NULL DEFAULT 'OK', audit_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS dead_letter_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT, trans_num VARCHAR(64), raw_payload TEXT NOT NULL,
            error_reason VARCHAR(512) NOT NULL, source VARCHAR(64) NOT NULL DEFAULT 'KAFKA_STREAM',
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    for stmt in statements:
        conn.execute(text(stmt))


def init_db() -> None:
    """Initialise les tables relationnelles (PostgreSQL / Neon ou SQLite dev fallback)."""
    for d in (BRONZE_DIR, SILVER_DIR, GOLD_DIR, REJECTED_DIR, os.path.dirname(FALLBACK_SQLITE_PATH)):
        os.makedirs(d, exist_ok=True)
    engine = get_engine()
    with engine.begin() as conn:
        if is_postgres():
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                raw_sql = f.read()
            for stmt in [s.strip() for s in raw_sql.split(";") if s.strip()]:
                conn.execute(text(stmt))
        else:
            _init_sqlite_fallback(conn)
    backend = "PostgreSQL" if is_postgres() else f"SQLite ({FALLBACK_SQLITE_PATH})"
    print(f"✅ Base de données opérationnelle initialisée : {backend}")


def mask_credit_card(cc_num: Any) -> str:
    """Masque strictement le PAN conformément à PCI-DSS (format `**** **** **** 1234`)."""
    digits = "".join(ch for ch in str(cc_num or "") if ch.isdigit())
    if len(digits) < 4:
        return "**** **** **** ****"
    return f"**** **** **** {digits[-4:]}"


def salted_sha256_hash(raw_value: str) -> str:
    """Pseudonymisation irréversible SHA-256 salée via SECRET_SALT (.env)."""
    salt = os.getenv("SECRET_SALT", "")
    if not salt:
        salt = "MISSING_ENV_SECRET_SALT"
    return hashlib.sha256(f"{salt}:{raw_value}".encode("utf-8")).hexdigest()


def pseudonymize_name(first: Optional[str], last: Optional[str]) -> Tuple[str, str]:
    """Retourne `(libellé masqué, hash SHA-256 salé complet)` conforme RGPD."""
    f = (first or "").strip()
    l = (last or "").strip()
    full = f"{f} {l}".strip()
    if not full:
        return "Anonyme", salted_sha256_hash("anonymous")
    digest = salted_sha256_hash(full.lower())
    f_masked = f"{f[0]}***" if f else "***"
    l_masked = f"{l[0]}***" if l else "***"
    return f"{f_masked} {l_masked} (ID:{digest[:6].upper()})", digest


def _partition_path(zone_dir: str, filename: str, target_date: Optional[str] = None) -> str:
    dt = datetime.datetime.strptime(target_date, "%Y-%m-%d") if target_date else datetime.datetime.now()
    pdir = os.path.join(zone_dir, f"year={dt.year}", f"month={dt.month:02d}", f"day={dt.day:02d}")
    os.makedirs(pdir, exist_ok=True)
    return os.path.join(pdir, filename)


def _append_parquet(parquet_path: str, df_new: pd.DataFrame, dedup_col: Optional[str] = None) -> None:
    if os.path.exists(parquet_path):
        try:
            df_existing = pd.read_parquet(parquet_path)
            df_out = pd.concat([df_existing, df_new], ignore_index=True)
        except Exception:
            df_out = df_new
    else:
        df_out = df_new
    if dedup_col and dedup_col in df_out.columns:
        df_out = df_out.drop_duplicates(subset=[dedup_col], keep="last")
    df_out.to_parquet(parquet_path, index=False, engine="pyarrow")


def write_to_bronze_lake(tx: Dict[str, Any]) -> None:
    """Stockage zone Bronze Parquet partitionné Y/M/D (PAN déjà masqué avant écriture)."""
    try:
        parquet_file = _partition_path(BRONZE_DIR, "raw_transactions_stream.parquet")
        record = dict(tx)
        record["cc_num_masked"] = mask_credit_card(tx.get("cc_num"))
        record.pop("cc_num", None)
        record["ingested_at"] = datetime.datetime.now().isoformat()
        _append_parquet(parquet_file, pd.DataFrame([record]), dedup_col="trans_num")
    except Exception as exc:
        print(f"⚠️ Erreur écriture Data Lake Bronze : {exc}")


def _sanitize_payload_pii(raw_payload: Any) -> Dict[str, Any]:
    """Masque PAN et pseudonymise/supprime les PII directs avant écriture DLQ / Quarantaine."""
    if not isinstance(raw_payload, dict):
        return {"raw": str(raw_payload)}
    sanitized = dict(raw_payload)
    sanitized["cc_num_masked"] = mask_credit_card(sanitized.pop("cc_num", sanitized.get("cc_num_masked")))
    if sanitized.get("first") or sanitized.get("last"):
        masked_name, pseudo_hash = pseudonymize_name(sanitized.get("first"), sanitized.get("last"))
        sanitized["customer_name_masked"] = masked_name
        sanitized["customer_pseudo_hash"] = pseudo_hash
    for col in ("first", "last", "street", "dob", "job", "zip"):
        sanitized.pop(col, None)
    return sanitized


def write_to_rejected_lake(raw_payload: Any, error_reason: str, source: str) -> None:
    """Stockage quarantaine `data_lake/rejected/` en Parquet partitionné Y/M/D."""
    try:
        parquet_file = _partition_path(REJECTED_DIR, "rejected_transactions.parquet")
        sanitized = _sanitize_payload_pii(raw_payload)
        trans_num = str(sanitized.get("trans_num", ""))
        df_rej = pd.DataFrame([{
            "trans_num": trans_num,
            "error_reason": str(error_reason),
            "source": source,
            "payload_json": json.dumps(sanitized, default=str, ensure_ascii=False),
            "rejected_at": datetime.datetime.now().isoformat(),
        }])
        _append_parquet(parquet_file, df_rej)
    except Exception as exc:
        print(f"⚠️ Erreur écriture zone rejected/ : {exc}")


def insert_dlq(raw_payload: Any, error_reason: str, source: str = "KAFKA_STREAM") -> None:
    """Persiste un rejet dans `dead_letter_queue` SQL ET dans `data_lake/rejected/`."""
    sanitized = _sanitize_payload_pii(raw_payload)
    payload_str = json.dumps(sanitized, default=str, ensure_ascii=False)
    trans_num = str(sanitized.get("trans_num", ""))

    with get_engine().begin() as conn:
        conn.execute(
            text("INSERT INTO dead_letter_queue (trans_num, raw_payload, error_reason, source) VALUES (:tn, :rp, :er, :sr)"),
            {"tn": trans_num, "rp": payload_str, "er": str(error_reason)[:500], "sr": source},
        )
    write_to_rejected_lake(sanitized, error_reason, source)


def _normalize_timestamp_str(raw_val: Any) -> datetime.datetime:
    if raw_val is None or raw_val == "":
        return datetime.datetime.now()
    if isinstance(raw_val, (int, float)) and float(raw_val) > 1e11:
        return datetime.datetime.fromtimestamp(float(raw_val) / 1000.0)
    try:
        return pd.to_datetime(raw_val).to_pydatetime().replace(tzinfo=None)
    except Exception:
        return datetime.datetime.now()


def insert_transaction(tx: Dict[str, Any], score_result: Dict[str, Any], alert_channel: Optional[str] = None) -> None:
    """Persiste une transaction scorée (idempotente sur `trans_num`) + alerte + Data Lake Bronze."""
    trans_num = str(tx.get("trans_num") or f"txn_{int(datetime.datetime.now().timestamp() * 1000)}")
    cc_masked = mask_credit_card(tx.get("cc_num", ""))
    customer_masked, pseudo_hash = pseudonymize_name(tx.get("first"), tx.get("last"))
    is_fraud_bool = bool(score_result.get("is_fraud", False))
    prob = float(score_result.get("fraud_probability", 0.0))
    trans_dt = _normalize_timestamp_str(tx.get("current_time") or tx.get("trans_date_trans_time"))

    params = {
        "trans_num": trans_num,
        "cc_num": cc_masked,
        "merchant": str(tx.get("merchant", "Unknown"))[:128],
        "category": str(tx.get("category", "general"))[:64],
        "amt": float(tx.get("amt", 0.0)),
        "customer_name": customer_masked,
        "customer_pseudo_hash": pseudo_hash,
        "city": str(tx.get("city", ""))[:64],
        "state": str(tx.get("state", ""))[:16],
        "city_pop": int(float(tx.get("city_pop") or 1000)),
        "distance_km": float(score_result.get("distance_km", 0.0)),
        "trans_time": trans_dt if is_postgres() else trans_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "is_fraud_predicted": is_fraud_bool if is_postgres() else (1 if is_fraud_bool else 0),
        "fraud_probability": prob,
        "risk_level": str(score_result.get("risk_level", "LOW")),
        "decision": str(score_result.get("decision", "ALLOW")),
        "model_version": str(score_result.get("model_source", "champion"))[:64],
    }

    upsert_sql = (
        """INSERT INTO transactions (
            trans_num, cc_num, merchant, category, amt, customer_name, customer_pseudo_hash,
            city, state, city_pop, distance_km, trans_time,
            is_fraud_predicted, fraud_probability, risk_level, decision, model_version
        ) VALUES (
            :trans_num, :cc_num, :merchant, :category, :amt, :customer_name, :customer_pseudo_hash,
            :city, :state, :city_pop, :distance_km, :trans_time,
            :is_fraud_predicted, :fraud_probability, :risk_level, :decision, :model_version
        ) ON CONFLICT (trans_num) DO UPDATE SET
            fraud_probability = EXCLUDED.fraud_probability,
            is_fraud_predicted = EXCLUDED.is_fraud_predicted,
            risk_level = EXCLUDED.risk_level,
            decision = EXCLUDED.decision,
            scored_at = CURRENT_TIMESTAMP"""
        if is_postgres()
        else """INSERT OR REPLACE INTO transactions (
            trans_num, cc_num, merchant, category, amt, customer_name, customer_pseudo_hash,
            city, state, city_pop, distance_km, trans_time,
            is_fraud_predicted, fraud_probability, risk_level, decision, model_version
        ) VALUES (
            :trans_num, :cc_num, :merchant, :category, :amt, :customer_name, :customer_pseudo_hash,
            :city, :state, :city_pop, :distance_km, :trans_time,
            :is_fraud_predicted, :fraud_probability, :risk_level, :decision, :model_version
        )"""
    )

    fraud_threshold = float(os.getenv("FRAUD_THRESHOLD", "0.50"))
    with get_engine().begin() as conn:
        conn.execute(text(upsert_sql), params)
        if is_fraud_bool or prob >= fraud_threshold:
            conn.execute(
                text("""INSERT INTO fraud_alerts (trans_num, amt, merchant, fraud_probability, risk_level, alert_channel)
                        VALUES (:trans_num, :amt, :merchant, :fraud_probability, :risk_level, :alert_channel)"""),
                {
                    "trans_num": trans_num,
                    "amt": params["amt"],
                    "merchant": params["merchant"],
                    "fraud_probability": prob,
                    "risk_level": params["risk_level"],
                    "alert_channel": alert_channel or "CONSOLE_AND_LOG",
                },
            )
    write_to_bronze_lake(tx)


def transform_bronze_to_silver(target_date: Optional[str] = None) -> Dict[str, Any]:
    """ETL Bronze -> Silver : validation Pandera, quarantaine `rejected/`, hash salé & suppression PII."""
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    bronze_file = _partition_path(BRONZE_DIR, "raw_transactions_stream.parquet", target)
    if not os.path.exists(bronze_file):
        return {"date": target, "bronze_rows": 0, "silver_rows": 0, "rejected_rows": 0}

    df_bronze = pd.read_parquet(bronze_file)
    valid_df, rejected_df = validate_transactions_dataframe(df_bronze)

    if not rejected_df.empty:
        rej_file = _partition_path(REJECTED_DIR, "rejected_transactions.parquet", target)
        _append_parquet(rej_file, rejected_df.drop(columns=[c for c in PII_DIRECT_COLUMNS if c in rejected_df.columns]))

    if valid_df.empty:
        return {"date": target, "bronze_rows": len(df_bronze), "silver_rows": 0, "rejected_rows": len(rejected_df)}

    silver_df = valid_df.copy()
    silver_df["customer_pseudo_hash"] = [
        pseudonymize_name(
            None if pd.isna(row.get("first")) else str(row.get("first")),
            None if pd.isna(row.get("last")) else str(row.get("last")),
        )[1]
        for _, row in silver_df.iterrows()
    ]
    if "cc_num_masked" not in silver_df.columns:
        silver_df["cc_num_masked"] = silver_df.get("cc_num", "").map(mask_credit_card)
    silver_df = silver_df.drop(columns=[c for c in PII_DIRECT_COLUMNS if c in silver_df.columns])

    engineered = prepare_features(valid_df)
    for col in engineered.columns:
        silver_df[f"feat_{col}"] = engineered[col].values
    silver_df["silver_processed_at"] = datetime.datetime.now().isoformat()

    silver_file = _partition_path(SILVER_DIR, "clean_transactions_silver.parquet", target)
    silver_df.to_parquet(silver_file, index=False, engine="pyarrow")
    return {
        "date": target,
        "bronze_rows": len(df_bronze),
        "silver_rows": len(silver_df),
        "rejected_rows": len(rejected_df),
        "silver_path": silver_file,
    }


def build_gold_and_drift(target_date: Optional[str] = None) -> str:
    """Construit la zone Gold (features + KPIs) et évalue la dérive statistique de base."""
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    silver_file = _partition_path(SILVER_DIR, "clean_transactions_silver.parquet", target)
    if not os.path.exists(silver_file):
        return "NO_DATA"

    df_silver = pd.read_parquet(silver_file)
    gold_cols = [c for c in df_silver.columns if c.startswith("feat_") or c in ("trans_num", "merchant", "category", "customer_pseudo_hash", "cc_num_masked")]
    gold_file = _partition_path(GOLD_DIR, "fraud_features_gold.parquet", target)
    df_silver[gold_cols].to_parquet(gold_file, index=False, engine="pyarrow")

    mean_amt = float(df_silver["feat_amt"].mean()) if "feat_amt" in df_silver.columns and len(df_silver) else 0.0
    return "DRIFT_ALERT" if mean_amt > 1500.0 else "OK"


def get_stats_summary() -> Dict[str, Any]:
    with get_engine().connect() as conn:
        row = dict(conn.execute(text("""
            SELECT
                COUNT(*) AS total_count,
                COALESCE(SUM(amt), 0) AS total_volume,
                COALESCE(SUM(CASE WHEN CAST(is_fraud_predicted AS INT) = 1 THEN 1 ELSE 0 END), 0) AS fraud_count,
                COALESCE(SUM(CASE WHEN CAST(is_fraud_predicted AS INT) = 1 THEN amt ELSE 0 END), 0) AS fraud_volume
            FROM transactions
        """)).mappings().one())
        row["dlq_count"] = int(conn.execute(text("SELECT COUNT(*) FROM dead_letter_queue")).scalar_one())

    total = int(row["total_count"])
    frauds = int(row["fraud_count"])
    return {
        "total_count": total,
        "total_volume": round(float(row["total_volume"]), 2),
        "fraud_count": frauds,
        "fraud_volume": round(float(row["fraud_volume"]), 2),
        "fraud_rate_pct": round((frauds / total * 100.0), 2) if total > 0 else 0.0,
        "dlq_count": row["dlq_count"],
    }


def compute_daily_audit(target_date: Optional[str] = None) -> Dict[str, Any]:
    """Calcule et persiste de façon idempotente l'audit quotidien dans PostgreSQL + Gold."""
    target = target_date or datetime.date.today().strftime("%Y-%m-%d")
    drift_status = build_gold_and_drift(target)
    date_filter = "CAST(trans_time AS DATE) = CAST(:td AS DATE)" if is_postgres() else "date(trans_time) = date(:td)"

    with get_engine().begin() as conn:
        res = dict(conn.execute(text(f"""
            SELECT
                COUNT(*) AS total_tx,
                COALESCE(SUM(amt), 0) AS total_amt,
                COALESCE(SUM(CASE WHEN CAST(is_fraud_predicted AS INT) = 1 THEN 1 ELSE 0 END), 0) AS total_frauds,
                COALESCE(SUM(CASE WHEN CAST(is_fraud_predicted AS INT) = 1 THEN amt ELSE 0 END), 0) AS total_fraud_amt
            FROM transactions
            WHERE {date_filter}
        """), {"td": target}).mappings().one())

        cat_row = conn.execute(text(f"""
            SELECT category, COUNT(*) AS c
            FROM transactions
            WHERE CAST(is_fraud_predicted AS INT) = 1 AND {date_filter}
            GROUP BY category ORDER BY c DESC LIMIT 1
        """), {"td": target}).mappings().first()

        dlq_date_filter = "CAST(received_at AS DATE) = CAST(:td AS DATE)" if is_postgres() else "date(received_at) = date(:td)"
        dlq_count = int(conn.execute(text(f"SELECT COUNT(*) FROM dead_letter_queue WHERE {dlq_date_filter}"), {"td": target}).scalar_one())

        total_tx = int(res["total_tx"])
        frauds = int(res["total_frauds"])
        total_amt = round(float(res["total_amt"]), 2)
        fraud_amt = round(float(res["total_fraud_amt"]), 2)
        rate = round((frauds / total_tx * 100.0), 2) if total_tx > 0 else 0.0
        top_cat = cat_row["category"] if cat_row else "Aucune"

        audit_sql = (
            """INSERT INTO daily_audit_summary (
                audit_date, total_transactions, total_volume_eur, frauds_detected,
                fraud_volume_eur, fraud_rate_pct, top_fraud_category, dlq_rejected_count, data_drift_status
            ) VALUES (:ad, :tt, :tv, :fd, :fv, :fr, :tc, :dlq, :ds)
            ON CONFLICT (audit_date) DO UPDATE SET
                total_transactions = EXCLUDED.total_transactions,
                total_volume_eur = EXCLUDED.total_volume_eur,
                frauds_detected = EXCLUDED.frauds_detected,
                fraud_volume_eur = EXCLUDED.fraud_volume_eur,
                fraud_rate_pct = EXCLUDED.fraud_rate_pct,
                top_fraud_category = EXCLUDED.top_fraud_category,
                dlq_rejected_count = EXCLUDED.dlq_rejected_count,
                data_drift_status = EXCLUDED.data_drift_status,
                audit_generated_at = CURRENT_TIMESTAMP"""
            if is_postgres()
            else """INSERT OR REPLACE INTO daily_audit_summary (
                audit_date, total_transactions, total_volume_eur, frauds_detected,
                fraud_volume_eur, fraud_rate_pct, top_fraud_category, dlq_rejected_count, data_drift_status
            ) VALUES (:ad, :tt, :tv, :fd, :fv, :fr, :tc, :dlq, :ds)"""
        )
        conn.execute(text(audit_sql), {
            "ad": target, "tt": total_tx, "tv": total_amt, "fd": frauds,
            "fv": fraud_amt, "fr": rate, "tc": top_cat, "dlq": dlq_count, "ds": drift_status,
        })

    return {
        "audit_date": target,
        "total_transactions": total_tx,
        "total_volume_eur": total_amt,
        "frauds_detected": frauds,
        "fraud_volume_eur": fraud_amt,
        "fraud_rate_pct": rate,
        "top_fraud_category": top_cat,
        "dlq_rejected_count": dlq_count,
        "data_drift_status": drift_status,
    }


if __name__ == "__main__":
    init_db()
