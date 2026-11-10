#!/usr/bin/env python3
"""Offline BV1-Luna v1.2 revalidation of ONE blocked BV1 task. Explicit, authorised,
sample-scoped lane (analysis issue #1; Mira eDbvxr/jRyQzQ 2026-11-10).

No model call, no attempt-budget reset, no transport or structural waiver, no
change to the spec. A preserved v1 answer that failed only quote_sentence_boundary
is re-judged by the v1.2 validator (analysis luna_v1_2.py). v1.2 is syntactic and
cannot tell attribution (`"Stop!" I said.`) from a new sentence, so the lane
requires --occurrence: the start offset, in the captured source, of the evidence
sentence a reviewer has read in context and confirmed is a full sentence. The
reviewer's authorization is recorded with that span and its context.

Selection: the first v1 attempt (time order) that is the v1 arm's own record for
this sample, bound to the unchanged source, sent v1's exact request, passed v1's
transport and structural checks, failed only on quote_sentence_boundary, and
passes v1.2 at the reviewed occurrence. Targeted-arm attempts are never selected.

Writes (apply only), each atomically and never over a different existing file:
the output (the attempt's own answer text), its provenance sidecar, the arm
binding, and a receipt under the phase's bv1_offline_receipts/. Then the job is
marked done with those receipts and only dependency-blocked descendants are
released. v1 and targeted attempt trees are fingerprinted before and after.
A repeat invocation after success is a verified no-op.

--check writes nothing and makes no calls; it prints the candidates, the
selected attempt and the occurrence context for review.
"""
import argparse, fcntl, hashlib, json, os, re, sqlite3, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ineligibility as INEL
import worker
from apply_luna_v1_1 import tree_fingerprint
from engine import digest

REASON = "quote_sentence_boundary"
CONTEXT = 240


def sha(b):
    return hashlib.sha256(b).hexdigest()


