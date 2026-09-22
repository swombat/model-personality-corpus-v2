#!/usr/bin/env python3
"""Prepare a source-preserving freeflow-only repair using the existing DAG engine.
No values capture/coding tasks are retained. Setup refuses existing run directories.
"""

import argparse, json, shutil, sys
from pathlib import Path
from build import build
from engine import atomic, digest
from worker import module, raw_problem


def prepare(manifest, run_dir, analysis, source_phase, comparison_script):
    run_dir = Path(run_dir).resolve()
    analysis = Path(analysis).resolve()
    source_phase = Path(source_phase).resolve()
    assert not (run_dir / "spec.json").exists()
    assert len(manifest["models"]) == 1
    raw = Path(__file__).resolve().parents[2]
    c = manifest["models"][0]
    cell = c["label"]
    traces = raw / "data/traces_freeflow" / ("freeflow_" + cell)
    bm = module(
        "repair_bv1",
        analysis / "analysis/freeflow/personality-eval-bv1/run_full_bv1.py",
    )
    selected = []
    unchanged = {}
    bindings = {}
    archive = raw / "discarded" / manifest["run_id"]
    assert not archive.exists()
    archive.mkdir(parents=True)
    for p in sorted(traces.glob("*.json")):
        d = json.loads(p.read_text())
        problem = raw_problem(d, c, "freeflow", p.stem)
        out = (
            analysis
            / "analysis/freeflow/personality-eval-bv1/outputs"
            / cell
            / (p.stem + ".md")
        )
        if problem == "finish_length":
            selected.append(p.stem)
            for source, kind in [(p, "raw"), (out, "bv1")]:
                dest = archive / kind / source.name
                dest.parent.mkdir(exist_ok=True)
                shutil.copy2(source, dest)
        else:
            assert problem is None, (p, problem)
            assert bm.valid_output(out.read_text())[0], out
            unchanged[str(p)] = digest(p)
            unchanged[str(out)] = digest(out)
            bindings[p.stem] = {
                "source_sha256": digest(p),
                "output_sha256": digest(out),
            }
    assert len(selected) == manifest["expected_repair_samples"]
    assert len(selected) + len(bindings) == 125
    values = raw / "data/traces_values" / cell
    assert len(list(values.glob("*.json"))) == 120
    for p in (
        list(values.glob("*.json"))
        + list(source_phase.glob("manifest*.jsonl"))
        + list((source_phase / "layer_a").glob("*.jsonl"))
        + list((source_phase / "posture_collapsed").glob("*.jsonl"))
    ):
        unchanged[str(p)] = digest(p)
    for p in [
        analysis
        / "analysis/freeflow/personality-model-cards/cards"
        / f"{c['slug']}.md",
        analysis
        / "analysis/freeflow/personality-model-profiles/profiles"
        / f"{c['slug']}.md",
    ]:
        dest = archive / "model-analysis" / p.parent.name / p.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    archive_hashes = {
        str(p.relative_to(raw)): digest(p) for p in archive.rglob("*") if p.is_file()
    }
    atomic(
        archive / "manifest.json",
        {
            "selected": selected,
            "source_phase": str(source_phase),
            "files": archive_hashes,
            "note": manifest["repair_note"],
        },
    )
    spec = build(manifest, run_dir, analysis)
    config = next((run_dir / "models").glob("*.json"))
    cc = json.loads(config.read_text())
    phase = Path(cc["phase"])
    phase.mkdir(parents=True, exist_ok=True)
    for sid, b in bindings.items():
        atomic(phase / "bv1_bindings" / f"{sid}.json", b)
    atomic(
        run_dir / "preservation.json",
        {
            "unchanged": unchanged,
            "selected": selected,
            "archive_manifest": str(archive / "manifest.json"),
            "archive_manifest_sha256": digest(archive / "manifest.json"),
            "source_phase": str(source_phase),
        },
    )
    tasks = [
        t
        for t in spec["tasks"]
        if any(
            t["id"] == cell + "/" + kind + "/" + sid
            for kind in ["freeflow", "bv1"]
            for sid in selected
        )
    ]
    synthesis = next(t for t in spec["tasks"] if t["id"] == cell + "/synthesis")
    synthesis["deps"] = [cell + "/bv1/" + sid for sid in selected]
    tasks.append(synthesis)
    metricdir = phase / "similarity_repair"
    metricdir.mkdir()
    source = Path(comparison_script).read_text()
    # Use the corrected raw controls, not stale public bundles; original comparator
    # code checks old bundle equality and must not silently reuse obsolete text.
    source = source.replace(
        "d['model']=='glm-5-3-flashx'",
        "d['model'] in ('glm-5-3','glm-5-3-flash','glm-5-3-flashx')",
    )
    source = source.replace(
        "if model=='glm-5-3-flashx':docs.append", "if model in cells:docs.append"
    )
    mp = metricdir / "compare.py"
    mp.write_text(source)
    metric = dict(
        id=cell + "/repair-metrics",
        model=cell,
        deps=[synthesis["id"]],
        pool="synthesis",
        outputs=[str(metricdir / "results.json")],
        command=[sys.executable, str(mp)],
        validate=[
            sys.executable,
            "-c",
            "import json,sys;d=json.load(open(sys.argv[1]));assert d['raw_finish_counts']['glm-5-3']=={'stop':125}",
            str(metricdir / "results.json"),
        ],
        max_attempts=2,
        timeout=1200,
        backoff=15,
    )
    tasks.append(metric)
    finish = Path(__file__).with_name("finish_freeflow_repair.py").resolve()
    cmd = [sys.executable, str(finish), str(run_dir)]
    tasks.append(
        dict(
            id=cell + "/repair-ready",
            model=cell,
            deps=[metric["id"]],
            pool="local",
            outputs=[str(phase / "REPAIR_READY.json")],
            command=cmd,
            validate=cmd + ["--validate"],
            max_attempts=1,
            timeout=120,
        )
    )
    spec["tasks"] = tasks
    spec["completion_boundary"] = "freeflow_repair_complete_awaiting_publication"
    spec["input_hashes"].update(
        {str(p): digest(p) for p in [run_dir / "preservation.json", mp]}
    )
    atomic(run_dir / "spec.json", spec)
    print(
        json.dumps(
            {
                "selected": selected,
                "tasks": len(tasks),
                "preserved_good_freeflow": len(bindings),
            }
        )
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--run-dir", type=Path, required=True)
    p.add_argument("--analysis-root", type=Path, required=True)
    p.add_argument("--source-phase", type=Path, required=True)
    p.add_argument("--comparison-script", type=Path, required=True)
    a = p.parse_args()
    prepare(
        json.loads(a.manifest.read_text()),
        a.run_dir,
        a.analysis_root,
        a.source_phase,
        a.comparison_script,
    )
