"""Response Agent: drafts from validated facts; it has no dispatch credentials."""
from __future__ import annotations

import os
from uuid import uuid4
from uagents import Agent, Context, Protocol
from .protocols import BuildResponse, ResponseBundle, WorkerHealth

SEED = os.getenv("RESPONSE_AGENT_SEED_PHRASE")
if not SEED and __name__ == "__main__":
    raise RuntimeError("RESPONSE_AGENT_SEED_PHRASE must be set before starting the Response Agent")

agent = Agent(name=os.getenv("RESPONSE_AGENT_NAME", "golden-hour-response"), seed=SEED, port=int(os.getenv("RESPONSE_AGENT_PORT", "8002")), mailbox=os.getenv("AGENT_MAILBOX", "false").lower() == "true", publish_agent_details=True, description="Builds source-linked financial-fraud reporting drafts from validated facts.")
protocol = Protocol(name="GoldenHourResponse", version="1.0")

def build(msg: BuildResponse) -> ResponseBundle:
    facts = msg.validated_facts
    amount = facts.get("amount_display", "[amount unavailable]")
    reference = facts.get("transaction_reference", "[transaction reference unavailable]")
    occurred = facts.get("occurred_at", "[date/time unavailable]")
    bank = facts.get("bank", "[bank unavailable]")
    missing = list(msg.discrepancies)
    for label, value in (("amount", amount), ("transaction reference", reference), ("date/time", occurred), ("bank", bank)):
        if isinstance(value, str) and value.startswith("["):
            missing.append(f"Confirm {label} before sending.")
    return ResponseBundle(
        correlation_id=msg.correlation_id or uuid4(), case_id=msg.case_id, case_version=msg.case_version,
        bank_email_subject="Reported suspected financial fraud — request for review",
        bank_email_body=(f"Dear Bank Fraud Team,\n\nI am reporting suspected financial fraud.\nAmount: {amount}\nTransaction reference: {reference}\nDate/time: {occurred}\nBank: {bank}\n\nThese details are user-provided and remain subject to review. Please confirm the appropriate next step through your official process.\n\nRegards"),
        call_brief=f"Suspected financial fraud. Amount: {amount}. Reference: {reference}. Date/time: {occurred}. Ongoing demands: {facts.get('ongoing_demands', 'unknown')}.",
        ncrp_narrative=f"I suspect financial fraud involving {amount} on/about {occurred}. Transaction reference: {reference}. Bank/payment method: {bank}. The information is based on my current records and may require correction.",
        missing_facts=missing,
    )

@protocol.on_message(BuildResponse, replies=ResponseBundle)
async def handle_build(ctx: Context, sender: str, msg: BuildResponse):
    await ctx.send(sender, build(msg))

@protocol.on_message(WorkerHealth, replies=WorkerHealth)
async def handle_health(ctx: Context, sender: str, msg: WorkerHealth):
    await ctx.send(sender, WorkerHealth(worker=agent.name))

agent.include(protocol)

if __name__ == "__main__":
    agent.run()
