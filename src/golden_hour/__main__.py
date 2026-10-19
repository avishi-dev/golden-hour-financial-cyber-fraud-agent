from __future__ import annotations
import asyncio
import os
from .store import Store
from .workflow import Coordinator, URGENT

async def run() -> None:
    print("Golden Hour Coordinator (local smoke mode)")
    print(URGENT)
    if not os.getenv("ASI_ONE_API_KEY"):
        print("ASI_ONE_API_KEY is not configured; local smoke mode stops before model execution.")
        return
    coordinator = Coordinator(Store(os.getenv("DATABASE_PATH", "golden_hour.sqlite3")))
    case = coordinator.start_case("local-demo", "I suspect a financial fraud and need help organizing the report.")
    case = await coordinator.intake(case, case.narrative)
    print(f"case_id={case.case_id} state={case.state} version={case.version}")

def main() -> None:
    asyncio.run(run())

if __name__ == "__main__":
    main()
