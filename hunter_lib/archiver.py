"""Wayback + archive.today + local snapshot + SHA-256 archiver.

Used by evidence-officer subagent and the evidence-capture hook.
stdlib-only; chromium headless screenshot is best-effort.
"""
from __future__ import annotations
import urllib.parse
import urllib.request
import hashlib
import pathlib
import subprocess
import shutil

from . import evidence_log

UA = "hunter-archiver/0.1 (+https://github.com/drtamar/the-hunter)"
CASES_ROOT = pathlib.Path("case")


def _wayback_save(url: str) -> str:
    req = urllib.request.Request(
        f"https://web.archive.org/save/{url}",
        headers={"User-Agent": UA},
    )
    try:
        r = urllib.request.urlopen(req, timeout=30)
        loc = r.headers.get("Content-Location") or r.headers.get("Location") or ""
        if loc and not loc.startswith("http"):
            loc = "https://web.archive.org" + loc
        return loc
    except Exception:
        return ""


def _archive_today(url: str) -> str:
    data = urllib.parse.urlencode({"url": url, "run": "1"}).encode()
    req = urllib.request.Request(
        "https://archive.ph/",
        data=data,
        headers={"User-Agent": UA},
    )
    try:
        r = urllib.request.urlopen(req, timeout=60)
        refresh = r.headers.get("Refresh", "")
        if "url=" in refresh:
            return refresh.split("url=", 1)[1].strip()
        return r.url or ""
    except Exception:
        return ""


def _fetch(url: str, out_path: pathlib.Path) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            out_path.write_bytes(r.read())
        return True
    except Exception:
        return False


def _sha256(path: pathlib.Path) -> str:
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _screenshot(url: str, out_path: pathlib.Path) -> bool:
    for binary in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        if not shutil.which(binary):
            continue
        try:
            subprocess.run(
                [binary, "--headless", "--disable-gpu",
                 f"--screenshot={out_path}", "--window-size=1280,1800", url],
                check=True, timeout=45,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            if out_path.exists() and out_path.stat().st_size > 0:
                return True
        except Exception:
            continue
    return False


def _downgrade(grade: str) -> str:
    order = "ABCDEF"
    i = order.index(grade) if grade in order else len(order) - 1
    return order[min(i + 1, len(order) - 1)]


def auto_capture(
    case_id: str,
    url: str,
    collected_by: str = "auto-hook",
    source_grade: str = "A",
) -> dict:
    """One-call capture: fetch + screenshot + Wayback + archive.today + hash + seal.

    Returns the sealed evidence row.
    """
    ev_id = evidence_log.next_id(case_id)
    raw_dir = CASES_ROOT / case_id / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / f"{ev_id}.html"
    shot_path = raw_dir / f"{ev_id}.png"

    fetched = _fetch(url, raw_path)
    shot = _screenshot(url, shot_path) if fetched else False
    wb = _wayback_save(url)
    at = _archive_today(url)

    sha = {
        "raw": _sha256(raw_path) if fetched else "",
        "screenshot": _sha256(shot_path) if shot else "",
    }

    grade = source_grade
    if not wb:
        grade = _downgrade(grade)
    if not fetched:
        grade = "F"

    return evidence_log.seal(
        case_id=case_id,
        ev_id=ev_id,
        kind="url",
        source=url,
        sha256=sha,
        archives={"wayback": wb, "archive_today": at},
        source_grade=grade,
        collected_by=collected_by,
    )
