"""Small reviewed-rule reader. It intentionally contains no inferred deadlines."""
from __future__ import annotations

import json
from pathlib import Path

from .models import ActionTask, Case, RuleEntry


class Rulebook:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path(__file__).parents[2] / "rulebook.json"
        self.entries = [RuleEntry.model_validate(item) for item in json.loads(self.path.read_text(encoding="utf-8"))]

    def tasks_for(self, case: Case) -> list[ActionTask]:
        """Only surface reviewed universal guidance; missing facts never create a deadline."""
        tasks = [ActionTask(route="financial-fraud", title=entry.action_text, rule_id=entry.rule_id) for entry in self.entries if entry.status == "source_verified"]
        if any((transaction.method or "").lower() == "upi" for transaction in case.transactions):
            tasks.append(ActionTask(route="upi", title="Ask the relevant UPI app or payment service provider for its verified complaint route; no separate filing is assumed.", prerequisite="Confirm the affected app/provider."))
        return tasks
