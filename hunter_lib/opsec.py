"""Outbound HTTP wrapper enforcing scope.opsec settings.

Rotates User-Agent, suppresses Referer leak, respects scope.opsec.proxy.
Called from skills/opsec-firewall and by Python-side subagent tooling.
"""
from __future__ import annotations
import random
import urllib.request
import pathlib

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "curl/8.6.0",
    "Wget/1.21.4",
]


def _load_scope(scope_path: str = "scope/scope.yaml") -> dict:
    p = pathlib.Path(scope_path)
    if not p.exists() or yaml is None:
        return {}
    return yaml.safe_load(p.read_text()) or {}


def pick_ua(stable: bool = False) -> str:
    return UA_POOL[0] if stable else random.choice(UA_POOL)


def http_get(url: str, scope_path: str = "scope/scope.yaml", stable: bool = False, timeout: int = 20) -> tuple[int, bytes, dict]:
    """Outbound GET respecting scope.opsec. Returns (status, body, headers).

    On error returns (0, error-bytes, {}).
    """
    scope = _load_scope(scope_path)
    opsec = scope.get("opsec", {}) or {}
    proxy = (opsec.get("proxy", "") or "").strip()

    headers = {"User-Agent": pick_ua(stable=stable), "Accept": "*/*"}
    if opsec.get("block_referer_leak", True):
        headers["Referer"] = ""

    if proxy:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    else:
        opener = urllib.request.build_opener()

    req = urllib.request.Request(url, headers=headers)
    try:
        r = opener.open(req, timeout=timeout)
        return r.status, r.read(), dict(r.headers)
    except Exception as e:
        return 0, str(e).encode(), {}
