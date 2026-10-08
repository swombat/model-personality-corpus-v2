"""Offline apply -> synthesis -> ready -> ready-validation for bv1-ineligibility-v1.

Real engine database, apply helper, worker bv1/synthesis/ready. Stubbed: the
BV1 evaluator modules (no API), the values stages, and the aggregation scripts
(they only record what they were given). No network.
"""
import json, sqlite3, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ineligibility as INEL
import worker
from engine import Engine, atomic, digest
from apply_ineligibility import apply

SIDS = ["S_1", "S_2", "X_1"]
LABEL, SLUG, PREFIX = "m-or-pin-x", "m", "CAP_run_m"
UNPUNCTUATED = "\n".join(f"Line {i} walks quietly through the morning air" for i in range(10))
EVAL_STUB = """EXTRA = 'instruction v1'
OUT = OUTPUTS = None
def valid_output(text, source=None):
    return (text.startswith('## ok'), '')
def process(*a, **k):
    raise RuntimeError('no API in tests')
"""
PACKETS_STUB = """import csv, json
def main():
    rows = list(csv.DictReader(open(MANIFEST), delimiter='\\t'))
    (PHASE / 'packets_seen.json').write_text(json.dumps({'pids': [r['pid'] for r in rows], 'coverage': COVERAGE}))
"""
ASSEMBLE_STUB = """def main():
    for folder, leaf in [('personality-model-cards', 'cards'), ('personality-model-profiles', 'profiles')]:
        p = ROOT / 'analysis/freeflow' / folder / leaf / 'm.md'
        p.parent.mkdir(parents=True, exist_ok=True)
        note = COVERAGE['disclosure'] if COVERAGE else 'Based on 125 freeflow samples.'
        p.write_text(note + ' ' + 'word ' * 60)
"""


