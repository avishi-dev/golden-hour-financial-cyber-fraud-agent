from __future__ import annotations
from typing import Any
from uuid import UUID, uuid4
from uagents import Model

class AnalyzeEvidence(Model):
    schema_version: str = "1.0"
    message_id: UUID | None = None
    correlation_id: UUID | None = None
    case_id: UUID
    case_version: int
    evidence_refs: list[str] = []
    evidence_text: list[str] = []

class EvidenceResult(Model):
    schema_version: str = "1.0"
    correlation_id: UUID
    extracted_facts: dict[str, Any] = {}
    discrepancies: list[str] = []
    injection_flags: list[str] = []
    supporting_evidence_ids: list[str] = []

class BuildResponse(Model):
    schema_version: str = "1.0"
    correlation_id: UUID | None = None
    case_id: UUID
    case_version: int
    validated_facts: dict[str, Any] = {}
    discrepancies: list[str] = []

class ResponseBundle(Model):
    schema_version: str = "1.0"
    correlation_id: UUID
    case_id: UUID
    case_version: int
    bank_email_subject: str
    bank_email_body: str
    call_brief: str
    ncrp_narrative: str
    missing_facts: list[str] = []

class ExecuteApprovedAction(Model):
    schema_version: str = "1.0"
    correlation_id: UUID | None = None
    case_id: UUID
    case_version: int
    approval_id: UUID
    payload_digest: str
    recipient: str
    subject: str
    body: str
    idempotency_key: str

class ActionExecutionResult(Model):
    schema_version: str = "1.0"
    correlation_id: UUID
    approval_id: UUID
    state: str
    provider_ref: str | None = None
    detail: str = ""

class WorkerHealth(Model):
    schema_version: str = "1.0"
    worker: str
    available: bool = True
    supported_schema_version: str = "1.0"
