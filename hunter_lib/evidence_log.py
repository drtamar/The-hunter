"""Evidence ledger — append-only JSONL with sequential EV-IDs.

Protocol from drtamar/huntkit (EV-IDs + capture-evidence) fused with
drtamar/UAP_OSINT-v0.1 (Superseded / Contradicted markers).
"""
from __future__ import annotations
import json
import pathlib
import datetime
import hashlib
import re

CASES_ROOT = pathlib.Path("case")


def _ledger_path(case_id: str) -> pathlib.Path:
    return CASES_ROOT / case_id / "evidence.jsonl"


def next_id(case_id: str) -> str:
    """Return the next sequential EV-NNNN for a case."""
    p = _ledger_path(case_id)
    if not p.exists():
        return "EV-0001"
    highest = 0
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = re.match(r"EV-(\d+)", row.get("ev_id", ""))
            if m:
                highest = max(highest, int(m.group(1)))
    return f"EV-{highest + 1:04d}"


def issue(case_id: str, *_args, **_kwargs) -> str:
    """Back-compat alias for next_id()."""
    return next_id(case_id)


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def seal(
    case_id: str,
    ev_id: str,
    kind: str,
    source: str,
    sha256,
    archives: dict,
    source_grade: str,
    collected_by: str = "hunter",
    notes: str = "",
) -> dict:
    """Append a sealed evidence row to the ledger and return the row."""
    sha = sha256 if isinstance(sha256, dict) else {"raw": sha256}
    row = {
        "ev_id": ev_id,
        "case_id": case_id,
        "kind": kind,
        "source": source,
        "collected_by": collected_by,
        "collected_at": _now(),
        "sha256": sha,
        "archives": archives,
        "source_grade": source_grade,
        "status": "sealed",
        "superseded_by": None,
        "contradicted_by": [],
        "notes": notes,
    }
    p = _ledger_path(case_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def supersede(case_id: str, new_ev_id: str, old_ev_id: str, reason: str, **seal_kwargs) -> dict:
    """Mark new_ev_id as superseding old_ev_id; appends both rows."""
    row = seal(case_id, new_ev_id, **seal_kwargs)
    note = {
        "ev_id": new_ev_id,
        "supersedes": old_ev_id,
        "reason": reason,
        "at": _now(),
    }
    with _ledger_path(case_id).open("a") as f:
        f.write(json.dumps(note) + "\n")
    return row


def contradict(case_id: str, new_ev_id: str, contradicts_ids, reason: str, **seal_kwargs) -> dict:
    """Mark new_ev_id as contradicting one or more EV-IDs."""
    row = seal(case_id, new_ev_id, **seal_kwargs)
    ids = contradicts_ids if isinstance(contradicts_ids, list) else [contradicts_ids]
    note = {
        "ev_id": new_ev_id,
        "contradicts": ids,
        "reason": reason,
        "at": _now(),
    }
    with _ledger_path(case_id).open("a") as f:
        f.write(json.dumps(note) + "\n")
    return row


def read_all(case_id: str) -> list[dict]:
    p = _ledger_path(case_id)
    if not p.exists():
        return []
    out = []
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def verify(case_id: str) -> dict:
    """Rehash every sealed raw/screenshot and compare to ledger SHA-256s.

    Returns a drift report; any mismatch is a chain-of-custody breach.
    """
    report = {"case_id": case_id, "checked": 0, "matched": 0, "mismatched": [], "missing": []}
    case_dir = CASES_ROOT / case_id
    for row in read_all(case_id):
        if row.get("status") != "sealed":
            continue
        ev_id = row.get("ev_id", "")
        sha = row.get("sha256", {}) or {}
        for kind, expected in sha.items():
            if not expected:
                continue
            if kind == "raw":
                fp = case_dir / "raw" / f"{ev_id}.html"
            elif kind == "screenshot":
                fp = case_dir / "raw" / f"{ev_id}.png"
            else:
                continue
            report["checked"] += 1
            if not fp.exists():
                report["missing"].append({"ev_id": ev_id, "file": str(fp)})
                continue
            actual = hashlib.sha256(fp.read_bytes()).hexdigest()
            if actual == expected:
                report["matched"] += 1
            else:
                report["mismatched"].append(
                    {"ev_id": ev_id, "file": str(fp), "expected": expected, "actual": actual}
                )
    return report
