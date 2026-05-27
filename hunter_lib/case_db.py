"""Case-DB: SQLite-backed engagement workspace manager.

Adapted from drtamar/claudeos (findings tracker + engagement workspace pattern).
Opens a CASE-YYYY-NNNN per investigation, creates the on-disk workspace,
and maintains a SQLite index for fast lookup. JSONL files remain the
source of truth for evidence and findings; SQLite is just an index.
"""
from __future__ import annotations
import sqlite3
import json
import hashlib
import datetime
import pathlib

DB_PATH = pathlib.Path("case/cases.db")
CASES_ROOT = pathlib.Path("case")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
  case_id     TEXT PRIMARY KEY,
  target      TEXT NOT NULL,
  opened_at   TEXT NOT NULL,
  scope_hash  TEXT,
  status      TEXT DEFAULT 'open',
  meta        TEXT
);
CREATE TABLE IF NOT EXISTS findings (
  finding_id   TEXT PRIMARY KEY,
  case_id      TEXT,
  kind         TEXT,
  value        TEXT,
  status       TEXT,
  source_grade TEXT,
  ev_ids       TEXT,
  collected_by TEXT,
  collected_at TEXT,
  notes        TEXT,
  FOREIGN KEY(case_id) REFERENCES cases(case_id)
);
CREATE INDEX IF NOT EXISTS idx_findings_case ON findings(case_id);
CREATE INDEX IF NOT EXISTS idx_findings_value ON findings(value);
"""


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.executescript(_SCHEMA)
    return c


def _next_case_id() -> str:
    year = datetime.datetime.utcnow().year
    c = _conn()
    n = c.execute(
        "SELECT COUNT(*) FROM cases WHERE case_id LIKE ?",
        (f"CASE-{year}-%",),
    ).fetchone()[0]
    return f"CASE-{year}-{n + 1:04d}"


def open_case(target: str, scope_path: str = "scope/scope.yaml") -> str:
    """Open a new case, materialize the on-disk workspace, return its ID."""
    case_id = _next_case_id()
    now = datetime.datetime.utcnow().isoformat() + "Z"
    scope_hash = ""
    sp = pathlib.Path(scope_path)
    if sp.exists():
        scope_hash = hashlib.sha256(sp.read_bytes()).hexdigest()
    case_dir = CASES_ROOT / case_id
    (case_dir / "raw").mkdir(parents=True, exist_ok=True)
    (case_dir / "reports").mkdir(parents=True, exist_ok=True)
    for jf in ("evidence.jsonl", "findings.jsonl", "alerts.jsonl", "audit.jsonl", "hypotheses.jsonl"):
        (case_dir / jf).touch()
    c = _conn()
    c.execute(
        "INSERT INTO cases (case_id, target, opened_at, scope_hash, status, meta) VALUES (?, ?, ?, ?, ?, ?)",
        (case_id, target, now, scope_hash, "open", json.dumps({})),
    )
    c.commit()
    return case_id


def list_cases(status: str | None = None) -> list[tuple]:
    q = "SELECT case_id, target, opened_at, status FROM cases"
    args: tuple = ()
    if status:
        q += " WHERE status = ?"
        args = (status,)
    q += " ORDER BY opened_at DESC"
    return _conn().execute(q, args).fetchall()


def get_case(case_id: str) -> dict | None:
    row = _conn().execute(
        "SELECT case_id, target, opened_at, scope_hash, status, meta FROM cases WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if not row:
        return None
    keys = ["case_id", "target", "opened_at", "scope_hash", "status", "meta"]
    out = dict(zip(keys, row))
    try:
        out["meta"] = json.loads(out["meta"] or "{}")
    except json.JSONDecodeError:
        out["meta"] = {}
    return out


def close_case(case_id: str) -> None:
    c = _conn()
    c.execute("UPDATE cases SET status = 'closed' WHERE case_id = ?", (case_id,))
    c.commit()


def add_finding(
    case_id: str,
    kind: str,
    value: str,
    status: str,
    source_grade: str,
    ev_ids,
    collected_by: str,
    notes: str = "",
) -> str:
    fid = "F-" + hashlib.sha256(f"{case_id}|{kind}|{value}|{collected_by}".encode()).hexdigest()[:10]
    now = datetime.datetime.utcnow().isoformat() + "Z"
    ev = ev_ids if isinstance(ev_ids, list) else [ev_ids]
    row = {
        "finding_id": fid,
        "case_id": case_id,
        "kind": kind,
        "value": value,
        "status": status,
        "source_grade": source_grade,
        "ev_ids": ev,
        "collected_by": collected_by,
        "collected_at": now,
        "notes": notes,
    }
    with (CASES_ROOT / case_id / "findings.jsonl").open("a") as f:
        f.write(json.dumps(row) + "\n")
    c = _conn()
    c.execute(
        "INSERT OR REPLACE INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (fid, case_id, kind, value, status, source_grade, json.dumps(ev), collected_by, now, notes),
    )
    c.commit()
    return fid


def list_findings(case_id: str, kind: str | None = None) -> list[dict]:
    q = "SELECT finding_id, kind, value, status, source_grade, ev_ids, collected_by, collected_at, notes FROM findings WHERE case_id = ?"
    args = (case_id,)
    if kind:
        q += " AND kind = ?"
        args = (case_id, kind)
    rows = _conn().execute(q, args).fetchall()
    keys = ["finding_id", "kind", "value", "status", "source_grade", "ev_ids", "collected_by", "collected_at", "notes"]
    out = []
    for r in rows:
        d = dict(zip(keys, r))
        try:
            d["ev_ids"] = json.loads(d["ev_ids"] or "[]")
        except json.JSONDecodeError:
            d["ev_ids"] = []
        out.append(d)
    return out
