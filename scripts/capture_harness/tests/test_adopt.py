import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Engine, atomic, digest
from adopt_existing import adopt
from worker import prompts


class AdoptTests(unittest.TestCase):
    def exercise(self, finish="stop", running=False):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            config = p / "model.json"
            raw = p / "raw.json"
            specfile = p / "spec.json"
            state = p / "state"
            atomic(config, {"model": "vendor/model", "or_provider": "Vendor"})
            atomic(
                raw,
                {
                    "condition": "CTRL1",
                    "prompt": prompts("values")["CTRL1"],
                    "result": "Answer",
                    "raw": {
                        "provider": "Vendor",
                        "model": "vendor/model",
                        "choices": [
                            {"finish_reason": finish, "message": {"content": "Answer"}}
                        ],
                    },
                },
            )
            task = {
                "id": "m/raw",
                "model": "m",
                "pool": "capture",
                "deps": [],
                "outputs": [str(raw)],
                "command": [
                    sys.executable,
                    "worker.py",
                    str(config),
                    "raw",
                    "--probe",
                    "values",
                    "--sample",
                    "CTRL1_1",
                ],
                "validate": [sys.executable, "-c", "pass"],
                "timeout": 10,
                "max_attempts": 2,
            }
            spec = {
                "tasks": [task],
                "pools": {"capture": 1},
                "input_hashes": {str(config): digest(config)},
            }
            atomic(specfile, spec)
            e = Engine(spec, state)
            if running:
                e.db.execute("UPDATE jobs SET state='running',attempts=1")
                e.db.commit()
            n = adopt(specfile, state)
            row = dict(e.db.execute("SELECT * FROM jobs").fetchone())
            e.db.close()
            e.lock.close()
            return n, row

    def test_adopts_only_verified_artifact(self):
        n, row = self.exercise()
        self.assertEqual(n, 1)
        self.assertEqual(row["state"], "done")
        self.assertEqual(row["attempts"], 0)

    def test_invalid_raw_stays_queued(self):
        n, row = self.exercise("length")
        self.assertEqual(n, 0)
        self.assertEqual(row["state"], "pending")

    def test_does_not_steal_live_lease(self):
        n, row = self.exercise(running=True)
        self.assertEqual(n, 0)
        self.assertEqual(row["state"], "running")
        self.assertEqual(row["attempts"], 1)
