#!/usr/bin/env python3
"""Drain durable escalation outbox through an explicitly configured command.
The command receives one final argument: a bounded, trusted checkpoint prompt.
No corpus/model-response text or secrets are included in the prompt.
"""

import argparse, fcntl, json, os, signal, subprocess, time, uuid
from pathlib import Path
from engine import atomic


def drain(directory, command, timeout=600):
    directory = Path(directory).resolve()
    with (directory / "notify.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        for f in sorted((directory / "outbox").glob("*.json")):
            d = json.loads(f.read_text())
            if d["state"] == "delivered" and not d.get("acknowledgement_verified"):
                d.update(state="delivery_unverified", next_at=0)
                atomic(f, d)
            if (
                d["state"] == "delivered"
                or d["delivery_attempts"] >= 3
                or d.get("next_at", 0) > time.time()
            ):
                continue
            nonce = uuid.uuid4().hex
            ack_path = (
                directory / "outbox" / "receipts" / (f.stem + "." + nonce + ".json")
            )
            ack_path.parent.mkdir(exist_ok=True)
            d.update(
                delivery_attempts=d["delivery_attempts"] + 1,
                state="delivering",
                ack_path=str(ack_path),
                nonce=nonce,
            )
            atomic(f, d)
            prompt = f"""Mira capture-harness checkpoint: {d["kind"]} for {d["model"]}.
Read only {d["status_path"]} and the nearby STATUS.md first. This is a bounded escalation, not a request to redo working samples. Inspect the relevant task logs and record diagnosis and the smallest safe recovery plan. Never change provider, prompts, reasoning policy, taxonomy, consensus thresholds, valid samples, or budgets to manufacture success. Do not invoke Lume or other agents. Do not publish/tag/release. No secrets in output. Write a concise acknowledgement and diagnosis in the required receipt. A blocked-model notification means ordinary technical retries have been exhausted; analysis_complete instead means verified analysis is ready for publication review. Run directory: {directory}
"""
            if d["kind"] == "notification_self_test":
                prompt = "This is a capture-harness notification transport self-test, not a corpus failure. Only write the required acknowledgement file below; do not inspect other files or modify memory. Set summary to CAPTURE_ESCALATION_ACK."
            fields = {
                "nonce": nonce,
                "model": d["model"],
                "kind": d["kind"],
                "acknowledged": True,
            }
            prompt += (
                "\nCompletion requires you to WRITE a JSON file at ACK_PATH, not merely reply in chat. Include every ACK_FIELDS field exactly and add a nonempty summary string containing your diagnosis (no secrets). Your journal reflex may run afterwards; it must not replace this receipt.\nACK_PATH: "
                + json.dumps(str(ack_path))
                + "\nACK_FIELDS: "
                + json.dumps(fields)
                + "\n"
            )
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
                try:
                    ack = json.loads(ack_path.read_text())
                    ack_ok = (
                        all(ack.get(k) == v for k, v in fields.items())
                        and isinstance(ack.get("summary"), str)
                        and bool(ack["summary"].strip())
                    )
                except (OSError, ValueError, AttributeError):
                    ack_ok = False
                d.update(
                    state="delivered" if rc == 0 and ack_ok else "delivery_failed",
                    acknowledgement_verified=ack_ok,
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
