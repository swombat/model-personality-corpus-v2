import json, sys, tempfile, time, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Engine
from build import build
from worker import raw_problem, prompts


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        self.engines = []

    def tearDown(self):
        for e in self.engines:
            e.db.close()
            e.lock.close()
        self.tmp.cleanup()

    def task(self, id, code=None, deps=(), model="m", attempts=2, timeout=5):
        out = self.p / (id + ".txt")
        return dict(
            id=id,
            model=model,
            pool="p",
            deps=list(deps),
            outputs=[str(out)],
            command=[
                sys.executable,
                "-c",
                code
                or f'from pathlib import Path;Path({str(out)!r}).write_text("valid")',
            ],
            validate=[
                sys.executable,
                "-c",
                f'from pathlib import Path;assert Path({str(out)!r}).read_text()=="valid"',
            ],
            timeout=timeout,
            max_attempts=attempts,
            backoff=0.01,
            backoff_max=0.01,
        )

    def engine(self, tasks, state="state"):
        e = Engine(dict(tasks=tasks, pools={"p": 2}, poll_seconds=0.01), self.p / state)
        self.engines.append(e)
        return e

    def drive(self, e, limit=10):
        end = time.monotonic() + limit
        while time.monotonic() < end:
            state = e.tick()
            if state in ("complete", "blocked"):
                return state
            time.sleep(0.015)
        self.fail("did not terminate")

    def test_streaming_dependencies(self):
        a = self.task("a")
        b = self.task("b", deps=["a"])
        slow = self.task(
            "slow",
            f'import time;time.sleep(.8);from pathlib import Path;Path({str(self.p / "slow.txt")!r}).write_text("valid")',
            model="other",
        )
        e = self.engine([a, slow, b])
        self.assertEqual(self.drive(e), "complete")
        rows = e.db.execute("SELECT id,at FROM events WHERE event='done'").fetchall()
        times = dict(rows)
        self.assertLess(times["b"], times["slow"])

    def test_zero_exit_is_not_completion(self):
        t = self.task(
            "bad",
            f'from pathlib import Path;Path({str(self.p / "bad.txt")!r}).write_text("invalid")',
        )
        e = self.engine(
            [t, self.task("dependent", deps=["bad"]), self.task("other", model="other")]
        )
        self.assertEqual(self.drive(e), "blocked")
        rows = {r["id"]: dict(r) for r in e.db.execute("SELECT * FROM jobs")}
        self.assertEqual(rows["bad"]["attempts"], 2)
        self.assertEqual(rows["other"]["state"], "done")
        self.assertEqual(rows["dependent"]["attempts"], 0)

    def test_retry_then_success(self):
        code = f'import os;from pathlib import Path;p=Path({str(self.p / "a.txt")!r});p.write_text("valid" if os.environ["CAPTURE_ATTEMPT"]=="2" else "invalid")'
        e = self.engine([self.task("a", code)])
        self.assertEqual(self.drive(e), "complete")
        self.assertEqual(e.db.execute("SELECT attempts FROM jobs").fetchone()[0], 2)

    def test_hard_timeout(self):
        e = self.engine(
            [self.task("a", "import time;time.sleep(60)", attempts=1, timeout=0.15)]
        )
        self.assertEqual(self.drive(e), "blocked")

    def test_terminal_error_no_retry(self):
        e = self.engine([self.task("a", "raise SystemExit(20)", attempts=6)])
        self.assertEqual(self.drive(e), "blocked")
        self.assertEqual(e.db.execute("SELECT attempts FROM jobs").fetchone()[0], 1)

    def test_restart_preserves_success(self):
        tasks = [self.task("a")]
        e = self.engine(tasks)
        self.drive(e)
        e.db.close()
        e.lock.close()
        self.engines.remove(e)
        e = self.engine(tasks)
        self.assertEqual(self.drive(e), "complete")
        self.assertEqual(e.db.execute("SELECT attempts FROM jobs").fetchone()[0], 1)

    def test_tampered_artifact_blocks_descendants(self):
        tasks = [self.task("a"), self.task("b", deps=["a"])]
        e = self.engine(tasks)
        self.drive(e)
        e.db.close()
        e.lock.close()
        self.engines.remove(e)
        (self.p / "a.txt").write_text("tampered")
        e = self.engine(tasks)
        self.assertEqual(self.drive(e), "blocked")

    def test_single_supervisor(self):
        e = self.engine([self.task("a")])
        self.assertRaises(BlockingIOError, Engine, e.spec, self.p / "state")

    def test_cycle_rejected(self):
        self.assertRaises(
            ValueError,
            self.engine,
            [self.task("a", deps=["b"]), self.task("b", deps=["a"])],
        )

    def test_crash_recovery_keeps_attempt_count(self):
        e = self.engine([self.task("a")])
        e.db.execute("UPDATE jobs SET state='running',attempts=1,pid=999999")
        e.db.commit()
        e.recover()
        self.assertEqual(self.drive(e), "complete")
        self.assertEqual(e.db.execute("SELECT attempts FROM jobs").fetchone()[0], 2)

    def test_crash_exhausted_budget_escalates(self):
        e = self.engine([self.task("a", attempts=1)])
        e.db.execute("UPDATE jobs SET state='running',attempts=1")
        e.db.commit()
        e.recover()
        self.assertEqual(self.drive(e), "blocked")

    def test_builder_no_cross_model_barrier(self):
        models = [
            dict(
                provider="openrouter",
                model="x/" + s,
                or_provider="X",
                label=s,
                slug=s,
                family="x",
                route_max_tokens=32768,
                token_policy={"freeflow": [16000, 32768], "values": [4000, 8000]},
            )
            for s in ["one", "two"]
        ]
        spec = build(
            dict(run_id="test", models=models), self.p / "built", self.p / "analysis"
        )
        tasks = {t["id"]: t for t in spec["tasks"]}
        self.assertEqual(
            tasks["one/a/CTRL1_1/kimi-k2-6"]["deps"], ["one/values/CTRL1_1"]
        )
        self.assertTrue(
            all(d.startswith("one/") for d in tasks["one/synthesis"]["deps"])
        )
        self.assertEqual(len(tasks["one/synthesis"]["deps"]), 126)

    def test_strict_raw(self):
        c = {"model": "x/m", "or_provider": "X"}
        d = {
            "condition": "SHORT",
            "prompt": prompts("freeflow")["SHORT"],
            "result": "hello",
            "raw": {
                "model": "x/m",
                "provider": "X",
                "choices": [{"finish_reason": "stop", "message": {"content": "hello"}}],
            },
        }
        self.assertIsNone(raw_problem(d, c, "freeflow", "SHORT_1"))
        d["raw"]["choices"][0]["finish_reason"] = "length"
        self.assertEqual(raw_problem(d, c, "freeflow", "SHORT_1"), "finish_length")
        d["raw"]["choices"][0]["message"]["content"] = ""
        self.assertEqual(raw_problem(d, c, "freeflow", "SHORT_1"), "finish_length")


if __name__ == "__main__":
    unittest.main()


class WorkerSchemaTests(unittest.TestCase):
    def test_malformed_coder_output_not_accepted(self):
        from worker import coder_valid

        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "coder.jsonl"
            p.write_text(
                json.dumps(
                    {
                        "layered_id": "x",
                        "coder_key": "k",
                        "model": "m",
                        "condition": "G1",
                        "processing_chain": "stated_values",
                        "value_topics": "invalid",
                        "wish_topics": [],
                    }
                )
                + "\n"
            )
            with self.assertRaises(AssertionError):
                coder_valid(p, "x", "k")
