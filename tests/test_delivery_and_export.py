from datetime import timedelta
from pathlib import Path

import pytest

from golden_hour.models import CaseState, Transaction, utcnow
from golden_hour.store import Store
from golden_hour.workflow import Coordinator
from golden_hour.email_provider import record_send_result
from golden_hour.models import DispatchJob


def test_export_writes_versioned_pdf_and_external_manifest(tmp_path: Path):
    coordinator = Coordinator(Store(tmp_path / "case.sqlite3"))
    case = coordinator.start_case("alice", "A suspicious transfer was reported.")
    case.transactions.append(Transaction(amount_minor=1200000, reference="REF-12"))
    case.state = CaseState.NEEDS_REVIEW
    coordinator.store.save_case(case)
    pdf, manifest = coordinator.export_pdf(case, tmp_path / "exports")
    assert pdf.read_bytes().startswith(b"%PDF-")
    assert '"case_version": 1' in manifest.read_text()
    assert pdf.with_suffix(".manifest.json") == manifest


def test_approved_email_is_sent_once_and_provider_failure_is_honest(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    monkeypatch.setenv("DEMO_SENDING_ENABLED", "true")
    monkeypatch.setenv("EMAIL_PROVIDER_FORCE_FAILURE", "true")
    coordinator = Coordinator(Store(tmp_path / "case.sqlite3"))
    case = coordinator.start_case("alice", "test")
    approval = coordinator.create_approval(case, "demo@example.test", "subject", "body")
    approval = coordinator.approve_email(approval.approval_id, "alice", case)
    job = coordinator.execute_approved_email(approval, case)
    assert job.state == "failed"
    with pytest.raises(ValueError, match="Duplicate"):
        coordinator.execute_approved_email(approval, case)


def test_reminder_needs_configured_channel_and_can_be_cancelled(monkeypatch, tmp_path: Path):
    coordinator = Coordinator(Store(tmp_path / "case.sqlite3"))
    case = coordinator.start_case("alice", "test")
    with pytest.raises(ValueError, match="No supported"):
        coordinator.create_reminder(case, "Follow up", utcnow() + timedelta(hours=1), "Asia/Kolkata", "email")
    monkeypatch.setenv("DEMO_RECIPIENT_EMAIL", "demo@example.test")
    reminder = coordinator.create_reminder(case, "Follow up", utcnow() + timedelta(hours=1), "Asia/Kolkata", "email")
    assert reminder.scheduler_ref
    assert coordinator.cancel_reminder(reminder.reminder_id, case).state == "cancelled"


def test_ambiguous_provider_timeout_is_not_labelled_a_failure():
    job = DispatchJob(idempotency_key="once", approval_id=__import__("uuid").uuid4())
    assert record_send_result(job, error=TimeoutError("timed out")).state == "status_unknown"
