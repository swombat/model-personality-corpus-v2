#!/usr/bin/env python3
"""Declare blocked BV1 tasks ineligible (bv1-ineligibility-v1). Never an evaluation.

Only a blocked BV1-Luna task whose source has no sentence-terminal punctuation,
and whose every preserved attempt failed quote_sentence_boundary, qualifies. The
receipt is recomputed from the source, the evaluator instruction, the attempt
directory and the task history; the reviewer reference authorises it but is not
evidence. Original attempts and events are kept. The task becomes done with
reason "ineligible: ..." and an `ineligible_applied` event, and only
dependency-blocked descendants are released.
"""
import argparse, fcntl, hashlib, json, sqlite3, sys, time
from pathlib import Path

from engine import atomic, digest
import ineligibility as INEL


def apply(spec_path, directory, ids, reviewer, check_only=False):
    import worker

    directory = Path(directory).resolve()
    spec = json.loads(Path(spec_path).read_text())
    db = sqlite3.connect(directory / "state.sqlite", timeout=30)
    fingerprint = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    assert db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()[0] == fingerprint
    assert reviewer.strip(), "reviewer reference required"
    tasks = {t["id"]: t for t in spec["tasks"]}
    lock = (directory / "repair.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        for id in ids:
            task = tasks[id]
            cmd = task["command"]
            assert cmd[3] == "bv1" and "--validate" not in cmd, "not a BV1 task"
            sid = cmd[cmd.index("--sample") + 1]
            c = json.loads(Path(cmd[2]).read_text())
            assert INEL.task_id(c, sid) == id
            phase = Path(c["phase"])
            bv_out, outputs, binding_dir = worker.bv1_paths(c, phase)
            arm = worker.module(
                "capture_luna",
                Path(c["analysis_root"]) / "analysis/freeflow/personality-eval-bv1/luna_v1.py",
            )
            src = worker.trace_path(c, "freeflow", sid)
            out = outputs / c["label"] / (sid + ".md")
            binding = binding_dir / (sid + ".json")
            receipt = dict(INEL.facts(c, sid, src, bv_out, arm), reviewer=reviewer)
            INEL.check(receipt, c, sid, src, bv_out, arm, out, binding)
            INEL.check_history(directory / "state.sqlite", id, receipt["attempts"])
            path = INEL.receipt_path(phase, sid)
            assert not path.exists(), "receipt already exists"
            if check_only:
                print(json.dumps({"id": id, "would_write": str(path), "attempts": len(receipt["attempts"])}), flush=True)
                continue
            atomic(path, receipt)
            receipts = json.dumps({str(path.resolve()): digest(path)})
            with db:
                assert (
                    db.execute(
                        "UPDATE jobs SET state='done',reason=?,receipts=?,pid=NULL WHERE id=? AND state='blocked'",
                        (f"ineligible: {INEL.VERSION}", receipts, id),
                    ).rowcount
                    == 1
                )
                db.execute(
                    "INSERT INTO events VALUES(?,?,?,?)",
                    (
                        time.time(),
                        id,
                        "ineligible_applied",
                        json.dumps(
                            {
                                "version": INEL.VERSION,
                                "receipt": str(path),
                                "receipt_sha256": digest(path),
                                "reviewer": reviewer,
                                "attempts": len(receipt["attempts"]),
                            }
                        ),
                    ),
                )
                descendants = {id}
                for _ in tasks:
                    found = {
                        i for i, t in tasks.items() if any(d in descendants for d in t["deps"])
                    }
                    if found <= descendants:
                        break
                    descendants |= found
                for dep in descendants - {id}:
                    db.execute(
                        "UPDATE jobs SET state='pending',reason=NULL,next_at=0 WHERE id=? AND state='blocked' AND reason='dependency blocked'",
                        (dep,),
                    )
            print(json.dumps({"id": id, "ineligible": str(path)}), flush=True)
    finally:
        db.close()
        lock.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--check", action="store_true", help="validate only; write nothing")
    p.add_argument("ids", nargs="+")
    a = p.parse_args()
    apply(a.spec, a.state, a.ids, a.reviewer, a.check)
