"""Safe text fallback for cards: an explicit token is required for consent."""
from __future__ import annotations

import re
from uuid import UUID

from .models import Approval

_APPROVAL = re.compile(r"^APPROVE\s+([0-9a-fA-F-]{36})$")


def review_text(approval: Approval) -> str:
    attachments = ", ".join(approval.attachment_hashes) if approval.attachment_hashes else "none"
    return (
        f"Review required — case version {approval.case_version}\n"
        f"Recipient: {approval.recipient}\nSubject: {approval.subject}\n"
        f"Attachments (SHA-256): {attachments}\n\n{approval.body}\n\n"
        f"To approve only this exact payload before {approval.expires_at.isoformat()}, reply exactly: APPROVE {approval.approval_id}"
    )


def approval_id_from_text(text: str) -> UUID | None:
    match = _APPROVAL.fullmatch(text.strip())
    return UUID(match.group(1)) if match else None
