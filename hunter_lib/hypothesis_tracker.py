"""Hypothesis tracker — Confirmed / Indeterminate / Refuted with Heuer ACH.

Pattern from drtamar/intellyweave. Append-only JSONL per case;
later rows for the same hypothesis_id override earlier ones (read latest).
"""
from __future__ import annotations
import json
import pathlib
import datetime
from collections import defaultdict

CASES_ROOT = pathlib.Path("case")


def _path(case_id: str) -> pathlib.Path:
    return CASES_ROOT / case_id / "hypotheses.jsonl"


def _classify(support_grades: list[str], contradict_grades: list[str]) -> str:
    grade_a_support = sum(1 for g in support_grades if g == "A")
    grade_a_contra = sum(1 for g in contradict_grades if g == "A")
    if grade_a_contra >= 1:
        return "Refuted"
    if grade_a_support >= 2:
        return "Confirmed"
    return "Indeterminate"


def write(
    case_id: str,
    hypothesis_id: str,
    claim: str,
    support_ev_ids: list[str],
    contradict_ev_ids: list[str],
    support_grades: list[str],
    contradict_grades: list[str],
    status: str | None = None,
    rationale: str = "",
) -> dict:
    if status is None:
        status = _classify(support_grades, contradict_grades)
    row = {
        "hypothesis_id": hypothesis_id,
        "case_id": case_id,
        "claim": claim,
        "status": status,
        "support_ev": support_ev_ids,
        "contradict_ev": contradict_ev_ids,
        "support_grades": support_grades,
        "contradict_grades": contradict_grades,
        "rationale": rationale,
        "at": datetime.datetime.utcnow().isoformat() + "Z",
    }
    p = _path(case_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a") as f:
        f.write(json.dumps(row) + "\n")
    return row


def latest(case_id: str) -> dict[str, dict]:
    """Return the latest row per hypothesis_id (later wins)."""
    p = _path(case_id)
    if not p.exists():
        return {}
    out: dict[str, dict] = {}
    with p.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                hid = row.get("hypothesis_id")
                if hid:
                    out[hid] = row
            except json.JSONDecodeError:
                continue
    return out


def summary(case_id: str) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for r in latest(case_id).values():
        counts[r.get("status", "Indeterminate")] += 1
    return dict(counts)