def write_new(path, data):
    """Atomic create; an existing file must already hold exactly these bytes."""
    path = Path(path)
    if path.exists():
        assert path.read_bytes() == data, f"refusing to overwrite a different {path}"
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".tmp{os.getpid()}")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def jbytes(obj):
    return (json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n").encode()


def arm_module(c):
    return worker.module("capture_luna_offline_v1_2",
                         Path(c["analysis_root"]) / "analysis/freeflow/personality-eval-bv1/luna_v1_2.py")


def candidates(c, phase, sid, src, row, V12):
    v1_out = worker.bv1_paths(c, phase, worker.LUNA_ARM)[0]
    adir = INEL.attempt_dir(v1_out, c, sid)
    source = row["text"]
    out = []
    for f in sorted(adir.glob("*.json")):
        raw = f.read_bytes()
        r = json.loads(raw)
        resp = r.get("response") or {}
        text = V12.attempt_text(r)
        checks = {
            "recorded_arm_is_v1": r.get("arm") == worker.LUNA_ARM,
            "in_v1_attempt_dir": f.parent.resolve() == adir.resolve(),
            "sample_id": r.get("sample_id") == f"{c['label']}/{sid}.json",
            "recorded_failure": str(r.get("qa_pass")) == "False" and r.get("qa_reason") == REASON,
            "source_bound": r.get("source_sha256") == digest(src),
            "request_is_v1": json.dumps(r.get("request"), sort_keys=True) == json.dumps(V12.payload(row), sort_keys=True),
            "transport": bool(V12.transport_valid(int(r.get("http_status") or 0), resp)),
            "v12_valid": V12.valid_output(text, source)[0],
        }
        quote = None
        m = re.search(r"## Evidence line\s*\n>\s*([^\n]+)", text)
        if m:
            quote = m.group(1).strip()
        out.append({"file": str(f), "attempt_sha256": sha(raw), "checks": checks, "eligible": all(checks.values()),
                    "quote": quote, "accepted_starts": V12.closed_quote_starts(source, quote) if quote else [],
                    "text": text, "record": r})
    return adir, out


def apply(spec_path, directory, task_id, authorization=None, occurrence=None, check_only=False):
    directory = Path(directory).resolve()
    db = sqlite3.connect(directory / "state.sqlite", timeout=30)
    try:
        return _apply(db, spec_path, directory, task_id, authorization, occurrence, check_only)
    finally:
        db.close()


def _apply(db, spec_path, directory, task_id, authorization, occurrence, check_only):
    spec = json.loads(Path(spec_path).read_text())
    fingerprint = sha(json.dumps(spec, sort_keys=True).encode())
    assert db.execute("SELECT v FROM meta WHERE k='spec'").fetchone()[0] == fingerprint
    assert all(digest(p) == h for p, h in spec.get("input_hashes", {}).items()), "spec input changed since compilation"
    tasks = {t["id"]: t for t in spec["tasks"]}
    task = tasks[task_id]
    cmd = task["command"]
    assert cmd[3] == "bv1" and "--validate" not in cmd, "not a BV1 task"
    sid = cmd[cmd.index("--sample") + 1]
    c = json.loads(Path(cmd[2]).read_text())
    c.setdefault("_config", str(Path(cmd[2]).resolve()))
    assert INEL.task_id(c, sid) == task_id
    assert c.get("bv1_evaluator") == worker.LUNA_ARM, "not a Luna v1 capture"
    phase = Path(c["phase"])
    src = worker.trace_path(c, "freeflow", sid)
    text = json.loads(src.read_text())["result"]
    assert not worker.luna_v11_applies(c, text), "unpunctuated source: belongs to v1.1"
    V12 = arm_module(c)
    arm = worker.LUNA_V12_OFFLINE_ARM
    assert V12.ARM == arm
    v1_out, _, v1_bind = worker.bv1_paths(c, phase, worker.LUNA_ARM)
    t_out, _, t_bind = worker.bv1_paths(c, phase, worker.LUNA_TARGETED_ARM)
    bv_out, outputs, bindings = worker.bv1_paths(c, phase, arm)
    out = outputs / c["label"] / (sid + ".md")
    prov = V12.provenance_path(out)
    binding = bindings / (sid + ".json")
    receipt_file = phase / "bv1_offline_receipts" / (sid + ".json")
    row = {"pid": c["id_prefix"] + "_BV1_" + sid, "condition": json.loads(src.read_text())["condition"],
           "source": str(src), "outpath": str(out), "text": text,
           "sample_id": c["label"] + "/" + sid + ".json"}
    state, reason = db.execute("SELECT state,reason FROM jobs WHERE id=?", (task_id,)).fetchone()

    if state == "done" and receipt_file.exists():
        # Repeat invocation: verify what was applied, change nothing.
        r = json.loads(receipt_file.read_text())
        assert r["arm"] == arm and r["task"] == task_id
        assert worker.bv1(c, phase, sid, validate=True)["evaluator_arm"] == arm
        assert V12.provenance_ok(out, row), "applied output no longer matches its provenance"
        return {"id": task_id, "noop": True, "applied": True, "receipt": str(receipt_file)}

    assert state == "blocked" and not (reason or "").startswith("dependency"), "only blocked roots qualify"
    assert not INEL.receipt_path(phase, sid).exists(), "task has an ineligibility receipt"
    assert not (v1_bind / (sid + ".json")).exists(), "task has a v1 binding"
    assert not (t_bind / (sid + ".json")).exists(), "task has a targeted binding"
    v1_attempts = INEL.attempt_dir(v1_out, c, sid)
    t_attempts = INEL.attempt_dir(t_out, c, sid)
    before = (tree_fingerprint(v1_attempts), tree_fingerprint(t_attempts))

    adir, cands = candidates(c, phase, sid, src, row, V12)
    selected = next((x for x in cands if x["eligible"]), None)
    sel = {"id": task_id, "sample": sid, "state": state, "reason": reason, "arm": arm,
           "validator": V12.VALIDATOR, "validator_code_sha256": V12.code_sha256(),
           "source": str(src), "source_sha256": digest(src),
           "candidates": [{k: v for k, v in x.items() if k not in ("text", "record")} for x in cands],
           "selected": None, "output": str(out), "binding": str(binding), "receipt": str(receipt_file),
           "v1_attempts": before[0], "targeted_attempts": before[1], "writes": 0, "model_calls": 0}
    if selected:
        q = selected["quote"]
        sel["selected"] = {"file": selected["file"], "attempt_sha256": selected["attempt_sha256"], "quote": q,
                           "accepted_starts": selected["accepted_starts"],
                           "contexts": {str(s): text[max(0, s - CONTEXT):s + len(q) + CONTEXT] for s in selected["accepted_starts"]}}
    if check_only:
        return sel

    assert selected, "no eligible preserved v1 attempt"
    assert authorization and authorization.strip(), "authorization required"
    assert occurrence is not None and occurrence in selected["accepted_starts"], \
        "--occurrence must be a reviewed start offset that v1.2 accepts"
    lock = (directory / "repair.lock").open("a+")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        # Fresh rechecks immediately before any write.
        adir2, cands2 = candidates(c, phase, sid, src, row, V12)
        again = next((x for x in cands2 if x["eligible"]), None)
        assert again and again["file"] == selected["file"] and again["attempt_sha256"] == selected["attempt_sha256"]
        assert (tree_fingerprint(v1_attempts), tree_fingerprint(t_attempts)) == before, "attempt trees changed"
        q = again["quote"]
        context = text[max(0, occurrence - CONTEXT):occurrence + len(q) + CONTEXT]
        body = (again["text"].rstrip() + "\n").encode()
        rec = again["record"]
        write_new(out, body)
        provenance = {
            "arm": arm, "validator": V12.VALIDATOR, "validator_code_sha256": V12.code_sha256(),
            "original_arm": worker.LUNA_ARM, "attempt_file": again["file"], "attempt_sha256": again["attempt_sha256"],
            "source_sha256": digest(src), "request_sha256": V12.request_sha256(row),
            "response_sha256": sha(json.dumps(rec.get("response"), sort_keys=True, ensure_ascii=False).encode()),
            "output_sha256": sha(body),
        }
        write_new(prov, jbytes(provenance))
        assert V12.provenance_ok(out, row), "provenance does not verify"
        write_new(binding, jbytes({"source_sha256": digest(src), "output_sha256": sha(body), "evaluator_arm": arm}))
        receipt = dict(provenance, task=task_id, sample=sid, authorization=authorization,
                       occurrence={"start": occurrence, "end": occurrence + len(q), "quote": q,
                                   "context": context, "context_sha256": sha(context.encode())},
                       v1_attempts=before[0], targeted_attempts=before[1],
                       output=str(out), provenance=str(prov), binding=str(binding))
        write_new(receipt_file, jbytes(receipt))
        row_check = worker.bv1(c, phase, sid, validate=True)
        assert row_check["evaluator_arm"] == arm
        assert (tree_fingerprint(v1_attempts), tree_fingerprint(t_attempts)) == before, "attempt trees changed"
        receipts = json.dumps({str(p.resolve()): digest(p) for p in (out, prov, binding, receipt_file)})
        with db:
            assert db.execute(
                "UPDATE jobs SET state='done',reason=?,receipts=?,pid=NULL WHERE id=? AND state='blocked'",
                (f"evaluated: {arm} (offline revalidation {authorization})", receipts, task_id),
            ).rowcount == 1
            db.execute("INSERT INTO events VALUES(?,?,?,?)", (time.time(), task_id, "bv1_offline_revalidation_applied",
                       json.dumps({"arm": arm, "authorization": authorization, "receipt": str(receipt_file),
                                   "receipt_sha256": digest(receipt_file)})))
            descendants = {task_id}
            for _ in tasks:
                found = {i for i, t in tasks.items() if any(d in descendants for d in t["deps"])}
                if found <= descendants:
                    break
                descendants |= found
            for dep in descendants - {task_id}:
                db.execute("UPDATE jobs SET state='pending',reason=NULL,next_at=0 "
                           "WHERE id=? AND state='blocked' AND reason='dependency blocked'", (dep,))
        sel.update(applied=True, writes=4, output_sha256=sha(body))
        return sel
    finally:
        lock.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("spec", type=Path)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--authorization")
    p.add_argument("--occurrence", type=int)
    p.add_argument("--check", action="store_true", help="dry run: no calls, writes nothing")
    p.add_argument("id")
    a = p.parse_args()
    print(json.dumps(apply(a.spec, a.state, a.id, a.authorization, a.occurrence, a.check), indent=1, ensure_ascii=False))
