"""Offline: synthesis/ready run against a dedicated analysis worktree, with the
spec and the shared checkout untouched (Mira jlpobj/YvvmNY)."""
import json, shutil, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import worker
from engine import digest
from test_ineligibility_flow import Flow, LABEL
import run_with_analysis_root as LANE

SYN, READY = f"{LABEL}/synthesis", f"{LABEL}/ready"
CORPUS = Path(__file__).resolve().parents[3]


class AnalysisRootLaneTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        f = self.f = Flow(self.td.name, evaluated_x=True)
        f.sql("UPDATE jobs SET state='pending',reason=NULL WHERE id IN (?,?)", (SYN, READY))
        self.wt = Path(self.td.name) / "mpac-wt"
        shutil.copytree(f.root, self.wt)
        self.wphase = self.wt / f.phase.relative_to(f.root)
        # The fixture's placeholder spec outputs, present in the worktree only.
        for t in f.spec["tasks"]:
            if t["id"] in (SYN, READY):
                for p in t["outputs"]:
                    q = self.wt / Path(p).relative_to(f.root)
                    q.parent.mkdir(parents=True, exist_ok=True)
                    q.write_text("placeholder " + t["id"])
        self.spec_bytes = (f.run / "spec.json").read_bytes()
        self.shared = sorted(str(p.relative_to(f.root)) for p in f.root.rglob("*") if p.is_file())

    def tearDown(self):
        self.f.close()
        self.td.cleanup()

    def lane(self, ids, **kw):
        return LANE.apply(self.f.run / "spec.json", self.f.run / "state", ids, "YvvmNY:test", self.wt, CORPUS, **kw)

    def state(self, id):
        return self.f.engine.db.execute("SELECT state,reason,receipts FROM jobs WHERE id=?", (id,)).fetchone()

    def assert_shared_untouched(self):
        self.assertEqual(sorted(str(p.relative_to(self.f.root)) for p in self.f.root.rglob("*") if p.is_file()), self.shared)
        self.assertEqual((self.f.run / "spec.json").read_bytes(), self.spec_bytes)

    def test_check_is_a_dry_run(self):
        before = (self.state(SYN), self.state(READY))
        [s, r] = self.lane([SYN, READY], check_only=True)
        self.assertEqual((s["action"], r["action"]), ("synthesis", "ready"))
        self.assertTrue(s["deps_done"])
        self.assertFalse(r["deps_done"])
        self.assertTrue(all(o.startswith(str(self.wt)) for o in s["outputs"] + r["outputs"]))
        self.assertEqual((self.state(SYN), self.state(READY)), before)
        self.assertFalse((self.wphase / "ANALYSIS_READY.json").exists())
        self.assert_shared_untouched()

    def test_runs_in_the_worktree_only(self):
        raw = worker.RAW
        self.lane([SYN, READY])
        self.assertIs(worker.RAW, raw)  # restored
        for id in (SYN, READY):
            state, reason, receipts = self.state(id)
            self.assertEqual(state, "done")
            self.assertIn(str(self.wt.resolve()), reason)
            for p, h in json.loads(receipts).items():
                self.assertTrue(p.startswith(str(self.wt.resolve())))
                self.assertEqual(digest(p), h)
        self.assertTrue((self.wt / "analysis/freeflow/personality-model-cards/cards/m.md").exists())
        self.assertTrue((self.wphase / "ANALYSIS_READY.json").exists())
        self.assertFalse((self.f.root / "analysis/freeflow/personality-model-cards").exists())
        self.assertFalse((self.f.phase / "ANALYSIS_READY.json").exists())
        self.assert_shared_untouched()
        events = self.f.engine.db.execute("SELECT id FROM events WHERE event='analysis_root_lane_done'").fetchall()
        self.assertEqual(sorted(e[0] for e in events), [READY, SYN])
        with self.assertRaisesRegex(AssertionError, "not pending"):  # already done
            self.lane([SYN])

    def test_refuses_task_whose_dependency_is_not_done(self):
        with self.assertRaisesRegex(AssertionError, "dependency"):
            self.lane([READY])
        self.assertEqual(self.state(READY)[0], "pending")
        self.assert_shared_untouched()

    def test_refuses_other_tasks(self):
        with self.assertRaisesRegex(AssertionError, "synthesis/ready"):
            self.lane([f"{LABEL}/bv1/S_1"])

    def test_refuses_the_configs_own_root(self):
        with self.assertRaisesRegex(AssertionError, "already the config"):
            LANE.apply(self.f.run / "spec.json", self.f.run / "state", [SYN], "t", self.f.root, CORPUS)

    def test_config_drift_is_rejected_before_any_work(self):
        # Mira ezrPbe: a compiled spec carries input_hashes (the model config among
        # them); a changed config must stop the lane before generation.
        import hashlib
        f = self.f
        spec = json.loads((f.run / "spec.json").read_text())
        spec["input_hashes"] = {str(f.config): digest(f.config)}
        (f.run / "spec.json").write_text(json.dumps(spec))
        f.sql("UPDATE meta SET v=? WHERE k='spec'",
              (hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest(),))
        self.lane([SYN], check_only=True)  # unchanged inputs pass
        c = json.loads(f.config.read_text())
        c["model"] = "review/MODIFIED-CONFIG"
        f.config.write_text(json.dumps(c))
        before = (self.state(SYN), sorted(p for p in self.wt.rglob("*") if p.is_file()))
        with self.assertRaisesRegex(AssertionError, "input changed"):
            self.lane([SYN])
        self.assertEqual((self.state(SYN), sorted(p for p in self.wt.rglob("*") if p.is_file())), before)
        self.assertFalse((self.wt / "analysis/freeflow/personality-model-cards").exists())
        self.assertEqual(f.engine.db.execute("SELECT COUNT(*) FROM events WHERE event='analysis_root_lane_done'").fetchone()[0], 0)

    def test_values_integration_checks_traces_under_the_lane_raw_root(self):
        # The values helper verifies traces against helper.RAW; the worker sets
        # it to its own raw root, which the lane points at --raw-root.
        helper = self.wt / "analysis/values-probe/final/scripts/integrate_capture_values.py"
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.write_text("RAW = None\n"
                          "def integrate(phases, validate=False):\n"
                          "    from pathlib import Path\n"
                          "    p = Path(phases[0]) / ('raw_seen_validate' if validate else 'raw_seen')\n"
                          "    p.write_text(str(RAW))\n")
        worker.integrate_values = self.f.patched["integrate_values"]  # the real one; Flow restores it
        raw = Path(self.td.name) / "held-corpus"
        (raw / "scripts/capture_harness").mkdir(parents=True)
        (raw / "data").mkdir()
        LANE.apply(self.f.run / "spec.json", self.f.run / "state", [SYN, READY], "t", self.wt, raw)
        self.assertEqual((self.wphase / "raw_seen").read_text(), str(raw.resolve()))
        self.assertEqual((self.wphase / "raw_seen_validate").read_text(), str(raw.resolve()))
        self.assertEqual(self.state(READY)[0], "done")
        self.assert_shared_untouched()


if __name__ == "__main__":
    unittest.main()
