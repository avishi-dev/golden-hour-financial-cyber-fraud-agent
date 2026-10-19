"""Dependency-free, deliberately plain PDF and JSON manifest export for the demo."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .models import Case


def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _lines(case: Case) -> list[str]:
    rows = [
        "Golden Hour — UNOFFICIAL DEMO DOCUMENT",
        f"Case ID: {case.case_id}", f"Case version: {case.version}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}", "",
        "Incident summary (user-provided):", case.narrative or "[unavailable]", "",
        "Transactions:",
    ]
    if not case.transactions:
        rows.append("No confirmed transaction has been recorded.")
    for transaction in case.transactions:
        rows.append(f"{transaction.currency} {transaction.amount_minor / 100:.2f} | {transaction.method or 'method unavailable'} | ref: {transaction.reference or 'unavailable'} | {transaction.confirmation_state}")
    rows.extend(["", "Evidence index:"])
    rows.extend(f"{item.evidence_id}: {item.filename}; SHA-256 {item.sha256}" for item in case.evidence)
    if not case.evidence:
        rows.append("No evidence supplied.")
    rows.extend(["", "Unresolved items:"] + (case.contradictions or ["None recorded."]))
    return rows


def export_case(case: Case, directory: str | Path) -> tuple[Path, Path]:
    """Create a readable one-page PDF and a separately hashed manifest."""
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)
    pdf_path = target / f"golden-hour-{case.case_id}-v{case.version}.pdf"
    content_lines = _lines(case)
    stream = ["BT", "/F1 10 Tf", "48 780 Td"]
    for index, line in enumerate(content_lines[:58]):
        if index:
            stream.append("0 -13 Td")
        stream.append(f"({_pdf_escape(line[:110])}) Tj")
    stream.append("ET")
    body = "\n".join(stream).encode("latin-1", "replace")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(body)).encode() + b" >>\nstream\n" + body + b"\nendstream",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output)); output.extend(f"{index} 0 obj\n".encode()); output.extend(obj); output.extend(b"\nendobj\n")
    xref = len(output); output.extend(f"xref\n0 {len(objects)+1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    pdf_path.write_bytes(output)
    manifest = {"case_id": str(case.case_id), "case_version": case.version, "pdf_sha256": hashlib.sha256(output).hexdigest(), "evidence": [{"id": item.evidence_id, "sha256": item.sha256} for item in case.evidence], "integrity_note": "Hashes identify recorded bytes; they do not establish authenticity or legal admissibility."}
    manifest_path = pdf_path.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return pdf_path, manifest_path
