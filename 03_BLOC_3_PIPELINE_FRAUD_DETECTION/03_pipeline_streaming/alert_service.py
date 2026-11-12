import os
import json
import time
import importlib
import smtplib
from email.message import EmailMessage
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
features_mod = importlib.import_module("01_train.features")
db_mod = importlib.import_module("05_database.db_manager")

features_mod.load_project_env()
mask_credit_card = db_mod.mask_credit_card
pseudonymize_name = db_mod.pseudonymize_name

ALERTS_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fraud_alerts.log")


class AlertService:
    """Service d'alerting fraude temps réel : Console + JSONL + E-mail SMTP (Mailpit / Gmail)."""

    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "localhost").strip()
        self.smtp_port = int(os.getenv("SMTP_PORT", "1025"))
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "false").strip().lower() in ("1", "true", "yes")
        self.smtp_user = (os.getenv("SMTP_USER") or os.getenv("GMAIL_USER") or "").strip()
        raw_pass = (os.getenv("SMTP_PASSWORD") or os.getenv("GMAIL_PASSWORD") or "").strip()
        # Les mots de passe d'application Google comportent parfois des espaces (4x4 caractères)
        self.smtp_password = raw_pass.replace(" ", "") if "gmail" in self.smtp_host.lower() else raw_pass
        self.sender = os.getenv("ALERT_SENDER", "fraud-alerts@fintech-rncp41993.local").strip()
        self.recipient = os.getenv("ALERT_RECIPIENT", "risk-fraud-alerts@fintech-rncp41993.local").strip()
        if "gmail" in self.smtp_host.lower() and self.smtp_user:
            if not self.sender or self.sender.endswith(".local"):
                self.sender = self.smtp_user
            if not self.recipient or self.recipient.endswith(".local"):
                self.recipient = self.smtp_user

    def _send_smtp_email(self, subject: str, body: str) -> bool:
        if not self.smtp_host:
            return False
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.sender
        msg["To"] = self.recipient
        msg.set_content(body)
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=5) as server:
                if self.smtp_use_tls:
                    server.starttls()
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            return True
        except Exception as exc:
            print(f"⚠️ Envoi SMTP indisponible ({self.smtp_host}:{self.smtp_port} -> {exc}). Log local conservé.")
            return False

    def notify_fraud(self, tx: Dict[str, Any], score: Dict[str, Any]) -> str:
        """Déclenche une alerte stricte PCI-DSS / RGPD (PAN et identité masqués)."""
        cc_masked = mask_credit_card(tx.get("cc_num") or tx.get("cc_num_masked"))
        holder_masked, pseudo_hash = pseudonymize_name(tx.get("first"), tx.get("last"))

        amt = float(tx.get("amt", 0.0))
        prob = float(score.get("fraud_probability", 0.0))
        risk = str(score.get("risk_level", "HIGH"))
        decision = str(score.get("decision", "BLOCK"))
        merchant = str(tx.get("merchant", "Unknown"))
        category = str(tx.get("category", "general"))
        city = str(tx.get("city", ""))
        trans_num = str(tx.get("trans_num", "unknown"))
        model_source = str(score.get("model_source", "mlflow@champion"))
        now_iso = time.strftime("%Y-%m-%d %H:%M:%S")

        print(
            f"\n🚨 [ALERTE FRAUDE {risk}] {trans_num} | {amt:.2f} € | {merchant} "
            f"| Porteur={holder_masked} | Carte={cc_masked} | Prob={prob*100:.2f}% | {decision}\n"
        )

        subject = f"[ALERTE FRAUDE {risk}] {amt:.2f} EUR - {merchant} ({prob*100:.1f}%)"
        email_body = (
            f"Alerte Fraude Temps Réel — Pipeline RNCP 41993 (Bloc 3)\n"
            f"{'=' * 56}\n"
            f"Horodatage         : {now_iso}\n"
            f"Transaction ID     : {trans_num}\n"
            f"Statut / Décision  : {risk} -> {decision}\n"
            f"Probabilité Fraude : {prob*100:.2f} %\n"
            f"Montant            : {amt:.2f} EUR\n"
            f"Commerçant         : {merchant} ({category})\n"
            f"Localisation       : {city}\n"
            f"Porteur (RGPD)     : {holder_masked}\n"
            f"Hash SHA-256 salé  : {pseudo_hash[:16]}...\n"
            f"Carte (PCI-DSS)    : {cc_masked}\n"
            f"Source Modèle      : {model_source}\n"
        )
        smtp_sent = self._send_smtp_email(subject, email_body)
        channel = "SMTP_EMAIL_AND_LOG" if smtp_sent else "CONSOLE_AND_LOG"

        alert_record = {
            "timestamp": now_iso,
            "trans_num": trans_num,
            "amt": amt,
            "merchant": merchant,
            "category": category,
            "customer_masked": holder_masked,
            "customer_pseudo_hash": pseudo_hash,
            "cc_masked": cc_masked,
            "fraud_probability": prob,
            "risk_level": risk,
            "decision": decision,
            "alert_channel": channel,
        }
        with open(ALERTS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(alert_record, ensure_ascii=False) + "\n")

        return channel
