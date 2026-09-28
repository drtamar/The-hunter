"""Alias / identity / infrastructure graph.

Pattern from drtamar/newsroom-extension (structural-dependency-mapping).
Nodes are typed (email, domain, ip, wallet, handle, etc.); edges have
confidence in [0..1] and a reason string.
"""
from __future__ import annotations
import json
import pathlib
import hashlib
import re

CASES_ROOT = pathlib.Path("case")
_SAFE_RE = re.compile(r"[^A-Za-z0-9_]")


def _path(case_id: str) -> pathlib.Path:
    return CASES_ROOT / case_id / "alias_graph.json"


def _node_id(kind: str, value: str) -> str:
    return f"{kind}:{value.lower()}"


def _safe(node_id: str) -> str:
    return _SAFE_RE.sub("_", node_id)


def load(case_id: str) -> dict:
    p = _path(case_id)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except json.JSONDecodeError:
            pass
    return {"nodes": {}, "edges": []}


def save(case_id: str, graph: dict) -> None:
    p = _path(case_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(graph, indent=2))


def add_node(case_id: str, kind: str, value: str, ev_ids: list[str] | None = None, attrs: dict | None = None) -> str:
    g = load(case_id)
    nid = _node_id(kind, value)
    if nid not in g["nodes"]:
        g["nodes"][nid] = {"kind": kind, "value": value, "ev_ids": [], "attrs": {}}
    if ev_ids:
        g["nodes"][nid]["ev_ids"] = sorted(set(g["nodes"][nid]["ev_ids"]) | set(ev_ids))
    if attrs:
        g["nodes"][nid]["attrs"].update(attrs)
    save(case_id, g)
    return nid


def add_edge(
    case_id: str,
    src_kind: str,
    src_value: str,
    dst_kind: str,
    dst_value: str,
    confidence: float,
    reason: str,
    ev_ids: list[str] | None = None,
) -> str:
    add_node(case_id, src_kind, src_value)
    add_node(case_id, dst_kind, dst_value)
    g = load(case_id)
    src = _node_id(src_kind, src_value)
    dst = _node_id(dst_kind, dst_value)
    eid = hashlib.sha256(f"{src}|{dst}|{reason}".encode()).hexdigest()[:12]
    g["edges"].append({
        "id": eid,
        "src": src,
        "dst": dst,
        "confidence": float(confidence),
        "reason": reason,
        "ev_ids": ev_ids or [],
    })
    save(case_id, g)
    return eid


def to_mermaid(case_id: str) -> str:
    g = load(case_id)
    lines = ["graph LR"]
    for nid, n in g["nodes"].items():
        lines.append(f'  {_safe(nid)}["{n["kind"]}:{n["value"]}"]')
    for e in g["edges"]:
        lines.append(f'  {_safe(e["src"])} ---|{e["confidence"]:.2f}| {_safe(e["dst"])}')
    return "\n".join(lines)
