from __future__ import annotations
import sqlite3
from pathlib import Path
from uuid import UUID
from .models import Approval, Case, DispatchJob, Reminder

class Store:
    """Durable MVP store. JSON records are owner-scoped; no arbitrary SQL is exposed."""
    def __init__(self, path: str | Path = "golden_hour.sqlite3") -> None:
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, owner TEXT NOT NULL, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS approvals (id TEXT PRIMARY KEY, case_id TEXT NOT NULL, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, idempotency_key TEXT UNIQUE NOT NULL, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS reminders (id TEXT PRIMARY KEY, case_id TEXT NOT NULL, record TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS processed_messages (id TEXT PRIMARY KEY)")
    def save_case(self, case: Case) -> None:
        self._put("cases", str(case.case_id), case.owner_id, case.model_dump_json())
    def get_case(self, case_id: UUID, owner_id: str) -> Case | None:
        row = self._get("cases", str(case_id))
        if not row or row[0] != owner_id:
            return None
        return Case.model_validate_json(row[1])
    def save_approval(self, approval: Approval) -> None:
        self._put("approvals", str(approval.approval_id), str(approval.case_id), approval.model_dump_json())
    def get_approval(self, approval_id: UUID) -> Approval | None:
        row = self._get("approvals", str(approval_id))
        return Approval.model_validate_json(row[1]) if row else None
    def latest_case(self, owner_id: str) -> Case | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT record FROM cases WHERE owner=? ORDER BY rowid DESC LIMIT 1", (owner_id,)).fetchone()
        return Case.model_validate_json(row[0]) if row else None
    def save_job(self, job: DispatchJob) -> bool:
        with sqlite3.connect(self.path) as db:
            try:
                db.execute("INSERT INTO jobs(id,idempotency_key,record) VALUES (?,?,?)", (str(job.job_id), job.idempotency_key, job.model_dump_json()))
                return True
            except sqlite3.IntegrityError:
                return False
    def get_job_by_key(self, idempotency_key: str) -> DispatchJob | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT record FROM jobs WHERE idempotency_key=?", (idempotency_key,)).fetchone()
        return DispatchJob.model_validate_json(row[0]) if row else None
    def update_job(self, job: DispatchJob) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE jobs SET record=? WHERE id=?", (job.model_dump_json(), str(job.job_id)))
    def save_reminder(self, reminder: Reminder) -> None:
        self._put("reminders", str(reminder.reminder_id), str(reminder.case_id), reminder.model_dump_json())
    def get_reminder(self, reminder_id: UUID) -> Reminder | None:
        row = self._get("reminders", str(reminder_id))
        return Reminder.model_validate_json(row[1]) if row else None
    def mark_message_processed(self, message_id: UUID) -> bool:
        with sqlite3.connect(self.path) as db:
            try:
                db.execute("INSERT INTO processed_messages(id) VALUES (?)", (str(message_id),))
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
