#!/usr/bin/env python3
"""Drain durable escalation outbox through an explicitly configured command.
The command receives one final argument: a bounded, trusted checkpoint prompt.
No corpus/model-response text or secrets are included in the prompt.
"""

import argparse, fcntl, json, os, signal, subprocess, time
from pathlib import Path
from engine import atomic


def drain(directory, command, timeout=600):
    directory = Path(directory)
    with (directory / "notify.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        for f in sorted((directory / "outbox").glob("*.json")):
            d = json.loads(f.read_text())
            if (
                d["state"] == "delivered"
                or d["delivery_attempts"] >= 3
                or d.get("next_at", 0) > time.time()
            ):
                continue
            d.update(delivery_attempts=d["delivery_attempts"] + 1, state="delivering")
            atomic(f, d)
            prompt = f"""Mira capture-harness checkpoint: {d["kind"]} for {d["model"]}.
Read only {d["status_path"]} and the nearby STATUS.md first. This is a bounded escalation, not a request to redo working samples. Inspect the relevant task logs and record diagnosis and the smallest safe recovery plan. Never change provider, prompts, reasoning policy, taxonomy, consensus thresholds, valid samples, or budgets to manufacture success. Do not invoke Lume or other agents. Do not publish/tag/release. No secrets in output. Return a concise acknowledgement and diagnosis. This harness has already exhausted ordinary technical retries. Run directory: {directory}
"""
            out = directory / "outbox" / (f.stem + ".response.log")
            try:
                with out.open("ab") as log:
                    p = subprocess.Popen(
                        command + [prompt],
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    try:
                        rc = p.wait(timeout=timeout)
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait()
                        rc = 124
                d.update(
                    state="delivered" if rc == 0 else "delivery_failed",
                    returncode=rc,
                    next_at=time.time() + 300,
                    finished_at=time.time(),
                )
            except OSError as e:
                d.update(
                    state="delivery_failed",
                    error=type(e).__name__,
                    next_at=time.time() + 300,
                )
            atomic(f, d)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("directory", type=Path)
    p.add_argument("--command-json", required=True)
    a = p.parse_args()
    drain(a.directory, json.loads(a.command_json))
