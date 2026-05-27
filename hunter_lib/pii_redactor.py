"""Investigator-PII redactor.

Reads scope/scope.yaml → victim_pii and scrubs every match from text before
the text is saved/published. Returns (clean_text, hits) so callers can audit
what was scrubbed via a sidecar redactions file.
"""
from __future__ import annotations
import re
import pathlib

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


def _load_scope(scope_path: str) -> dict:
    p = pathlib.Path(scope_path)
    if not p.exists() or yaml is None:
        return {}
    return yaml.safe_load(p.read_text()) or {}


def _normalize_phone(s: str) -> str:
    return re.sub(r"\D", "", s)


def redact_text(text: str, scope_yaml_path: str = "scope/scope.yaml") -> tuple[str, list[dict]]:
    """Return (clean_text, hits).

    hits = [{kind, original, replacement, position|count}, ...]
    """
    scope = _load_scope(scope_yaml_path)
    pii = scope.get("victim_pii", {}) or {}
    hits: list[dict] = []
    clean = text

    # Names — word-boundary, case-insensitive.
    for name in pii.get("names", []) or []:
        if not name:
            continue
        pattern = r"\b" + re.escape(name) + r"\b"
        for m in re.finditer(pattern, clean, re.IGNORECASE):
            hits.append({"kind": "name", "original": m.group(0), "replacement": "[REDACTED-PII]", "position": m.start()})
        clean = re.sub(pattern, "[REDACTED-PII]", clean, flags=re.IGNORECASE)

    # Emails — exact match, case-insensitive.
    for email in pii.get("emails", []) or []:
        if not email:
            continue
        new, n = re.subn(re.escape(email), "[REDACTED-EMAIL]", clean, flags=re.IGNORECASE)
        if n:
            hits.append({"kind": "email", "original": email, "replacement": "[REDACTED-EMAIL]", "count": n})
            clean = new

    # Phones — normalize to digits, last-N match.
    for phone in pii.get("phones", []) or []:
        if not phone:
            continue
        norm = _normalize_phone(phone)
        if len(norm) < 7:
            continue
        last7 = norm[-7:]
        pattern = r"\+?\(?\d[\d\s\-\(\)\.]{6,20}"
        out_parts = []
        last = 0
        for m in re.finditer(pattern, clean):
            if _normalize_phone(m.group(0)).endswith(last7):
                out_parts.append(clean[last:m.start()])
                out_parts.append("[REDACTED-PHONE]")
                hits.append({"kind": "phone", "original": m.group(0), "replacement": "[REDACTED-PHONE]", "position": m.start()})
                last = m.end()
        out_parts.append(clean[last:])
        clean = "".join(out_parts)

    # Addresses — literal, conservative.
    for addr in pii.get("addresses", []) or []:
        if not addr:
            continue
        new, n = re.subn(re.escape(addr), "[REDACTED-ADDR]", clean, flags=re.IGNORECASE)
        if n:
            hits.append({"kind": "address", "original": addr, "replacement": "[REDACTED-ADDR]", "count": n})
            clean = new

    # Bank accounts — last-4 preserved as marker.
    for ba in pii.get("bank_accounts", []) or []:
        if not ba:
            continue
        s = str(ba)
        if len(s) >= 4:
            marker = f"[REDACTED-BANK-***{s[-4:]}]"
            n = clean.count(s)
            if n:
                clean = clean.replace(s, marker)
                hits.append({"kind": "bank", "original": s, "replacement": marker, "count": n})

    # Wallets — keep first-4 / last-4 for context.
    for w in pii.get("wallets", []) or []:
        if not w:
            continue
        s = str(w)
        if len(s) >= 8:
            marker = f"[REDACTED-WALLET-{s[:4]}…{s[-4:]}]"
            n_ci = re.subn(re.escape(s), marker, clean, flags=re.IGNORECASE)
            if n_ci[1]:
                clean = n_ci[0]
                hits.append({"kind": "wallet", "original": s, "replacement": marker, "count": n_ci[1]})

    # Investigator IP addresses.
    for ip in pii.get("ip_addresses", []) or []:
        if not ip:
            continue
        new, n = re.subn(re.escape(ip) + r"\b", "[REDACTED-IP]", clean)
        if n:
            hits.append({"kind": "ip", "original": ip, "replacement": "[REDACTED-IP]", "count": n})
            clean = new

    # External case-ID aliases.
    for alias in pii.get("case_id_aliases", []) or []:
        if not alias:
            continue
        new, n = re.subn(re.escape(alias), "[REDACTED-EXT-CASE]", clean, flags=re.IGNORECASE)
        if n:
            hits.append({"kind": "case_alias", "original": alias, "replacement": "[REDACTED-EXT-CASE]", "count": n})
            clean = new

    return clean, hits
