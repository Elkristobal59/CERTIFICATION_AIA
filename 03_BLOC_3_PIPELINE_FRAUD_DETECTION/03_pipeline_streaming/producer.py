import os
import sys
import json
import time
import uuid
import argparse
import importlib
import urllib.request
from typing import Any, Dict, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

features_mod = importlib.import_module("01_train.features")
features_mod.load_project_env()

SAMPLE_CSV_PATH = os.path.join(BASE_DIR, "sample_fraud_data.csv")
PARENT_CSV_PATH = os.path.join(os.path.dirname(BASE_DIR), "fraudTest.csv")


class FraudTransactionProducer:
    """Producteur Kafka temps réel consommant l'API Hugging Face (ou fallback dataset local)."""

    def __init__(self, bootstrap_servers: Optional[str] = None, topic: Optional[str] = None):
        self.bootstrap_servers = bootstrap_servers or os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.topic = topic or os.getenv("KAFKA_TOPIC_RAW", "raw-transactions")
        self.hf_url = os.getenv(
            "HF_STREAM_URL",
            "https://sdacelo-real-time-fraud-detection.hf.space/current-transactions",
        )
        self.producer = Producer({"bootstrap.servers": self.bootstrap_servers})
        self.delivered_count = 0
        self.failed_count = 0
        self._sample_df = None
        self.ensure_topic(self.topic)

    def ensure_topic(self, topic_name: str) -> None:
        """Crée le topic Kafka s'il n'existe pas encore (évite la latence d'auto-création)."""
        try:
            admin = AdminClient({"bootstrap.servers": self.bootstrap_servers})
            fs = admin.create_topics([NewTopic(topic_name, num_partitions=1, replication_factor=1)])
            for _, fut in fs.items():
                try:
                    fut.result(timeout=5)
                except Exception:
                    pass
        except Exception:
            pass

    def _delivery_report(self, err, msg):
        if err is not None:
            self.failed_count += 1
            print(f"❌ Échec livraison Kafka ({msg.topic()}): {err}")
        else:
            self.delivered_count += 1

    def _load_fallback_rows(self) -> Optional[pd.DataFrame]:
        if self._sample_df is not None:
            return self._sample_df
        for candidate in (PARENT_CSV_PATH, SAMPLE_CSV_PATH):
            if os.path.exists(candidate):
                self._sample_df = pd.read_csv(candidate, nrows=10000)
                return self._sample_df
        return None

    def fetch_hf_transaction(self, timeout_sec: float = 10.0) -> Optional[Dict[str, Any]]:
        """Interroge le flux temps réel Hugging Face Jedha (format JSON colonne-orienté ou liste)."""
        try:
            req = urllib.request.Request(
                self.hf_url,
                headers={"User-Agent": "FraudDetection-RNCP41993/2.0", "Accept": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
                raw_text = resp.read().decode("utf-8")
            payload = json.loads(raw_text)
            if isinstance(payload, str):
                payload = json.loads(payload)
            if isinstance(payload, dict) and {"columns", "data"}.issubset(payload.keys()):
                cols = payload["columns"]
                rows = payload["data"]
                if rows:
                    return dict(zip(cols, rows[0]))
            if isinstance(payload, list) and payload and isinstance(payload[0], dict):
                return payload[0]
            if isinstance(payload, dict) and payload:
                return payload
        except Exception as exc:
            print(f"ℹ️ API Hugging Face indisponible ({exc}). Bascule sur replay dataset contrôlé.")
        return None

    def build_fallback_transaction(self, simulate_fraud: bool = False) -> Dict[str, Any]:
        """Construit une transaction réaliste (légitime ou frauduleuse) à partir du schéma exact."""
        df = self._load_fallback_rows()
        sampled_from_csv = False
        if df is not None and not df.empty:
            if simulate_fraud:
                subset = df[(df["is_fraud"] == 1) & (df["amt"] >= 300)]
                if subset.empty:
                    subset = df[df["is_fraud"] == 1]
            else:
                subset = df[df["is_fraud"] == 0]
            raw_row = (subset if not subset.empty else df).sample(1).iloc[0].to_dict()
            row = {k: (None if pd.isna(v) else v) for k, v in raw_row.items()}
            row.pop("is_fraud", None)
            row.pop("Unnamed: 0", None)
            sampled_from_csv = not subset.empty
        else:
            row = {
                "cc_num": "4532019283745512",
                "merchant": "fraud_Luxe_Jewelry_Online" if simulate_fraud else "Carrefour Market Lyon",
                "category": "shopping_net" if simulate_fraud else "grocery_pos",
                "amt": 842.65 if simulate_fraud else 42.50,
                "first": "Claire",
                "last": "Dupont",
                "gender": "F",
                "street": "12 Rue de la République",
                "city": "Lyon",
                "state": "FR",
                "zip": 69001,
                "lat": 45.7640,
                "long": 4.8357,
                "city_pop": 12000 if simulate_fraud else 513275,
                "job": "Data Analyst",
                "dob": "1958-09-10" if simulate_fraud else "1990-05-14",
                "merch_lat": 45.92 if simulate_fraud else 45.7680,
                "merch_long": 5.55 if simulate_fraud else 4.8410,
                "trans_date_trans_time": time.strftime("%Y-%m-%d 23:45:00") if simulate_fraud else time.strftime("%Y-%m-%d %H:%M:%S"),
            }

        row["trans_num"] = f"txn_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        row["current_time"] = int(time.time() * 1000)
        if simulate_fraud and not sampled_from_csv:
            row["amt"] = max(float(row.get("amt", 0.0)), 842.65)
            row["trans_date_trans_time"] = time.strftime("%Y-%m-%d 23:45:00")
        return row

    def send(self, tx: Dict[str, Any]) -> None:
        key = str(tx.get("trans_num", "")).encode("utf-8")
        value = json.dumps(tx, default=str, ensure_ascii=False).encode("utf-8")
        self.producer.produce(self.topic, key=key, value=value, callback=self._delivery_report)
        self.producer.poll(0)

    def flush(self, timeout: float = 5.0) -> int:
        return self.producer.flush(timeout)

    def close(self) -> None:
        self.flush(5.0)


def main():
    parser = argparse.ArgumentParser(description="Producteur Kafka de transactions (Hugging Face -> raw-transactions)")
    parser.add_argument("--count", type=int, default=10, help="Nombre de transactions à émettre (0 = continu)")
    parser.add_argument("--interval", type=float, default=1.0, help="Pause en secondes entre envois")
    parser.add_argument("--offline", action="store_true", help="Utiliser uniquement le replay local sans appeler HF")
    args = parser.parse_args()

    producer = FraudTransactionProducer()
    print(f"📡 Producteur Kafka connecté à {producer.bootstrap_servers} (topic={producer.topic})")
    sent = 0
    try:
        while args.count == 0 or sent < args.count:
            tx = None if args.offline else producer.fetch_hf_transaction()
            if tx is None:
                tx = producer.build_fallback_transaction(simulate_fraud=(sent % 4 == 3))
            producer.send(tx)
            sent += 1
            print(f"📤 [{sent}] Émis sur `{producer.topic}` : {tx.get('trans_num')} | {float(tx.get('amt', 0)):.2f} €")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\n🛑 Arrêt producteur demandé.")
    finally:
        producer.close()
        print(f"✅ Producteur fermé proprement ({producer.delivered_count} délivrées, {producer.failed_count} échecs).")


if __name__ == "__main__":
    main()
