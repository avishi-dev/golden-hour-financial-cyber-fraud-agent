"""Bounded evidence ingestion; active or oversized files are never processed."""
from __future__ import annotations

import hashlib
import json
from uuid import uuid4

from .models import EvidenceItem

MAX_EVIDENCE_BYTES = 5 * 1024 * 1024
TEXT_TYPES = {"text/plain", "application/json", "message/rfc822"}


def ingest_bytes(filename: str, mime_type: str, content: bytes) -> EvidenceItem:
    if len(content) > MAX_EVIDENCE_BYTES:
        raise ValueError("Evidence exceeds the 5 MiB demo limit")
    if mime_type not in TEXT_TYPES:
        raise ValueError("This demo accepts bounded text, JSON, and email text only; image/PDF extraction requires the reviewed production adapter")
    text = content.decode("utf-8", errors="replace")
    if mime_type == "application/json":
        try:
            text = json.dumps(json.loads(text), ensure_ascii=False, indent=2)
        except json.JSONDecodeError as exc:
            raise ValueError("JSON evidence is malformed") from exc
    return EvidenceItem(evidence_id=f"ev-{uuid4().hex[:12]}", filename=filename, sha256=hashlib.sha256(content).hexdigest(), mime_type=mime_type, extracted_text=text, size_bytes=len(content))
