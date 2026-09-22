import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import Engine, atomic
from worker import next_cap, card_ready
from recover_blocked import recover
from metadata import write_metadata


class FixTests(unittest.TestCase):
    def test_interrupted_request_not_completed_ceiling(self):
        self.assertEqual(
            next_cap(
                [16000, 32768],
                [16000, 32768],
                {"capture_policy": {"max_tokens": 16000}},
                "finish_length",
            ),
            32768,
        )
        self.assertEqual(next_cap([16000, 32768], [32768], {}, "finish_length"), 32768)
        with self.assertRaises(SystemExit):
            next_cap(
                [16000, 32768],
                [32768],
                {"capture_policy": {"max_tokens": 32768}},
                "finish_length",
            )

    def test_card_ready_requires_integrated_values(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            c = {"slug": "m", "analysis_root": td}
            with self.assertRaises(FileNotFoundError):
                card_ready(c, p)
            atomic(p / "VALUES_CARD.json", {"analyzed_values_samples": 0})
            with self.assertRaises(AssertionError):
                card_ready(c, p)

    def test_metadata_source_and_conflict(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            c = dict(
                model="v/m",
                slug="m",
                phase=str(p / "phase"),
                analysis_root=td,
                release_date="2026-09-21",
            )
            with self.assertRaises(AssertionError):
                write_metadata(c)
            c["release_date_source"] = (
                "User supplied launch date; https://example.org/release"
            )
            write_metadata(c)
            write_metadata(c, True)
            c["release_date"] = "2026-09-22"
            with self.assertRaises(AssertionError):
                write_metadata(c)

    def test_listing_date_is_not_release_date(self):
        with tempfile.TemporaryDirectory() as td:
            c = dict(slug="m", phase=td, analysis_root=td, created=1790021264)
            write_metadata(c)
            self.assertEqual(
                json.loads((Path(td) / "model_metadata.json").read_text())[
                    "release_date_status"
                ],
                "unknown",
            )

    def test_repair_preserves_budget_and_unblocks_only_descendants(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            out = p / "out"
            cmd = [
                sys.executable,
                "-c",
                f'from pathlib import Path;Path({str(out)!r}).write_text("ok")',
            ]
            task = dict(
                id="root",
                model="m",
                deps=[],
                pool="p",
                outputs=[str(out)],
                command=cmd,
                validate=[sys.executable, "-c", "pass"],
                max_attempts=1,
                timeout=3,
            )
            child = dict(task, id="child", deps=["root"])
            other = dict(task, id="other")
            spec = dict(tasks=[task, child, other], pools={"p": 1})
            atomic(p / "spec.json", spec)
            e = Engine(spec, p / "state")
            e.db.execute("UPDATE jobs SET state='blocked',reason='exit 1',attempts=1")
            e.db.execute(
                "UPDATE jobs SET reason='dependency blocked',attempts=0 WHERE id='child'"
            )
            e.db.commit()
            recover(p / "spec.json", p / "state", ["root"], "test-authorization", 1)
            rows = {r["id"]: dict(r) for r in e.db.execute("SELECT * FROM jobs")}
            self.assertEqual(rows["root"]["state"], "done")
            self.assertEqual(rows["root"]["attempts"], 1)
            self.assertEqual(rows["child"]["state"], "pending")
            self.assertEqual(rows["other"]["state"], "blocked")
            # A restart of the repair command cannot refill its used allowance.
            e.db.execute("UPDATE jobs SET state='blocked' WHERE id='root'")
            e.db.commit()
            recover(p / "spec.json", p / "state", ["root"], "test-authorization", 1)
            self.assertEqual(
                e.db.execute("SELECT state FROM jobs WHERE id='root'").fetchone()[0],
                "blocked",
            )
            e.db.close()
            e.lock.close()
