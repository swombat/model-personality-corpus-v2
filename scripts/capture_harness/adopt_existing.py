#!/usr/bin/env python3
"""Verify existing raw files locally without waiting behind slow capture requests.
Atomic pending->done transitions only; never steals a running worker's lease.
The worker's exact validator and output hash contract remain authoritative.
"""

import argparse
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from engine import Engine, digest
from worker import raw_problem


def adopt(spec_path, directory):
    spec = json.loads(Path(spec_path).read_text())
    directory = Path(directory)
    if not (directory / "state.sqlite").exists():
        engine = Engine(spec, directory)
        engine.db.close()
        engine.lock.close()
    db = sqlite3.connect(directory / "state.sqlite")
    expected = hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()
    if db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()[0] != expected:
        raise ValueError("run contract mismatch")
    configs = {}
    adopted = 0
    for task in spec["tasks"]:
        command = task["command"]
        if len(command) < 4 or command[3] != "raw":
            continue
        config_path = command[2]
        if config_path not in configs:
            if digest(config_path) != spec["input_hashes"][config_path]:
                raise ValueError("model configuration changed")
            configs[config_path] = json.loads(Path(config_path).read_text())
        probe = command[command.index("--probe") + 1]
        sid = command[command.index("--sample") + 1]
        path = Path(task["outputs"][0])
        try:
            before = digest(path)
            if raw_problem(
                json.loads(path.read_text()), configs[config_path], probe, sid
            ):
                continue
            if digest(path) != before:
                continue
        except (OSError, ValueError, TypeError):
            continue
        # A concurrent scheduler may already have leased this task. In that
        # case it alone owns verification/commit; don't change it underneath.
        with db:
            n = db.execute(
                "UPDATE jobs SET state='done',reason=NULL,receipts=? WHERE id=? AND state='pending'",
                (json.dumps({str(path.resolve()): before}), task["id"]),
            ).rowcount
            if n:
                db.execute(
                    "INSERT INTO events VALUES(?,?,?,?)",
                    (time.time(), task["id"], "adopted_verified_raw", before),
                )
                adopted += 1
    db.close()
    return adopted


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("--state", type=Path, required=True)
    a = p.parse_args()
    print("Verified and adopted raw tasks:", adopt(a.spec, a.state))
