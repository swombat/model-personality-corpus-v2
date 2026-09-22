#!/usr/bin/env python3
"""Explicit bounded repair lane. Never resets original attempts or changes the spec.
Only listed blocked roots run, under the normal output lock and validator.
An authorization ID has a persistent per-task allowance; restarting cannot refill it.
"""

import argparse, fcntl, hashlib, json, os, signal, sqlite3, subprocess, sys, time
from pathlib import Path
from engine import digest


def recover(spec_path, directory, ids, authorization, limit=2):
    directory = Path(directory).resolve()
    spec = json.loads(Path(spec_path).read_text())
    db = sqlite3.connect(directory / "state.sqlite", timeout=30)
    fingerprint = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    assert db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()[0] == fingerprint
    assert all(digest(p) == h for p, h in spec.get("input_hashes", {}).items())
    tasks = {t["id"]: t for t in spec["tasks"]}
    assert 1 <= limit <= 3 and authorization.strip()
    assert all(i in tasks for i in ids)
    db.execute(
        "CREATE TABLE IF NOT EXISTS repairs(authorization TEXT,id TEXT,used INTEGER, allowance INTEGER, PRIMARY KEY(authorization,id))"
    )
    db.commit()
    lock = (directory / "repair.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        for id in ids:
            task = tasks[id]
            db.execute(
                "INSERT OR IGNORE INTO repairs VALUES(?,?,0,?)",
                (authorization, id, limit),
            )
            db.commit()
            assert (
                db.execute(
                    "SELECT allowance FROM repairs WHERE authorization=? AND id=?",
                    (authorization, id),
                ).fetchone()[0]
                == limit
            )
            while True:
                state, reason = db.execute(
                    "SELECT state,reason FROM jobs WHERE id=?", (id,)
                ).fetchone()
                if state == "done":
                    break
                assert state == "blocked" and not (reason or "").startswith(
                    "dependency"
                ), "only blocked roots may be repaired"
                assert all(
                    db.execute("SELECT state FROM jobs WHERE id=?", (d,)).fetchone()[0]
                    == "done"
                    for d in task["deps"]
                )
                used = db.execute(
                    "SELECT used FROM repairs WHERE authorization=? AND id=?",
                    (authorization, id),
                ).fetchone()[0]
                if used >= limit:
                    break
                used += 1
                with db:
                    db.execute(
                        "UPDATE repairs SET used=? WHERE authorization=? AND id=?",
                        (used, authorization, id),
                    )
                    db.execute(
                        "INSERT INTO events VALUES(?,?,?,?)",
                        (
                            time.time(),
                            id,
                            "authorized_repair_started",
                            json.dumps(
                                {
                                    "authorization": authorization,
                                    "attempt": used,
                                    "limit": limit,
                                }
                            ),
                        ),
                    )
                logdir = directory / "repairs"
                logdir.mkdir(exist_ok=True)
                key = hashlib.sha256((authorization + id).encode()).hexdigest()[:20]
                args = [
                    sys.executable,
                    str(Path(__file__).with_name("engine.py")),
                    "child",
                    "--resource",
                    str(
                        Path(spec.get("lock_root", directory / "locks"))
                        / hashlib.sha256(task.get("resource", id).encode()).hexdigest()
                    ),
                    "--attempt",
                    str(used),
                    "--timeout",
                    str(task["timeout"]),
                    "--payload",
                    json.dumps(
                        {"command": task["command"], "validate": task["validate"]}
                    ),
                ]
                with (logdir / f"{key}.{used}.log").open("ab") as log:
                    p = subprocess.Popen(
                        args,
                        cwd=spec.get("cwd"),
                        stdout=log,
                        stderr=subprocess.STDOUT,
                        start_new_session=True,
                    )
                    try:
                        rc = p.wait(timeout=task["timeout"] + 10)
                    except subprocess.TimeoutExpired:
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait()
                        rc = 124
                receipts = None
                if rc == 0:
                    try:
                        receipts = json.dumps(
                            {str(Path(f).resolve()): digest(f) for f in task["outputs"]}
                        )
                    except OSError:
                        rc = 1
                with db:
                    db.execute(
                        "INSERT INTO events VALUES(?,?,?,?)",
                        (
                            time.time(),
                            id,
                            "authorized_repair_finished",
                            json.dumps(
                                {
                                    "authorization": authorization,
                                    "attempt": used,
                                    "returncode": rc,
                                }
                            ),
                        ),
                    )
                    if rc == 0:
                        assert (
                            db.execute(
                                "UPDATE jobs SET state='done',reason=NULL,receipts=?,pid=NULL WHERE id=? AND state='blocked'",
                                (receipts, id),
                            ).rowcount
                            == 1
                        )
                        # Release only dependency-blocked descendants; the live
                        # engine checks all dependencies again before scheduling.
                        descendants = {id}
                        for _ in tasks:
                            found = {
                                i
                                for i, t in tasks.items()
                                if any(d in descendants for d in t["deps"])
                            }
                            if found <= descendants:
                                break
                            descendants |= found
                        for dep in descendants - {id}:
                            db.execute(
                                "UPDATE jobs SET state='pending',reason=NULL,next_at=0 WHERE id=? AND state='blocked' AND reason='dependency blocked'",
                                (dep,),
                            )
                print(
                    json.dumps({"id": id, "repair_attempt": used, "returncode": rc}),
                    flush=True,
                )
                if rc in (0, 20, 21, 22):
                    break
    finally:
        db.close()
        lock.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--authorization", required=True)
    p.add_argument("--limit", type=int, default=2)
    p.add_argument("ids", nargs="+")
    a = p.parse_args()
    recover(a.spec, a.state, a.ids, a.authorization, a.limit)
