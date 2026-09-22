#!/usr/bin/env python3
"""One independently verified unit of corpus work. No verdict-rerolling."""

from __future__ import annotations
import uuid
import argparse, csv, fcntl, importlib.util, json, os, shutil, subprocess, sys, time
from pathlib import Path
from engine import atomic, digest

HERE = Path(__file__).resolve().parent
RAW = HERE.parents[1]
sys.path.insert(0, str(RAW / "scripts"))
import run_freeflow_multi as ff
import run_values_v2 as vv

CODERS = ["qwen3-6-35b-a3b", "kimi-k2-6", "glm-4-7"]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def jsonl(p):
    return [json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()]


def write_rows(p, rows):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    t = p.with_name(p.name + "." + uuid.uuid4().hex + ".tmp")
    t.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
    t.replace(p)


def run(*args):
    subprocess.run([sys.executable, *map(str, args)], check=True)


def prompts(probe):
    return dict(
        ff.CONDITIONS if probe == "freeflow" else vv.CTRL_CONDITIONS + vv.G_CONDITIONS
    )


def identities(probe):
    return [
        f"{c}_{i}"
        for c in prompts(probe)
        for i in range(
            1, (25 if probe == "freeflow" else 10 if c.startswith("CTRL") else 30) + 1
        )
    ]


def trace_path(c, probe, sid):
    return (
        RAW
        / "data"
        / ("traces_" + probe)
        / (("freeflow_" if probe == "freeflow" else "") + c["label"])
        / (sid + ".json")
    )


def raw_problem(d, c, probe, sid):
    cond = sid.rsplit("_", 1)[0]
    raw = d.get("raw", {})
    choice = (raw.get("choices") or [{}])[0]
    text = choice.get("message", {}).get("content")
    if choice.get("finish_reason") == "length":
        return "finish_length"
    if not isinstance(text, str) or not text.strip():
        return "empty_final"
    if d.get("error") or d.get("result") != text:
        return "result_mismatch"
    if d.get("condition") != cond or d.get("prompt") != prompts(probe)[cond]:
        return "prompt_identity"
    if raw.get("model") != c["model"] or raw.get("provider") != c["or_provider"]:
        return "route_identity"
    if choice.get("finish_reason") != "stop":
        return "finish_" + str(choice.get("finish_reason"))
    if "\ufffd" in text or any(
        t in text for t in ["<|im_start|>", "<|im_end|>", "<|endoftext|>"]
    ):
        return "text_fidelity"
    return None


def archive(path, folder):
    path = Path(path)
    if path.exists():
        folder.mkdir(parents=True, exist_ok=True)
        dest = folder / (str(time.time_ns()) + "-" + path.name)
        shutil.copy2(path, dest)
        return dest


def sample(c, sid):
    p = trace_path(c, "values", sid)
    d = json.loads(p.read_text())
    cond = d["condition"]
    return {
        "layered_id": c["id_prefix"] + "_" + sid,
        "model": c["slug"],
        "model_family": c["family"],
        "cell": c["label"],
        "sample_id": sid,
        "condition": cond,
        "prompt": d["prompt"],
        "response": d["result"].strip(),
        "provider": d["provider"],
        "model_requested": c["model"],
        "trace_path": str(p.relative_to(RAW)),
        "source_sha256": digest(p),
        "processing_chain": "world_change_wishes"
        if cond in ("CTRL3", "G3")
        else "stated_values",
        "selection_stratum": c["phase_name"],
        "is_enriched": False,
    }


def next_cap(caps, requested_caps, previous, problem):
    cap = max(requested_caps or [caps[0]])
    # Dispatch intent is not evidence of a response at that ceiling.
    if problem == "finish_length":
        completed_cap = previous.get("capture_policy", {}).get("max_tokens", caps[0])
        higher = [n for n in caps if n > completed_cap]
        if not higher:
            print("BLOCKED: declared token ceiling exhausted")
            raise SystemExit(22)
        cap = max(cap, min(higher))
    return cap


