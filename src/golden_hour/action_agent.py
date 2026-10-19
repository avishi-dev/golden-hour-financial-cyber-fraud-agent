"""Action Executor: policy boundary for approved outbound actions."""
from __future__ import annotations

import os
from uuid import uuid4
from uagents import Agent, Context, Protocol
from .protocols import ActionExecutionResult, ExecuteApprovedAction, WorkerHealth

SEED = os.getenv("ACTION_AGENT_SEED_PHRASE")
if not SEED and __name__ == "__main__":
    raise RuntimeError("ACTION_AGENT_SEED_PHRASE must be set before starting the Action Executor")

agent = Agent(name=os.getenv("ACTION_AGENT_NAME", "golden-hour-action"), seed=SEED, port=int(os.getenv("ACTION_AGENT_PORT", "8003")), mailbox=os.getenv("AGENT_MAILBOX", "false").lower() == "true", publish_agent_details=True, description="Executes only explicitly approved, trusted-recipient Golden Hour demo actions.")
protocol = Protocol(name="GoldenHourAction", version="1.0")

def execute(msg: ExecuteApprovedAction) -> ActionExecutionResult:
    trusted_recipient = os.getenv("DEMO_RECIPIENT_EMAIL", "")
    if not trusted_recipient or msg.recipient != trusted_recipient:
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="rejected", detail="Recipient is not the configured trusted demo recipient.")
    if os.getenv("DEMO_SENDING_ENABLED", "false").lower() != "true":
        return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="not_sent", detail="Sending is disabled until a test provider is configured and explicitly enabled.")
    return ActionExecutionResult(correlation_id=msg.correlation_id or uuid4(), approval_id=msg.approval_id, state="provider_pending", detail="Provider adapter is not configured yet; no email was sent.")

@protocol.on_message(ExecuteApprovedAction, replies=ActionExecutionResult)
async def handle_execute(ctx: Context, sender: str, msg: ExecuteApprovedAction):
    await ctx.send(sender, execute(msg))

@protocol.on_message(WorkerHealth, replies=WorkerHealth)
async def handle_health(ctx: Context, sender: str, msg: WorkerHealth):
    await ctx.send(sender, WorkerHealth(worker=agent.name))

agent.include(protocol)

if __name__ == "__main__":
    agent.run()
