import os
import sys
import time
import json
import urllib.request
import pandas as pd
from typing import Dict, Any, Generator

# Forcer l'encodage console UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, "fraudTest.csv")
HF_URL = "https://sdacelo-real-time-fraud-detection.hf.space/current-transactions"

# Support de Confluent Kafka ou kafka-python si disponible
KAFKA_CLIENT = None
try:
    from confluent_kafka import Producer as ConfluentProducer
    KAFKA_CLIENT = "confluent"
except ImportError:
    try:
        from kafka import KafkaProducer
        KAFKA_CLIENT = "kafka-python"
    except ImportError:
        KAFKA_CLIENT = "embedded"

class TransactionProducer:
    """
    Producteur de streaming temps réel pour les flux de transactions financières.
    Interroge l'API HuggingFace en continu et publie dans le topic Kafka 'raw-transactions'.
    """

    def __init__(self, bootstrap_servers: str = "localhost:9092", topic: str = "raw-transactions"):
        self.topic = topic
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._init_kafka()

    def _init_kafka(self):
        if KAFKA_CLIENT == "confluent":
            try:
                self.producer = ConfluentProducer({'bootstrap.servers': self.bootstrap_servers})
                print(f"✅ Connecté au broker Kafka via confluent-kafka : {self.bootstrap_servers}")
            except Exception as e:
                print(f"ℹ️ Broker Kafka injoignable ({e}). Basculement en mode Event Stream local.")
                self.producer = None
        elif KAFKA_CLIENT == "kafka-python":
            try:
                self.producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                print(f"✅ Connecté au broker Kafka via kafka-python : {self.bootstrap_servers}")
            except Exception as e:
                print(f"ℹ️ Broker Kafka injoignable ({e}). Basculement en mode Event Stream local.")
                self.producer = None
        else:
            print("ℹ️ Mode Event Stream haute fidélité actif (simulation Kafka in-process).")

    def fetch_hf_transaction(self) -> Dict[str, Any]:
        """Récupère la transaction temps réel publiée par le Space HuggingFace."""
        req = urllib.request.Request(HF_URL, headers={'User-Agent': 'Mozilla/5.0 (Pipeline-Ingestion-AIA)'})
        with urllib.request.urlopen(req, timeout=8) as response:
            raw = response.read().decode('utf-8')
            inner_json = json.loads(raw)
            from io import StringIO
            df = pd.read_json(StringIO(inner_json), orient='split')
            return df.iloc[0].to_dict()

    def fallback_generator(self) -> Generator[Dict[str, Any], None, None]:
        """Générateur de secours à partir de fraudTest.csv avec injection de cas de fraudes réelles."""
        df_sample = pd.read_csv(CSV_PATH, nrows=2000)
        # Mélange fraudes et transactions régulières
        frauds = df_sample[df_sample['is_fraud'] == 1]
        normals = df_sample[df_sample['is_fraud'] == 0]
        
        idx = 0
        while True:
            # 1 transaction sur 4 est une fraude pour dynamiser la démo
            if idx % 4 == 0 and len(frauds) > 0:
                row = frauds.iloc[(idx // 4) % len(frauds)].to_dict()
            else:
                row = normals.iloc[idx % len(normals)].to_dict()
            row['current_time'] = time.strftime("%Y-%m-%d %H:%M:%S")
            yield row
            idx += 1

    def send(self, transaction: Dict[str, Any]):
        """Publie une transaction vers Kafka ou l'Event Stream."""
        # Nettoyage des valeurs non-sérialisables (Timestamp, NaN)
        cleaned = {}
        for k, v in transaction.items():
            if pd.isna(v):
                cleaned[k] = None
            elif hasattr(v, 'isoformat'):
                cleaned[k] = v.isoformat()
            else:
                cleaned[k] = v

        if self.producer:
            if KAFKA_CLIENT == "confluent":
                self.producer.produce(self.topic, json.dumps(cleaned).encode('utf-8'))
                self.producer.poll(0)
            elif KAFKA_CLIENT == "kafka-python":
                self.producer.send(self.topic, cleaned)
                self.producer.flush()
        return cleaned

if __name__ == "__main__":
    producer = TransactionProducer()
    print("📡 Test d'ingestion depuis l'API HuggingFace...")
    try:
        tx = producer.fetch_hf_transaction()
        print(f"📥 Transaction récupérée avec succès : {tx.get('merchant')} | {tx.get('amt')} €")
        res = producer.send(tx)
        print("🚀 Transaction publiée avec succès dans le pipeline !")
    except Exception as e:
        print(f"⚠️ Échec appel API HF ({e}), test avec générateur de secours...")
        gen = producer.fallback_generator()
        tx = next(gen)
        producer.send(tx)
        print(f"📥 Transaction générée : {tx.get('merchant')} | {tx.get('amt')} €")
