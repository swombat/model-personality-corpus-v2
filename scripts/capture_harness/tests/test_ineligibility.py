"""bv1-ineligibility-v1 fixtures (2026-10-08). No API calls."""
import json, sqlite3, sys, tempfile, types, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ineligibility as INEL

LINES = "\n".join(
    f"Line number {i} walks quietly through the morning air" for i in range(1, 11)
)


class Fixture:
    def __init__(self, td, source_text=LINES, attempts=4, reasons=None, passes=None):
        self.root = Path(td)
        self.c = {
            "id_prefix": "CAP_run_m",
            "label": "m-or-pin-x",
            "slug": "m",
            "bv1_evaluator": INEL.LUNA_ARM,
        }
        self.sid = "MID_15"
        self.arm = types.SimpleNamespace(EXTRA="instruction v1")
        self.source = self.root / "trace" / "MID_15.json"
        self.source.parent.mkdir(parents=True)
        self.source.write_text(json.dumps({"result": source_text}))
        self.bv_out = self.root / "bv_out"
        self.out = self.root / "outputs" / "MID_15.md"
        self.binding = self.root / "bindings" / "MID_15.json"
        d = INEL.attempt_dir(self.bv_out, self.c, self.sid)
        d.mkdir(parents=True)
        src_hash = INEL.sha256(self.source)
        for i in range(attempts):
            reason = (reasons or {}).get(i, INEL.QA_REASON)
            ok = (passes or {}).get(i, False)
            (d / f"{1000 + i}.json").write_text(
                json.dumps(
                    {"arm": INEL.LUNA_ARM, "source_sha256": src_hash, "qa_pass": ok, "qa_reason": reason}
                )
            )
        self.attempts = d

    def receipt(self, reviewer="BjZoXJ:mira"):
        return dict(INEL.facts(self.c, self.sid, self.source, self.bv_out, self.arm), reviewer=reviewer)

    def check(self, receipt):
        return INEL.check(receipt, self.c, self.sid, self.source, self.bv_out, self.arm, self.out, self.binding)


