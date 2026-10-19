from __future__ import annotations
import json
import os
from typing import Any
import httpx
from dotenv import load_dotenv

load_dotenv()

TOOLS = [{"type":"function","function":{"name":"record_intake_facts","description":"Extract only facts stated by the user. Never infer authorization, authenticity, liability, deadlines, or recipient addresses.","strict":True,"parameters":{"type":"object","properties":{"amount_minor":{"type":["integer","null"]},"currency":{"type":["string","null"]},"payment_method":{"type":["string","null"]},"transaction_reference":{"type":["string","null"]},"ongoing_demands":{"type":["boolean","null"]},"suspected_pattern":{"type":["string","null"]}},"required":["amount_minor","currency","payment_method","transaction_reference","ongoing_demands","suspected_pattern"],"additionalProperties":False}}}]

class ASI1Client:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("ASI_ONE_API_KEY")
        self.model = model or os.getenv("ASI_ONE_MODEL", "asi1")
    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        if not self.api_key:
            raise RuntimeError("ASI_ONE_API_KEY is not configured")
        payload: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": 0, "max_tokens": 900, "parallel_tool_calls": False}
        if tools: payload["tools"] = tools
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post("https://api.asi1.ai/v1/chat/completions", headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, json=payload)
            response.raise_for_status()
            return response.json()
    @staticmethod
    def extract_tool_arguments(response: dict[str, Any]) -> dict[str, Any] | None:
        calls = response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
        return json.loads(calls[0]["function"]["arguments"]) if calls else None
