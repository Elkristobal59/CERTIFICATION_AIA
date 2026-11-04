import os
import time
import json
import datetime
from typing import Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_PATH = os.path.join(BASE_DIR, "03_pipeline_streaming", "fraud_alerts.log")

class AlertService:
    """Service de notification de fraude temps réel demandé par le métier."""
    
    def __init__(self, log_path: str = LOG_PATH):
        self.log_path = log_path

    def notify_fraud(self, tx: Dict[str, Any], score: Dict[str, Any]):
        trans_num = tx.get("trans_num", "N/A")
        amt = tx.get("amt", 0.0)
        merchant = tx.get("merchant", "Inconnu")
        category = tx.get("category", "Général")
        # Conformité PCI-DSS & RGPD
        f = (tx.get('first') or '').strip()
        l = (tx.get('last') or '').strip()
        full = f"{f} {l}".strip()
        customer = f"{f[0]}*** {l[0]}***" if (f or l) else "Client Anonyme"
        cc_raw = str(tx.get('cc_num', ''))
        cc_masked = f"{cc_raw[:6]}******{cc_raw[-4:]}" if len(cc_raw) >= 10 else "************"
        prob = score.get("fraud_probability", 0.0)
        risk = score.get("risk_level", "HIGH")
        decision = score.get("decision", "BLOCK")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


        alert_box = f"""
╔══════════════════════════════════════════════════════════════════════════╗
║ 🚨 ALERTE FRAUDE EN TEMPS RÉEL INTERCEPTÉE ! 🚨                          ║
╠══════════════════════════════════════════════════════════════════════════╣
║ 🕒 Date & Heure    : {now_str:<44} ║
║ 🆔 Transaction     : {str(trans_num):<44} ║
║ 💳 Montant         : {amt:>8.2f} €                                      ║
║ 👤 Porteur Carte   : {customer:<44} ║
║ 🏪 Marchand        : {merchant:<44} ║
║ 🏷️ Catégorie       : {category:<44} ║
║ ⚠️ Probabilité     : {prob*100:>5.1f} % (Niveau : {risk:<18})            ║
║ 🛡️ Décision Auto   : {decision:<44} ║
╚══════════════════════════════════════════════════════════════════════════╝
"""
        print(alert_box)
        
        # Enregistrement dans le fichier de log immuable
        record = {
            "timestamp": now_str,
            "trans_num": trans_num,
            "amt": amt,
            "merchant": merchant,
            "category": category,
            "customer": customer,
            "fraud_probability": prob,
            "risk_level": risk,
            "decision": decision
        }
        
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

alert_engine = AlertService()

if __name__ == "__main__":
    test_tx = {"trans_num": "txn_test_12345", "amt": 892.40, "merchant": "fraud_HighEnd_Electronics", "category": "shopping_net", "first": "John", "last": "Doe"}
    test_score = {"fraud_probability": 0.945, "risk_level": "CRITICAL", "decision": "BLOCK_IMMEDIATE"}
    alert_engine.notify_fraud(test_tx, test_score)
