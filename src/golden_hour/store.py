from __future__ import annotations
import sqlite3
from pathlib import Path
from uuid import UUID
from .models import Approval, Case, DispatchJob

class Store:
    """Durable MVP store. JSON records are owner-scoped; no arbitrary SQL is exposed."""
    def __init__(self, path: str | Path = "golden_hour.sqlite3") -> None:
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, owner TEXT NOT NULL, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, case_id TEXT NOT NULL, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL, record TEXT NOT NULL)")
    def save_case(self, case: Case) -> None:
        self._put("cases", str(case.case_id), case.owner_id, case.model_dump_json())
    def get_case(self, case_id: UUID, owner_id: str) -> Case | None:
        row = self._get("cases", str(case_id))
        if not row or row[0] != owner_id:
            return None
        return Case.model_validate_json(row[1])
    def save_approval(self, approval: Approval) -> None:
        self._put("approvals", str(approval.approval_id), str(approval.case_id), approval.model_dump_json())
    def save_job(self, job: DispatchJob) -> bool:
        with sqlite3.connect(self.path) as db:
            try:
                db.execute("INSERT INTO jobs(id,idempotency_key,record) VALUES (?,?,?)", (str(job.job_id), job.idempotency_key, job.model_dump_json()))
                return True
            except sqlite3.IntegrityError:
                return False
    def _put(self, table: str, key: str, owner: str, record: str) -> None:
        column = "owner" if table == "cases" else "case_id"
        with sqlite3.connect(self.path) as db:
            db.execute(f"INSERT OR REPLACE INTO {table}(id,{column},record) VALUES (?,?,?)", (key, owner, record))
    def _get(self, table: str, key: str) -> tuple[str, str] | None:
        column = "owner" if table == "cases" else "case_id"
        with sqlite3.connect(self.path) as db:
            return db.execute(f"SELECT {column},record FROM {table} WHERE id=?", (key,)).fetchone()
