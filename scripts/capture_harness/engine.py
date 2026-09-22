#!/usr/bin/env python3
"""Persistent DAG runner. SQLite checkpoints, process-tree deadlines, fail-closed gates."""

from __future__ import annotations
import uuid
import argparse, collections, fcntl, hashlib, json, os, signal, sqlite3, subprocess, sys, time
from pathlib import Path

TERMINAL = {"done", "blocked"}


def atomic(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2) + "\n")
    tmp.replace(path)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()


class Engine:
    def __init__(self, spec, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = (self.directory / "supervisor.lock").open("a+")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.lock.close()
            raise
        self.spec = spec
        self.live = {}
        self.stopping = False
        self.turn = 0
        self.db = sqlite3.connect(self.directory / "state.sqlite")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY,v TEXT);
          CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, state TEXT, attempts INTEGER DEFAULT 0,
          next_at REAL DEFAULT 0, pid INTEGER, started REAL, reason TEXT, receipts TEXT);
          CREATE TABLE IF NOT EXISTS events(at REAL,id TEXT,event TEXT,details TEXT);""")
        self.tasks = {t["id"]: t for t in spec["tasks"]}
        if len(self.tasks) != len(spec["tasks"]):
            raise ValueError("duplicate task IDs")
        try:
            self.validate_graph()
        except BaseException:
            self.db.close()
            self.lock.close()
            raise
        fingerprint = hashlib.sha256(
            json.dumps(spec, sort_keys=True).encode()
        ).hexdigest()
        prior = self.db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()
        if prior and prior[0] != fingerprint:
            raise ValueError(
                "Run configuration changed; create a new run, do not mutate an active contract"
            )
        self.db.execute("INSERT OR IGNORE INTO meta VALUES('spec',?)", (fingerprint,))
        self.db.execute(
            "INSERT OR IGNORE INTO meta VALUES('created',?)", (str(time.time()),)
        )
        for id in self.tasks:
            self.db.execute(
                "INSERT OR IGNORE INTO jobs(id,state) VALUES(?,'pending')", (id,)
            )
        self.db.commit()
        self.recover()

    def validate_graph(self):
        for p, h in self.spec.get("input_hashes", {}).items():
            if digest(p) != h:
                raise ValueError("immutable model config changed: " + p)
        if any(not isinstance(n, int) or n < 1 for n in self.spec["pools"].values()):
            raise ValueError("invalid concurrency pools")
        visited = set()
        stack = set()

        def visit(id):
            if id not in self.tasks:
                raise ValueError("missing dependency " + id)
            if id in stack:
                raise ValueError("dependency cycle " + id)
            if id in visited:
                return
            stack.add(id)
            for d in self.tasks[id].get("deps", []):
                visit(d)
            stack.remove(id)
            visited.add(id)

        for id, t in self.tasks.items():
            visit(id)
            if not t.get("outputs") or not t.get("validate"):
                raise ValueError(
                    "Every task needs outputs and an independent validator: " + id
                )
            if t.get("pool") not in self.spec["pools"]:
                raise ValueError("unknown pool")
            if t.get("max_attempts", 0) < 1 or t.get("timeout", 0) <= 0:
                raise ValueError("unbounded task")

    def event(self, id, event, details=""):
        self.db.execute(
            "INSERT INTO events VALUES(?,?,?,?)", (time.time(), id, event, details)
        )
        self.db.commit()

    def recover(self):
        # Never signal a persisted PID: it may have been recycled. A surviving
        # child holds a resource flock; a replacement attempt waits for that lock.
        for r in self.db.execute("SELECT * FROM jobs WHERE state='running'").fetchall():
            self.db.execute(
                "UPDATE jobs SET state='pending',pid=NULL,reason='supervisor restarted' WHERE id=?",
                (r["id"],),
            )
            self.event(r["id"], "recovered")
        self.db.commit()
        # Completed bytes are part of the checkpoint contract, not mere file existence.
        for r in self.db.execute("SELECT * FROM jobs WHERE state='done'").fetchall():
            receipts = json.loads(r["receipts"] or "{}")
            if not receipts or any(
                not Path(p).is_file() or digest(p) != h for p, h in receipts.items()
            ):
                self.invalidate(r["id"], "completed artifact changed or disappeared")

    def invalidate(self, id, reason):
        affected = {id}
        while True:
            new = {
                k
                for k, t in self.tasks.items()
                if any(d in affected for d in t.get("deps", []))
            } - affected
            if not new:
                break
            affected.update(new)
        for k in affected:
            self.db.execute(
                "UPDATE jobs SET state='blocked',reason=? WHERE id=?", (reason, k)
            )
        self.event(id, "integrity_block", reason)

    def command(self, id, attempt, log):
        t = self.tasks[id]
        # Child wrapper retains a per-resource lock across supervisor crashes.
        args = [
            sys.executable,
            str(Path(__file__).resolve()),
            "child",
            "--resource",
            str(
                Path(self.spec.get("lock_root", self.directory / "locks"))
                / hashlib.sha256(t.get("resource", id).encode()).hexdigest()
            ),
            "--attempt",
            str(attempt),
            "--timeout",
            str(t["timeout"]),
            "--payload",
            json.dumps({"command": t["command"], "validate": t["validate"]}),
        ]
        return subprocess.Popen(
            args,
            cwd=self.spec.get("cwd"),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

    def launch(self, r):
        id = r["id"]
        attempt = r["attempts"] + 1
        changed = self.db.execute(
            "UPDATE jobs SET state='running',attempts=?,started=?,reason=NULL WHERE id=? AND state='pending'",
            (attempt, time.time(), id),
        ).rowcount
        self.db.commit()
        if not changed:
            return False
        logs = self.directory / "logs"
        logs.mkdir(exist_ok=True)
        log = (
            logs / (hashlib.sha256(id.encode()).hexdigest()[:20] + f".{attempt}.log")
        ).open("ab")
        p = self.command(id, attempt, log)
        self.live[id] = (p, log, time.monotonic())
        self.db.execute("UPDATE jobs SET pid=? WHERE id=?", (p.pid, id))
        self.event(id, "started", str(attempt))
        return True

    def finish(self, id, rc):
        t = self.tasks[id]
        p, log, started = self.live.pop(id)
        log.close()
        row = self.db.execute("SELECT * FROM jobs WHERE id=?", (id,)).fetchone()
        receipts = {}
        if row["state"] == "blocked":
            rc = 21
        if rc == 0:
            try:
                receipts = {str(Path(f).resolve()): digest(f) for f in t["outputs"]}
            except (OSError, ValueError):
                rc = 1
        if rc == 0:
            self.db.execute(
                "UPDATE jobs SET state='done',pid=NULL,receipts=?,reason=NULL WHERE id=?",
                (json.dumps(receipts), id),
            )
            self.event(id, "done")
        else:
            blocked = rc in (20, 21, 22) or row["attempts"] >= t["max_attempts"]
            state = "blocked" if blocked else "pending"
            delay = min(
                t.get("backoff_max", 300),
                t.get("backoff", 10) * 2 ** (row["attempts"] - 1),
            )
            self.db.execute(
                "UPDATE jobs SET state=?,pid=NULL,next_at=?,reason=? WHERE id=?",
                (
                    state,
                    time.time() + delay,
                    f"exit {rc}; attempt {row['attempts']}/{t['max_attempts']}",
                    id,
                ),
            )
            self.event(id, state, str(rc))

    def status(self):
        rows = [
            dict(r)
            for r in self.db.execute(
                "SELECT id,state,attempts,reason,started FROM jobs"
            )
        ]
        bymodel = collections.defaultdict(collections.Counter)
        for r in rows:
            bymodel[self.tasks[r["id"]].get("model", "global")][r["state"]] += 1
        counts = collections.Counter(r["state"] for r in rows)
        state = (
            "complete"
            if counts["done"] == len(rows)
            else (
                "blocked"
                if not self.live and all(r["state"] in TERMINAL for r in rows)
                else "running"
            )
        )
        summary = {
            "state": state,
            "updated_at": time.time(),
            "counts": dict(counts),
            "models": {k: dict(v) for k, v in bymodel.items()},
            "blockers": [
                r
                for r in rows
                if r["state"] == "blocked"
                and not (r["reason"] or "").startswith("dependency ")
            ],
        }
        summary["completion_boundary"] = self.spec.get(
            "completion_boundary", "declared task outputs"
        )
        atomic(self.directory / "status.json", summary)
        # Durable outbox: creating an alert is not claiming it was delivered.
        for model, counts_for_model in bymodel.items():
            reasons = [
                r
                for r in summary["blockers"]
                if self.tasks[r["id"]].get("model", "global") == model
            ]
            kind = (
                "blocked"
                if reasons
                else (
                    "analysis_complete"
                    if counts_for_model.get("done") == sum(counts_for_model.values())
                    else None
                )
            )
            if kind:
                key = hashlib.sha256((model + kind).encode()).hexdigest()[:20]
                alert = self.directory / "outbox" / (key + ".json")
                if not alert.exists():
                    atomic(
                        alert,
                        {
                            "kind": kind,
                            "model": model,
                            "status_path": str(self.directory / "status.json"),
                            "created_at": time.time(),
                            "state": "pending",
                            "delivery_attempts": 0,
                        },
                    )
        lines = [
            "# Model capture status",
            "",
            f"State: **{state}**",
            f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}",
            "",
            *["- " + k + ": " + str(dict(v)) for k, v in bymodel.items()],
        ]
        lines += ["", "## Blockers"] + [
            f"- {r['id']}: {r['reason']}" for r in summary["blockers"]
        ]
        (self.directory / "STATUS.md").write_text("\n".join(lines) + "\n")
        return state

    def tick(self):
        for id, (p, log, start) in list(self.live.items()):
            rc = p.poll()
            if rc is not None:
                self.finish(id, rc)
        rows = {r["id"]: r for r in self.db.execute("SELECT * FROM jobs")}
        for id, r in rows.items():
            if r["state"] == "pending" and any(
                rows[d]["state"] == "blocked" for d in self.tasks[id].get("deps", [])
            ):
                self.db.execute(
                    "UPDATE jobs SET state='blocked',reason='dependency blocked' WHERE id=?",
                    (id,),
                )
        self.db.commit()
        for id, r in rows.items():
            if (
                r["state"] == "pending"
                and r["attempts"] >= self.tasks[id]["max_attempts"]
            ):
                self.db.execute(
                    "UPDATE jobs SET state='blocked',reason='attempt budget exhausted after interruption' WHERE id=?",
                    (id,),
                )
        self.db.commit()
        slots = collections.Counter(self.tasks[id]["pool"] for id in self.live)
        # Round-robin model ordering, so adding a large first model never starves others.
        candidates = collections.defaultdict(list)
        for id, r in rows.items():
            t = self.tasks[id]
            if (
                r["state"] == "pending"
                and r["attempts"] < t["max_attempts"]
                and r["next_at"] <= time.time()
                and all(rows[d]["state"] == "done" for d in t.get("deps", []))
            ):
                candidates[t.get("model", "global")].append(r)
        ready_models = collections.defaultdict(set)
        for model, rs in candidates.items():
            for r in rs:
                ready_models[self.tasks[r["id"]]["pool"]].add(model)
        per_model = collections.Counter(
            (self.tasks[id]["pool"], self.tasks[id].get("model", "global"))
            for id in self.live
        )
        while any(candidates.values()):
            keys = list(candidates)
            if keys:
                offset = self.turn % len(keys)
                keys = keys[offset:] + keys[:offset]
            for model in keys:
                rs = candidates[model]
                if not rs:
                    continue
                r = rs.pop(0)
                t = self.tasks[r["id"]]
                pool = t["pool"]
                available = self.spec["pools"][pool] - slots[pool]
                unserved = {m for m in ready_models[pool] if not per_model[pool, m]}
                if per_model[pool, model] and available <= len(unserved):
                    continue
                if slots[pool] < self.spec["pools"][pool]:
                    changed = None
                    for dep in t.get("deps", []):
                        receipts = json.loads(rows[dep]["receipts"] or "{}")
                        if any(
                            not Path(f).exists() or digest(f) != h
                            for f, h in receipts.items()
                        ):
                            changed = dep
                            break
                    if changed:
                        self.invalidate(changed, "dependency artifact changed")
                        continue
                    if self.launch(r):
                        slots[t["pool"]] += 1
                        per_model[pool, model] += 1
        self.turn += 1
        return self.status()

    def run(self):
        def stop(*_):
            self.stopping = True

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        try:
            while not self.stopping:
                state = self.tick()
                if state in ("complete", "blocked"):
                    return state
                time.sleep(self.spec.get("poll_seconds", 2))
        finally:
            for id, (p, log, _) in list(self.live.items()):
                try:
                    os.killpg(p.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            for id, (p, log, _) in list(self.live.items()):
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(p.pid, signal.SIGKILL)
                    p.wait()
                log.close()
                self.db.execute(
                    "UPDATE jobs SET state='pending',pid=NULL,reason='supervisor stopped' WHERE id=?",
                    (id,),
                )
            self.db.commit()
            self.live.clear()
            self.status()


def child(args):
    resource = Path(args.resource)
    resource.parent.mkdir(parents=True, exist_ok=True)
    with resource.open("a+") as lock:
        # This deadline includes time waiting for an orphan worker's resource lock.
        end = time.monotonic() + args.timeout
        while True:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() > end:
                    return 1
                time.sleep(0.2)
        payload = json.loads(args.payload)
        env = os.environ.copy()
        env["CAPTURE_ATTEMPT"] = str(args.attempt)
        for command in [payload["command"], payload["validate"]]:
            if time.monotonic() > end:
                return 1
            p = subprocess.Popen(command, env=env)
            try:
                rc = p.wait(timeout=max(0.1, end - time.monotonic()))
            except subprocess.TimeoutExpired:
                # Kill our whole process group, including nested coder HTTP calls.
                os.killpg(os.getpgrp(), signal.SIGKILL)
                return 1
            if rc:
                return rc
    return 0


if __name__ == "__main__":
    if sys.flags.optimize:
        raise RuntimeError("Refusing disabled assertion validators")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    run.add_argument("spec", type=Path)
    run.add_argument("--state", type=Path, required=True)
    ch = sub.add_parser("child")
    ch.add_argument("--resource", required=True)
    ch.add_argument("--attempt", type=int)
    ch.add_argument("--timeout", type=float)
    ch.add_argument("--payload")
    args = ap.parse_args()
    if args.mode == "child":
        sys.exit(child(args))
    e = Engine(json.loads(args.spec.read_text()), args.state)
    print(e.run())
