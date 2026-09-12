"""Email delivery layer.

This project supports real SMTP when credentials are provided in the environment.
If they are missing, it falls back to a local log file so the demo still works
end to end without requiring external infrastructure.
"""
import datetime
import json
import os

LOG_PATH = os.path.join(os.path.dirname(__file__), "emails_sent.log")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM = os.getenv("SMTP_FROM") or SMTP_USERNAME


def _log_email(record: dict) -> dict:
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def send_email(to: str, subject: str, body: str) -> dict:
    record = {
        "to": to,
        "subject": subject,
        "body": body,
        "sent_at": datetime.datetime.utcnow().isoformat(),
    }

    if SMTP_HOST and SMTP_USERNAME and SMTP_PASSWORD:
        try:
            import smtplib
            from email.message import EmailMessage

            msg = EmailMessage()
            msg["Subject"] = subject
            msg["From"] = SMTP_FROM or "noreply@campus.local"
            msg["To"] = to
            msg.set_content(body)

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)

            record["delivery"] = "smtp"
            record["status"] = "sent"
            return record
        except Exception as exc:
            record["delivery"] = "smtp-fallback"
            record["status"] = "logged"
            record["error"] = str(exc)
            return _log_email(record)

    record["delivery"] = "local-log"
    record["status"] = "logged"
    return _log_email(record)