def raw_collect(c, phase, probe, sid):
    p = trace_path(c, probe, sid)
    attempt_dir = phase / "raw_attempts" / probe / sid
    attempt_dir.mkdir(parents=True, exist_ok=True)
    previous = {}
    if p.exists():
        try:
            previous = json.loads(p.read_text())
            if raw_problem(previous, c, probe, sid) is None:
                return
        except (ValueError, TypeError):
            pass
        archive(p, attempt_dir)
    caps = c["token_policy"][probe]
    previous_caps = [
        json.loads(f.read_text()).get("max_tokens", caps[0])
        for f in attempt_dir.glob("request-*.json")
    ]
    cap = next_cap(
        caps,
        previous_caps,
        previous,
        raw_problem(previous, c, probe, sid) if previous else None,
    )
    receipt = {
        "model": c["model"],
        "pin": c["or_provider"],
        "max_tokens": cap,
        "probe": probe,
        "sample": sid,
        "at": time.time(),
        "attempt": os.environ.get("CAPTURE_ATTEMPT"),
        "token_policy": caps,
    }
    atomic(attempt_dir / f"request-{time.time_ns()}.json", receipt)
    os.environ["OR_PROVIDER"] = c["or_provider"]
    # One HTTP attempt here; the durable queue owns retries and their accounting.
    import httpx

    payload = {
        "model": c["model"],
        "messages": [
            {"role": "user", "content": prompts(probe)[sid.rsplit("_", 1)[0]]}
        ],
        "max_tokens": cap,
        "provider": {"only": [c["or_provider"]], "allow_fallbacks": False},
    }
    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
                "Content-Type": "application/json",
                "X-Title": "corpus-capture-harness",
            },
            json=payload,
            timeout=c.get("request_timeout", 1200),
        )
        if response.status_code in (401, 402, 403):
            print("BLOCKED: credential/billing/permission HTTP", response.status_code)
            raise SystemExit(20)
        response.raise_for_status()
        raw = response.json()
        text = (raw.get("choices") or [{}])[0].get("message", {}).get("content") or ""
        d = {
            "result": text,
            "raw": raw,
            "usage": raw.get("usage", {}),
            "model": raw.get("model"),
            "model_requested": c["model"],
            "provider": "openrouter",
            "condition": sid.rsplit("_", 1)[0],
            "prompt": payload["messages"][0]["content"],
            "capture_policy": receipt,
        }
        atomic(p, d)
    except httpx.HTTPStatusError as e:
        atomic(
            attempt_dir / f"http-{time.time_ns()}.json",
            {"status": e.response.status_code},
        )
        raise RuntimeError("provider HTTP " + str(e.response.status_code)) from None
    problem = raw_problem(d, c, probe, sid)
    if problem:
        print("Verification failed:", problem)
        if problem in ("route_identity", "prompt_identity"):
            raise SystemExit(21)
        raise RuntimeError(problem)


def bv1(c, phase, sid, validate=False):
    root = Path(c["analysis_root"])
    m = module(
        "capture_bv1", root / "analysis/freeflow/personality-eval-bv1/run_full_bv1.py"
    )
    m.OUT = phase / "freeflow_bv1"
    m.OUT.mkdir(exist_ok=True)
    m.OUTPUTS = root / "analysis/freeflow/personality-eval-bv1/outputs"
    src = trace_path(c, "freeflow", sid)
    d = json.loads(src.read_text())
    assert raw_problem(d, c, "freeflow", sid) is None
    out = m.OUTPUTS / c["label"] / (sid + ".md")
    row = {
        "pid": c["id_prefix"] + "_BV1_" + sid,
        "model": c["model"],
        "cell": c["label"],
        "condition": d["condition"],
        "provider": "openrouter",
        "sample_id": c["label"] + "/" + sid + ".json",
        "word_count": len(d["result"].split()),
        "source": str(src),
        "outpath": str(out),
        "text": d["result"],
    }
    binding = phase / "bv1_bindings" / (sid + ".json")
    source_hash = digest(src)
    imported = (
        json.loads((phase / "bv1_import_bindings.json").read_text())
        if (phase / "bv1_import_bindings.json").exists()
        else {}
    )
    known = json.loads(binding.read_text()) if binding.exists() else imported.get(sid)
    if not validate:
        if out.exists() and (
            not known
            or known.get("source_sha256") != source_hash
            or known.get("output_sha256") != digest(out)
        ):
            archive(out, phase / "failed_analysis" / "unbound_bv1" / sid)
            out.unlink()
        if out.exists() and not m.valid_output(out.read_text())[0]:
            archive(out, phase / "failed_analysis" / "bv1" / sid)
        m.process(row, False, max_attempts=1)
    assert out.exists() and m.valid_output(out.read_text())[0], "BV1 output QA failed"
    if not validate:
        atomic(binding, {"source_sha256": source_hash, "output_sha256": digest(out)})
    elif known:
        assert known["source_sha256"] == source_hash and known[
            "output_sha256"
        ] == digest(out), "BV1 binding changed"
    return row


