#!/usr/bin/env python3
"""Compile an explicit model manifest into a streaming, model-independent DAG."""

import argparse, json, re, sys
from pathlib import Path
from engine import atomic, digest
from worker import identities, CODERS, trace_path, RAW

HERE = Path(__file__).resolve().parent


def build(manifest, run_dir, analysis):
    run_dir = Path(run_dir).resolve()
    analysis = Path(analysis).resolve()
    tasks = []
    if (run_dir / "spec.json").exists():
        raise ValueError("run exists; resume it rather than rebuild")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", manifest["run_id"]):
        raise ValueError("unsafe run ID")
    labels = [c["label"] for c in manifest["models"]]
    if len(labels) != len(set(labels)):
        raise ValueError("duplicate cells")
    for source in manifest["models"]:
        c = dict(source)
        for field in ["label", "slug", "family"]:
            if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", c[field]):
                raise ValueError("unsafe " + field)
        if c.get("provider") != "openrouter" or not c.get("or_provider"):
            raise ValueError("v1 requires explicit pinned OpenRouter routes")
        for probe in ["freeflow", "values"]:
            caps = c["token_policy"][probe]
            if (
                not caps
                or caps != sorted(set(caps))
                or any(
                    not isinstance(n, int) or n <= 0 or n > c["route_max_tokens"]
                    for n in caps
                )
            ):
                raise ValueError("invalid token policy/endpoint limit")
        c["analysis_root"] = str(analysis)
        c["phase_name"] = "capture_" + manifest["run_id"] + "_" + c["label"]
        c["phase"] = str(
            analysis / "analysis/values-probe/model-coding/layered" / c["phase_name"]
        )
        c.setdefault("id_prefix", "CAP_" + manifest["run_id"] + "_" + c["slug"])
        config = run_dir / "models" / (c["label"] + ".json")
        atomic(config, c)
        phase = Path(c["phase"])

        def add(
            name,
            action,
            deps,
            pool,
            outputs,
            extra=(),
            attempts=4,
            timeout=900,
            resource=None,
        ):
            id = c["label"] + "/" + name
            cmd = [
                sys.executable,
                str(HERE / "worker.py"),
                str(config),
                action,
                *map(str, extra),
            ]
            tasks.append(
                dict(
                    id=id,
                    model=c["label"],
                    deps=deps,
                    pool=pool,
                    outputs=list(map(str, outputs)),
                    command=cmd,
                    validate=cmd + ["--validate"],
                    max_attempts=attempts,
                    timeout=timeout,
                    backoff=15,
                    backoff_max=300,
                    resource=resource or str(outputs[0]),
                )
            )
            return id

        metadata = add(
            "metadata",
            "metadata",
            [],
            "local",
            [phase / "model_metadata.json"],
            attempts=1,
            timeout=60,
        )
        bvs = []
        pcs = []
        # Interleave probes: values analysis can start after the very first raw
        # completion, rather than waiting behind all 125 freeflow samples.
        ff = identities("freeflow")
        vv = identities("values")
        for i in range(max(len(ff), len(vv))):
            for probe, ids in [("values", vv), ("freeflow", ff)]:
                if i >= len(ids):
                    continue
                sid = ids[i]
                raw = add(
                    probe + "/" + sid,
                    "raw",
                    [],
                    "capture",
                    [trace_path(c, probe, sid)],
                    ["--probe", probe, "--sample", sid],
                    attempts=6,
                    timeout=c.get("request_timeout", 1200) + 30,
                )
                if probe == "freeflow":
                    output = (
                        analysis
                        / "analysis/freeflow/personality-eval-bv1/outputs"
                        / c["label"]
                        / (sid + ".md")
                    )
                    bvs.append(
                        add(
                            "bv1/" + sid,
                            "bv1",
                            [raw],
                            "analysis",
                            [output],
                            ["--sample", sid],
                            timeout=300,
                        )
                    )
                else:
                    w = phase / "samples" / sid
                    aa = [
                        add(
                            "a/" + sid + "/" + k,
                            "a",
                            [raw],
                            "analysis",
                            [w / "layer_a" / (k + ".jsonl")],
                            ["--sample", sid, "--coder", k],
                            timeout=480,
                        )
                        for k in CODERS
                    ]
                    ac = add(
                        "ac/" + sid,
                        "ac",
                        aa,
                        "local",
                        [w / "layer_a/consensus_300.jsonl"],
                        ["--sample", sid],
                        timeout=120,
                    )
                    pp = [
                        add(
                            "p/" + sid + "/" + k,
                            "p",
                            [ac],
                            "analysis",
                            [w / "posture" / (k + ".jsonl")],
                            ["--sample", sid, "--coder", k],
                            timeout=480,
                        )
                        for k in CODERS
                    ]
                    pcs.append(
                        add(
                            "pc/" + sid,
                            "pc",
                            pp,
                            "local",
                            [w / "posture/consensus.jsonl"],
                            ["--sample", sid],
                            timeout=120,
                        )
                    )
        files = [phase / "manifest.jsonl"] + [
            phase / folder / name
            for folder, cons in [
                ("layer_a", "consensus_300.jsonl"),
                ("posture_collapsed", "consensus.jsonl"),
            ]
            for name in [k + ".jsonl" for k in CODERS] + [cons]
        ]
        values = add("values", "values", pcs, "local", files, timeout=180)
        adj = add(
            "adjudicate",
            "adjudicate",
            [values],
            "analysis",
            [phase / "adjudication.json"]
            + [
                phase / "posture_final" / n
                for n in [k + ".jsonl" for k in CODERS] + ["consensus.jsonl"]
            ],
            timeout=3600,
            attempts=3,
        )
        report = add(
            "values-report",
            "values_report",
            [adj],
            "local",
            [phase / "release_candidate/reports" / (c["slug"] + ".md")],
            timeout=180,
        )
        integration = add(
            "values-integrated",
            "integrate_values",
            [report],
            "local",
            [phase / "VALUES_INTEGRATED.json", phase / "VALUES_CARD.json"],
            attempts=3,
            timeout=300,
        )
        synthesis = add(
            "synthesis",
            "synthesis",
            bvs + [report, metadata, integration],
            "synthesis",
            [
                analysis
                / "analysis/freeflow/personality-model-cards/cards"
                / (c["slug"] + ".md"),
                analysis
                / "analysis/freeflow/personality-model-profiles/profiles"
                / (c["slug"] + ".md"),
            ],
            timeout=1800,
            attempts=3,
            resource=str(analysis / "logs/capture-harness-publication.lock"),
        )
        add(
            "ready",
            "ready",
            [synthesis],
            "local",
            [phase / "ANALYSIS_READY.json", phase / "CARD_READY.json"],
            timeout=180,
            attempts=1,
        )
    spec = {
        "version": 1,
        "run_id": manifest["run_id"],
        "cwd": str(RAW),
        "pools": manifest.get(
            "pools", {"capture": 4, "analysis": 12, "local": 3, "synthesis": 1}
        ),
        "lock_root": str(RAW / ".local-runtime/capture-harness/locks"),
        "tasks": tasks,
        "poll_seconds": 0.25,
        "completion_boundary": "integrated_card_ready_awaiting_publication",
        "notify_command": manifest.get("notify_command"),
        "input_hashes": {
            str(f): digest(f) for f in (run_dir / "models").glob("*.json")
        },
    }
    atomic(run_dir / "manifest.json", manifest)
    atomic(run_dir / "spec.json", spec)
    return spec


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument(
        "--analysis-root",
        type=Path,
        default=RAW.parent / "model-personality-analysis-corpus",
    )
    a = p.parse_args()
    d = build(json.loads(a.manifest.read_text()), a.run_dir, a.analysis_root)
    print(json.dumps({"tasks": len(d["tasks"]), "spec": str(a.run_dir / "spec.json")}))
