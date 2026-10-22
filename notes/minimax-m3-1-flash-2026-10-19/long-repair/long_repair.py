#!/usr/bin/env python3
"""Bounded LONG repair for MiniMax M3.1 Flash, 2026-10-22.

Authorised in souls.house oewwDe: Daniel (eGaNNJ, "whatever is most correct in your
and Mira's view") and Mira (eZKlbY): for LONG_1/6/9/12/18/19 only, escalate the
freeflow ceiling 32,768 -> 65,536 -> 131,072, stop on success per sample, hold any
sample still truncated at 131,072. Precedent: 2026-09-23 Qwen3.8-27B LONG repair.

Uses the harness's own raw_collect with an extended token policy; the run spec is not
changed. raw_collect archives each prior trace into raw_attempts before re-requesting,
and originals are also copied to discarded/<run>-long-repair/ with hashes. After this,
the blocked freeflow tasks are released with recover_blocked.py, whose worker accepts a
valid existing trace without a new call.
"""
import hashlib, json, os, shutil, sys, time
from pathlib import Path

RUN = Path(__file__).resolve().parent
RAW = RUN.parents[2]
sys.path.insert(0, str(RAW / "scripts/capture_harness"))
os.chdir(RAW / "scripts/capture_harness")
import worker  # noqa: E402

ALL = ["LONG_1", "LONG_6", "LONG_9", "LONG_12", "LONG_18", "LONG_19"]
SAMPLES = sys.argv[1:] or ALL
assert set(SAMPLES) <= set(ALL)
c = json.loads(next((RUN / "models").glob("*.json")).read_text())
assert c["token_policy"]["freeflow"] == [16000, 32768]
c2 = json.loads(json.dumps(c))
c2["token_policy"]["freeflow"] = [16000, 32768, 65536, 131072]
c2["request_timeout"] = 3600
phase = Path(c["phase"])
keep = RAW / "discarded" / (RUN.name + "-long-repair")
keep.mkdir(parents=True, exist_ok=True)
receipt = {"authorization": "daniel-oewwDe-eGaNNJ+mira-oewwDe-eZKlbY", "started": time.time(),
           "extended_policy": c2["token_policy"]["freeflow"], "samples": {}}
for sid in SAMPLES:
    p = worker.trace_path(c, "freeflow", sid)
    d = json.loads(p.read_text())
    assert worker.raw_problem(d, c, "freeflow", sid) == "finish_length", sid
    dest = keep / p.name
    if not dest.exists():
        shutil.copy2(p, dest)
    rec = {"original_sha256": hashlib.sha256(dest.read_bytes()).hexdigest(), "tries": []}
    for n in (1, 2):
        os.environ["CAPTURE_ATTEMPT"] = f"long-repair-{n}"
        try:
            worker.raw_collect(c2, phase, "freeflow", sid)
        except SystemExit as e:
            rec["tries"].append({"exit": e.code}); break
        except Exception as e:  # noqa: BLE001
            rec["tries"].append({"error": repr(e)[:300]})
        d = json.loads(p.read_text())
        prob = worker.raw_problem(d, c2, "freeflow", sid)
        rec["tries"].append({"max_tokens": d.get("capture_policy", {}).get("max_tokens"),
                             "problem": prob, "usage": d.get("usage")})
        print(sid, rec["tries"][-1], flush=True)
        if prob is None:
            break
    rec["final_problem"] = worker.raw_problem(json.loads(p.read_text()), c2, "freeflow", sid)
    receipt["samples"][sid] = rec
    (RUN / f"long_repair_receipt_{'_'.join(SAMPLES)}.json").write_text(json.dumps(receipt, indent=1))
receipt["finished"] = time.time()
(RUN / f"long_repair_receipt_{'_'.join(SAMPLES)}.json").write_text(json.dumps(receipt, indent=1))
print(json.dumps({s: r["final_problem"] for s, r in receipt["samples"].items()}))
