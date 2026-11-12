import os
import sys
import glob
import time
import uuid
import importlib
import urllib.request
import json

from confluent_kafka import Consumer, TopicPartition

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

features_mod = importlib.import_module("01_train.features")
producer_mod = importlib.import_module("03_pipeline_streaming.producer")
consumer_mod = importlib.import_module("03_pipeline_streaming.consumer")
audit_mod = importlib.import_module("04_batch_airflow.run_daily_audit")
db_mod = importlib.import_module("05_database.db_manager")

features_mod.load_project_env()
FraudTransactionProducer = producer_mod.FraudTransactionProducer
FraudConsumer = consumer_mod.FraudConsumer
generate_daily_audit = audit_mod.generate_daily_audit
init_db = db_mod.init_db
get_stats_summary = db_mod.get_stats_summary


def _check_service(name: str, url: str) -> str:
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return f"ONLINE (HTTP {r.status})"
    except Exception as exc:
        return f"OFFLINE ({exc})"


def main():
    print("=" * 72)
    print("🚀 DÉMO END-TO-END TEMPS RÉEL & BATCH — BLOC 3 FRAUD DETECTION (RNCP 41993)")
    print("=" * 72)

    init_db()
    smtp_host = os.getenv("SMTP_HOST", "localhost")
    smtp_port = os.getenv("SMTP_PORT", "1025")
    print(f"• MLflow Tracking  : {_check_service('MLflow', os.getenv('MLFLOW_TRACKING_URI', 'http://localhost:5000'))}")
    print(f"• API Scoring      : {_check_service('API', 'http://localhost:8080/health')}")
    if smtp_host in ("localhost", "127.0.0.1", "mailpit"):
        print(f"• Mailpit SMTP UI  : {_check_service('Mailpit', 'http://localhost:8025/api/v1/messages')}")
    else:
        print(f"• Alerting SMTP    : CONFIGURÉ ({smtp_host}:{smtp_port} -> {os.getenv('ALERT_RECIPIENT', '')})")

    producer = FraudTransactionProducer()
    producer.ensure_topic(os.getenv("KAFKA_TOPIC_DLQ", "fraud-dlq"))

    # Capture de l'offset haut courant avant émission pour ne consommer que le batch courant
    probe = Consumer({
        "bootstrap.servers": producer.bootstrap_servers,
        "group.id": f"probe-{uuid.uuid4().hex[:8]}",
    })
    md = probe.list_topics(producer.topic, timeout=5.0)
    parts = list(md.topics[producer.topic].partitions.keys())
    start_offsets = {}
    for pid in parts:
        _, high = probe.get_watermark_offsets(TopicPartition(producer.topic, pid), timeout=5.0)
        start_offsets[pid] = max(0, high)
    probe.close()

    consumer = FraudConsumer(
        group_id=f"fraud-demo-{uuid.uuid4().hex[:8]}",
        auto_offset_reset="earliest",
        use_api=True,
        start_offsets=start_offsets,
    )

    try:
        demo_batch = []
        hf_tx = producer.fetch_hf_transaction(timeout_sec=8.0)
        if hf_tx:
            hf_tx.setdefault("trans_num", f"txn_hf_{int(time.time() * 1000)}")
            demo_batch.append(("HF_LIVE", hf_tx))
        else:
            demo_batch.append(("LEGIT_1", producer.build_fallback_transaction(simulate_fraud=False)))

        demo_batch.append(("LEGIT_2", producer.build_fallback_transaction(simulate_fraud=False)))
        demo_batch.append(("FRAUD_HIGH_RISK", producer.build_fallback_transaction(simulate_fraud=True)))

        bad_tx = producer.build_fallback_transaction(simulate_fraud=False)
        bad_tx["amt"] = -150.0
        bad_tx["trans_num"] = f"txn_corrupted_{uuid.uuid4().hex[:6]}"
        demo_batch.append(("DLQ_INVALID", bad_tx))

        print(f"\n📡 Émission de {len(demo_batch)} transactions sur le broker Kafka (`{producer.topic}`)...")
        for label, tx in demo_batch:
            producer.send(tx)
            print(f"   📤 [{label}] -> {tx.get('trans_num')} | amt={tx.get('amt')} €")
        producer.flush(5.0)

        print(f"\n🎧 Consommation temps réel depuis Kafka -> Pandera -> API /predict -> SMTP ({smtp_host})/Neon/Bronze...")
        stream_stats = consumer.poll_messages(max_messages=len(demo_batch), idle_timeout_sec=12.0)
        print(f"📈 Bilan Streaming Kafka : {stream_stats}")
    finally:
        producer.close()
        consumer.close()

    print("\n⚙️ Lancement du pipeline Batch Medallion (Bronze -> Silver -> Gold + OpenLineage)...")
    batch_summary = generate_daily_audit()

    db_stats = get_stats_summary()
    print("\n" + "-" * 72)
    print("📊 ÉTAT FINAL POSTGRESQL & DATA LAKE MEDALLION")
    print(f"• PostgreSQL `transactions`      : {db_stats['total_count']} ({db_stats['fraud_count']} fraudes | {db_stats['fraud_rate_pct']}%)")
    print(f"• PostgreSQL `dead_letter_queue` : {db_stats['dlq_count']} rejet(s) Pandera")
    for zone in ("bronze", "silver", "gold", "rejected", "lineage"):
        files = glob.glob(os.path.join(BASE_DIR, "data_lake", zone, "**", "*.*"), recursive=True)
        files = [f for f in files if not f.endswith(".gitkeep")]
        print(f"• Data Lake `{zone}/`{' ' * (10 - len(zone))}: {len(files)} fichier(s)")

    if smtp_host in ("localhost", "127.0.0.1", "mailpit"):
        try:
            with urllib.request.urlopen("http://localhost:8025/api/v1/messages", timeout=3) as r:
                mail_info = json.loads(r.read().decode("utf-8"))
            print(f"• E-mails d'alerte dans Mailpit  : {mail_info.get('total', 0)} message(s)")
        except Exception:
            pass
    else:
        print(f"• Alerting SMTP TLS              : {smtp_host}:{smtp_port} -> {os.getenv('ALERT_RECIPIENT', '')}")
    print("=" * 72)
    return {"batch": batch_summary, "db": db_stats}


if __name__ == "__main__":
    main()