class ReceiptTests(unittest.TestCase):
    def test_valid_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            self.assertEqual(f.check(r), r)
            self.assertEqual(len(r["attempts"]), 4)

    def test_source_with_period_is_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td, LINES + "\nThe end.")
            with self.assertRaisesRegex(AssertionError, "eligible sentence"):
                f.check(f.receipt())

    def test_source_with_ellipsis_is_eligible(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td, LINES + "\nAnd then…")
            with self.assertRaises(AssertionError):
                f.check(f.receipt())

    def test_other_qa_reason_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td, reasons={2: "quote_not_exact"})
            with self.assertRaisesRegex(AssertionError, "another reason"):
                f.check(f.receipt())

    def test_transport_failure_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td, reasons={0: "transport_finish_provider_or_model"})
            with self.assertRaises(AssertionError):
                f.check(f.receipt())

    def test_a_passing_attempt_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td, passes={3: True}, reasons={3: ""})
            with self.assertRaisesRegex(AssertionError, "passed QA"):
                f.check(f.receipt())

    def test_listed_subset_cannot_hide_an_attempt(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            r["attempts"] = r["attempts"][:3]
            with self.assertRaisesRegex(AssertionError, "attempts"):
                f.check(r)

    def test_attempt_added_after_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            (f.attempts / "9999.json").write_text(json.dumps({"qa_pass": True}))
            with self.assertRaises(AssertionError):
                f.check(r)

    def test_attempt_bytes_changed(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            p = sorted(f.attempts.glob("*.json"))[0]
            p.write_text(p.read_text() + " ")
            with self.assertRaises(AssertionError):
                f.check(r)

    def test_source_changed(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            f.source.write_text(json.dumps({"result": LINES + "\nAnother line here"}))
            with self.assertRaisesRegex(AssertionError, "source_sha256|attempts|eligibility"):
                f.check(r)

    def test_instruction_changed(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            f.arm.EXTRA = "instruction v2"
            with self.assertRaisesRegex(AssertionError, "instruction_sha256"):
                f.check(r)

    def test_other_capture_or_arm(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            r["capture"] = "CAP_other_m"
            with self.assertRaisesRegex(AssertionError, "capture"):
                f.check(r)
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            f.c["bv1_evaluator"] = "legacy-deepseek"
            with self.assertRaises(AssertionError):
                f.check(f.receipt())

    def test_reviewer_required_and_not_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            with self.assertRaisesRegex(AssertionError, "reviewer"):
                f.check(f.receipt(reviewer=" "))
            g = Fixture(Path(td) / "g", LINES + ".")
            with self.assertRaises(AssertionError):
                g.check(g.receipt(reviewer="BjZoXJ:mira"))

    def test_extra_field_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = dict(f.receipt(), evaluated=True)
            with self.assertRaisesRegex(AssertionError, "unexpected receipt fields"):
                f.check(r)

    def test_collision_with_evaluation(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            f.out.parent.mkdir(parents=True)
            f.out.write_text("## Evidence line\n> x")
            with self.assertRaisesRegex(AssertionError, "output exists"):
                f.check(r)
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td)
            r = f.receipt()
            f.binding.parent.mkdir(parents=True)
            f.binding.write_text("{}")
            with self.assertRaisesRegex(AssertionError, "binding exists"):
                f.check(r)

    def test_no_attempts(self):
        with tempfile.TemporaryDirectory() as td:
            f = Fixture(td, attempts=0)
            with self.assertRaisesRegex(AssertionError, "no preserved attempts"):
                f.check(f.receipt())


class HistoryTests(unittest.TestCase):
    def db(self, td, state="blocked", counted=4, started=4, done=False):
        p = Path(td) / "state.sqlite"
        db = sqlite3.connect(p)
        db.execute("CREATE TABLE jobs(id TEXT,state TEXT,attempts INTEGER)")
        db.execute("CREATE TABLE events(at REAL,id TEXT,event TEXT,details TEXT)")
        db.execute("INSERT INTO jobs VALUES('t',?,?)", (state, counted))
        for i in range(started):
            db.execute("INSERT INTO events VALUES(?,?,?,?)", (i, "t", "started", str(i + 1)))
            db.execute("INSERT INTO events VALUES(?,?,?,?)", (i + 0.5, "t", "pending", "1"))
        if done:
            db.execute("INSERT INTO events VALUES(99,'t','done','')")
        db.commit()
        db.close()
        return p

    def test_matching_history(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertTrue(INEL.check_history(self.db(td), "t", [{}] * 4))

    def test_preserved_fewer_than_started(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(AssertionError, "history mismatch"):
                INEL.check_history(self.db(td), "t", [{}] * 3)

    def test_started_more_than_counted(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(AssertionError, "history mismatch"):
                INEL.check_history(self.db(td, started=5), "t", [{}] * 4)

    def test_task_ever_done(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(AssertionError, "completed"):
                INEL.check_history(self.db(td, done=True), "t", [{}] * 4)

    def test_task_not_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(AssertionError, "blocked"):
                INEL.check_history(self.db(td, state="pending"), "t", [{}] * 4)

    def test_unknown_task(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(AssertionError, "unknown task"):
                INEL.check_history(self.db(td), "nope", [])


def row(sid, ineligible=False):
    r = {"sample_id": f"cell/{sid}.json"}
    if ineligible:
        r.update(ineligible=True, receipt_sha256="h" + sid)
    return r


class CoverageTests(unittest.TestCase):
    ids = ["A_1", "A_2", "A_3"]

    def test_complete_run_unchanged(self):
        self.assertIsNone(INEL.coverage([row(i) for i in self.ids], self.ids))

    def test_one_ineligible(self):
        cov = INEL.coverage([row("A_1"), row("A_2", True), row("A_3")], self.ids)
        self.assertEqual(cov["expected"], 3)
        self.assertEqual(cov["evaluated"], 2)
        self.assertEqual(cov["evaluated_ids"], ["A_1", "A_3"])
        self.assertEqual([i["sample"] for i in cov["ineligible"]], ["A_2"])
        self.assertIn("BV1 analysis: 2/3 freeflow samples evaluated", cov["disclosure"])
        self.assertIn("A_2", cov["disclosure"])
        self.assertIn("not claimed to be unbiased", cov["disclosure"])

    def test_duplicate_ids(self):
        with self.assertRaisesRegex(AssertionError, "duplicate"):
            INEL.coverage([row("A_1"), row("A_1", True), row("A_2"), row("A_3")], self.ids)

    def test_unexpected_id(self):
        with self.assertRaisesRegex(AssertionError, "expected set"):
            INEL.coverage([row("A_1"), row("A_2"), row("B_9")], self.ids)

    def test_missing_id(self):
        with self.assertRaisesRegex(AssertionError, "expected set"):
            INEL.coverage([row("A_1"), row("A_2")], self.ids)

    def test_zero_evaluable_blocks(self):
        with self.assertRaisesRegex(AssertionError, "no evaluable"):
            INEL.coverage([row(i, True) for i in self.ids], self.ids)


if __name__ == "__main__":
    unittest.main()
