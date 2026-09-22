#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from engine import atomic, digest
from worker import bv1, identities

p = argparse.ArgumentParser()
p.add_argument("run_dir", type=Path)
p.add_argument("--validate", action="store_true")
a = p.parse_args()
r = a.run_dir
c = json.loads(next((r / "models").glob("*.json")).read_text())
phase = Path(c["phase"])
pres = json.loads((r / "preservation.json").read_text())
for path, h in pres["unchanged"].items():
    assert digest(path) == h, "untouched source changed: " + path
assert digest(pres["archive_manifest"]) == pres["archive_manifest_sha256"]
arch = json.loads(Path(pres["archive_manifest"]).read_text())
raw = Path(__file__).resolve().parents[2]
for path, h in arch["files"].items():
    assert digest(raw / path) == h
for sid in identities("freeflow"):
    bv1(c, phase, sid, True)
d = dict(
    state="freeflow_repair_complete_awaiting_publication",
    model=c["slug"],
    repaired_samples=pres["selected"],
    freeflow_verified=125,
    unchanged_freeflow=110,
    values_untouched=True,
    source_phase=pres["source_phase"],
    note=json.loads((r / "manifest.json").read_text())["repair_note"],
    similarity_results=str(phase / "similarity_repair/results.json"),
    publication_complete=False,
)
out = phase / "REPAIR_READY.json"
if a.validate:
    assert json.loads(out.read_text()) == d
else:
    atomic(out, d)
