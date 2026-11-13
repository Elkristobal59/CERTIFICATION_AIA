import os
import sys
import json
import time
import argparse
import importlib
from typing import Any, Callable, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests
from confluent_kafka import Consumer, KafkaError, Producer, TopicPartition

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

features_mod = importlib.import_module("01_train.features")
api_mod = importlib.import_module("02_api.app")
quality_mod = importlib.import_module("03_pipeline_streaming.quality_gate")
alert_mod = importlib.import_module("03_pipeline_streaming.alert_service")
db_mod = importlib.import_module("05_database.db_manager")

features_mod.load_project_env()
validate_transaction_record = quality_mod.validate_transaction_record
AlertService = alert_mod.AlertService
init_db = db_mod.init_db
insert_dlq = db_mod.insert_dlq
insert_transaction = db_mod.insert_transaction
mask_credit_card = db_mod.mask_credit_card
sanitize_payload_pii = db_mod._sanitize_payload_pii


class FraudConsumer:
    """Consommateur Kafka temps réel : Pandera Quality Gate -> Scoring @champion -> Alertes -> PostgreSQL/Bronze."""

    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        topic: Optional[str] = None,
        dlq_topic: Optional[str] = None,
        group_id: Optional[str] = None,
        auto_offset_reset: str = "latest",
        use_api: bool = True,
        start_offsets: Optional[Dict[int, int]] = None,
    ):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC_RAW", "raw-transactions")
        self.dlq_topic = dlq_topic or os.getenv("KAFKA_TOPIC_DLQ", "fraud-dlq")
        self.group_id = group_id or os.getenv("KAFKA_GROUP_ID", "fraud-scoring-group")
        self.api_url = os.getenv("API_SCORING_URL", "http://localhost:8080/predict").strip()
        self.fraud_threshold = float(os.getenv("FRAUD_THRESHOLD", "0.50"))
        self.use_api = use_api and bool(self.api_url)

        self.alert_engine = AlertService()
        self.dlq_producer = Producer({"bootstrap.servers": self.bootstrap_servers})
        self.consumer = Consumer({
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": auto_offset_reset,
            "enable.auto.commit": True,
        })
        if start_offsets is not None:
            tps = [TopicPartition(self.topic, pid, off) for pid, off in start_offsets.items()]
            self.consumer.assign(tps)
        else:
            self.consumer.subscribe([self.topic])

    def _send_to_dlq(self, raw_payload: Any, reason: str) -> None:
        sanitized = sanitize_payload_pii(raw_payload) if isinstance(raw_payload, dict) else {"raw": str(raw_payload)}
        dlq_event = {
            "error_reason": reason,
            "payload": sanitized,
            "rejected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        try:
            self.dlq_producer.produce(
                self.dlq_topic,
                value=json.dumps(dlq_event, default=str, ensure_ascii=False).encode("utf-8"),
            )
            self.dlq_producer.poll(0)
        except Exception as exc:
            print(f"⚠️ Erreur publication Kafka DLQ ({self.dlq_topic}): {exc}")

        insert_dlq(raw_payload, reason, source="KAFKA_STREAM")
        print(f"☣️  [DLQ PANDERA] Rejet -> `{self.dlq_topic}` & `rejected/` : {reason}")

    def score_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Appelle le microservice FastAPI (/predict) ou infère directement via @champion MLflow."""
        if self.use_api:
            try:
                resp = requests.post(self.api_url, json=tx, timeout=4.0)
                if resp.status_code == 200:
                    return resp.json()
                print(f"ℹ️ API HTTP {resp.status_code} ({self.api_url}) -> bascule inférence locale.")
            except Exception as exc:
                print(f"ℹ️ API HTTP injoignable ({exc}) -> chargement direct modèle MLflow/@champion.")
                self.use_api = False

        return api_mod.process_single(tx)

    def process_message(self, raw_payload: Any) -> str:
        """Valide, score, alerte et persiste un message Kafka unitaire."""
        if isinstance(raw_payload, (bytes, bytearray)):
            raw_payload = raw_payload.decode("utf-8", errors="replace")
        if isinstance(raw_payload, str):
            try:
                tx = json.loads(raw_payload)
            except json.JSONDecodeError as exc:
                self._send_to_dlq(raw_payload, f"JSON invalide : {exc}")
                return "DLQ"
        else:
            tx = raw_payload

        is_valid, reason = validate_transaction_record(tx)
        if not is_valid:
            self._send_to_dlq(tx, reason)
            return "DLQ"

        score = self.score_transaction(tx)
        is_fraud = bool(score.get("is_fraud", False)) or float(score.get("fraud_probability", 0.0)) >= self.fraud_threshold
        alert_channel = None
        if is_fraud:
            alert_channel = self.alert_engine.notify_fraud(tx, score)

        insert_transaction(tx, score, alert_channel=alert_channel)
        tag = "FRAUD" if is_fraud else "LEGIT"
        print(
            f"✅ [{tag}] {score['trans_num']} | {score['amt']:.2f} € | {score['distance_km']:.1f} km "
            f"| Prob={score['fraud_probability']*100:.1f}% | {score['decision']} ({score['latency_ms']}ms)"
        )
        return tag

    def poll_messages(self, max_messages: Optional[int] = None, idle_timeout_sec: float = 8.0) -> Dict[str, int]:
        """Consomme réellement les messages depuis le broker Kafka jusqu'à `max_messages` ou inactivité."""
        stats = {"consumed": 0, "legit": 0, "fraud": 0, "dlq": 0}
        last_activity = time.time()

        while True:
            if max_messages is not None and stats["consumed"] >= max_messages:
                break
            if (time.time() - last_activity) >= idle_timeout_sec:
                break

            msg = self.consumer.poll(0.5)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    print(f"⚠️ Erreur Kafka Consumer : {msg.error()}")
                continue

            last_activity = time.time()
            outcome = self.process_message(msg.value())
            stats["consumed"] += 1
            stats[outcome.lower()] = stats.get(outcome.lower(), 0) + 1

        self.dlq_producer.flush(5.0)
        return stats

    def close(self) -> None:
        self.dlq_producer.flush(5.0)
        self.consumer.close()


def main():
    parser = argparse.ArgumentParser(description="Consommateur Kafka temps réel — Scoring & Alerting Fraude")
    parser.add_argument("--max-messages", type=int, default=None, help="Nombre max de messages avant arrêt")
    parser.add_argument("--idle-timeout", type=float, default=30.0, help="Arrêt si aucun message pendant N sec (0 = infini)")
    parser.add_argument("--no-api", action="store_true", help="Désactiver l'appel HTTP et scorer localement")
    args = parser.parse_args()

    init_db()
    consumer = FraudConsumer(use_api=not args.no_api)
    print(f"🎧 Consumer Kafka en écoute sur `{consumer.topic}` (group={consumer.group_id}, API={consumer.api_url})")
    try:
        if args.idle_timeout <= 0 and args.max_messages is None:
            while True:
                consumer.poll_messages(max_messages=10, idle_timeout_sec=10.0)
        else:
            stats = consumer.poll_messages(max_messages=args.max_messages, idle_timeout_sec=args.idle_timeout)
            print(f"📊 Bilan consommation : {stats}")
    except KeyboardInterrupt:
        print("\n🛑 Arrêt consumer demandé.")
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
