from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
from pydantic import BaseModel, ConfigDict, Field

def utcnow() -> datetime:
    return datetime.now(timezone.utc)

class CaseState(str, Enum):
    INTAKE = "intake"
    NEEDS_CLARIFICATION = "needs_clarification"
    BUILDING = "building"
    NEEDS_REVIEW = "needs_review"
    READY = "ready"
    ACTION_PENDING = "action_pending"
    FOLLOW_UP = "follow_up"

class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    transaction_id: UUID = Field(default_factory=uuid4)
    amount_minor: int = Field(ge=0)
    currency: str = "INR"
    method: str | None = None
    reference: str | None = None
    occurred_at: datetime | None = None
    recipient: str | None = None
    authorization_status: str = "unclear"
    source_refs: list[str] = Field(default_factory=list)
    confirmation_state: str = "extracted_unconfirmed"

class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str
    filename: str
    sha256: str
    mime_type: str
    extracted_text: str = ""
    untrusted: bool = True

class Case(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: UUID = Field(default_factory=uuid4)
    owner_id: str
    language: str = "en"
    state: CaseState = CaseState.INTAKE
    version: int = 1
    narrative: str = ""
    suspected_pattern: str | None = None
    ongoing_demands: bool | None = None
    device_compromise_statement: str | None = None
    transactions: list[Transaction] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    injection_flags: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)

class Approval(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approval_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    case_version: int
    action_type: str
    recipient: str
    subject: str
    body: str
    attachment_hashes: list[str] = Field(default_factory=list)
    payload_digest: str
    expires_at: datetime
    approved: bool = False

class DispatchJob(BaseModel):
    model_config = ConfigDict(extra="forbid")
    job_id: UUID = Field(default_factory=uuid4)
    idempotency_key: str
    approval_id: UUID
    state: str = "draft"
    provider_ref: str | None = None
    error: str | None = None

class AnalyzeEvidenceRequest(BaseModel):
    schema_version: str = "1.0"
    message_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    case_id: UUID
    case_version: int
    evidence: list[EvidenceItem]

class EvidenceAnalysisResult(BaseModel):
    schema_version: str = "1.0"
    correlation_id: UUID
    extracted_facts: dict[str, Any] = Field(default_factory=dict)
    discrepancies: list[str] = Field(default_factory=list)
    injection_flags: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
