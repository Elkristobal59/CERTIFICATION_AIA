import os
import sys
import sqlite3
import datetime
import hashlib
import json
import pandas as pd
from typing import Dict, Any, List, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "05_database", "fraud_pipeline.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "05_database", "schema.sql")
LAKE_DIR = os.path.join(BASE_DIR, "data_lake", "bronze")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialise les tables de la base de données relationnelle opérationnelle."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(LAKE_DIR, exist_ok=True)
    conn = get_connection()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)
    conn.commit()
    conn.close()
    print(f"✅ Base de données opérationnelle initialisée : {DB_PATH}")

def mask_credit_card(cc_num: Any) -> str:
    """
    Masque le numéro de carte bancaire conformément aux exigences strictes de PCI-DSS.
    Format : 6 premiers chiffres (BIN/IIN) + astérisques + 4 derniers chiffres.
    Exemple : 453288******9812
    """
    s = str(cc_num).strip().replace("-", "").replace(" ", "")
    if len(s) < 10:
        return "************"
    return f"{s[:6]}{'*' * (len(s) - 10)}{s[-4:]}"

def pseudonymize_name(first: Optional[str], last: Optional[str]) -> str:
    """
    Pseudonymise le porteur de carte (RGPD / Privacy-by-Design).
    Format : Initiale prénom + astérisques + Initiale nom + astérisques + Hash HMAC/SHA256 court.
    """
    f = (first or "").strip()
    l = (last or "").strip()
    full = f"{f} {l}".strip()
    if not full:
        return "Anonyme"
    token = hashlib.sha256(full.encode('utf-8')).hexdigest()[:6].upper()
    f_masked = f"{f[0]}***" if f else "***"
    l_masked = f"{l[0]}***" if l else "***"
    return f"{f_masked} {l_masked} (ID:{token})"

def write_to_bronze_lake(tx: Dict[str, Any]):
    """
    Persiste les transactions brutes en format Apache Parquet dans le Data Lake (Zone Bronze).
    Partitionné par date : data_lake/bronze/year=YYYY/month=MM/day=DD/
    """
    try:
        now = datetime.datetime.now()
        partition_dir = os.path.join(
            LAKE_DIR,
            f"year={now.year}",
            f"month={now.month:02d}",
            f"day={now.day:02d}"
        )
        os.makedirs(partition_dir, exist_ok=True)
        parquet_file = os.path.join(partition_dir, "raw_transactions_stream.parquet")
        
        # Copie sécurisée de la transaction brute (avec cc_num masqué pour le lake)
        lake_record = dict(tx)
        lake_record["cc_num_masked"] = mask_credit_card(tx.get("cc_num"))
        lake_record.pop("cc_num", None)
        lake_record["ingested_at"] = now.isoformat()
        
        df_new = pd.DataFrame([lake_record])
        if os.path.exists(parquet_file):
            try:
                df_existing = pd.read_parquet(parquet_file)
                df_combined = pd.concat([df_existing, df_new], ignore_index=True)
                df_combined.to_parquet(parquet_file, index=False, engine="pyarrow")
            except Exception:
                df_new.to_parquet(parquet_file, index=False, engine="pyarrow")
        else:
            df_new.to_parquet(parquet_file, index=False, engine="pyarrow")
    except Exception as e:
        print(f"⚠️ Erreur écriture Data Lake Bronze : {e}")

