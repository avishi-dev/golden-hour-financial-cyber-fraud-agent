from uuid import uuid4
from golden_hour.response_agent import build
from golden_hour.protocols import BuildResponse

def test_response_bundle_preserves_unknowns_and_discrepancies():
    bundle = build(BuildResponse(case_id=uuid4(), case_version=2, validated_facts={"amount_display": "₹12,000"}, discrepancies=["Receipt and statement amounts conflict."]))
    assert "₹12,000" in bundle.bank_email_body
    assert "Receipt and statement amounts conflict." in bundle.missing_facts
    assert "[transaction reference unavailable]" in bundle.call_brief
