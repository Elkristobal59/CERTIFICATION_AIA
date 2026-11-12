-- Schéma PostgreSQL Opérationnel pour la Détection de Fraude (Bloc 3 - RNCP 41993)
-- 100 % compatible PostgreSQL Docker local, Neon PostgreSQL et AWS RDS / Aurora

-- 1. Transactions scorées (conformes PCI-DSS & RGPD : PAN masqué + nom pseudonymisé SHA-256 salé)
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    trans_num VARCHAR(64) UNIQUE NOT NULL,
    cc_num VARCHAR(32) NOT NULL,
    merchant VARCHAR(128) NOT NULL,
    category VARCHAR(64) NOT NULL,
    amt NUMERIC(12, 2) NOT NULL CHECK (amt >= 0),
    customer_name VARCHAR(128) NOT NULL,
    customer_pseudo_hash VARCHAR(64) NOT NULL,
    city VARCHAR(64),
    state VARCHAR(16),
    city_pop INTEGER,
    distance_km NUMERIC(8, 2) NOT NULL DEFAULT 0,
    trans_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_fraud_predicted BOOLEAN NOT NULL DEFAULT FALSE,
    fraud_probability NUMERIC(6, 4) NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    model_version VARCHAR(64) DEFAULT 'champion',
    scored_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trans_time ON transactions(trans_time);
CREATE INDEX IF NOT EXISTS idx_is_fraud ON transactions(is_fraud_predicted);
CREATE INDEX IF NOT EXISTS idx_merchant ON transactions(merchant);

-- 2. Journal des alertes de fraude temps réel (Console + Log JSON + E-mail SMTP)
CREATE TABLE IF NOT EXISTS fraud_alerts (
    id SERIAL PRIMARY KEY,
    trans_num VARCHAR(64) NOT NULL REFERENCES transactions(trans_num) ON DELETE CASCADE,
    amt NUMERIC(12, 2) NOT NULL,
    merchant VARCHAR(128),
    fraud_probability NUMERIC(6, 4) NOT NULL,
    risk_level VARCHAR(16) NOT NULL,
    alert_channel VARCHAR(64) NOT NULL DEFAULT 'SMTP_EMAIL_AND_LOG',
    alert_sent_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Synthèses quotidiennes idempotentes pour l'audit matinal (DAG Apache Airflow)
CREATE TABLE IF NOT EXISTS daily_audit_summary (
    id SERIAL PRIMARY KEY,
    audit_date DATE UNIQUE NOT NULL,
    total_transactions INTEGER NOT NULL,
    total_volume_eur NUMERIC(14, 2) NOT NULL,
    frauds_detected INTEGER NOT NULL,
    fraud_volume_eur NUMERIC(14, 2) NOT NULL,
    fraud_rate_pct NUMERIC(5, 2) NOT NULL,
    top_fraud_category VARCHAR(64),
    dlq_rejected_count INTEGER NOT NULL DEFAULT 0,
    data_drift_status VARCHAR(32) NOT NULL DEFAULT 'OK',
    audit_generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 4. Dead Letter Queue (DLQ) relationnelle pour tracer les rejets Pandera / Kafka
CREATE TABLE IF NOT EXISTS dead_letter_queue (
    id SERIAL PRIMARY KEY,
    trans_num VARCHAR(64),
    raw_payload TEXT NOT NULL,
    error_reason VARCHAR(512) NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'KAFKA_STREAM',
    received_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
