-- Schéma Opérationnel pour la Détection de Fraude (Bloc 3 - RNCP 41993)
-- Compatible SQLite & PostgreSQL (Aurora / RDS)

-- 1. Table principale de stockage des transactions enrichies
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trans_num VARCHAR(64) UNIQUE NOT NULL,
    cc_num VARCHAR(32),
    merchant VARCHAR(128),
    category VARCHAR(64),
    amt DECIMAL(10, 2) NOT NULL,
    customer_name VARCHAR(128),
    city VARCHAR(64),
    state VARCHAR(16),
    city_pop INTEGER,
    distance_km DECIMAL(8, 2),
    trans_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_fraud_predicted BOOLEAN NOT NULL DEFAULT 0,
    fraud_probability DECIMAL(5, 4) NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trans_time ON transactions(trans_time);
CREATE INDEX IF NOT EXISTS idx_is_fraud ON transactions(is_fraud_predicted);
CREATE INDEX IF NOT EXISTS idx_merchant ON transactions(merchant);

-- 2. Table des alertes de fraudes temps réel
CREATE TABLE IF NOT EXISTS fraud_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trans_num VARCHAR(64) NOT NULL,
    amt DECIMAL(10, 2) NOT NULL,
    merchant VARCHAR(128),
    fraud_probability DECIMAL(5, 4) NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    alert_channel VARCHAR(32) DEFAULT 'CONSOLE_AND_LOG',
    alert_sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (trans_num) REFERENCES transactions(trans_num)
);

-- 3. Table des synthèses quotidiennes pour l'audit matinal (DAG Airflow)
CREATE TABLE IF NOT EXISTS daily_audit_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    audit_date DATE UNIQUE NOT NULL,
    total_transactions INTEGER NOT NULL,
    total_volume_eur DECIMAL(14, 2) NOT NULL,
    frauds_detected INTEGER NOT NULL,
    fraud_volume_eur DECIMAL(14, 2) NOT NULL,
    fraud_rate_pct DECIMAL(5, 2) NOT NULL,
    top_fraud_category VARCHAR(64),
    audit_generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Table Dead Letter Queue (DLQ) pour isoler les messages corrompus/invalides
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trans_num VARCHAR(64),
    raw_payload TEXT NOT NULL,
    error_reason VARCHAR(255) NOT NULL,
    source VARCHAR(64) DEFAULT 'KAFKA_STREAM',
    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

