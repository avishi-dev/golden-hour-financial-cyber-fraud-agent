"""Small, auditable SMTP adapter for the explicitly configured demo inbox."""
from __future__ import annotations

import os
import smtplib
from email.message import EmailMessage
from uuid import uuid4

from .models import DispatchJob


def send_demo_email(*, recipient: str, subject: str, body: str, idempotency_key: str) -> tuple[str, str]:
    """Return (state, provider reference); never claim delivery from SMTP acceptance."""
    configured = os.getenv("DEMO_RECIPIENT_EMAIL", "")
    if not configured or recipient != configured:
        raise ValueError("Recipient is not the configured trusted demo recipient")
    if os.getenv("DEMO_SENDING_ENABLED", "false").lower() != "true":
        return "not_sent", "sending disabled"
    if os.getenv("EMAIL_PROVIDER_FORCE_FAILURE", "false").lower() == "true":
        raise OSError("forced provider failure")
    host = os.getenv("SMTP_HOST")
    sender = os.getenv("SMTP_FROM")
    if not host or not sender:
        return "not_sent", "SMTP_HOST and SMTP_FROM must be configured"
    message = EmailMessage()
    message["From"] = sender
    message["To"] = configured
    message["Subject"] = subject
    message["Message-ID"] = f"<{uuid4()}@golden-hour.demo>"
    message["X-Golden-Hour-Idempotency-Key"] = idempotency_key
    message.set_content(body)
    port = int(os.getenv("SMTP_PORT", "587"))
    username, password = os.getenv("SMTP_USERNAME"), os.getenv("SMTP_PASSWORD")
    with smtplib.SMTP(host, port, timeout=20) as client:
        client.starttls()
        if username:
            client.login(username, password or "")
        client.send_message(message)
    return "provider_accepted", message["Message-ID"]


def record_send_result(job: DispatchJob, result: tuple[str, str] | None = None, error: Exception | None = None) -> DispatchJob:
    if error is not None:
        job.state, job.error = "failed", str(error)
    elif result is not None:
        job.state, job.provider_ref = result
    return job
