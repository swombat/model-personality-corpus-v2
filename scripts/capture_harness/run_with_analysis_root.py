#!/usr/bin/env python3
"""Run listed model-level tasks (synthesis, ready) against a dedicated analysis worktree. Explicit lane.

For a held model whose analysis state lives in its own worktree of the analysis
repo (and whose raw traces live in a corpus worktree), the compiled spec still
names the shared checkouts. The spec is fingerprinted and is not changed.
This lane runs the task's own worker function with the config's analysis_root
and phase rewritten in memory to --analysis-root, and the worker's raw-trace
root set to --raw-root, then validates it the same way, and marks the job done
with receipts naming the files actually written. Each spec output must map to
a file under the worktree; the shared checkout's copies of those paths are
fingerprinted before and after and must not change. Tasks run in the order
given, each only when pending with every dependency done. Nothing else runs.

--check writes nothing and runs nothing.
"""
import argparse, fcntl, hashlib, json, sqlite3, time
from pathlib import Path

from engine import digest

ACTIONS = ("synthesis", "ready")


def _state(path):
    path = Path(path)
    return digest(path) if path.is_file() else None


def apply(spec_path, directory, ids, reviewer, analysis_root, raw_root, check_only=False):
    import worker

    directory = Path(directory).resolve()
    analysis_root = Path(analysis_root).resolve()
    raw_root = Path(raw_root).resolve()
    spec = json.loads(Path(spec_path).read_text())
    db = sqlite3.connect(directory / "state.sqlite", timeout=30)
    fingerprint = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    assert db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()[0] == fingerprint
    assert reviewer.strip(), "reviewer reference required"
    assert (raw_root / "scripts/capture_harness").is_dir() and (raw_root / "data").is_dir(), "not a corpus checkout"
    tasks = {t["id"]: t for t in spec["tasks"]}
    lock = (directory / "repair.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    results = []
    original_raw = worker.RAW
    try:
        worker.RAW = raw_root  # trace_path() reads this module global
        for id in ids:
            task = tasks[id]
            cmd = task["command"]
            action = cmd[3]
            assert action in ACTIONS and len(cmd) == 4, "only synthesis/ready tasks"
            c = json.loads(Path(cmd[2]).read_text())
            c["_config"] = str(Path(cmd[2]).resolve())  # as worker.main(): locates the run state
            old = Path(c["analysis_root"])
            assert old != analysis_root, "analysis root is already the config's"
            c["phase"] = str(analysis_root / Path(c["phase"]).relative_to(old))
            c["analysis_root"] = str(analysis_root)
            phase = Path(c["phase"])
            assert phase.is_dir(), "phase missing in the worktree"
            outputs = [analysis_root / Path(p).relative_to(old) for p in task["outputs"]]
            shared = {p: _state(p) for p in task["outputs"]}
            state = db.execute("SELECT state FROM jobs WHERE id=?", (id,)).fetchone()[0]
            deps = {d: db.execute("SELECT state FROM jobs WHERE id=?", (d,)).fetchone()[0] for d in task["deps"]}
            sel = {
                "id": id, "action": action, "state": state,
                "deps_done": all(s == "done" for s in deps.values()), "deps": len(deps),
                "analysis_root": str(analysis_root), "raw_root": str(raw_root),
                "outputs": [str(p) for p in outputs], "outputs_exist": [p.exists() for p in outputs],
                "shared_outputs_exist": [s is not None for s in shared.values()],
            }
            if check_only:
                print(json.dumps(sel), flush=True)
                results.append(sel)
                continue
            assert state == "pending", "task is not pending"
            assert sel["deps_done"], "a dependency is not done"
            fn = getattr(worker, action)
            fn(c, phase, False)
            fn(c, phase, True)
            assert {p: _state(p) for p in task["outputs"]} == shared, "shared checkout outputs changed"
            receipts = json.dumps({str(p.resolve()): digest(p) for p in outputs})
            with db:
                assert db.execute(
                    "UPDATE jobs SET state='done',reason=?,receipts=?,pid=NULL WHERE id=? AND state='pending'",
                    (f"done with analysis root {analysis_root}", receipts, id),
                ).rowcount == 1
                db.execute("INSERT INTO events VALUES(?,?,?,?)", (time.time(), id, "analysis_root_lane_done",
                           json.dumps({"reviewer": reviewer, "analysis_root": str(analysis_root), "raw_root": str(raw_root),
                                       "receipts": json.loads(receipts)})))
            sel.update(applied=True, receipts=json.loads(receipts))
            print(json.dumps(sel), flush=True)
            results.append(sel)
    finally:
        worker.RAW = original_raw
        db.close()
        lock.close()
    return results


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--analysis-root", type=Path, required=True)
    p.add_argument("--raw-root", type=Path, required=True, help="corpus checkout holding this model's raw traces")
    p.add_argument("--check", action="store_true", help="dry run: writes nothing, runs nothing")
    p.add_argument("ids", nargs="+")
    a = p.parse_args()
    apply(a.spec, a.state, a.ids, a.reviewer, a.analysis_root, a.raw_root, a.check)
