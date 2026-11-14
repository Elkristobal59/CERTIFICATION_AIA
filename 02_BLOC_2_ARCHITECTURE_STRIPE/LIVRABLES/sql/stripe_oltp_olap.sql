-- =============================================================================
-- STRIPE AI INFRASTRUCTURE - DDL POSTGRESQL / REDSHIFT COMPLET (OLTP + OLAP)
-- Généré à partir des schémas DBML de référence : stripe_oltp.dbml & stripe_olap.dbml
-- Certification Architecte IA (RNCP 41993) - Bloc 2
-- =============================================================================

-- -----------------------------------------------------------------------------
-- PARTIE 1 : SYSTÈME TRANSACTIONNEL OLTP (3NF - ACID)
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS oltp;
SET search_path TO oltp, public;

-- Entité marchande opérant sur Stripe Connect ou Checkout
CREATE TABLE IF NOT EXISTS oltp.Merchant (
    merchant_id varchar(32) PRIMARY KEY UNIQUE,
    business_name varchar(150) NOT NULL,
    legal_entity_type varchar(50),
    mcc_code varchar(4) NOT NULL,
    country varchar(2) NOT NULL,
    settlement_currency varchar(3) NOT NULL,
    payout_schedule varchar(20) DEFAULT 'daily',
    risk_level varchar(20) DEFAULT 'standard',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);
COMMENT ON TABLE oltp.Merchant IS 'Entité marchande opérant sur Stripe Connect ou Checkout';

-- Client final (acheteur). Conforme RGPD & CCPA : données PII pseudonymisées
CREATE TABLE IF NOT EXISTS oltp.Customer (
    customer_id varchar(32) PRIMARY KEY UNIQUE,
    merchant_id varchar(32),
    email_hash varchar(64) NOT NULL,
    country varchar(2),
    risk_score FLOAT DEFAULT 0.0,
    do_not_sell_or_share BOOLEAN DEFAULT false,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP
);
COMMENT ON TABLE oltp.Customer IS 'Client final (acheteur). Conforme RGPD & CCPA : données PII pseudonymisées';

