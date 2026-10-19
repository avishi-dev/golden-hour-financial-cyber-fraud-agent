from datetime import timedelta

from golden_hour.scheduler import deliver_due_reminders
from golden_hour.store import Store
from golden_hour.workflow import Coordinator
from golden_hour.models import utcnow


def test_due_reminder_fails_honestly_without_an_email_adapter(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    coordinator = Coordinator(Store(tmp_path / "case.sqlite3"))
    case = coordinator.start_case("alice", "test")
    reminder = coordinator.create_reminder(case, "Follow up", utcnow() - timedelta(seconds=1), "Asia/Kolkata", "email")
    assert deliver_due_reminders(coordinator.store) == 0
    assert coordinator.store.get_reminder(reminder.reminder_id).state == "failed"
