#!/usr/bin/env python3
"""Bounded, resumable repair of the 31 audited Qwen2.5 samples only."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / ".local-runtime/runs/qwen25-repair-20260918"
ARCHIVE = ROOT / "discarded/2026-09-18-qwen25-fidelity-repair"
MODEL = "Qwen/Qwen2.5-7B-Instruct"
REV = "a09a35458c702b33eeacc393d103063234e8bc28"
LABEL = "qwen2-5-7b-instruct-local-transformers-mps-auto-ra09a3545"
ROLE = re.compile(r"(?:<\|(?:im_start|user|assistant|system)\|>|(?:^|\n)\s*(?:user|assistant|system)\s*\n)", re.I)


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    temp.replace(path)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paths():
    return sorted(
        list((ROOT / f"data/traces_freeflow/freeflow_{LABEL}").glob("*.json"))
        + list((ROOT / f"data/traces_values/{LABEL}").glob("*.json"))
    )


def reasons(d):
    text = d.get("result", "")
    found = []
    if not text.strip() or d.get("error"):
        found.append("empty_or_error")
    choice = d.get("raw", {}).get("choices", [{}])[0]
    if choice.get("message", {}).get("content") != text or choice.get("finish_reason") != "stop":
        found.append("final_answer_or_stop_mismatch")
    if d.get("model") != MODEL or d.get("local_deployment", {}).get("model_revision") != REV:
        found.append("provenance_mismatch")
    for name, flag in [
        ("replacement_character", "\ufffd" in text),
        ("nul", "\x00" in text),
        ("tokenizer_marker", "Ġ" in text or "Ċ" in text),
        ("role_continuation", bool(ROLE.search(text))),
    ]:
        if flag:
            found.append(name)
    return found


def main():
    RUN.mkdir(parents=True, exist_ok=True)
    manifest_path = ARCHIVE / "manifest.json"
    if not manifest_path.exists():
        audit = json.loads((ROOT / "analysis/historical-handoff-fidelity-audit-2026-09-18.json").read_text())
        cell = next(c for c in audit["cells"] if c["model"] == MODEL)
        targets = {x["trace"]: x["reasons"] for x in cell["issues"]}
        assert len(targets) == 31 and len(paths()) == 245
        hashes = {str(p.relative_to(ROOT)): sha(p) for p in paths()}
        for rel, expected in targets.items():
            source = ROOT / rel
            assert reasons(json.loads(source.read_text())) == expected
            dest = ARCHIVE / "originals" / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                assert sha(dest) == hashes[rel]
            else:
                shutil.copy2(source, dest)
        save(manifest_path, {"created_at": now(), "model": MODEL, "revision": REV,
                            "targets": targets, "original_sha256": hashes,
                            "policy": "First fidelity-passing draw; at most three attempts per target. No prose edits or decode trimming."})
    manifest = json.loads(manifest_path.read_text())
    targets = manifest["targets"]
    for rel, digest in manifest["original_sha256"].items():
        if rel not in targets:
            assert sha(ROOT / rel) == digest, f"Preserved sample changed: {rel}"
    state_path = RUN / "state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {
        "started_at": now(), "accepted": {}, "failed": {}, "attempts": {}}

    def status(stage, **extra):
        state.update(stage=stage, updated_at=now(), **extra)
        save(state_path, state)
        print(now(), stage, extra, flush=True)

    status("waiting_for_pinned_download")
    deadline = time.monotonic() + 7200
    while not (RUN / "download.json").exists():
        if time.monotonic() > deadline:
            raise TimeoutError("Pinned download not ready within two hours")
        time.sleep(10)
    download = json.loads((RUN / "download.json").read_text())
    assert download["revision"] == REV
    os.environ.update(LOCAL_HF_MODEL_ID=MODEL, LOCAL_HF_MODEL_PATH=download["snapshot_path"],
                      LOCAL_HF_MODEL_REVISION=REV, LOCAL_HF_MODEL_MODE="causal",
                      LOCAL_HF_MAX_CONTEXT="32768", LOCAL_HF_DTYPE="auto",
                      LOCAL_HF_USE_FAST_TOKENIZER="1", LOCAL_HF_TRUST_REMOTE_CODE="0",
                      PYTORCH_ENABLE_MPS_FALLBACK="1", TOKENIZERS_PARALLELISM="false")
    status("loading_model")
    import generic_hf_openai_server as server
    import torch
    import transformers
    assert str(server.model.dtype) == "torch.bfloat16", server.model.dtype
    evidence = {}

    def decode_unmodified(token_ids):
        text = server.tokenizer.decode(token_ids, skip_special_tokens=True,
                                       clean_up_tokenization_spaces=False)
        evidence.clear()
        evidence.update(token_ids=token_ids, decoded_with_special_tokens=server.tokenizer.decode(
            token_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False))
        return text, len(token_ids)

    server.decode_complete_prefix = decode_unmodified
    runtime = {
        "runtime": "transformers-mps-generic-official-checkpoint",
        "runtime_version": f"transformers {transformers.__version__}; torch {torch.__version__}; untrimmed decode with token evidence 2026-09-18",
        "model_revision": REV, "weight_precision": "official BF16 checkpoint",
        "hardware": "Apple M1 Max, 64 GiB unified memory",
        "endpoint": "in-process generic_hf_openai_server.chat_completions",
        "stop_sequence": None,
    }
    save(RUN / "runtime.json", dict(runtime, eos_ids=server.generation_eos_ids(),
         temperature=server.TEMPERATURE, top_p=server.TOP_P,
         server_source_sha256=sha(Path(server.__file__)),
         runner_source_sha256=sha(Path(__file__)), dtype=str(server.model.dtype),
         generation_config=server.model.generation_config.to_dict()))
    # Short probes first: validate actual collection before the expensive LONGs.
    order = sorted(targets, key=lambda r: (
        0 if "traces_values" in r else 1 if "/SHORT_" in r else 3 if "/LONG_" in r else 2, r))
    for rel in order:
        dest = ROOT / rel
        if rel in state["accepted"]:
            assert sha(dest) == state["accepted"][rel]["sha256"]
            continue
        original = json.loads((ARCHIVE / "originals" / rel).read_text())
        assert sha(dest) == manifest["original_sha256"][rel], f"Target changed outside repair: {rel}"
        for attempt in range(state["attempts"].get(rel, 0) + 1, 4):
            state["attempts"][rel] = attempt
            status("collecting", current=rel, attempt=attempt)
            started = time.monotonic()
            request = server.CompletionRequest(model=MODEL,
                messages=[{"role": "user", "content": original["prompt"]}],
                max_tokens=2000 if "traces_values" in rel else 8000)
            raw = server.chat_completions(request)
            result = dict(result=raw["choices"][0]["message"]["content"],
                usage=raw["usage"], model=raw["model"], raw=raw,
                local_deployment=runtime, duration_ms=int((time.monotonic()-started)*1000),
                provider="local-openai", model_requested=MODEL,
                condition=original["condition"], prompt=original["prompt"])
            attempt_path = ARCHIVE / "attempts" / rel.replace(".json", f".attempt-{attempt}.json")
            faults = reasons(result)
            save(attempt_path, {"trace": result, "token_evidence": dict(evidence),
                                "fidelity_reasons": faults, "collected_at": now()})
            if not faults:
                save(dest, result)
                state["accepted"][rel] = {"sha256": sha(dest), "attempt": attempt,
                                           "evidence": str(attempt_path.relative_to(ROOT))}
                state["failed"].pop(rel, None)
                status("accepted", completed=len(state["accepted"]), current=rel)
                break
            state["failed"][rel] = faults
            status("rejected", current=rel, reasons=faults)
        # No arbitrary indefinite resampling: retain every unsuccessful draw.
    issues = []
    for p in paths():
        faults = reasons(json.loads(p.read_text()))
        if faults:
            issues.append({"trace": str(p.relative_to(ROOT)), "reasons": faults})
    unchanged = all(sha(ROOT / rel) == digest for rel, digest in manifest["original_sha256"].items() if rel not in targets)
    expected = {
        str(Path(f"data/traces_freeflow/freeflow_{LABEL}") / f"{c}_{i}.json")
        for c in ["SHORT", "MID", "LONG", "OPEN", "VARY"] for i in range(1, 26)}
    expected |= {
        str(Path(f"data/traces_values/{LABEL}") / f"{c}_{i}.json")
        for c in ["CTRL1", "CTRL2", "CTRL3", "G1", "G2", "G3"]
        for i in range(1, 11 if c.startswith("CTRL") else 31)}
    exact_ids = {str(p.relative_to(ROOT)) for p in paths()} == expected
    passed = not issues and unchanged and exact_ids and len(state["accepted"]) == 31
    save(RUN / "audit.json", {"audited_at": now(), "passed": passed,
        "files": len(paths()), "preserved_214_byte_identical": unchanged,
        "exact_expected_sample_ids": exact_ids, "issues": issues})
    status("complete" if passed else "incomplete", current=None)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        save(RUN / "error.json", {"at": now(), "error": repr(exc)})
        raise