-- Token de paiement sécurisé. Strictement conforme PCI-DSS Level 1 (zéro PAN stocké)
CREATE TABLE IF NOT EXISTS oltp.PaymentMethod (
    payment_method_id varchar(32) PRIMARY KEY,
    customer_id varchar(32),
    type varchar(30) NOT NULL,
    fingerprint varchar(64) NOT NULL,
    card_brand varchar(20),
    card_last4 varchar(4),
    card_exp_month INT,
    card_exp_year INT,
    card_country varchar(2),
    card_funding varchar(20),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.PaymentMethod IS 'Token de paiement sécurisé. Strictement conforme PCI-DSS Level 1 (zéro PAN stocké)';

-- Table maîtresse OLTP. Clé de voûte de l encaissement temps réel. Propriétés ACID garanties.
CREATE TABLE IF NOT EXISTS oltp.Transaction (
    transaction_id varchar(32) PRIMARY KEY UNIQUE,
    merchant_id varchar(32) NOT NULL,
    customer_id varchar(32),
    payment_method_id varchar(32) NOT NULL,
    subscription_id varchar(32),
    exchange_rate_id varchar(40),
    amount BIGINT NOT NULL,
    currency varchar(3) NOT NULL,
    stripe_fee BIGINT NOT NULL,
    net_amount BIGINT NOT NULL,
    status varchar(25) NOT NULL,
    failure_code varchar(50),
    client_ip varchar(45),
    ip_country varchar(2),
    device_type varchar(20),
    fraud_score FLOAT,
    fraud_action varchar(20),
    idempotency_key varchar(64) UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    captured_at TIMESTAMP
);
COMMENT ON TABLE oltp.Transaction IS 'Table maîtresse OLTP. Clé de voûte de l encaissement temps réel. Propriétés ACID garanties.';

-- Enregistrement d inférence temps réel pour traçabilité MLOps et réentraînement
CREATE TABLE IF NOT EXISTS oltp.FraudEvaluation (
    evaluation_id varchar(32) PRIMARY KEY,
    transaction_id varchar(32) NOT NULL,
    model_version varchar(50) NOT NULL,
    inference_latency_ms FLOAT NOT NULL,
    risk_score FLOAT NOT NULL,
    rule_triggers varchar(255),
    vector_distance FLOAT,
    feature_vector_id varchar(64),
    final_decision varchar(20) NOT NULL,
    evaluated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.FraudEvaluation IS 'Enregistrement d inférence temps réel pour traçabilité MLOps et réentraînement';

-- Remboursements partiels ou totaux
CREATE TABLE IF NOT EXISTS oltp.Refund (
    refund_id varchar(32) PRIMARY KEY,
    transaction_id varchar(32) NOT NULL,
    amount BIGINT NOT NULL,
    currency varchar(3) NOT NULL,
    reason varchar(50),
    status varchar(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.Refund IS 'Remboursements partiels ou totaux';

-- Chargebacks et contestations de paiements
CREATE TABLE IF NOT EXISTS oltp.Dispute (
    dispute_id varchar(32) PRIMARY KEY,
    transaction_id varchar(32) NOT NULL,
    amount BIGINT NOT NULL,
    currency varchar(3) NOT NULL,
    reason varchar(50) NOT NULL,
    status varchar(30) NOT NULL,
    evidence_due_by TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.Dispute IS 'Chargebacks et contestations de paiements';

-- Virements bancaires automatiques vers les comptes des marchands
CREATE TABLE IF NOT EXISTS oltp.MerchantPayout (
    payout_id varchar(32) PRIMARY KEY,
    merchant_id varchar(32) NOT NULL,
    amount BIGINT NOT NULL,
    currency varchar(3) NOT NULL,
    destination_bank_account_last4 varchar(4),
    status varchar(20) NOT NULL,
    arrival_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.MerchantPayout IS 'Virements bancaires automatiques vers les comptes des marchands';

-- Donnée de référence : Catalogue produits et plans tarifaires marchands
CREATE TABLE IF NOT EXISTS oltp.ProductCatalog (
    product_id varchar(32) PRIMARY KEY,
    merchant_id varchar(32) NOT NULL,
    product_name varchar(120) NOT NULL,
    category varchar(50) NOT NULL,
    unit_price_cents BIGINT NOT NULL,
    currency varchar(3) NOT NULL,
    billing_type varchar(20) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.ProductCatalog IS 'Donnée de référence : Catalogue produits et plans tarifaires marchands';

-- Gestion des abonnements et facturation récurrente (Smart Retries)
CREATE TABLE IF NOT EXISTS oltp.Subscription (
    subscription_id varchar(32) PRIMARY KEY,
    merchant_id varchar(32) NOT NULL,
    customer_id varchar(32) NOT NULL,
    product_id varchar(32) NOT NULL,
    payment_method_id varchar(32) NOT NULL,
    status varchar(25) NOT NULL,
    billing_cycle varchar(20) NOT NULL,
    current_period_start TIMESTAMP NOT NULL,
    current_period_end TIMESTAMP NOT NULL,
    retry_attempt_count INT DEFAULT 0,
    cancel_at_period_end BOOLEAN DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE oltp.Subscription IS 'Gestion des abonnements et facturation récurrente (Smart Retries)';

-- Donnée de référence : Pays, régions réglementaires et zones monétaires
CREATE TABLE IF NOT EXISTS oltp.CountryReference (
    country_code varchar(2) PRIMARY KEY,
    country_name varchar(100) NOT NULL,
    region_code varchar(30) NOT NULL,
    regulatory_zone varchar(30) NOT NULL,
    default_currency varchar(3) NOT NULL,
    is_sepa_zone BOOLEAN DEFAULT false,
    sanction_risk_tier varchar(20) DEFAULT 'low'
);
COMMENT ON TABLE oltp.CountryReference IS 'Donnée de référence : Pays, régions réglementaires et zones monétaires';

-- Donnée de référence : Historique horodaté des taux de change multi-devises
CREATE TABLE IF NOT EXISTS oltp.CurrencyExchangeRate (
    rate_id varchar(40) PRIMARY KEY,
    base_currency varchar(3) NOT NULL,
    target_currency varchar(3) NOT NULL,
    exchange_rate NUMERIC(14,6) NOT NULL,
    effective_from TIMESTAMP NOT NULL,
    effective_to TIMESTAMP,
    source_provider varchar(40) DEFAULT 'ECB_FIXING'
);
COMMENT ON TABLE oltp.CurrencyExchangeRate IS 'Donnée de référence : Historique horodaté des taux de change multi-devises';

-- Contraintes d'intégrité référentielle (OLTP)
ALTER TABLE oltp.Merchant ADD CONSTRAINT fk_merchant_country FOREIGN KEY (country) REFERENCES oltp.CountryReference(country_code);
ALTER TABLE oltp.Customer ADD CONSTRAINT fk_customer_merchant_id FOREIGN KEY (merchant_id) REFERENCES oltp.Merchant(merchant_id);
ALTER TABLE oltp.PaymentMethod ADD CONSTRAINT fk_paymentmethod_customer_id FOREIGN KEY (customer_id) REFERENCES oltp.Customer(customer_id);
ALTER TABLE oltp.Transaction ADD CONSTRAINT fk_transaction_merchant_id FOREIGN KEY (merchant_id) REFERENCES oltp.Merchant(merchant_id);
ALTER TABLE oltp.Transaction ADD CONSTRAINT fk_transaction_customer_id FOREIGN KEY (customer_id) REFERENCES oltp.Customer(customer_id);
ALTER TABLE oltp.Transaction ADD CONSTRAINT fk_transaction_payment_method_id FOREIGN KEY (payment_method_id) REFERENCES oltp.PaymentMethod(payment_method_id);
ALTER TABLE oltp.Transaction ADD CONSTRAINT fk_transaction_subscription_id FOREIGN KEY (subscription_id) REFERENCES oltp.Subscription(subscription_id);
ALTER TABLE oltp.Transaction ADD CONSTRAINT fk_transaction_exchange_rate_id FOREIGN KEY (exchange_rate_id) REFERENCES oltp.CurrencyExchangeRate(rate_id);
ALTER TABLE oltp.FraudEvaluation ADD CONSTRAINT fk_fraudevaluation_transaction_id FOREIGN KEY (transaction_id) REFERENCES oltp.Transaction(transaction_id);
ALTER TABLE oltp.Refund ADD CONSTRAINT fk_refund_transaction_id FOREIGN KEY (transaction_id) REFERENCES oltp.Transaction(transaction_id);
ALTER TABLE oltp.Dispute ADD CONSTRAINT fk_dispute_transaction_id FOREIGN KEY (transaction_id) REFERENCES oltp.Transaction(transaction_id);
ALTER TABLE oltp.MerchantPayout ADD CONSTRAINT fk_merchantpayout_merchant_id FOREIGN KEY (merchant_id) REFERENCES oltp.Merchant(merchant_id);
ALTER TABLE oltp.ProductCatalog ADD CONSTRAINT fk_productcatalog_merchant_id FOREIGN KEY (merchant_id) REFERENCES oltp.Merchant(merchant_id);
ALTER TABLE oltp.Subscription ADD CONSTRAINT fk_subscription_merchant_id FOREIGN KEY (merchant_id) REFERENCES oltp.Merchant(merchant_id);
ALTER TABLE oltp.Subscription ADD CONSTRAINT fk_subscription_customer_id FOREIGN KEY (customer_id) REFERENCES oltp.Customer(customer_id);
ALTER TABLE oltp.Subscription ADD CONSTRAINT fk_subscription_product_id FOREIGN KEY (product_id) REFERENCES oltp.ProductCatalog(product_id);
ALTER TABLE oltp.Subscription ADD CONSTRAINT fk_subscription_payment_method_id FOREIGN KEY (payment_method_id) REFERENCES oltp.PaymentMethod(payment_method_id);

-- -----------------------------------------------------------------------------
-- PARTIE 2 : ENTREPÔT ANALYTIQUE OLAP (SCHÉMA EN ÉTOILE / GALAXIE)
-- -----------------------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS olap;
SET search_path TO olap, public;

-- Dimension Marchand (analyse sectorielle, maturité et profil de risque)
CREATE TABLE IF NOT EXISTS olap.DimMerchant (
    merchant_key SERIAL PRIMARY KEY,
    merchant_id varchar(32) NOT NULL,
    business_name varchar(150),
    mcc_code varchar(4),
    mcc_category_name varchar(50),
    country varchar(2),
    risk_level varchar(20),
    created_year INT,
    created_month INT,
    is_active BOOLEAN
);
COMMENT ON TABLE olap.DimMerchant IS 'Dimension Marchand (analyse sectorielle, maturité et profil de risque)';

-- Dimension Client (segmentation RFM, cohorte et profil de risque)
CREATE TABLE IF NOT EXISTS olap.DimCustomer (
    customer_key SERIAL PRIMARY KEY,
    customer_id varchar(32) NOT NULL,
    merchant_id varchar(32) NOT NULL,
    country varchar(2),
    risk_segment varchar(20),
    rfm_tier varchar(20),
    do_not_sell_or_share BOOLEAN DEFAULT false,
    account_age_days INT,
    created_year INT
);
COMMENT ON TABLE olap.DimCustomer IS 'Dimension Client (segmentation RFM, cohorte et profil de risque)';

-- Dimension Produit pour le suivi de performance des offres et abonnements
CREATE TABLE IF NOT EXISTS olap.DimProduct (
    product_key SERIAL PRIMARY KEY,
    product_id varchar(32) NOT NULL,
    merchant_id varchar(32) NOT NULL,
    product_name varchar(120) NOT NULL,
    category varchar(50),
    billing_type varchar(20),
    unit_price_cents BIGINT,
    is_active BOOLEAN
);
COMMENT ON TABLE olap.DimProduct IS 'Dimension Produit pour le suivi de performance des offres et abonnements';

-- Dimension Temps standard pour agrégations chronologiques rapides
CREATE TABLE IF NOT EXISTS olap.DimDate (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    month INT NOT NULL,
    month_name varchar(20) NOT NULL,
    week_of_year INT NOT NULL,
    day_of_month INT NOT NULL,
    day_of_week INT NOT NULL,
    day_name varchar(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    is_holiday BOOLEAN DEFAULT false
);
COMMENT ON TABLE olap.DimDate IS 'Dimension Temps standard pour agrégations chronologiques rapides';

-- Dimension Moyen de paiement pour audit des coûts d interchange et risques
CREATE TABLE IF NOT EXISTS olap.DimPaymentMethod (
    payment_method_key SERIAL PRIMARY KEY,
    type varchar(30) NOT NULL,
    card_brand varchar(20),
    card_country varchar(2),
    card_funding varchar(20),
    is_cross_border BOOLEAN
);
COMMENT ON TABLE olap.DimPaymentMethod IS 'Dimension Moyen de paiement pour audit des coûts d interchange et risques';

-- Dimension Géographie pour détection de clusters de cybercriminalité et conformité
CREATE TABLE IF NOT EXISTS olap.DimGeoLocation (
    geo_key SERIAL PRIMARY KEY,
    country_code varchar(2) NOT NULL,
    region varchar(100),
    city varchar(100),
    regulatory_zone varchar(30),
    is_high_risk_country BOOLEAN DEFAULT false,
    is_datacenter_or_vpn BOOLEAN DEFAULT false
);
COMMENT ON TABLE olap.DimGeoLocation IS 'Dimension Géographie pour détection de clusters de cybercriminalité et conformité';

-- Dimension État et motifs de rejet
CREATE TABLE IF NOT EXISTS olap.DimStatus (
    status_key SERIAL PRIMARY KEY,
    payment_status varchar(25) NOT NULL,
    failure_code varchar(50),
    dispute_reason varchar(50),
    fraud_action varchar(20)
);
COMMENT ON TABLE olap.DimStatus IS 'Dimension État et motifs de rejet';

-- Table de faits principale. Grain : 1 ligne = 1 transaction unitaire
CREATE TABLE IF NOT EXISTS olap.FactTransactions (
    fact_txn_key BIGINT PRIMARY KEY,
    date_key INT NOT NULL,
    merchant_key INT NOT NULL,
    customer_key INT,
    product_key INT,
    payment_method_key INT NOT NULL,
    geo_key INT NOT NULL,
    status_key INT NOT NULL,
    gross_amount_cents BIGINT NOT NULL,
    stripe_fee_cents BIGINT NOT NULL,
    interchange_fee_cents BIGINT,
    net_merchant_amount_cents BIGINT NOT NULL,
    refunded_amount_cents BIGINT DEFAULT 0,
    is_disputed INT DEFAULT 0,
    is_recurring INT DEFAULT 0,
    fraud_score FLOAT,
    inference_latency_ms FLOAT,
    transaction_count INT DEFAULT 1
);
COMMENT ON TABLE olap.FactTransactions IS 'Table de faits principale. Grain : 1 ligne = 1 transaction unitaire';

-- Table de faits agrégée quotidienne. Grain : 1 ligne = 1 marchand par jour
CREATE TABLE IF NOT EXISTS olap.FactDailyMerchantRevenue (
    fact_daily_key BIGINT PRIMARY KEY,
    date_key INT NOT NULL,
    merchant_key INT NOT NULL,
    total_volume_cents BIGINT NOT NULL,
    successful_txns_count INT NOT NULL,
    failed_txns_count INT NOT NULL,
    refunded_txns_count INT NOT NULL,
    total_fees_collected_cents BIGINT NOT NULL,
    total_payout_cents BIGINT NOT NULL,
    chargeback_count INT NOT NULL DEFAULT 0,
    fraud_blocked_count INT NOT NULL DEFAULT 0
);
COMMENT ON TABLE olap.FactDailyMerchantRevenue IS 'Table de faits agrégée quotidienne. Grain : 1 ligne = 1 marchand par jour';

-- Table de faits d audit de sécurité et de performance de l IA Radar
CREATE TABLE IF NOT EXISTS olap.FactFraudAlerts (
    fact_alert_key BIGINT PRIMARY KEY,
    date_key INT NOT NULL,
    merchant_key INT NOT NULL,
    payment_method_key INT NOT NULL,
    geo_key INT NOT NULL,
    risk_score FLOAT NOT NULL,
    vector_distance FLOAT,
    prevented_loss_cents BIGINT NOT NULL,
    action_taken varchar(20) NOT NULL,
    is_false_positive INT DEFAULT 0
);
COMMENT ON TABLE olap.FactFraudAlerts IS 'Table de faits d audit de sécurité et de performance de l IA Radar';

-- Table de faits conformité et audit réglementaire automatisé
CREATE TABLE IF NOT EXISTS olap.FactComplianceAudits (
    fact_audit_key BIGINT PRIMARY KEY,
    date_key INT NOT NULL,
    merchant_key INT,
    geo_key INT,
    regulation_framework varchar(20) NOT NULL,
    event_type varchar(40) NOT NULL,
    records_affected INT NOT NULL DEFAULT 1,
    resolution_sla_hours FLOAT NOT NULL,
    compliance_status varchar(20) NOT NULL
);
COMMENT ON TABLE olap.FactComplianceAudits IS 'Table de faits conformité et audit réglementaire automatisé';

-- Table de synthèse mensuelle / Vue Matérialisée pour BI Produit (< 200 ms)
CREATE TABLE IF NOT EXISTS olap.AggMonthlyProductPerformance (
    agg_monthly_key BIGINT PRIMARY KEY,
    year_month INT NOT NULL,
    merchant_key INT NOT NULL,
    product_key INT NOT NULL,
    monthly_gpv_cents BIGINT NOT NULL,
    active_subscriptions_count INT NOT NULL,
    renewal_success_rate_pct FLOAT NOT NULL,
    churn_rate_pct FLOAT NOT NULL
);
COMMENT ON TABLE olap.AggMonthlyProductPerformance IS 'Table de synthèse mensuelle / Vue Matérialisée pour BI Produit (< 200 ms)';

-- Contraintes d'intégrité référentielle (OLAP)
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_date_key FOREIGN KEY (date_key) REFERENCES olap.DimDate(date_key);
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_merchant_key FOREIGN KEY (merchant_key) REFERENCES olap.DimMerchant(merchant_key);
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_customer_key FOREIGN KEY (customer_key) REFERENCES olap.DimCustomer(customer_key);
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_product_key FOREIGN KEY (product_key) REFERENCES olap.DimProduct(product_key);
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_payment_method_key FOREIGN KEY (payment_method_key) REFERENCES olap.DimPaymentMethod(payment_method_key);
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_geo_key FOREIGN KEY (geo_key) REFERENCES olap.DimGeoLocation(geo_key);
ALTER TABLE olap.FactTransactions ADD CONSTRAINT fk_facttransactions_status_key FOREIGN KEY (status_key) REFERENCES olap.DimStatus(status_key);
ALTER TABLE olap.FactDailyMerchantRevenue ADD CONSTRAINT fk_factdailymerchantrevenue_date_key FOREIGN KEY (date_key) REFERENCES olap.DimDate(date_key);
ALTER TABLE olap.FactDailyMerchantRevenue ADD CONSTRAINT fk_factdailymerchantrevenue_merchant_key FOREIGN KEY (merchant_key) REFERENCES olap.DimMerchant(merchant_key);
ALTER TABLE olap.FactFraudAlerts ADD CONSTRAINT fk_factfraudalerts_date_key FOREIGN KEY (date_key) REFERENCES olap.DimDate(date_key);
ALTER TABLE olap.FactFraudAlerts ADD CONSTRAINT fk_factfraudalerts_merchant_key FOREIGN KEY (merchant_key) REFERENCES olap.DimMerchant(merchant_key);
ALTER TABLE olap.FactFraudAlerts ADD CONSTRAINT fk_factfraudalerts_payment_method_key FOREIGN KEY (payment_method_key) REFERENCES olap.DimPaymentMethod(payment_method_key);
ALTER TABLE olap.FactFraudAlerts ADD CONSTRAINT fk_factfraudalerts_geo_key FOREIGN KEY (geo_key) REFERENCES olap.DimGeoLocation(geo_key);
ALTER TABLE olap.FactComplianceAudits ADD CONSTRAINT fk_factcomplianceaudits_date_key FOREIGN KEY (date_key) REFERENCES olap.DimDate(date_key);
ALTER TABLE olap.FactComplianceAudits ADD CONSTRAINT fk_factcomplianceaudits_merchant_key FOREIGN KEY (merchant_key) REFERENCES olap.DimMerchant(merchant_key);
ALTER TABLE olap.FactComplianceAudits ADD CONSTRAINT fk_factcomplianceaudits_geo_key FOREIGN KEY (geo_key) REFERENCES olap.DimGeoLocation(geo_key);
ALTER TABLE olap.AggMonthlyProductPerformance ADD CONSTRAINT fk_aggmonthlyproductperformance_merchant_key FOREIGN KEY (merchant_key) REFERENCES olap.DimMerchant(merchant_key);
ALTER TABLE olap.AggMonthlyProductPerformance ADD CONSTRAINT fk_aggmonthlyproductperformance_product_key FOREIGN KEY (product_key) REFERENCES olap.DimProduct(product_key);

-- -----------------------------------------------------------------------------
-- PARTIE 3 : INDEXATION & OPTIMISATION DES REQUÊTES
-- -----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_oltp_txn_merchant_created ON oltp.Transaction(merchant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_oltp_txn_customer ON oltp.Transaction(customer_id);
CREATE INDEX IF NOT EXISTS idx_oltp_pm_fingerprint ON oltp.PaymentMethod(fingerprint);
CREATE INDEX IF NOT EXISTS idx_oltp_sub_next_billing ON oltp.Subscription(status, next_billing_date);
CREATE INDEX IF NOT EXISTS idx_olap_fact_txn_date_merch ON olap.FactTransactions(date_key, merchant_key);
CREATE INDEX IF NOT EXISTS idx_olap_fact_txn_fraud ON olap.FactTransactions(fraud_score) WHERE fraud_score >= 60;
