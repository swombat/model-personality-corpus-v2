"""Offline BV1-Luna v1.1 routing and apply lane (analysis e5b4f5912, Mira eBmBDj).

Same fixture as test_ineligibility_flow: real engine database, worker
bv1/synthesis/ready; stubbed evaluator modules (no API) and aggregation scripts.
"""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ineligibility as INEL
import worker
from engine import atomic, digest
from test_ineligibility_flow import Flow, LABEL
import apply_luna_v1_1 as LANE

V11_STUB = """import json
from pathlib import Path
ARM = 'bv1-luna-v1.1-20261016'
CALLS = []
def valid_output(text, source=None):
    return (text.startswith('## ok v1.1'), '')
def provenance_ok(out, row):
    p = Path(str(out) + '.provenance.json')
    return p.exists() and json.loads(p.read_text())['arm'] == ARM
def process(row, outdir):
    CALLS.append(row['pid'])
    out = Path(row['outpath']); out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():  # mirrors luna_v1_1.process
        if provenance_ok(out, row):
            return
        raise RuntimeError('exists without provenance')
    d = Path(outdir) / 'attempt_responses' / row['pid']; d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob('*.json'))) + 1
    fail = Path(outdir).parent / 'FAIL_NEXT_CALL'
    if fail.exists():
        fail.unlink()
        (d / f'{n}.json').write_text(json.dumps({'arm': ARM, 'qa_pass': False}))
        raise RuntimeError('injected evaluator failure')
    (d / f'{n}.json').write_text(json.dumps({'arm': ARM, 'qa_pass': True}))
    out.write_text('## ok v1.1 evaluation\\n')
    Path(str(out) + '.provenance.json').write_text(json.dumps({'arm': ARM}))
"""
TASK = f"{LABEL}/bv1/X_1"


class LaneTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.flow = None

    def tearDown(self):
        if self.flow:
            self.flow.close()
        self.td.cleanup()

    def make(self, **kw):
        f = self.flow = Flow(self.td.name, **kw)
        (f.root / "analysis/freeflow/personality-eval-bv1/luna_v1_1.py").write_text(V11_STUB)
        return f

    def lane(self, f, **kw):
        return LANE.apply(f.run / "spec.json", f.run / "state", [TASK], "eBmBDj:test", **kw)

    def state(self, f, id=TASK):
        return f.engine.db.execute("SELECT state,reason,receipts FROM jobs WHERE id=?", (id,)).fetchone()

    def v1_snapshot(self, f):
        return LANE.v1_records(worker, f.c, f.phase, "X_1")

    def test_routing_unpunctuated_without_v1_record_goes_to_v11_and_dag_never_generates(self):
        f = self.make()
        with self.assertRaises(SystemExit) as e:
            worker.bv1(f.c, f.phase, "X_1")
        self.assertEqual(e.exception.code, 21)
        self.assertFalse(worker.bv1_paths(f.c, f.phase, worker.LUNA_V11_ARM)[1].exists())

    def test_existing_v1_evaluation_keeps_v1(self):
        f = self.make(evaluated_x=True)
        row = worker.bv1(f.c, f.phase, "X_1", True)
        self.assertEqual(row["evaluator_arm"], worker.LUNA_ARM)

    def test_punctuated_samples_stay_v1(self):
        f = self.make()
        self.assertEqual(worker.bv1(f.c, f.phase, "S_1", True)["evaluator_arm"], worker.LUNA_ARM)

    def test_check_is_a_dry_run(self):
        f = self.make()
        before = (self.state(f), self.v1_snapshot(f))
        [sel] = self.lane(f, check_only=True)
        self.assertEqual(sel["arm"], worker.LUNA_V11_ARM)
        self.assertIn("/arms/" + worker.LUNA_V11_ARM + "/outputs/", sel["v11_output"])
        self.assertIn("freeflow_bv1_luna_v1_1", sel["v11_attempts"])
        self.assertIn("bv1_bindings_luna_v1_1", sel["v11_binding"])
        self.assertEqual(sel["v1_records"]["attempts"]["files"], 4)
        self.assertFalse(Path(sel["v11_output"]).exists())
        self.assertFalse(Path(sel["v11_attempts"]).exists())
        self.assertEqual((self.state(f), self.v1_snapshot(f)), before)

    def test_apply_evaluates_releases_and_keeps_v1_untouched(self):
        f = self.make()
        v1 = self.v1_snapshot(f)
        [sel] = self.lane(f)
        state, reason, receipts = self.state(f)
        self.assertEqual((state, reason), ("done", "evaluated: " + worker.LUNA_V11_ARM))
        self.assertEqual(set(json.loads(receipts)),
                         {str(Path(p).resolve()) for p in (sel["v11_output"], sel["v11_output"] + ".provenance.json", sel["v11_binding"])})
        self.assertEqual(json.loads(Path(sel["v11_binding"]).read_text())["evaluator_arm"], worker.LUNA_V11_ARM)
        self.assertEqual(self.v1_snapshot(f), v1)
        self.assertEqual(self.state(f, f"{LABEL}/synthesis")[0], "pending")
        worker.synthesis(f.c, f.phase, False)
        self.assertFalse(INEL.coverage_path(f.phase).exists())
        worker.ready(f.c, f.phase, False)
        self.assertEqual(json.loads((f.phase / "ANALYSIS_READY.json").read_text())["bv1"], 125)
        worker.ready(f.c, f.phase, True)
        with self.assertRaises(AssertionError):  # already applied
            self.lane(f)

    def test_refuses_punctuated_source(self):
        f = self.make(unpunctuated_x=False)
        with self.assertRaisesRegex(AssertionError, "punctuated"):
            self.lane(f, check_only=True)

    def test_ineligible_task_needs_explicit_supersession(self):
        f = self.make()
        f.apply()  # bv1-ineligibility-v1, as Qwen MID_15 on 2026-10-08
        receipt = INEL.receipt_path(f.phase, "X_1")
        self.assertEqual(worker.bv1(f.c, f.phase, "X_1", True).get("ineligible"), True)
        with self.assertRaisesRegex(AssertionError, "supersede"):
            self.lane(f, check_only=True)
        [sel] = self.lane(f, check_only=True, supersede=True)
        self.assertEqual(sel["supersedes_ineligibility_receipt"], str(receipt))
        self.assertTrue(receipt.exists())
        [sel] = self.lane(f, supersede=True)
        self.assertFalse(receipt.exists())
        aside = Path(sel["superseded"]["receipt"])
        self.assertTrue(aside.exists() and aside.parent.name == "bv1_ineligible_superseded")
        self.assertEqual(worker.bv1(f.c, f.phase, "X_1", True)["evaluator_arm"], worker.LUNA_V11_ARM)

    # Mira empoaj: the supersession must be failure-safe and retryable.
    def attempts(self, f):
        d = Path(LANE.INEL.attempt_dir(worker.bv1_paths(f.c, f.phase, worker.LUNA_V11_ARM)[0], f.c, "X_1"))
        return sorted(json.loads(p.read_text())["qa_pass"] for p in d.glob("*.json")) if d.exists() else []

    def assert_still_ineligible(self, f, receipt, receipt_sha):
        self.assertTrue(receipt.exists())
        self.assertEqual(digest(receipt), receipt_sha)
        self.assertEqual(self.state(f)[:2], ("done", INEL.APPLIED_REASON))
        self.assertFalse(any((f.phase / "bv1_ineligible_superseded").glob("*")) if (f.phase / "bv1_ineligible_superseded").exists() else False)
        self.assertEqual(f.engine.db.execute("SELECT count(*) FROM events WHERE event='luna_v1_1_applied'").fetchone()[0], 0)
        self.assertTrue(worker.bv1(f.c, f.phase, "X_1", True).get("ineligible"))

    def test_supersession_survives_evaluator_failure_and_retries(self):
        f = self.make()
        f.apply()
        receipt = INEL.receipt_path(f.phase, "X_1"); sha = digest(receipt)
        (f.phase / "FAIL_NEXT_CALL").write_text("")
        with self.assertRaisesRegex(RuntimeError, "injected evaluator failure"):
            self.lane(f, supersede=True)
        self.assert_still_ineligible(f, receipt, sha)
        self.assertEqual(self.attempts(f), [False])  # the failed v1.1 attempt is kept
        [sel] = self.lane(f, supersede=True)  # same command, retried
        self.assertFalse(receipt.exists())
        self.assertEqual(sel["superseded"]["receipt_sha256"], sha)
        self.assertEqual(digest(sel["superseded"]["receipt"]), sha)
        self.assertEqual(self.state(f)[:2], ("done", "evaluated: " + worker.LUNA_V11_ARM))
        self.assertEqual(self.attempts(f), [False, True])

    def test_supersession_survives_commit_failure_and_retries_without_a_second_call(self):
        f = self.make()
        f.apply()
        receipt = INEL.receipt_path(f.phase, "X_1"); sha = digest(receipt)
        real = LANE.time
        class Boom:
            time_ns = staticmethod(real.time_ns)
            @staticmethod
            def time():
                raise OSError("injected failure inside the commit")
        LANE.time = Boom
        try:
            with self.assertRaisesRegex(OSError, "inside the commit"):
                self.lane(f, supersede=True)
        finally:
            LANE.time = real
        self.assert_still_ineligible(f, receipt, sha)
        self.assertEqual(self.attempts(f), [True])  # evaluated, not yet recorded
        [sel] = self.lane(f, check_only=True, supersede=True)
        self.assertTrue(sel["v11_output_exists"])
        [sel] = self.lane(f, supersede=True)
        self.assertEqual(self.attempts(f), [True])  # reused via provenance: no second call
        self.assertFalse(receipt.exists())
        self.assertEqual(self.state(f)[:2], ("done", "evaluated: " + worker.LUNA_V11_ARM))

    def test_blocked_task_retries_after_evaluator_failure(self):
        f = self.make()
        (f.phase / "FAIL_NEXT_CALL").write_text("")
        with self.assertRaises(RuntimeError):
            self.lane(f)
        self.assertEqual(self.state(f)[:2], ("blocked", "exit 1; attempt 4/4"))
        self.lane(f)
        self.assertEqual(self.state(f)[0], "done")
        self.assertEqual(self.attempts(f), [False, True])

    def test_dedicated_analysis_worktree(self):
        import shutil
        f = self.make()
        alt = Path(self.td.name) / "mpac-worktree"
        shutil.copytree(f.root, alt)
        [sel] = self.lane(f, check_only=True, analysis_root=alt)
        self.assertTrue(sel["v11_output"].startswith(str(alt) + "/"))
        self.assertTrue(sel["v11_binding"].startswith(str(alt / "phase") + "/"))
        self.assertEqual(sel["v1_records"]["attempts"]["files"], 4)
        [sel] = self.lane(f, analysis_root=alt)
        self.assertTrue(Path(sel["v11_output"]).exists())
        self.assertFalse(worker.bv1_paths(f.c, f.phase, worker.LUNA_V11_ARM)[1].exists())  # shared root untouched


if __name__ == "__main__":
    unittest.main()
