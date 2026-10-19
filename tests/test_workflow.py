from datetime import timedelta
from pathlib import Path
import pytest
from golden_hour.models import Approval, Case, utcnow
from golden_hour.store import Store
from golden_hour.workflow import Coordinator

def test_owner_scoping_and_persistence(tmp_path: Path):
    store = Store(tmp_path / "case.sqlite3")
    case = Case(owner_id="alice", narrative="test")
    store.save_case(case)
    assert store.get_case(case.case_id, "alice").case_id == case.case_id
    assert store.get_case(case.case_id, "bob") is None

def test_approval_requires_trusted_recipient(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    coordinator = Coordinator(Store(tmp_path / "case.sqlite3"))
    case = coordinator.start_case("alice", "test")
    with pytest.raises(ValueError):
        coordinator.create_approval(case, "attacker@example.test", "x", "y")

def test_stale_or_unapproved_action_blocked(tmp_path: Path):
    coordinator = Coordinator(Store(tmp_path / "case.sqlite3"))
    case = coordinator.start_case("alice", "test")
    approval = Approval(case_id=case.case_id, case_version=case.version, action_type="email", recipient="demo@example.test", subject="x", body="y", payload_digest="d", expires_at=utcnow() + timedelta(minutes=1))
    with pytest.raises(ValueError):
        coordinator.queue_approved_email(approval, case)
