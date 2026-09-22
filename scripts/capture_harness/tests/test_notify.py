import json, sys, tempfile, unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine import atomic
from notify import drain


class NotifyTests(unittest.TestCase):
    def test_durable_ack_once(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            f = p / "outbox/a.json"
            atomic(
                f,
                {
                    "kind": "blocked",
                    "model": "test",
                    "status_path": str(p / "status.json"),
                    "state": "pending",
                    "delivery_attempts": 0,
                },
            )
            cmd = [
                sys.executable,
                "-c",
                f'import json,re,sys;from pathlib import Path;p=Path({str(p / "calls")!r});p.write_text(p.read_text()+"x" if p.exists() else "x");prompt=sys.argv[1];target=json.loads(re.search(r"ACK_PATH: (.+)",prompt)[1]);data=json.loads(re.search(r"ACK_FIELDS: (.+)",prompt)[1]);data["summary"]="ack";Path(target).write_text(json.dumps(data))',
            ]
            drain(p, cmd)
            drain(p, cmd)
            self.assertEqual((p / "calls").read_text(), "x")
            self.assertEqual(json.loads(f.read_text())["state"], "delivered")

    def test_failure_not_marked_delivered(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            f = p / "outbox/a.json"
            atomic(
                f,
                {
                    "kind": "blocked",
                    "model": "test",
                    "status_path": str(p / "status.json"),
                    "state": "pending",
                    "delivery_attempts": 0,
                },
            )
            drain(p, [sys.executable, "-c", "raise SystemExit(1)"])
            d = json.loads(f.read_text())
            self.assertEqual(d["state"], "delivery_failed")
            self.assertEqual(d["delivery_attempts"], 1)

    def test_zero_exit_without_ack_is_not_delivery(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)
            f = p / "outbox/a.json"
            atomic(
                f,
                {
                    "kind": "blocked",
                    "model": "test",
                    "status_path": str(p / "status.json"),
                    "state": "pending",
                    "delivery_attempts": 0,
                },
            )
            drain(p, [sys.executable, "-c", 'print("no shape")'])
            d = json.loads(f.read_text())
            self.assertEqual(d["state"], "delivery_failed")
            self.assertFalse(d["acknowledgement_verified"])