def insert_dlq(raw_payload: Any, error_reason: str, source: str = "KAFKA_STREAM") -> int:
    """
    Enregistre un message corrompu ou rejeté dans la Dead Letter Queue (DLQ).
    """
    conn = get_connection()
    cur = conn.cursor()
    payload_str = json.dumps(raw_payload) if isinstance(raw_payload, (dict, list)) else str(raw_payload)
    trans_num = ""
    if isinstance(raw_payload, dict):
        trans_num = str(raw_payload.get("trans_num", ""))
    try:
        cur.execute("""
            INSERT INTO dead_letter_queue (trans_num, raw_payload, error_reason, source)
            VALUES (?, ?, ?, ?)
        """, (trans_num, payload_str, str(error_reason), source))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def insert_transaction(tx: Dict[str, Any], score_result: Dict[str, Any]) -> int:
    """
    Insère une transaction scorée en base avec conformité PCI-DSS (carte masquée)
    et consigne une alerte immédiate si la fraude est détectée.
    """
    conn = get_connection()
    cur = conn.cursor()
    
    trans_num = str(tx.get("trans_num", f"txn_{int(datetime.datetime.now().timestamp()*1000)}"))
    # Conforme PCI-DSS : masque la carte bancaire
    cc_num_masked = mask_credit_card(tx.get("cc_num", ""))
    merchant = str(tx.get("merchant", "Unknown"))
    category = str(tx.get("category", "general"))
    amt = float(tx.get("amt", 0.0))
    # RGPD : pseudonymisation du nom
    customer_name = pseudonymize_name(tx.get("first"), tx.get("last"))
    city = str(tx.get("city", ""))
    state = str(tx.get("state", ""))
    city_pop = int(tx.get("city_pop", 1000))
    
    # Distance réelle calculée
    distance_km = float(score_result.get("distance_km", 0.0))
    
    is_fraud = 1 if score_result.get("is_fraud", False) else 0
    fraud_prob = float(score_result.get("fraud_probability", 0.0))
    risk_level = str(score_result.get("risk_level", "LOW"))
    decision = str(score_result.get("decision", "ALLOW"))
    
    trans_time = str(tx.get("current_time") or tx.get("trans_date_trans_time") or datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        cur.execute("""
            INSERT OR REPLACE INTO transactions (
                trans_num, cc_num, merchant, category, amt, customer_name,
                city, state, city_pop, distance_km, trans_time,
                is_fraud_predicted, fraud_probability, risk_level, decision
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trans_num, cc_num_masked, merchant, category, amt, customer_name,
            city, state, city_pop, distance_km, trans_time,
            is_fraud, fraud_prob, risk_level, decision
        ))
        
        # Enregistrement d'alerte immédiate si fraude
        if is_fraud or fraud_prob >= 0.50:
            cur.execute("""
                INSERT INTO fraud_alerts (
                    trans_num, amt, merchant, fraud_probability, risk_level, alert_channel
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                trans_num, amt, merchant, fraud_prob, risk_level, "CONSOLE_AND_LOG"
            ))
            
        conn.commit()
        
        # Écriture asynchrone / partitionnée dans le Data Lake Bronze
        write_to_bronze_lake(tx)
        
        return cur.lastrowid
    finally:
        conn.close()

def get_recent_transactions(limit: int = 15) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT trans_num, cc_num, merchant, category, amt, distance_km, trans_time,
               is_fraud_predicted, fraud_probability, risk_level, decision
        FROM transactions
        ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_stats_summary() -> Dict[str, Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            COUNT(*) as total_count,
            COALESCE(SUM(amt), 0) as total_volume,
            COALESCE(SUM(CASE WHEN is_fraud_predicted = 1 THEN 1 ELSE 0 END), 0) as fraud_count,
            COALESCE(SUM(CASE WHEN is_fraud_predicted = 1 THEN amt ELSE 0 END), 0) as fraud_volume
        FROM transactions
    """)
    row = dict(cur.fetchone())
    
    # Nombre de messages en DLQ
    try:
        cur.execute("SELECT COUNT(*) as dlq_count FROM dead_letter_queue")
        row["dlq_count"] = cur.fetchone()["dlq_count"]
    except Exception:
        row["dlq_count"] = 0
        
    conn.close()
    
    total = row["total_count"]
    frauds = row["fraud_count"]
    row["fraud_rate_pct"] = round((frauds / total * 100), 2) if total > 0 else 0.0
    row["total_volume"] = round(row["total_volume"], 2)
    row["fraud_volume"] = round(row["fraud_volume"], 2)
    return row

def compute_daily_audit(target_date: Optional[str] = None) -> Dict[str, Any]:
    """Calcule et persiste l'audit de la journée passée pour le DAG Airflow matinal."""
    if not target_date:
        target_date = datetime.date.today().strftime("%Y-%m-%d")
        
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_tx,
            COALESCE(SUM(amt), 0) as total_amt,
            COALESCE(SUM(CASE WHEN is_fraud_predicted = 1 THEN 1 ELSE 0 END), 0) as total_frauds,
            COALESCE(SUM(CASE WHEN is_fraud_predicted = 1 THEN amt ELSE 0 END), 0) as total_fraud_amt
        FROM transactions
        WHERE date(trans_time) = date(?)
    """, (target_date,))
    
    res = dict(cur.fetchone())
    total_tx = res["total_tx"]
    frauds = res["total_frauds"]
    total_amt = round(res["total_amt"], 2)
    fraud_amt = round(res["total_fraud_amt"], 2)
    rate = round((frauds / total_tx * 100), 2) if total_tx > 0 else 0.0
    
    # Trouver la catégorie de fraude la plus fréquente
    cur.execute("""
        SELECT category, COUNT(*) as c
        FROM transactions
        WHERE is_fraud_predicted = 1 AND date(trans_time) = date(?)
        GROUP BY category ORDER BY c DESC LIMIT 1
    """, (target_date,))
    cat_row = cur.fetchone()
    top_cat = cat_row["category"] if cat_row else "Aucune"
    
    # Sauvegarde dans daily_audit_summary
    cur.execute("""
        INSERT OR REPLACE INTO daily_audit_summary (
            audit_date, total_transactions, total_volume_eur,
            frauds_detected, fraud_volume_eur, fraud_rate_pct, top_fraud_category
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (target_date, total_tx, total_amt, frauds, fraud_amt, rate, top_cat))
    
    conn.commit()
    conn.close()
    
    return {
        "audit_date": target_date,
        "total_transactions": total_tx,
        "total_volume_eur": total_amt,
        "frauds_detected": frauds,
        "fraud_volume_eur": fraud_amt,
        "fraud_rate_pct": rate,
        "top_fraud_category": top_cat
    }

if __name__ == "__main__":
    init_db()
