"""Offline BV1-Luna v1 targeted repair: task-only routing, own arm, provenance,
authorised allowance (Mira YoAWMj). Same fixture as test_ineligibility_flow,
with X_1 punctuated and blocked after 4 v1 attempts."""
import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ineligibility as INEL
import worker
from apply_luna_v1_1 import tree_fingerprint
from test_ineligibility_flow import Flow, LABEL
import apply_bv1_targeted as LANE

STUB = """import json
from pathlib import Path
ARM = 'bv1-luna-v1-targeted-20261016'
def valid_output(text, source=None):
    return (text.startswith('## ok targeted'), '')
def provenance_ok(out, row):
    p = Path(str(out) + '.provenance.json')
    return p.exists() and json.loads(p.read_text())['arm'] == ARM
def process(row, outdir):
    out = Path(row['outpath']); out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():  # mirrors luna_v1_targeted.process
        if provenance_ok(out, row):
            return
        raise RuntimeError('exists without provenance')
    d = Path(outdir) / 'attempt_responses' / row['pid']; d.mkdir(parents=True, exist_ok=True)
    n = len(list(d.glob('*.json'))) + 1
    calls = Path(outdir).parent / 'TARGETED_CALLS'
    calls.write_text(str(int(calls.read_text()) + 1 if calls.exists() else 1))
    fails = Path(outdir).parent / 'FAIL_CALLS'
    if fails.exists() and int(fails.read_text()) > 0:
        fails.write_text(str(int(fails.read_text()) - 1))
        (d / f'{n}.json').write_text(json.dumps({'arm': ARM, 'qa_pass': False}))
        raise RuntimeError('injected evaluator failure')
    (d / f'{n}.json').write_text(json.dumps({'arm': ARM, 'qa_pass': True}))
    out.write_text('## ok targeted evaluation\\n')
    Path(str(out) + '.provenance.json').write_text(json.dumps({'arm': ARM}))
"""
TASK = f"{LABEL}/bv1/X_1"
AUTH = "mira-test-targeted"


class TargetedLaneTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.flow = None

    def tearDown(self):
        if self.flow:
            self.flow.close()
        self.td.cleanup()

    def make(self, **kw):
        kw.setdefault("unpunctuated_x", False)
        f = self.flow = Flow(self.td.name, **kw)
        (f.root / "analysis/freeflow/personality-eval-bv1/luna_v1_targeted.py").write_text(STUB)
        return f

    def lane(self, f, auth=AUTH, **kw):
        return LANE.apply(f.run / "spec.json", f.run / "state", [TASK], auth, **kw)

    def state(self, f, id=TASK):
        return f.engine.db.execute("SELECT state,reason,receipts FROM jobs WHERE id=?", (id,)).fetchone()

    def v1(self, f):
        return tree_fingerprint(INEL.attempt_dir(worker.bv1_paths(f.c, f.phase, worker.LUNA_ARM)[0], f.c, "X_1"))

    def phase_file(self, f, name):
        return worker.bv1_paths(f.c, f.phase, worker.LUNA_TARGETED_ARM)[0].parent / name

    def calls(self, f):
        p = self.phase_file(f, "TARGETED_CALLS")
        return int(p.read_text()) if p.exists() else 0

    def events(self, f, kind):
        return [json.loads(e[0]) for e in f.engine.db.execute(
            "SELECT details FROM events WHERE id=? AND event=? ORDER BY rowid", (TASK, kind))]

    def test_dag_never_routes_to_the_variant(self):
        f = self.make()
        # Unbound, the blocked punctuated sample is still a v1 task (normal QA failure path).
        with self.assertRaises(Exception):
            worker.bv1(f.c, f.phase, "X_1", True)
        self.assertFalse(worker.bv1_paths(f.c, f.phase, worker.LUNA_TARGETED_ARM)[1].exists())
        self.assertEqual(self.calls(f), 0)

    def test_check_is_a_dry_run(self):
        f = self.make()
        before = (self.state(f), self.v1(f))
        [sel] = self.lane(f, check_only=True)
        self.assertEqual(sel["arm"], worker.LUNA_TARGETED_ARM)
        self.assertIn("/arms/" + worker.LUNA_TARGETED_ARM + "/outputs/", sel["output"])
        self.assertIn("freeflow_bv1_luna_v1_targeted", sel["attempts"])
        self.assertIn("bv1_bindings_luna_v1_targeted", sel["binding"])
        self.assertEqual((sel["used"], sel["allowance"]), (0, 2))
        self.assertEqual(sel["v1_attempts"]["files"], 4)
        self.assertEqual((self.state(f), self.v1(f)), before)
        self.assertIsNone(f.engine.db.execute("SELECT 1 FROM sqlite_master WHERE name='targeted_repairs'").fetchone())
        self.assertEqual(self.calls(f), 0)

    def test_apply_marks_variant_everywhere_and_keeps_v1(self):
        f = self.make()
        v1 = self.v1(f)
        [sel] = self.lane(f)
        state, reason, receipts = self.state(f)
        self.assertEqual(state, "done")
        self.assertEqual(reason, f"evaluated: {worker.LUNA_TARGETED_ARM} (authorised repair {AUTH}, attempt 1/2)")
        self.assertEqual(set(json.loads(receipts)),
                         {str(Path(p).resolve()) for p in (sel["output"], sel["output"] + ".provenance.json", sel["binding"])})
        self.assertEqual(json.loads(Path(sel["binding"]).read_text())["evaluator_arm"], worker.LUNA_TARGETED_ARM)
        self.assertEqual(self.v1(f), v1)
        self.assertEqual(self.calls(f), 1)
        self.assertEqual([e["attempt"] for e in self.events(f, "bv1_targeted_repair_applied")], [1])
        # Afterwards the sample routes to the variant on its own, and only it does.
        self.assertEqual(worker.bv1(f.c, f.phase, "X_1", True)["evaluator_arm"], worker.LUNA_TARGETED_ARM)
        self.assertEqual(worker.bv1(f.c, f.phase, "S_1", True)["evaluator_arm"], worker.LUNA_ARM)
        with self.assertRaises(SystemExit) as e:  # the DAG still never generates it
            worker.bv1(f.c, f.phase, "X_1")
        self.assertEqual(e.exception.code, 21)
        # Release record names the variant sample.
        self.assertEqual(self.state(f, f"{LABEL}/synthesis")[0], "pending")
        worker.synthesis(f.c, f.phase, False)
        worker.ready(f.c, f.phase, False)
        record = json.loads((f.phase / "ANALYSIS_READY.json").read_text())
        self.assertEqual((record["bv1"], record["bv1_variant_arms"]), (125, {"X_1": worker.LUNA_TARGETED_ARM}))
        worker.ready(f.c, f.phase, True)
        with self.assertRaises(AssertionError):  # already applied
            self.lane(f)

    def test_stops_at_first_valid_result_and_charges_failures(self):
        f = self.make()
        self.phase_file(f, "FAIL_CALLS").write_text("1")
        [sel] = self.lane(f)
        self.assertTrue(sel["applied"])
        self.assertEqual((sel["used"], self.calls(f)), (2, 2))
        self.assertIn("attempt 2/2", self.state(f)[1])
        self.assertEqual(len(list(Path(sel["attempts"]).glob("*.json"))), 2)  # failed attempt kept

    def test_exhausted_allowance_leaves_task_blocked_and_cannot_be_refilled(self):
        f = self.make()
        self.phase_file(f, "FAIL_CALLS").write_text("5")
        before = self.state(f)
        [sel] = self.lane(f)
        self.assertFalse(sel["applied"])
        self.assertEqual(self.state(f), before)
        self.assertEqual(self.calls(f), 2)
        self.assertEqual(len(self.events(f, "bv1_targeted_repair_finished")), 2)
        [again] = self.lane(f)  # restart: same authorization, no refill
        self.assertFalse(again["applied"])
        self.assertEqual(self.calls(f), 2)
        with self.assertRaises(AssertionError):  # a different limit cannot widen it either
            self.lane(f, limit=3)
        self.assertFalse(Path(sel["output"]).exists())
        self.assertFalse(Path(sel["binding"]).exists())

    def inject_commit_failure(self, f):
        f.sql("CREATE TRIGGER fail_done BEFORE UPDATE ON jobs WHEN NEW.state='done' "
              "BEGIN SELECT RAISE(ABORT, 'injected commit failure'); END")

    def test_final_allowed_attempt_survives_commit_failure(self):
        # Mira YkpxzJ: attempt 1 fails QA, attempt 2 (the last allowed) is valid,
        # the job transaction fails. A retry finalizes it: no call, no charge.
        f = self.make()
        v1 = self.v1(f)
        self.phase_file(f, "FAIL_CALLS").write_text("1")
        self.inject_commit_failure(f)
        with self.assertRaises(Exception):
            self.lane(f)
        state, reason, _ = self.state(f)
        self.assertEqual(state, "blocked")
        self.assertEqual(self.calls(f), 2)
        self.assertEqual(f.engine.db.execute("SELECT used FROM targeted_repairs").fetchone()[0], 2)
        out = Path(worker.bv1_paths(f.c, f.phase, worker.LUNA_TARGETED_ARM)[1] / LABEL / "X_1.md")
        self.assertTrue(out.exists())
        self.assertEqual(self.events(f, "bv1_targeted_repair_applied"), [])
        f.sql("DROP TRIGGER fail_done")
        [sel] = self.lane(f)
        self.assertTrue(sel["applied"])
        self.assertEqual(self.calls(f), 2)  # no further call
        self.assertEqual(f.engine.db.execute("SELECT used FROM targeted_repairs").fetchone()[0], 2)  # no charge
        state, reason, _ = self.state(f)
        self.assertEqual(state, "done")
        self.assertIn(f"authorised repair {AUTH}, attempt 2/2", reason)  # original attribution
        self.assertEqual([e["attempt"] for e in self.events(f, "bv1_targeted_repair_applied")], [2])
        self.assertEqual(len(list(Path(sel["attempts"]).glob("*.json"))), 2)
        self.assertEqual(self.v1(f), v1)
        self.assertEqual(self.state(f, f"{LABEL}/synthesis")[0], "pending")

    def test_first_attempt_commit_failure_retry_does_not_call_again(self):
        f = self.make()
        self.inject_commit_failure(f)
        with self.assertRaises(Exception):
            self.lane(f)
        f.sql("DROP TRIGGER fail_done")
        [sel] = self.lane(f)
        self.assertTrue(sel["applied"])
        self.assertEqual(self.calls(f), 1)
        self.assertEqual(f.engine.db.execute("SELECT used FROM targeted_repairs").fetchone()[0], 1)
        self.assertIn("attempt 1/2", self.state(f)[1])

    def test_unprovenanced_output_is_never_finalized(self):
        f = self.make()
        out = Path(worker.bv1_paths(f.c, f.phase, worker.LUNA_TARGETED_ARM)[1] / LABEL / "X_1.md")
        out.parent.mkdir(parents=True)
        out.write_text("## ok targeted evaluation\n")  # no provenance sidecar
        with self.assertRaises(Exception):
            self.lane(f)
        self.assertEqual(self.state(f)[0], "blocked")
        self.assertEqual(self.calls(f), 0)

    def test_refuses_unpunctuated_source(self):
        f = self.make(unpunctuated_x=True)
        with self.assertRaisesRegex(AssertionError, "v1.1"):
            self.lane(f)
        self.assertEqual(self.calls(f), 0)

    def test_config_drift_is_rejected_before_any_work(self):
        import hashlib
        f = self.make()
        spec = json.loads((f.run / "spec.json").read_text())
        spec["input_hashes"] = {str(f.config): digest(f.config)}
        (f.run / "spec.json").write_text(json.dumps(spec))
        f.sql("UPDATE meta SET v=? WHERE k='spec'", (hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),))
        self.lane(f, check_only=True)  # unchanged inputs pass
        c = json.loads(f.config.read_text())
        c["model"] = "review/MODIFIED-CONFIG"
        f.config.write_text(json.dumps(c))
        with self.assertRaisesRegex(AssertionError, "input changed"):
            self.lane(f)
        self.assertEqual((self.state(f)[0], self.calls(f)), ("blocked", 0))
        self.assertIsNone(f.engine.db.execute("SELECT 1 FROM sqlite_master WHERE name='targeted_repairs'").fetchone())

    def test_unbound_output_fails_closed_without_a_call(self):
        f = self.make()
        out = Path(worker.bv1_paths(f.c, f.phase, worker.LUNA_TARGETED_ARM)[1] / LABEL / "X_1.md")
        out.parent.mkdir(parents=True)
        out.write_text("## ok targeted evaluation\n")
        Path(str(out) + ".provenance.json").write_text(json.dumps({"arm": worker.LUNA_TARGETED_ARM}))
        with self.assertRaisesRegex(AssertionError, "binding missing"):
            self.lane(f)
        self.assertEqual((self.state(f)[0], self.calls(f)), ("blocked", 0))
        self.assertTrue(out.exists())  # not archived, not replaced

    def test_refuses_task_with_v1_evaluation(self):
        f = self.make(evaluated_x=True)
        with self.assertRaises(AssertionError):
            self.lane(f)
        self.assertEqual(self.calls(f), 0)

    def test_refuses_dependency_blocked_task(self):
        f = self.make()
        f.engine.db.execute("UPDATE jobs SET reason='dependency blocked' WHERE id=?", (TASK,))
        f.engine.db.commit()
        with self.assertRaisesRegex(AssertionError, "blocked roots"):
            self.lane(f)


if __name__ == "__main__":
    unittest.main()
