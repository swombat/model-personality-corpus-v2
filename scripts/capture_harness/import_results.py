#!/usr/bin/env python3
"""Import verified prior values annotations without repeating paid work.
Run only after old writers have stopped. Frozen manifest hashes must match raw.
"""

import argparse, json
from pathlib import Path
from engine import digest, atomic
from worker import CODERS, RAW, sample, write_rows, bv1


def import_phase(run_dir, source):
    run_dir = Path(run_dir)
    source = Path(source)
    manifests = list(source.glob("manifest*.jsonl"))
    if len(manifests) != 1:
        raise ValueError("expected one frozen source manifest")
    originals = {
        r["layered_id"]: r
        for r in [
            json.loads(l) for l in manifests[0].read_text().splitlines() if l.strip()
        ]
    }
    maps = {}
    for folder in ["layer_a", "posture_collapsed"]:
        for k in CODERS:
            p = source / folder / (k + ".jsonl")
            rows = (
                [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
                if p.exists()
                else []
            )
            if len({r["layered_id"] for r in rows}) != len(rows):
                raise ValueError("duplicate source records")
            maps[folder, k] = {r["layered_id"]: r for r in rows}
    report = {}
    for config in sorted((run_dir / "models").glob("*.json")):
        c = json.loads(config.read_text())
        phase = Path(c["phase"])
        count = 0
        for id, s in originals.items():
            if s["cell"] != c["label"]:
                continue
            if digest(RAW / s["trace_path"]) != s["source_sha256"]:
                raise ValueError("source raw hash changed")
            current = sample(c, s["sample_id"])
            for field in [
                "layered_id",
                "model",
                "condition",
                "prompt",
                "response",
                "cell",
            ]:
                if current[field] != s[field]:
                    raise ValueError("manifest identity mismatch " + field)
            w = phase / "samples" / s["sample_id"]
            write_rows(w / "manifest.jsonl", [current])
            for folder, target in [
                ("layer_a", "layer_a"),
                ("posture_collapsed", "posture"),
            ]:
                for k in CODERS:
                    if id not in maps[folder, k]:
                        continue
                    row = maps[folder, k][id]
                    if not row.get("parse_clean", True):
                        continue
                    dest = w / target / (k + ".jsonl")
                    if dest.exists():
                        raise ValueError("target already exists; refusing overwrite")
                    write_rows(dest, [row])
                    count += 1
        # Reused legacy BV1 artifacts are explicitly adopted at the current raw
        # hash only after the old writer is stopped and its input run is named.
        bindings = {}
        for sid in __import__("worker").identities("freeflow"):
            try:
                row = bv1(c, phase, sid, True)
                bindings[sid] = {
                    "source_sha256": digest(row["source"]),
                    "output_sha256": digest(row["outpath"]),
                }
            except (OSError, AssertionError, ValueError):
                continue
        atomic(phase / "bv1_import_bindings.json", bindings)
        report[c["label"]] = {
            "values_annotations": count,
            "bv1": len(bindings),
            "source_phase": str(source),
        }
    atomic(run_dir / "import_receipt.json", report)
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("run_dir", type=Path)
    p.add_argument("source_phase", type=Path)
    p.add_argument("--old-writers-stopped", action="store_true", required=True)
    a = p.parse_args()
    print(json.dumps(import_phase(a.run_dir, a.source_phase), indent=2))
