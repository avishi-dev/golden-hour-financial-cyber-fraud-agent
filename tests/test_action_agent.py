from uuid import uuid4
from golden_hour.action_agent import execute
from golden_hour.protocols import ExecuteApprovedAction

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
