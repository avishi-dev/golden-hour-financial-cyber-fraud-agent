from datetime import timedelta
from uuid import uuid4

from golden_hour.interactions import approval_id_from_text, review_text
from golden_hour.models import Approval, utcnow


def test_only_explicit_approval_token_is_accepted():
    approval = Approval(case_id=uuid4(), case_version=3, action_type="email", recipient="demo@example.test", subject="review", body="body", payload_digest="digest", expires_at=utcnow() + timedelta(minutes=15))
    assert approval_id_from_text("okay") is None
    assert approval_id_from_text(f"APPROVE {approval.approval_id}") == approval.approval_id
    text = review_text(approval)
    assert "Recipient: demo@example.test" in text
    assert "case version 3" in text
