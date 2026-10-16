#!/usr/bin/env python3
"""Evaluate listed BV1 tasks under the BV1-Luna v1 targeted repair variant. Explicit, authorised lane.

Only a BV1 task in a Luna v1 capture whose source is punctuated qualifies, and
only if it is blocked by its own failure (never a dependency block), with no
ineligibility receipt and no v1 binding. Each call is charged to an
authorization's restart-persistent allowance (as in recover_blocked.py); never
mint a new authorization to refill an exhausted one. The run spec is not
changed. v1 attempts are never read as answers, moved or relabelled: the
variant writes only to its own attempt, output and binding directories, and the
task's receipts point at those files. Stops at the first valid result. Only
dependency-blocked descendants are released.

--check writes nothing and makes no calls.
"""
import argparse, fcntl, hashlib, json, sqlite3, time
from pathlib import Path

from engine import digest
import ineligibility as INEL
from apply_luna_v1_1 import tree_fingerprint


def apply(spec_path, directory, ids, authorization, limit=2, check_only=False):
    import worker

    directory = Path(directory).resolve()
    spec = json.loads(Path(spec_path).read_text())
    db = sqlite3.connect(directory / "state.sqlite", timeout=30)
    fingerprint = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    assert db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()[0] == fingerprint
    assert authorization.strip(), "authorization required"
    assert 1 <= limit <= 3
    tasks = {t["id"]: t for t in spec["tasks"]}
    if not check_only:
        db.execute(
            "CREATE TABLE IF NOT EXISTS targeted_repairs(authorization TEXT,id TEXT,used INTEGER,allowance INTEGER,PRIMARY KEY(authorization,id))"
        )
        db.commit()
    has_table = db.execute("SELECT 1 FROM sqlite_master WHERE name='targeted_repairs'").fetchone() is not None
    lock = (directory / "repair.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    arm = worker.LUNA_TARGETED_ARM
    results = []
    try:
        for id in ids:
            task = tasks[id]
            cmd = task["command"]
            assert cmd[3] == "bv1" and "--validate" not in cmd, "not a BV1 task"
            sid = cmd[cmd.index("--sample") + 1]
            c = json.loads(Path(cmd[2]).read_text())
            assert INEL.task_id(c, sid) == id
            assert c.get("bv1_evaluator") == worker.LUNA_ARM, "not a Luna v1 capture"
            phase = Path(c["phase"])
            src = worker.trace_path(c, "freeflow", sid)
            text = json.loads(src.read_text())["result"]
            assert not worker.luna_v11_applies(c, text), "unpunctuated source: belongs to v1.1"
            state, reason = db.execute("SELECT state,reason FROM jobs WHERE id=?", (id,)).fetchone()
            assert state == "blocked" and not (reason or "").startswith("dependency"), "only blocked roots qualify"
            assert not INEL.receipt_path(phase, sid).exists(), "task has an ineligibility receipt"
            v1_out, _, v1_bind = worker.bv1_paths(c, phase, worker.LUNA_ARM)
            assert not (v1_bind / (sid + ".json")).exists(), "task has a v1 binding"
            bv_out, outputs, bindings = worker.bv1_paths(c, phase, arm)
            out = outputs / c["label"] / (sid + ".md")
            v1_attempts = INEL.attempt_dir(v1_out, c, sid)
            before = tree_fingerprint(v1_attempts)
            if not check_only:
                db.execute("INSERT OR IGNORE INTO targeted_repairs VALUES(?,?,0,?)", (authorization, id, limit))
                db.commit()
            found = has_table and db.execute(
                "SELECT used,allowance FROM targeted_repairs WHERE authorization=? AND id=?", (authorization, id)
            ).fetchone()
            used, allowance = found or (0, limit)
            assert allowance == limit, "limit differs from this authorization's recorded allowance"
            sel = {
                "id": id, "sample": sid, "state": state, "reason": reason, "arm": arm,
                "authorization": authorization, "used": used, "allowance": allowance,
                "source_sha256": digest(src), "output": str(out),
                "attempts": str(INEL.attempt_dir(bv_out, c, sid)),
                "binding": str(bindings / (sid + ".json")),
                "output_exists": out.exists(), "v1_attempts": before,
            }
            if check_only:
                print(json.dumps(sel), flush=True)
                results.append(sel)
                continue
            done = False
            prov = Path(str(out) + ".provenance.json")
            binding = bindings / (sid + ".json")

            def finalize(attempt):
                receipts = json.dumps({str(p.resolve()): digest(p) for p in (out, prov, binding)})
                with db:
                    assert db.execute(
                        "UPDATE jobs SET state='done',reason=?,receipts=?,pid=NULL WHERE id=? AND state='blocked'",
                        (f"evaluated: {arm} (authorised repair {authorization}, attempt {attempt}/{allowance})", receipts, id),
                    ).rowcount == 1
                    db.execute("INSERT INTO events VALUES(?,?,?,?)", (time.time(), id, "bv1_targeted_repair_applied",
                               json.dumps({"arm": arm, "authorization": authorization, "attempt": attempt, "limit": allowance,
                                           "output": str(out), "output_sha256": digest(out)})))
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
                worker.bv1(c, phase, sid, validate=True)  # now routes to the variant on its own

            if out.exists():
                # A result an earlier run produced but did not finalize (e.g. the job
                # transaction failed). Finalize it with no call and no charge, even
                # when the allowance is exhausted. Validation only: it requires the
                # variant's provenance and binding. Anything else (no sidecar, no
                # binding) fails closed for review; generation is never re-entered
                # here, because the worker would archive an unbound output and call.
                worker.bv1(c, phase, sid, validate=True, lane=True, targeted=True)
                assert tree_fingerprint(v1_attempts) == before, "v1 attempts changed"
                def attempts(event):
                    return [json.loads(d)["attempt"] for (d,) in db.execute(
                        "SELECT details FROM events WHERE id=? AND event=? ORDER BY rowid", (id, event))
                        if json.loads(d).get("authorization") == authorization]
                # Attribution: the attempt recorded as succeeding; failing that
                # (its event was lost), the last attempt started, the only one
                # that can have written the output.
                won = attempts("bv1_targeted_repair_succeeded") or attempts("bv1_targeted_repair_started")
                assert won, "output exists without an attempt under this authorization"
                finalize(won[-1])
                done = True
            while not done and used < allowance:
                used += 1
                with db:
                    db.execute("UPDATE targeted_repairs SET used=? WHERE authorization=? AND id=?", (used, authorization, id))
                    db.execute("INSERT INTO events VALUES(?,?,?,?)", (time.time(), id, "bv1_targeted_repair_started",
                               json.dumps({"arm": arm, "authorization": authorization, "attempt": used, "limit": allowance})))
                try:
                    row = worker.bv1(c, phase, sid, lane=True, targeted=True)
                    assert row["evaluator_arm"] == arm
                    worker.bv1(c, phase, sid, validate=True, lane=True, targeted=True)
                    error = None
                except Exception as e:  # a failed evaluation: recorded, attempt kept, allowance charged
                    error = str(e)[:300]
                assert tree_fingerprint(v1_attempts) == before, "v1 attempts changed"
                with db:
                    db.execute("INSERT INTO events VALUES(?,?,?,?)", (time.time(), id,
                               "bv1_targeted_repair_finished" if error else "bv1_targeted_repair_succeeded",
                               json.dumps({"authorization": authorization, "attempt": used, "error": error})))
                if error:
                    print(json.dumps({"id": id, "attempt": used, "error": error}), flush=True)
                    continue
                finalize(used)
                done = True
            sel.update(used=used, applied=done, output_sha256=digest(out) if done else None)
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
    p.add_argument("--authorization", required=True)
    p.add_argument("--limit", type=int, default=2)
    p.add_argument("--check", action="store_true", help="dry run: no calls, writes nothing")
    p.add_argument("ids", nargs="+")
    a = p.parse_args()
    apply(a.spec, a.state, a.ids, a.authorization, a.limit, a.check)
