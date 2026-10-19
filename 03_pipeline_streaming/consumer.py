import os
import sys
import time
import json
import urllib.request
import importlib
from typing import Dict, Any, Optional

# Forcer l'encodage console UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Imports dynamiques pour supporter les dossiers avec chiffres
app_mod = importlib.import_module("02_api.app")
alert_mod = importlib.import_module("03_pipeline_streaming.alert_service")
db_mod = importlib.import_module("05_database.db_manager")

process_single = app_mod.process_single
load_model = app_mod.load_model
alert_engine = alert_mod.alert_engine
insert_transaction = db_mod.insert_transaction
insert_dlq = db_mod.insert_dlq
init_db = db_mod.init_db

API_URL = "http://127.0.0.1:8080/predict-raw"

# Vérification présence client Kafka
KAFKA_AVAILABLE = False
try:
    from confluent_kafka import Consumer as ConfluentConsumer, Producer as ConfluentProducer, KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    try:
        from kafka import KafkaConsumer, KafkaProducer
        KAFKA_AVAILABLE = "kafka-python"
    except ImportError:
        KAFKA_AVAILABLE = False


class TransactionConsumer:
    """
    Consommateur de streaming Apache Kafka pour le scoring et l'alerte de fraude en temps réel.
    - Écoute le topic 'raw-transactions'
    - Valide le schéma des messages (Data Quality Gate)
    - Isole les messages corrompus dans la Dead Letter Queue (DLQ 'fraud-dlq')
    - Effectue l'inférence via l'API ou le modèle local
    - Notifie en direct et persiste en base opérationnelle + Data Lake Bronze Parquet
    """

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "raw-transactions",
        dlq_topic: str = "fraud-dlq",
        group_id: str = "fraud-scoring-group",
        use_api_service: bool = False
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.dlq_topic = dlq_topic
        self.group_id = group_id
        self.use_api_service = use_api_service
        
        init_db()
        load_model()
        
        self.consumer = None
        self.dlq_producer = None
        self._init_kafka()

    def _init_kafka(self):
        """Initialise la connexion au cluster Kafka."""
        if KAFKA_AVAILABLE == True:
            try:
                self.consumer = ConfluentConsumer({
                    'bootstrap.servers': self.bootstrap_servers,
                    'group.id': self.group_id,
                    'auto.offset.reset': 'earliest',
                    'enable.auto.commit': True
                })
                self.consumer.subscribe([self.topic])
                
                self.dlq_producer = ConfluentProducer({'bootstrap.servers': self.bootstrap_servers})
                print(f"✅ Consommateur Kafka connecté au topic '{self.topic}' (Broker: {self.bootstrap_servers})")
            except Exception as e:
                print(f"ℹ️ Kafka non joignable ({e}). Mode événementiel direct activé.")
                self.consumer = None

    def validate_schema(self, tx: Dict[str, Any]) -> tuple[bool, str]:
        """
        Contrôle qualité des flux (C5) : validation de schéma et des règles métier.
        Vérifie la présence et la cohérence des attributs minimaux.
        """
        if not isinstance(tx, dict):
            return False, "Le payload n'est pas un dictionnaire JSON"
        
        if "amt" not in tx or tx["amt"] is None:
            return False, "Attribut 'amt' obligatoire manquant"
        
        try:
            amt_val = float(tx["amt"])
            if amt_val < 0:
                return False, f"Montant négatif invalide : {amt_val}"
        except (ValueError, TypeError):
            return False, f"Format du montant invalide : {tx.get('amt')}"
            
        return True, "OK"

    def send_to_dlq(self, raw_data: Any, reason: str):
        """Redirige les messages défectueux vers la Dead Letter Queue."""
        print(f"⚠️ [DLQ] Message rejeté et routé vers DLQ : {reason}")
        # 1. Base SQL DLQ
        insert_dlq(raw_data, error_reason=reason, source="KAFKA_STREAM")
        # 2. Topic Kafka DLQ
        if self.dlq_producer:
            try:
                payload = json.dumps({"payload": raw_data, "reason": reason, "rejected_at": time.time()}).encode('utf-8')
                self.dlq_producer.produce(self.dlq_topic, payload)
                self.dlq_producer.poll(0)
            except Exception as e:
                print(f"⚠️ Erreur publication Kafka DLQ : {e}")

    def score_via_http(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Appelle le microservice FastAPI via HTTP."""
        data = json.dumps(tx).encode('utf-8')
        req = urllib.request.Request(API_URL, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))

    def process_message(self, tx: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Traite une transaction de bout en bout avec contrôle de qualité."""
        # 1. Validation de schéma (C5)
        is_valid, reason = self.validate_schema(tx)
        if not is_valid:
            self.send_to_dlq(tx, reason)
            return None

        # 2. Scoring ML
        try:
            if self.use_api_service:
                score = self.score_via_http(tx)
            else:
                score = process_single(tx)
        except Exception:
            score = process_single(tx)

        # 3. Persistance dans la base relationnelle opérationnelle & Data Lake Bronze
        insert_transaction(tx, score)

        # 4. Alerte immédiate si suspicion de fraude (C4)
        is_fraud = score.get("is_fraud", False)
        prob = score.get("fraud_probability", 0.0)
        
        if is_fraud or prob >= 0.50:
            alert_engine.notify_fraud(tx, score)
        else:
            amt = float(tx.get("amt", 0.0))
            merchant = str(tx.get("merchant", "Inconnu"))[:25]
            lat_ms = score.get("latency_ms", 0.0)
            dist = score.get("distance_km", 0.0)
            print(f"  🟢 [VALIDE] {str(tx.get('trans_num'))[:16]}... | {amt:>7.2f} € | {merchant:<25} | Dist: {dist:>5.1f}km | Risque: {prob*100:>4.1f}% | Latence: {lat_ms:.1f}ms")

        return score

    def poll_messages(self, timeout: float = 1.0, max_messages: int = 10) -> int:
        """
        Consomme les messages en attente dans le topic Kafka réel.
        """
        if not self.consumer:
            return 0
            
        count = 0
        while count < max_messages:
            msg = self.consumer.poll(timeout=timeout)
            if msg is None:
                break
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"⚠️ Erreur Kafka Consumer : {msg.error()}")
                break
                
            try:
                tx_data = json.loads(msg.value().decode('utf-8'))
                self.process_message(tx_data)
                count += 1
            except Exception as e:
                self.send_to_dlq(msg.value().decode('utf-8', errors='replace'), f"JSON Decode Error: {e}")
                
        return count

    def close(self):
        if self.consumer:
            self.consumer.close()


if __name__ == "__main__":
    consumer = TransactionConsumer()
    print("🎧 Test de consommation unitaire...")
    sample_tx = {
        "trans_num": "test_txn_sample_01",
        "amt": 980.50,
        "merchant": "fraud_Luxury_Jewelry",
        "category": "shopping_net",
        "lat": 40.7128,
        "long": -74.0060,
        "merch_lat": 48.8566,
        "merch_long": 2.3522,
        "city_pop": 500000,
        "dob": "1992-04-12"
    }
    consumer.process_message(sample_tx)
