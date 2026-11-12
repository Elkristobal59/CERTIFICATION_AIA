-- Initialisation multi-bases au premier démarrage du conteneur PostgreSQL
CREATE DATABASE mlflow_db;
CREATE DATABASE airflow_db;
GRANT ALL PRIVILEGES ON DATABASE fraud_db TO fraud_user;
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO fraud_user;
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO fraud_user;