class Flow:
    def __init__(self, td, unpunctuated_x=True, evaluated_x=False):
        t = Path(td)
        self.run = t / "run"
        self.root = t / "mpac"
        self.phase = self.root / "phase"
        self.phase.mkdir(parents=True)
        bv = self.root / "analysis/freeflow/personality-eval-bv1"
        (bv).mkdir(parents=True)
        (bv / "run_full_bv1.py").write_text(EVAL_STUB)
        (bv / "luna_v1.py").write_text(EVAL_STUB)
        base = self.root / "analysis/values-probe/model-coding/layered/phase35_union_alpha_20260917"
        base.mkdir(parents=True)
        (base / "build_aggregate_packets.py").write_text(PACKETS_STUB)
        (base / "assemble_models.py").write_text(ASSEMBLE_STUB)
        self.config = self.run / "models" / f"{LABEL}.json"
        self.c = dict(
            label=LABEL, slug=SLUG, id_prefix=PREFIX, model="v/m",
            bv1_evaluator=INEL.LUNA_ARM, analysis_root=str(self.root),
            phase=str(self.phase), token_policy={},
        )
        atomic(self.config, self.c)
        self.c["_config"] = str(self.config.resolve())
        traces = t / "traces"
        for sid in SIDS:
            text = UNPUNCTUATED if (sid == "X_1" and unpunctuated_x) else f"Sample {sid}. It has sentences."
            atomic(traces / "freeflow" / f"{sid}.json", {"result": text, "condition": sid.split("_")[0]})
        atomic(traces / "values" / "V_1.json", {"result": "v"})
        self.traces = traces
        self.bv_out, self.outputs, self.bindings = worker.bv1_paths(self.c, self.phase)
        for sid in SIDS:
            if sid == "X_1" and not evaluated_x:
                continue
            out = self.outputs / LABEL / f"{sid}.md"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("## ok evaluation\n")
            atomic(self.bindings / f"{sid}.json", {
                "source_sha256": digest(traces / "freeflow" / f"{sid}.json"),
                "output_sha256": digest(out), "evaluator_arm": INEL.LUNA_ARM})
        if not evaluated_x:
            d = INEL.attempt_dir(self.bv_out, self.c, "X_1")
            d.mkdir(parents=True)
            for i in range(4):
                atomic(d / f"{100 + i}.json", {
                    "arm": INEL.LUNA_ARM, "qa_pass": False, "qa_reason": INEL.QA_REASON,
                    "source_sha256": digest(traces / "freeflow" / "X_1.json")})
        atomic(self.phase / "adjudication.json", {})
        task = lambda id, sid=None, deps=(): dict(
            id=id, deps=list(deps), pool="p", outputs=[str(self.outputs / LABEL / f"{sid or 'x'}.md")],
            command=["py", "worker.py", str(self.config), "bv1", "--sample", sid] if sid else ["py", "worker.py", str(self.config), id.split("/")[-1]],
            validate=["py", "-c", "pass"], max_attempts=4, timeout=3)
        bv1_ids = [f"{LABEL}/bv1/{s}" for s in SIDS]
        self.spec = dict(pools={"p": 1}, tasks=[task(i, s) for i, s in zip(bv1_ids, SIDS)]
                         + [task(f"{LABEL}/synthesis", deps=bv1_ids), task(f"{LABEL}/ready", deps=[f"{LABEL}/synthesis"])])
        atomic(self.run / "spec.json", self.spec)
        self.engine = Engine(self.spec, self.run / "state")
        db = self.engine.db
        for i in bv1_ids:
            if i.endswith("X_1") and not evaluated_x:
                db.execute("UPDATE jobs SET state='blocked',attempts=4,reason='exit 1; attempt 4/4' WHERE id=?", (i,))
                for n in range(4):
                    db.execute("INSERT INTO events VALUES(?,?,?,?)", (n, i, "started", str(n + 1)))
            else:
                db.execute("UPDATE jobs SET state='done',attempts=1 WHERE id=?", (i,))
        for i in (f"{LABEL}/synthesis", f"{LABEL}/ready"):
            db.execute("UPDATE jobs SET state='blocked',reason='dependency blocked' WHERE id=?", (i,))
        db.commit()
        self.patched = {}
        for name, value in dict(
            identities=lambda probe: SIDS if probe == "freeflow" else ["V_1"],
            trace_path=lambda c, probe, sid: self.traces / probe / f"{sid}.json",
            raw_problem=lambda *a: None,
            integrate_values=lambda *a, **k: None, card_ready=lambda *a, **k: None,
            assemble_values=lambda *a, **k: None, adjudicate=lambda *a, **k: None,
            values_report=lambda *a, **k: None,
        ).items():
            self.patched[name] = getattr(worker, name)
            setattr(worker, name, value)

    def close(self):
        for name, value in self.patched.items():
            setattr(worker, name, value)
        self.engine.db.close()
        self.engine.lock.close()

    def sql(self, q, args=()):
        self.engine.db.execute(q, args)
        self.engine.db.commit()

    def apply(self):
        apply(self.run / "spec.json", self.run / "state", [f"{LABEL}/bv1/X_1"], "BjZoXJ:test")


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.flow.close()
        self.td.cleanup()

    def test_apply_synthesis_ready_validate(self):
        f = self.flow = Flow(self.td.name)
        with self.assertRaises(AssertionError):  # no output, no receipt
            worker.synthesis(f.c, f.phase, False)
        # A receipt placed without application (or before an interrupted commit) is refused.
        manual = INEL.receipt_path(f.phase, "X_1")
        atomic(manual, dict(INEL.facts(f.c, "X_1", f.traces / "freeflow/X_1.json", f.bv_out,
                                       worker.module("t_luna", f.root / "analysis/freeflow/personality-eval-bv1/luna_v1.py")),
                            reviewer="forged"))
        with self.assertRaisesRegex(AssertionError, "not applied"):
            worker.synthesis(f.c, f.phase, False)
        manual.unlink()
        f.apply()
        rows = {r["id"]: r["state"] for r in f.engine.db.execute("SELECT id,state FROM jobs")}
        self.assertEqual(rows[f"{LABEL}/bv1/X_1"], "done")
        self.assertEqual(rows[f"{LABEL}/synthesis"], "pending")
        worker.synthesis(f.c, f.phase, False)
        cov = json.loads(INEL.coverage_path(f.phase).read_text())
        self.assertEqual((cov["expected"], cov["evaluated"]), (3, 2))
        seen = json.loads((f.phase / "packets_seen.json").read_text())
        self.assertEqual(len(seen["pids"]), 2)
        self.assertEqual(seen["coverage"], cov)
        worker.ready(f.c, f.phase, False)
        record = json.loads((f.phase / "ANALYSIS_READY.json").read_text())
        self.assertEqual(record["bv1"], 2)
        self.assertEqual(record["bv1_expected"], 3)
        self.assertEqual([i["sample"] for i in record["bv1_ineligible"]], ["X_1"])
        worker.ready(f.c, f.phase, True)
        # Altered ready record fails validation.
        path = f.phase / "ANALYSIS_READY.json"
        good = path.read_text()
        atomic(path, dict(record, bv1=999))
        with self.assertRaisesRegex(AssertionError, "BV1 counts differ"):
            worker.ready(f.c, f.phase, True)
        path.write_text(good)
        # Altered coverage record fails validation.
        cpath = INEL.coverage_path(f.phase)
        cgood = cpath.read_text()
        cpath.write_text("{}")
        with self.assertRaisesRegex(AssertionError, "coverage record"):
            worker.ready(f.c, f.phase, True)
        cpath.write_text(cgood)
        worker.ready(f.c, f.phase, True)
        # History changed after application.
        task = f"{LABEL}/bv1/X_1"
        f.sql("UPDATE jobs SET state='pending' WHERE id=?", (task,))
        with self.assertRaisesRegex(AssertionError, "not applied"):
            worker.ready(f.c, f.phase, True)
        f.sql("UPDATE jobs SET state='done' WHERE id=?", (task,))
        f.sql("UPDATE jobs SET attempts=999 WHERE id=?", (task,))
        with self.assertRaisesRegex(AssertionError, "history changed"):
            worker.ready(f.c, f.phase, True)
        f.sql("UPDATE jobs SET attempts=4 WHERE id=?", (task,))
        f.sql("DELETE FROM events WHERE id=? AND event='started' AND at=0", (task,))
        with self.assertRaisesRegex(AssertionError, "history changed"):
            worker.ready(f.c, f.phase, True)
        f.sql("INSERT INTO events VALUES(0,?,'started','1')", (task,))
        worker.ready(f.c, f.phase, True)
        f.sql("DELETE FROM events WHERE id=? AND event='ineligible_applied'", (task,))
        with self.assertRaisesRegex(AssertionError, "exactly one ineligible_applied"):
            worker.ready(f.c, f.phase, True)

    def test_apply_refuses_eligible_source(self):
        f = self.flow = Flow(self.td.name, unpunctuated_x=False)
        with self.assertRaisesRegex(AssertionError, "eligible sentence"):
            f.apply()
        self.assertFalse(INEL.receipt_path(f.phase, "X_1").exists())

    def test_complete_run_unchanged(self):
        f = self.flow = Flow(self.td.name, evaluated_x=True)
        worker.synthesis(f.c, f.phase, False)
        self.assertFalse(INEL.coverage_path(f.phase).exists())
        seen = json.loads((f.phase / "packets_seen.json").read_text())
        self.assertIsNone(seen["coverage"])
        self.assertEqual(len(seen["pids"]), 3)
        worker.ready(f.c, f.phase, False)
        record = json.loads((f.phase / "ANALYSIS_READY.json").read_text())
        self.assertEqual(record["bv1"], 125)
        self.assertNotIn("bv1_expected", record)
        self.assertNotIn("bv1_ineligible", record)
        worker.ready(f.c, f.phase, True)
        atomic(INEL.coverage_path(f.phase), {"stale": True})
        with self.assertRaisesRegex(AssertionError, "complete run"):
            worker.ready(f.c, f.phase, True)


if __name__ == "__main__":
    unittest.main()
