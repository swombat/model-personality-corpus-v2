#!/usr/bin/env python3
"""Evaluate listed BV1 tasks under BV1-Luna v1.1 (analysis e5b4f5912). Explicit, reviewed lane.

Only a BV1 task in a Luna v1 capture whose source has no . ! ? at all qualifies.
The task must be blocked by its own failure (never a dependency block), or, with
--supersede-ineligibility, done as bv1-ineligibility-v1; the receipt is then
moved aside, not deleted, and the supersession is an event. The run spec is not
changed. v1 attempts and outputs are never read as answers, moved or relabelled:
v1.1 writes only to its own attempt, output and binding directories, and the
task's recorded receipts point at those files. Only dependency-blocked
descendants are released.

--check writes nothing and makes no calls: it prints the selection, the arm, the
paths v1.1 would write, and fingerprints of the v1 records so they can be
compared after the run.
"""
import argparse, fcntl, hashlib, json, shutil, sqlite3, time
from pathlib import Path

from engine import atomic, digest
import ineligibility as INEL


def tree_fingerprint(path):
    """Names and hashes of every file under path (empty if absent)."""
    path = Path(path)
    if not path.exists():
        return {"files": 0, "sha256": None}
    files = sorted(p for p in path.rglob("*") if p.is_file())
    h = hashlib.sha256()
    for p in files:
        h.update(str(p.relative_to(path)).encode() + b"\0" + digest(p).encode() + b"\n")
    return {"files": len(files), "sha256": h.hexdigest()}


def v1_records(worker, c, phase, sid):
    bv_out, outputs, bindings = worker.bv1_paths(c, phase, worker.LUNA_ARM)
    out = outputs / c["label"] / (sid + ".md")
    return {
        "attempts": tree_fingerprint(INEL.attempt_dir(bv_out, c, sid)),
        "output_exists": out.exists(),
        "binding_exists": (bindings / (sid + ".json")).exists(),
    }


def apply(spec_path, directory, ids, reviewer, check_only=False, supersede=False):
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
    results = []
    try:
        for id in ids:
            task = tasks[id]
            cmd = task["command"]
            assert cmd[3] == "bv1" and "--validate" not in cmd, "not a BV1 task"
            sid = cmd[cmd.index("--sample") + 1]
            c = json.loads(Path(cmd[2]).read_text())
            assert INEL.task_id(c, sid) == id
            phase = Path(c["phase"])
            src = worker.trace_path(c, "freeflow", sid)
            text = json.loads(src.read_text())["result"]
            assert worker.luna_v11_applies(c, text), "source is punctuated or capture is not Luna v1"
            state, reason = db.execute("SELECT state,reason FROM jobs WHERE id=?", (id,)).fetchone()
            receipt = INEL.receipt_path(phase, sid)
            if state == "blocked":
                assert not (reason or "").startswith("dependency"), "only blocked roots qualify"
                assert not receipt.exists(), "blocked task with an ineligibility receipt"
            else:
                assert state == "done" and reason == INEL.APPLIED_REASON, "task is neither blocked nor ineligible"
                assert supersede and receipt.exists(), "ineligible task: needs --supersede-ineligibility"
            bv_out, outputs, bindings = worker.bv1_paths(c, phase, worker.LUNA_V11_ARM)
            out = outputs / c["label"] / (sid + ".md")
            assert not out.exists(), "v1.1 output already exists"
            before = v1_records(worker, c, phase, sid)
            sel = {
                "id": id,
                "sample": sid,
                "state": state,
                "reason": reason,
                "arm": worker.LUNA_V11_ARM,
                "source_sha256": digest(src),
                "v11_output": str(out),
                "v11_attempts": str(INEL.attempt_dir(bv_out, c, sid)),
                "v11_binding": str(bindings / (sid + ".json")),
                "supersedes_ineligibility_receipt": str(receipt) if receipt.exists() else None,
                "v1_records": before,
            }
            if check_only:
                print(json.dumps(sel), flush=True)
                results.append(sel)
                continue
            superseded = None
            if receipt.exists():
                aside = phase / "bv1_ineligible_superseded" / f"{sid}.{time.time_ns()}.json"
                aside.parent.mkdir(exist_ok=True)
                shutil.move(str(receipt), str(aside))
                superseded = {"receipt": str(aside), "receipt_sha256": digest(aside)}
            row = worker.bv1(c, phase, sid, lane=True)
            assert row["evaluator_arm"] == worker.LUNA_V11_ARM
            worker.bv1(c, phase, sid, validate=True)
            assert v1_records(worker, c, phase, sid) == before, "v1 records changed"
            prov = Path(str(out) + ".provenance.json")
            binding = bindings / (sid + ".json")
            receipts = json.dumps({str(p.resolve()): digest(p) for p in (out, prov, binding)})
            with db:
                assert (
                    db.execute(
                        "UPDATE jobs SET state='done',reason=?,receipts=?,pid=NULL WHERE id=? AND state=?",
                        (f"evaluated: {worker.LUNA_V11_ARM}", receipts, id, state),
                    ).rowcount
                    == 1
                )
                db.execute(
                    "INSERT INTO events VALUES(?,?,?,?)",
                    (time.time(), id, "luna_v1_1_applied",
                     json.dumps({"arm": worker.LUNA_V11_ARM, "reviewer": reviewer, "output": str(out),
                                 "output_sha256": digest(out), "superseded_ineligibility": superseded})),
                )
                descendants = {id}
                for _ in tasks:
                    found = {i for i, t in tasks.items() if any(d in descendants for d in t["deps"])}
                    if found <= descendants:
                        break
                    descendants |= found
                for dep in descendants - {id}:
                    db.execute(
                        "UPDATE jobs SET state='pending',reason=NULL,next_at=0 WHERE id=? AND state='blocked' AND reason='dependency blocked'",
                        (dep,),
                    )
            sel.update(applied=True, output_sha256=digest(out), superseded=superseded)
            print(json.dumps(sel), flush=True)
            results.append(sel)
    finally:
        db.close()
        lock.close()
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--check", action="store_true", help="dry run: no calls, writes nothing")
    p.add_argument("--supersede-ineligibility", action="store_true")
    p.add_argument("ids", nargs="+")
    a = p.parse_args()
    apply(a.spec, a.state, a.ids, a.reviewer, a.check, a.supersede_ineligibility)
