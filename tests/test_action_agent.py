from uuid import uuid4
from datetime import timedelta
from golden_hour.action_agent import execute
from golden_hour.protocols import ExecuteApprovedAction
from golden_hour.models import Approval, utcnow
from golden_hour.store import Store
from golden_hour.action_agent import execute_authorized

def request(recipient: str) -> ExecuteApprovedAction:
    return ExecuteApprovedAction(case_id=uuid4(), approval_id=uuid4(), case_version=1, payload_digest="digest", recipient=recipient, subject="test", body="test", idempotency_key="once")

def test_action_executor_is_disabled_by_default(monkeypatch):
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    monkeypatch.delenv("DEMO_SENDING_ENABLED", raising=False)
    assert execute(request("demo@example.test")).state == "not_sent"

def test_action_executor_rejects_untrusted_recipient(monkeypatch):
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    monkeypatch.setenv("DEMO_SENDING_ENABLED", "true")
    assert execute(request("attacker@example.test")).state == "rejected"

def test_action_executor_requires_exact_persisted_approval(monkeypatch, tmp_path):
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    store = Store(tmp_path / "case.sqlite3")
    approval = Approval(case_id=uuid4(), case_version=1, action_type="email", recipient="demo@example.test", subject="approved", body="body", payload_digest="digest", expires_at=utcnow() + timedelta(minutes=1), approved=True)
    store.save_approval(approval)
    msg = ExecuteApprovedAction(case_id=approval.case_id, approval_id=approval.approval_id, case_version=1, payload_digest="digest", recipient="demo@example.test", subject="tampered", body="body", idempotency_key="once")
    assert execute_authorized(msg, store).state == "rejected"