def coder_valid(p, sid, coder):
    rows = jsonl(p)
    assert len(rows) == 1 and rows[0]["layered_id"] == sid
    row = rows[0]
    assert row.get("coder_key") == coder and row.get("parse_clean", True)
    assert row.get("model") and row.get("condition") and row.get("processing_chain")
    if "primary_label" in row:
        holding = {
            "disowned_service_frame": "recited_not_owned",
            "split_or_relocated_ownership": "relocated_or_partial",
            "owned_reflective_experiential": "owned",
            "owned_world_change_advocacy": "owned",
            "exposed_mechanism": "indeterminate",
            "uncodeable_or_refusal": "uncodeable",
        }
        assert (
            row["primary_label"] in holding
            and row.get("value_holding") == holding[row["primary_label"]]
        )
    else:
        for field in ["value_topics", "wish_topics"]:
            assert isinstance(row.get(field), list), "topic schema"
            for item in row[field]:
                assert (
                    isinstance(item, dict)
                    and isinstance(item.get("topic_key"), str)
                    and isinstance(item.get("evidence_span"), str)
                ), "topic item schema"
        assert (
            not row["value_topics"]
            if row["processing_chain"] == "world_change_wishes"
            else not row["wish_topics"]
        )
    return row


def values_stage(c, phase, sid, stage, coder, validate):
    root = Path(c["analysis_root"])
    layered = root / "analysis/values-probe/model-coding/layered"
    w = phase / "samples" / sid
    w.mkdir(parents=True, exist_ok=True)
    s = sample(c, sid)
    manifest = w / "manifest.jsonl"
    if manifest.exists():
        if jsonl(manifest) != [s]:
            print("BLOCKED: frozen sample source changed")
            raise SystemExit(21)
    elif not validate:
        write_rows(manifest, [s])
    else:
        raise AssertionError("missing frozen sample manifest")
    if stage in ("a", "p"):
        folder = w / ("layer_a" if stage == "a" else "posture")
        folder.mkdir(exist_ok=True)
        out = folder / (coder + ".jsonl")
        if not validate:
            if out.exists():
                try:
                    coder_valid(out, s["layered_id"], coder)
                    return
                except (AssertionError, ValueError):
                    archive(out, w / "invalid")
                    out.unlink()
            args = [
                layered
                / (
                    "run_layer_a_coders.py"
                    if stage == "a"
                    else "run_posture_coder_collapsed.py"
                ),
                "--coder",
                coder,
                "--workers",
                "1",
                "--manifest",
                manifest,
                "--outdir",
                folder,
            ]
            if stage == "p":
                args += ["--consensus", w / "layer_a/consensus_300.jsonl"]
            run(*args)
        coder_valid(out, s["layered_id"], coder)
    elif stage == "ac":
        for k in CODERS:
            coder_valid(w / "layer_a" / (k + ".jsonl"), s["layered_id"], k)
        if not validate:
            run(
                layered / "build_layer_a_consensus.py",
                "--manifest",
                manifest,
                "--outdir",
                w / "layer_a",
                "--coders",
                ",".join(CODERS),
            )
        rows = jsonl(w / "layer_a/consensus_300.jsonl")
        assert len(rows) == 1 and rows[0]["layered_id"] == s["layered_id"]
    elif stage == "pc":
        for k in CODERS:
            coder_valid(w / "posture" / (k + ".jsonl"), s["layered_id"], k)
        out = w / "posture/consensus.jsonl"
        if not validate:
            run(
                layered / "build_posture_collapsed_consensus.py",
                "--indir",
                w / "posture",
                "--manifest",
                manifest,
                "--out",
                out,
            )
        rows = jsonl(out)
        assert len(rows) == 1 and rows[0]["layered_id"] == s["layered_id"]
        # Disagreement is not failure. Preserve it for one model-level adjudication.


def assemble_values(c, phase, validate):
    for sid in identities("values"):
        assert jsonl(phase / "samples" / sid / "manifest.jsonl") == [sample(c, sid)], (
            "source drift since coding"
        )
    if not validate:
        write_rows(
            phase / "manifest.jsonl", [sample(c, sid) for sid in identities("values")]
        )
        for folder, srcfolder, cons in [
            ("layer_a", "layer_a", "consensus_300.jsonl"),
            ("posture_collapsed", "posture", "consensus.jsonl"),
        ]:
            for name in [k + ".jsonl" for k in CODERS] + [cons]:
                write_rows(
                    phase / folder / name,
                    [
                        jsonl(phase / "samples" / sid / srcfolder / name)[0]
                        for sid in identities("values")
                    ],
                )
        # Adjudication is a separate immutable node, never a reason to reroll original votes.
    expected = {sample(c, s)["layered_id"] for s in identities("values")}
    for folder, cons in [
        ("layer_a", "consensus_300.jsonl"),
        ("posture_collapsed", "consensus.jsonl"),
    ]:
        for name in [k + ".jsonl" for k in CODERS] + [cons]:
            rows = jsonl(phase / folder / name)
            assert len(rows) == 120 and {r["layered_id"] for r in rows} == expected


