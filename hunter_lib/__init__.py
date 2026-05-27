"""hunter_lib — Python helpers for the Hunter OSINT super-agent.

Referenced by agents/, commands/, skills/, and hooks/. All modules are
stdlib-first; only pyyaml is required for scope parsing.
"""

__version__ = "0.1.0"
__all__ = [
    "case_db",
    "evidence_log",
    "archiver",
    "watchlist",
    "notifier",
    "hypothesis_tracker",
    "alias_graph",
    "source_grader",
    "pii_redactor",
    "opsec",
    "cli",
]
