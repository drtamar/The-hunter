"""A–F reliability grading per huntkit / military OSINT convention.

A = Reliable          (primary source, technically authenticated)
B = Usually reliable  (third-party with track record)
C = Fairly reliable   (community-curated, multi-source corroborated)
D = Not usually reliable
E = Unreliable
F = Cannot be judged
"""
from __future__ import annotations

GRADES = {
    "A": "Reliable — primary source, technically authenticated",
    "B": "Usually reliable — third-party with track record",
    "C": "Fairly reliable — community-curated, multi-source corroborated",
    "D": "Not usually reliable — single, unverified",
    "E": "Unreliable — anonymous, no evidence",
    "F": "Cannot be judged — corrupted/missing/manipulated",
}

_RANK = {g: i for i, g in enumerate("ABCDEF")}

_KIND_GRADES = {
    "rdap": "A", "whois": "A", "crt.sh": "A", "shodan": "A",
    "etherscan": "A", "blockchair": "A", "blockchain-explorer": "A",
    "wayback": "B", "archive.today": "B",
    "virustotal": "A", "urlhaus": "A", "otx": "A", "threatfox": "A",
    "phishtank": "A", "cisa-kev": "A", "ofac": "A", "greynoise": "A",
    "walletexplorer": "B",
    "chainabuse": "C", "abuseipdb": "C", "etherscamdb": "C",
    "third-party-mirror": "C",
    "user-screenshot": "B",
    "community-report": "C",
    "anonymous-tip": "E",
}


def is_better_or_equal(a: str, b: str) -> bool:
    return _RANK.get(a, 99) <= _RANK.get(b, 99)


def downgrade(grade: str, steps: int = 1) -> str:
    i = min(_RANK.get(grade, 0) + steps, 5)
    return "ABCDEF"[i]


def upgrade(grade: str, steps: int = 1) -> str:
    i = max(_RANK.get(grade, 0) - steps, 0)
    return "ABCDEF"[i]


def grade_for_source(source_kind: str) -> str:
    return _KIND_GRADES.get(source_kind, "C")


def report(grades: list[str]) -> dict:
    """Return a count per grade plus the best (dominant) grade seen."""
    counts = {g: 0 for g in "ABCDEF"}
    for g in grades:
        if g in counts:
            counts[g] += 1
    dominant = "F"
    for g in "ABCDEF":
        if counts[g] > 0:
            dominant = g
            break
    return {"counts": counts, "dominant": dominant}