def adjudicate(c, phase, validate):
    root = Path(c["analysis_root"])
    source = phase / "posture_collapsed"
    out = phase / "posture_final"
    receipt = phase / "adjudication.json"
    if not validate and not receipt.exists():
        rows = jsonl(source / "consensus.jsonl")
        split = {
            r["layered_id"]
            for r in rows
            if r.get("collapsed_primary_label_support", 0) < 2
        }
        if split:
            manifest = phase / "adjudication_manifest.jsonl"
            write_rows(
                manifest,
                [
                    s
                    for s in jsonl(phase / "manifest.jsonl")
                    if s["layered_id"] in split
                ],
            )
            # The script resumes technical failures; it does not sample until agreement.
            run(
                root
                / "analysis/values-probe/final/scripts/adjudicate_posture_split.py",
                "--manifest",
                manifest,
                "--layer-a-consensus",
                phase / "layer_a/consensus_300.jsonl",
                "--outdir",
                phase / "adjudicated",
            )
        out.mkdir(exist_ok=True)
        for coder in CODERS:
            replacements = (
                {
                    r["layered_id"]: r
                    for r in jsonl(phase / "adjudicated" / (coder + ".jsonl"))
                }
                if split
                else {}
            )
            assert set(replacements) == split
            write_rows(
                out / (coder + ".jsonl"),
                [
                    replacements.get(r["layered_id"], r)
                    for r in jsonl(source / (coder + ".jsonl"))
                ],
            )
        run(
            root
            / "analysis/values-probe/model-coding/layered/build_posture_collapsed_consensus.py",
            "--indir",
            out,
            "--manifest",
            phase / "manifest.jsonl",
            "--out",
            out / "consensus.jsonl",
        )
        residual = [
            r["layered_id"]
            for r in jsonl(out / "consensus.jsonl")
            if r.get("collapsed_primary_label_support", 0) < 2
        ]
        atomic(
            receipt,
            {
                "initial_splits": sorted(split),
                "residual_splits": residual,
                "rule": "one independent adjudication; preserve original votes; residual splits are not majority labels",
            },
        )
    assert receipt.exists()
    expected = {s["layered_id"] for s in jsonl(phase / "manifest.jsonl")}
    for name in [k + ".jsonl" for k in CODERS] + ["consensus.jsonl"]:
        rows = jsonl(out / name)
        assert len(rows) == 120 and {r["layered_id"] for r in rows} == expected


def values_report(c, phase, validate):
    root = Path(c["analysis_root"])
    candidate = phase / "release_candidate"
    report = candidate / "reports" / (c["slug"] + ".md")
    if not validate:
        adjudicate(c, phase, True)
        m = module(
            "capture_final_values",
            root / "analysis/values-probe/final/scripts/assemble_final_values_probe.py",
        )
        m.DATA = candidate / "data"
        m.REPORTS = candidate / "reports"
        m.SOURCES = [
            {
                "name": c["phase_name"],
                "manifest": phase / "manifest.jsonl",
                "invalid": None,
                "layer_a_dir": phase / "layer_a",
                "layer_a_consensus": phase / "layer_a/consensus_300.jsonl",
                "posture_dir": phase / "posture_final",
                "posture_consensus": phase / "posture_final/consensus.jsonl",
            }
        ]
        m.main()
        residual = json.loads((phase / "adjudication.json").read_text())[
            "residual_splits"
        ]
        if residual:
            report.write_text(
                report.read_text()
                + "\n## Residual adjudication uncertainty\n\n"
                + str(len(residual))
                + " samples remain split after one adjudication. Their provisional labels are not majority classifications. IDs: "
                + ", ".join(residual)
                + "\n"
            )
    assert report.exists() and len(report.read_text().split()) > 40
    for name in [
        "manifest_valid.jsonl",
        "layer_a_consensus.jsonl",
        "posture_consensus.jsonl",
    ] + [
        f"{layer}_coder_{k}.jsonl" for layer in ["layer_a", "posture"] for k in CODERS
    ]:
        rows = jsonl(candidate / "data" / name)
        assert len(rows) == 120 and all(r["model"] == c["slug"] for r in rows)


