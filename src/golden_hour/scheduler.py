"""A process-safe polling adapter. Hosting runs this periodically after durable deployment."""
from __future__ import annotations

import os

from .email_provider import send_demo_email
from .store import Store


def deliver_due_reminders(store: Store) -> int:
    delivered = 0
    recipient = os.getenv("DEMO_RECIPIENT_EMAIL", "")
    for reminder in store.due_reminders():
        if not recipient or reminder.channel != "email":
            reminder.state, reminder.error = "failed", "No supported reminder channel is configured."
        else:
            try:
                # Do not place case details or financial information in notification previews.
                state, provider_ref = send_demo_email(recipient=recipient, subject="Golden Hour follow-up reminder", body="You have an approved Golden Hour follow-up task. Open the case through the secure conversation to review it.", idempotency_key=f"reminder:{reminder.reminder_id}")
                reminder.state = "delivered" if state == "provider_accepted" else "failed"
                reminder.scheduler_ref = provider_ref
                if reminder.state == "delivered":
                    delivered += 1
            except Exception as exc:
                reminder.state, reminder.error = "failed", str(exc)
        store.save_reminder(reminder)
    return delivered
