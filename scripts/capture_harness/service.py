#!/usr/bin/env python3
"""Cross-platform service entry point. Workers live independently of the chat."""

import argparse, json, signal, subprocess, sys, time, threading
from pathlib import Path
from engine import atomic
from notify import drain

HERE = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument("spec", type=Path)
p.add_argument("--state", type=Path, required=True)
a = p.parse_args()
spec = json.loads(a.spec.read_text())
a.state.mkdir(parents=True, exist_ok=True)
stop = threading.Event()
child = None


def shutdown(*_):
    stop.set()
    if child and child.poll() is None:
        child.terminate()


signal.signal(signal.SIGTERM, shutdown)
signal.signal(signal.SIGINT, shutdown)


def notifications():
    while not stop.is_set():
        if spec.get("notify_command"):
            drain(a.state, spec["notify_command"])
        stop.wait(10)


thread = threading.Thread(target=notifications, daemon=True)
thread.start()
with (a.state / "supervisor.log").open("ab") as log:
    child = subprocess.Popen(
        [
            sys.executable,
            str(HERE / "engine.py"),
            "run",
            str(a.spec),
            "--state",
            str(a.state),
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    rc = child.wait()
if rc:
    atomic(a.state / "service_failure.json", {"returncode": rc, "at": time.time()})
    alert = a.state / "outbox/supervisor-failure.json"
    if not alert.exists():
        atomic(
            alert,
            {
                "kind": "blocked",
                "model": "supervisor",
                "status_path": str(a.state / "service_failure.json"),
                "created_at": time.time(),
                "state": "pending",
                "delivery_attempts": 0,
            },
        )
    # Allow the independent notifier a bounded interval to record delivery; a
    # restart can resume any undelivered outbox entry without losing the failure.
    deadline = time.monotonic() + 620
    while (
        spec.get("notify_command") and not stop.is_set() and time.monotonic() < deadline
    ):
        d = json.loads(alert.read_text())
        if d["state"] in ("delivered", "delivery_failed"):
            break
        stop.wait(1)
    stop.set()
    raise SystemExit(rc)
# Keep only the inexpensive outbox drain alive until all messages have receipts.
while not stop.is_set() and spec.get("notify_command"):
    pending = [json.loads(f.read_text()) for f in (a.state / "outbox").glob("*.json")]
    if all(d["state"] == "delivered" or d["delivery_attempts"] >= 3 for d in pending):
        break
    stop.wait(5)
stop.set()