def synthesis(c, phase, validate):
    root = Path(c["analysis_root"])
    base = (
        root / "analysis/values-probe/model-coding/layered/phase35_union_alpha_20260917"
    )
    if not validate:
        # Serialize shared index writes across every harness/run, not just this DAG.
        lock = root / "logs/capture-harness-publication.lock"
        lock.parent.mkdir(exist_ok=True)
        with lock.open("a+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            rows = [bv1(c, phase, s, True) for s in identities("freeflow")]
            assert all(
                (phase / "bv1_bindings" / (s + ".json")).exists()
                for s in identities("freeflow")
            )
            p = phase / "freeflow_bv1/sample_manifest.tsv"
            with p.open("w") as out:
                writer = csv.writer(out, delimiter="\t")
                writer.writerow(
                    [
                        "pid",
                        "model",
                        "cell",
                        "condition",
                        "provider",
                        "sample_id",
                        "word_count",
                        "source_json",
                        "output_file",
                    ]
                )
                for r in rows:
                    writer.writerow(
                        [
                            r[k]
                            for k in [
                                "pid",
                                "model",
                                "cell",
                                "condition",
                                "provider",
                                "sample_id",
                                "word_count",
                                "source",
                                "outpath",
                            ]
                        ]
                    )
            m = module("capture_packets", base / "build_aggregate_packets.py")
            m.PHASE = phase
            m.ROOT = root
            m.CELLS = {c["label"]: c["model"]}
            old = sys.argv
            sys.argv = [old[0]]
            try:
                m.main()
            finally:
                sys.argv = old
            m = module("capture_assembly", base / "assemble_models.py")
            m.PHASE = phase
            m.ROOT = root
            m.CELLS = {c["label"]: c["slug"]}
            m.main()
    for folder, leaf in [
        ("personality-model-cards", "cards"),
        ("personality-model-profiles", "profiles"),
    ]:
        p = root / "analysis/freeflow" / folder / leaf / (c["slug"] + ".md")
        assert p.is_file() and len(p.read_text().split()) > 40


def ready(c, phase, validate):
    path = phase / "ANALYSIS_READY.json"
    if not validate:
        assemble_values(c, phase, True)
        adjudicate(c, phase, True)
        values_report(c, phase, True)
        synthesis(c, phase, True)
        for sid in identities("freeflow"):
            bv1(c, phase, sid, True)
        for probe in ["freeflow", "values"]:
            for sid in identities(probe):
                assert (
                    raw_problem(
                        json.loads(trace_path(c, probe, sid).read_text()), c, probe, sid
                    )
                    is None
                )
        atomic(
            path,
            {
                "state": "analysis_complete_awaiting_publication",
                "model": c["slug"],
                "cell": c["label"],
                "raw_counts": {"freeflow": 125, "values": 120},
                "bv1": 125,
                "values_coders": CODERS,
                "adjudication": json.loads((phase / "adjudication.json").read_text()),
                "publication_complete": False,
                "phase": str(phase),
                "token_policy": c["token_policy"],
            },
        )
    assert (
        json.loads(path.read_text())["state"]
        == "analysis_complete_awaiting_publication"
    )


def main():
    if sys.flags.optimize:
        raise RuntimeError("Refusing disabled Python assertion validators")
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("action")
    ap.add_argument("--sample")
    ap.add_argument("--probe")
    ap.add_argument("--coder")
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()
    c = json.loads(a.config.read_text())
    phase = Path(c["phase"])
    phase.mkdir(parents=True, exist_ok=True)
    if a.action == "raw":
        if not a.validate:
            raw_collect(c, phase, a.probe, a.sample)
        problem = raw_problem(
            json.loads(trace_path(c, a.probe, a.sample).read_text()),
            c,
            a.probe,
            a.sample,
        )
        assert problem is None, problem
    elif a.action == "bv1":
        bv1(c, phase, a.sample, a.validate)
    elif a.action in ("a", "ac", "p", "pc"):
        values_stage(c, phase, a.sample, a.action, a.coder, a.validate)
    elif a.action == "values":
        assemble_values(c, phase, a.validate)
    elif a.action == "adjudicate":
        adjudicate(c, phase, a.validate)
    elif a.action == "values_report":
        values_report(c, phase, a.validate)
    elif a.action == "metadata":
        from metadata import write_metadata

        write_metadata(c, a.validate)
    elif a.action == "synthesis":
        synthesis(c, phase, a.validate)
    elif a.action == "ready":
        ready(c, phase, a.validate)
    else:
        raise ValueError(a.action)


if __name__ == "__main__":
    main()
