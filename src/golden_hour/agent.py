"""Agentverse/ASI:One-facing Coordinator using the official Agent Chat Protocol."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from uagents import Agent, Context, Protocol
from uagents_core.contrib.protocols.chat import ChatAcknowledgement, ChatMessage, TextContent, chat_protocol_spec
from dotenv import load_dotenv

from .store import Store
from .workflow import Coordinator, URGENT
from .localization import detect_language, urgent_guidance

load_dotenv()

NAME = os.getenv("AGENT_NAME", "golden-hour-coordinator")
SEED = os.getenv("AGENT_SEED_PHRASE")
if not SEED:
    raise RuntimeError("AGENT_SEED_PHRASE must be set before starting the Agentverse-facing agent")

agent = Agent(
    name=NAME,
    seed=SEED,
    port=int(os.getenv("AGENT_PORT", "8000")),
    endpoint=os.getenv("AGENT_ENDPOINT"),
    mailbox=os.getenv("AGENT_MAILBOX", "false").lower() == "true",
    publish_agent_details=True,
    readme_path=str(Path(__file__).parents[2] / "README.md"),
    description="Financial fraud first-response coordination: evidence review, reporting drafts, and approved test actions.",
    handle_messages_concurrently=True,
)
chat = Protocol(spec=chat_protocol_spec)
coordinator = Coordinator(Store(os.getenv("DATABASE_PATH", "golden_hour.sqlite3")))


def text_message(text: str) -> ChatMessage:
    return ChatMessage(timestamp=datetime.now(timezone.utc), msg_id=uuid4(), content=[TextContent(type="text", text=text)])


@chat.on_message(ChatAcknowledgement)
async def handle_ack(ctx: Context, sender: str, msg: ChatAcknowledgement) -> None:
    ctx.logger.debug("acknowledgement received from %s for %s", sender, msg.acknowledged_msg_id)


@chat.on_message(ChatMessage)
async def handle_chat(ctx: Context, sender: str, msg: ChatMessage) -> None:
    await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.now(timezone.utc), acknowledged_msg_id=msg.msg_id))
    if not coordinator.store.mark_message_processed(msg.msg_id):
        ctx.logger.info("duplicate chat message ignored: %s", msg.msg_id)
        return
    user_text = msg.text().strip()
    if not user_text:
        await ctx.send(sender, text_message("Please describe what happened in your own words. You can say unknown or unavailable for missing details."))
        return
    language = detect_language(user_text)
    # ACP senders may send several turns; resume only their own latest case.
    case = coordinator.store.latest_case(sender)
    if case is None:
        case = coordinator.start_case(sender, user_text)
        case.language = language
        coordinator.store.save_case(case)
    opened = {
        "hi": f"\n\nकेस खुल गया है: {case.case_id}। मैं केवल आपके बताए तथ्यों को व्यवस्थित करूँगा।",
        "hinglish": f"\n\nCase open ho gaya hai: {case.case_id}. Main sirf aapke bataye facts organize karunga.",
        "en": f"\n\nCase opened: {case.case_id}. I will now organize only the facts you provide.",
    }[language]
    await ctx.send(sender, text_message(urgent_guidance(language) + opened))
    try:
        updated = await coordinator.intake(case, user_text)
        status = {
            "hi": f"केस {updated.case_id} अभी {updated.state.value} स्थिति में है। वर्ज़न {updated.version}। किसी भी कार्रवाई से पहले निकाली गई जानकारी की समीक्षा करें।",
            "hinglish": f"Case {updated.case_id} abhi {updated.state.value} state mein hai. Version {updated.version}. Kisi bhi action se pehle extracted details review karein.",
            "en": f"Case {updated.case_id} is at {updated.state.value}. Version {updated.version}. Review the extracted details before any action is prepared.",
        }[language]
        await ctx.send(sender, text_message(status))
    except Exception as exc:
        ctx.logger.exception("intake failed", exc_info=exc)
        await ctx.send(sender, text_message("I preserved the case but could not complete extraction. Nothing was sent. Please continue with the urgent reporting steps above."))


agent.include(chat)

if __name__ == "__main__":
    agent.run()
