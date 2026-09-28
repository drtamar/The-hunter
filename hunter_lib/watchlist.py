"""Watchlist storage and signal dedup.

Pattern from drtamar/strike-monitor: tiered source weights, dedup-by-signal-hash,
append-only alerts. Backed by SQLite.
"""
from __future__ import annotations
import sqlite3
import json
import pathlib
import datetime
import hashlib

DB = pathlib.Path("case/watchlist.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS watches (
  watch_id          TEXT PRIMARY KEY,
  case_id           TEXT,
  kind              TEXT,
  value             TEXT,
  poll_interval_min INTEGER DEFAULT 60,
  source_tier       TEXT DEFAULT 'A',
  alert_on          TEXT,
  added_at          TEXT,
  last_polled_at    TEXT,
  last_signal_hash  TEXT,
  active            INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS alerts (
  alert_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  watch_id   TEXT,
  event      TEXT,
  confidence REAL,
  ev_id      TEXT,
  signal     TEXT,
  at         TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_watch ON alerts(watch_id);
CREATE INDEX IF NOT EXISTS idx_alerts_at ON alerts(at);
"""

_TIER_TRUST = {"A": 0.9, "B": 0.75, "C": 0.5}


def _c() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.executescript(_SCHEMA)
    return c


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def add(
    case_id: str,
    kind: str,
    value: str,
    poll_interval_min: int = 60,
    source_tier: str = "A",
    alert_on=None,
) -> str:
    wid = "W-" + hashlib.sha256(f"{case_id}|{kind}|{value}".encode()).hexdigest()[:10]
    c = _c()
    c.execute(
        "INSERT OR IGNORE INTO watches "
        "(watch_id, case_id, kind, value, poll_interval_min, source_tier, alert_on, added_at, last_polled_at, last_signal_hash, active) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, 1)",
        (
            wid, case_id, kind, value, poll_interval_min, source_tier,
            json.dumps(alert_on or ["appeared", "changed"]), _now(),
        ),
    )
    c.commit()
    return wid


def list_active() -> list[tuple]:
    return _c().execute(
        "SELECT watch_id, case_id, kind, value, poll_interval_min, source_tier, last_polled_at "
        "FROM watches WHERE active = 1 ORDER BY added_at DESC"
    ).fetchall()


def remove(watch_id: str) -> None:
    c = _c()
    c.execute("UPDATE watches SET active = 0 WHERE watch_id = ?", (watch_id,))
    c.commit()


def trust_of(source_tier: str) -> float:
    return _TIER_TRUST.get(source_tier, 0.5)


def record_signal(
    watch_id: str,
    signal: str,
    event: str = "changed",
    confidence: float = 1.0,
    ev_id: str = "",
) -> dict | None:
    """Dedup against last_signal_hash; only emit if changed. Return alert row or None."""
    sig_h = hashlib.sha256(signal.encode()).hexdigest()
    c = _c()
    prev = c.execute(
        "SELECT last_signal_hash FROM watches WHERE watch_id = ?", (watch_id,)
    ).fetchone()
    if prev and prev[0] == sig_h:
        return None
    now = _now()
    c.execute(
        "UPDATE watches SET last_polled_at = ?, last_signal_hash = ? WHERE watch_id = ?",
        (now, sig_h, watch_id),
    )
    c.execute(
        "INSERT INTO alerts (watch_id, event, confidence, ev_id, signal, at) VALUES (?, ?, ?, ?, ?, ?)",
        (watch_id, event, confidence, ev_id, signal[:512], now),
    )
    c.commit()
    return {
        "watch_id": watch_id,
        "event": event,
        "confidence": confidence,
        "ev_id": ev_id,
        "at": now,
    }


def recent_alerts(days: int = 7) -> list[tuple]:
    cutoff = (datetime.datetime.utcnow() - datetime.timedelta(days=days)).isoformat() + "Z"
    return _c().execute(
        "SELECT watch_id, event, confidence, ev_id, signal, at FROM alerts WHERE at >= ? ORDER BY at DESC",
        (cutoff,),
    ).fetchall()
