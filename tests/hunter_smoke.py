"""Hunter framework smoke tests.

Run with:  python -m unittest tests.hunter_smoke
Or just:   python tests/hunter_smoke.py

Uses a temp working directory so it never touches a real case/ folder.
"""
from __future__ import annotations
import os
import pathlib
import tempfile
import unittest


class HunterSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.mkdtemp(prefix="hunter-smoke-")
        self.prev_cwd = os.getcwd()
        os.chdir(self.tmp)
        # Force module-level paths to re-resolve under tmp by reimporting.
        import importlib
        import sys
        for mod in ("hunter_lib.case_db", "hunter_lib.evidence_log",
                    "hunter_lib.watchlist", "hunter_lib.alias_graph",
                    "hunter_lib.hypothesis_tracker"):
            if mod in sys.modules:
                importlib.reload(sys.modules[mod])

    def tearDown(self) -> None:
        os.chdir(self.prev_cwd)

    def test_open_case_creates_workspace(self) -> None:
        from hunter_lib import case_db
        cid = case_db.open_case(target="example.com")
        self.assertTrue(cid.startswith("CASE-"))
        case_dir = pathlib.Path(self.tmp) / "case" / cid
        self.assertTrue(case_dir.exists())
        self.assertTrue((case_dir / "evidence.jsonl").exists())
        self.assertTrue((case_dir / "findings.jsonl").exists())

    def test_evidence_id_is_sequential(self) -> None:
        from hunter_lib import case_db, evidence_log
        cid = case_db.open_case(target="example.com")
        first = evidence_log.next_id(cid)
        self.assertEqual(first, "EV-0001")
        evidence_log.seal(
            case_id=cid, ev_id=first, kind="url", source="https://example.com",
            sha256={"raw": "deadbeef"}, archives={"wayback": "", "archive_today": ""},
            source_grade="A", collected_by="test",
        )
        second = evidence_log.next_id(cid)
        self.assertEqual(second, "EV-0002")

    def test_finding_round_trip(self) -> None:
        from hunter_lib import case_db
        cid = case_db.open_case(target="example.com")
        fid = case_db.add_finding(
            case_id=cid, kind="domain", value="scammer.example.com",
            status="Confirmed", source_grade="A",
            ev_ids=["EV-0001"], collected_by="test", notes="",
        )
        self.assertTrue(fid.startswith("F-"))
        rows = case_db.list_findings(cid)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], "scammer.example.com")

    def test_watchlist_dedup(self) -> None:
        from hunter_lib import case_db, watchlist
        cid = case_db.open_case(target="example.com")
        wid = watchlist.add(case_id=cid, kind="domain", value="scammer.example.com")
        a1 = watchlist.record_signal(wid, "resolved=1.2.3.4", event="appeared", confidence=0.9, ev_id="EV-0001")
        a2 = watchlist.record_signal(wid, "resolved=1.2.3.4", event="appeared", confidence=0.9, ev_id="EV-0001")
        self.assertIsNotNone(a1)
        self.assertIsNone(a2)

    def test_hypothesis_classification(self) -> None:
        from hunter_lib import hypothesis_tracker as ht
        from hunter_lib import case_db
        cid = case_db.open_case(target="example.com")
        row = ht.write(
            cid, "H1", "X is the actor behind Y",
            support_ev_ids=["EV-0001", "EV-0002"], contradict_ev_ids=[],
            support_grades=["A", "A"], contradict_grades=[],
        )
        self.assertEqual(row["status"], "Confirmed")
        row2 = ht.write(
            cid, "H2", "Z owns wallet W",
            support_ev_ids=["EV-0003"], contradict_ev_ids=["EV-0004"],
            support_grades=["A"], contradict_grades=["A"],
        )
        self.assertEqual(row2["status"], "Refuted")

    def test_alias_graph_edges(self) -> None:
        from hunter_lib import alias_graph as ag
        from hunter_lib import case_db
        cid = case_db.open_case(target="example.com")
        ag.add_edge(cid, "email", "a@b.com", "domain", "b.com",
                    confidence=0.95, reason="registrant", ev_ids=["EV-0001"])
        m = ag.to_mermaid(cid)
        self.assertIn("graph LR", m)
        self.assertIn("0.95", m)

    def test_pii_redactor_scrubs_name_and_email(self) -> None:
        from hunter_lib import pii_redactor
        scope = pathlib.Path("scope/scope.yaml")
        scope.parent.mkdir(parents=True, exist_ok=True)
        scope.write_text(
            "victim_pii:\n"
            "  names: [\"Jane Doe\"]\n"
            "  emails: [\"jane@example.com\"]\n"
            "  phones: []\n"
            "  addresses: []\n"
            "  bank_accounts: []\n"
            "  wallets: []\n"
            "  ip_addresses: []\n"
        )
        text = "Email from jane@example.com to Jane Doe at home."
        clean, hits = pii_redactor.redact_text(text, scope_yaml_path=str(scope))
        self.assertNotIn("jane@example.com", clean)
        self.assertNotIn("Jane Doe", clean)
        kinds = {h["kind"] for h in hits}
        self.assertIn("email", kinds)
        self.assertIn("name", kinds)

    def test_source_grader_downgrade_upgrade(self) -> None:
        from hunter_lib import source_grader
        self.assertEqual(source_grader.downgrade("A"), "B")
        self.assertEqual(source_grader.upgrade("C"), "B")
        self.assertEqual(source_grader.grade_for_source("crt.sh"), "A")
        rep = source_grader.report(["A", "A", "C", "F"])
        self.assertEqual(rep["counts"]["A"], 2)
        self.assertEqual(rep["dominant"], "A")


if __name__ == "__main__":
    unittest.main()
