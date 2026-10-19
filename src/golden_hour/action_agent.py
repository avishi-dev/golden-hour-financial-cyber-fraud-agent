"""Action Executor: policy boundary for approved outbound actions."""
from __future__ import annotations

import os
import asyncio
from uuid import uuid4
from uagents import Agent, Context, Protocol
from .protocols import ActionExecutionResult, ExecuteApprovedAction, WorkerHealth
from .store import Store
from .models import DispatchJob, utcnow
from .email_provider import record_send_result, send_demo_email

SEED = os.getenv("ACTION_AGENT_SEED_PHRASE")
if not SEED and __name__ == "__main__":
    raise RuntimeError("ACTION_AGENT_SEED_PHRASE must be set before starting the Action Executor")

def _agent_loop():
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.new_event_loop()

agent = Agent(name=os.getenv("ACTION_AGENT_NAME", "golden-hour-action"), seed=SEED, port=int(os.getenv("ACTION_AGENT_PORT", "8003")), mailbox=os.getenv("AGENT_MAILBOX", "false").lower() == "true", publish_agent_details=True, description="Executes only explicitly approved, trusted-recipient Golden Hour demo actions.", loop=_agent_loop())
protocol = Protocol(name="GoldenHourAction", version="1.0")

def execute(msg: ExecuteApprovedAction) -> ActionExecutionResult:
    trusted_recipient = os.getenv("DEMO_RECIPIENT_EMAIL", "")
    if not trusted_recipient or msg.recipient != trusted_recipient:
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="rejected", detail="Recipient is not the configured trusted demo recipient.")
    if os.getenv("DEMO_SENDING_ENABLED", "false").lower() != "true":
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="not_sent", detail="Sending is disabled until a test provider is configured and explicitly enabled.")
    return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="provider_pending", detail="Provider adapter is not configured yet; no email was sent.")

def execute_authorized(msg: ExecuteApprovedAction, store: Store) -> ActionExecutionResult:
    """The executor trusts its own approval database, never a caller-supplied recipient."""
    approval = store.get_approval(msg.approval_id)
    if not approval or not approval.approved or approval.expires_at <= utcnow():
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="rejected", detail="Approval is missing, unapproved, or expired.")
    if (approval.case_id != msg.case_id or approval.case_version != msg.case_version or approval.payload_digest != msg.payload_digest or approval.recipient != msg.recipient or approval.subject != msg.subject or approval.body != msg.body):
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="rejected", detail="Execution payload does not exactly match the approval.")
    job = DispatchJob(idempotency_key=msg.idempotency_key, approval_id=approval.approval_id, state="queued")
    if not store.save_job(job):
        existing = store.get_job_by_key(msg.idempotency_key)
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state=existing.state if existing else "status_unknown", provider_ref=existing.provider_ref if existing else None, detail="Duplicate execution request was not sent again.")
    try:
        record_send_result(job, result=send_demo_email(recipient=approval.recipient, subject=approval.subject, body=approval.body, idempotency_key=job.idempotency_key))
    except Exception as exc:
        record_send_result(job, error=exc)
    store.update_job(job)
    return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state=job.state, provider_ref=job.provider_ref, detail=job.error or "Provider result recorded.")

@protocol.on_message(ExecuteApprovedAction, replies=ActionExecutionResult)
async def handle_execute(ctx: Context, sender: str, msg: ExecuteApprovedAction):
    await ctx.send(sender, execute_authorized(msg, Store(os.getenv("DATABASE_PATH", "golden_hour.sqlite3"))))

@protocol.on_message(WorkerHealth, replies=WorkerHealth)
async def handle_health(ctx: Context, sender: str, msg: WorkerHealth):
    await ctx.send(sender, WorkerHealth(worker=agent.name))

agent.include(protocol)

if __name__ == "__main__":
    agent.run()
