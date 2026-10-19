"""Typed, correlation-checked uAgent worker calls for the deployed Coordinator."""
from __future__ import annotations

import os

from uagents import Context

from .models import Case
from .protocols import AnalyzeEvidence, BuildResponse, EvidenceResult, ResponseBundle


class WorkerUnavailable(RuntimeError):
    pass


async def evidence_request(ctx: Context, case: Case) -> EvidenceResult:
    destination = os.getenv("EVIDENCE_AGENT_ADDRESS")
    if not destination:
        raise WorkerUnavailable("EVIDENCE_AGENT_ADDRESS is not configured")
    request = AnalyzeEvidence(case_id=case.case_id, case_version=case.version, evidence_refs=[item.evidence_id for item in case.evidence], evidence_text=[item.extracted_text for item in case.evidence])
    result, status = await ctx.send_and_receive(destination, request, EvidenceResult, timeout=20)
    if not isinstance(result, EvidenceResult) or result.correlation_id != request.correlation_id:
        raise WorkerUnavailable(f"Evidence worker did not return a valid correlated result: {status}")
    return result


async def response_request(ctx: Context, case: Case) -> ResponseBundle:
    destination = os.getenv("RESPONSE_AGENT_ADDRESS")
    if not destination:
        raise WorkerUnavailable("RESPONSE_AGENT_ADDRESS is not configured")
    transaction = case.transactions[0] if case.transactions else None
    facts = {
        "amount_display": f"{transaction.currency} {transaction.amount_minor / 100:.2f}" if transaction else "[amount unavailable]",
        "transaction_reference": transaction.reference if transaction else None,
        "occurred_at": transaction.occurred_at.isoformat() if transaction and transaction.occurred_at else None,
        "bank": "[bank unavailable]", "ongoing_demands": case.ongoing_demands,
    }
    request = BuildResponse(case_id=case.case_id, case_version=case.version, validated_facts=facts, discrepancies=case.contradictions)
    result, status = await ctx.send_and_receive(destination, request, ResponseBundle, timeout=20)
    if not isinstance(result, ResponseBundle) or result.correlation_id != request.correlation_id or result.case_version != case.version:
        raise WorkerUnavailable(f"Response worker did not return a valid current result: {status}")
    return result
