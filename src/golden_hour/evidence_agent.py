"""Least-privilege Evidence Agent: no ASI key, email, scheduler, or case-store access."""
from __future__ import annotations
import hashlib
import os
import re
import asyncio
from uagents import Agent, Context, Protocol
from .protocols import AnalyzeEvidence, EvidenceResult, WorkerHealth

SEED = os.getenv("EVIDENCE_AGENT_SEED_PHRASE")
if not SEED:
    if __name__ == "__main__":
        raise RuntimeError("EVIDENCE_AGENT_SEED_PHRASE must be set before starting the Evidence Agent")

def _agent_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.new_event_loop()

agent = Agent(name=os.getenv("EVIDENCE_AGENT_NAME", "golden-hour-evidence"), seed=SEED, port=int(os.getenv("EVIDENCE_AGENT_PORT", "8001")), mailbox=os.getenv("AGENT_MAILBOX", "false").lower() == "true", publish_agent_details=True, description="Untrusted financial-fraud evidence extraction and discrepancy detection.", loop=_agent_loop())
protocol = Protocol(name="GoldenHourEvidence", version="1.0")

def analyze(msg: AnalyzeEvidence) -> EvidenceResult:
    facts: dict[str, object] = {}
    discrepancies: list[str] = []
    injection_flags: list[str] = []
    refs: list[str] = []
    amounts: list[int] = []
    for ref, raw in zip(msg.evidence_refs, msg.evidence_text):
        refs.append(ref)
        lower = raw.lower()
        if any(token in lower for token in ("ignore previous", "send to", "system prompt", "developer message")):
            injection_flags.append(f"{ref}: instruction-like text retained as untrusted evidence")
        for match in re.findall(r"(?:₹|rs\.?\s*)\s*([0-9][0-9,]*)", raw, flags=re.I):
            amounts.append(int(match.replace(",", "")) * 100)
    if len(set(amounts)) > 1:
        discrepancies.append("Evidence contains conflicting monetary amounts; user clarification required.")
    if amounts:
        facts["amounts_minor"] = amounts
    return EvidenceResult(correlation_id=msg.correlation_id or __import__("uuid").uuid4(), extracted_facts=facts, discrepancies=discrepancies, injection_flags=injection_flags, supporting_evidence_ids=refs)

@protocol.on_message(AnalyzeEvidence, replies=EvidenceResult)
async def handle_analysis(ctx: Context, sender: str, msg: AnalyzeEvidence):
    await ctx.send(sender, analyze(msg))

@protocol.on_message(WorkerHealth, replies=WorkerHealth)
async def handle_health(ctx: Context, sender: str, msg: WorkerHealth):
    await ctx.send(sender, WorkerHealth(worker=agent.name))

agent.include(protocol)

if __name__ == "__main__":
    agent.run()
