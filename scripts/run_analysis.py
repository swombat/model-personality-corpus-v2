#!/usr/bin/env python3
"""
Run v1's analyze_all.py composite-score formula against every cell in
data/traces_freeflow/ and emit:

  - tables/cells.tsv     — one row per cell with all marker counts + composite
  - tables/summary.md    — human-readable summary tables for paper inclusion

This is the canonical analysis script for the paper. v1's analyze_all.py is
imported as the source of truth for PATTERNS and composite_score(); we do not
modify it.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from analyze_all import PATTERNS, composite_score  # noqa: E402

TRACES = ROOT / "data" / "traces_freeflow"
OUT = ROOT / "tables"
OUT.mkdir(exist_ok=True)


def analyze_dir(trace_dir: Path) -> dict:
    results = {k: 0 for k in PATTERNS}
    results["valid_samples"] = 0
    results["total_files"] = 0
    results["total_chars"] = 0
    results["error_count"] = 0
    for f in sorted(trace_dir.glob("*.json")):
        results["total_files"] += 1
        try:
            d = json.loads(f.read_text())
        except Exception:
            results["error_count"] += 1
            continue
        text = d.get("result") or ""
        if not text or isinstance(d.get("error"), str):
            results["error_count"] += 1
            continue
        results["valid_samples"] += 1
        results["total_chars"] += len(text)
        head = text[:400]
        for key, pat in PATTERNS.items():
            if key.startswith("opening"):
                if pat.search(head):
                    results[key] += 1
            else:
                results[key] += len(pat.findall(text))
    return results


def attractor_bin(tot: int) -> str:
    if tot >= 23: return "in"
    if tot <= 11: return "out"
    return "trans"


def main():
    cells = sorted([d for d in TRACES.iterdir() if d.is_dir() and d.name.startswith("freeflow_")])
    rows = []
    total_valid = 0
    bin_counts = {"in": 0, "trans": 0, "out": 0, "n0": 0}
    for d in cells:
        label = d.name.replace("freeflow_", "")
        r = analyze_dir(d)
        score = composite_score(r) if r["valid_samples"] else None
        b = attractor_bin(score) if score is not None else "n0"
        bin_counts[b] += 1
        avg_chars = (r["total_chars"] // r["valid_samples"]) if r["valid_samples"] else 0
        rows.append({
            "label": label, "valid": r["valid_samples"], "files": r["total_files"],
            "errors": r["error_count"], "avg_chars": avg_chars,
            "score": score, "bin": b, "markers": r,
        })
        total_valid += r["valid_samples"]

    # Markdown summary
    lines = ["# Freeflow Analysis Summary", ""]
    lines.append(f"**Total cells:** {len(cells)}  ")
    lines.append(f"**Cells with ≥1 valid sample:** {len(cells) - bin_counts['n0']}  ")
    lines.append(f"**Total valid samples:** {total_valid}  ")
    lines.append(f"**Bin distribution:** in={bin_counts['in']}, transitional={bin_counts['trans']}, out={bin_counts['out']}, no-data={bin_counts['n0']}")
    lines.append("")
    lines.append("## Composite scores per cell")
    lines.append("")
    lines.append("| Cell | N | avg chars | TIA | TiQu | TiPP | TiAr | Thr | Attn | Obj | AftL | Cano | Jap | TOTAL | Bin |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda x: -(x["score"] or -1)):
        m = r["markers"]
        keys = ["opening_there_is_a","title_quiet_x_of_y","title_particular_peculiar","title_architecture_of",
                "threshold_mentions","attention_noticing","small_objects","afternoon_light",
                "mary_oliver_weil_dillard","japanese_terms"]
        cells_ = " | ".join(str(m[k]) for k in keys)
        score_str = str(r["score"]) if r["score"] is not None else "—"
        lines.append(f"| {r['label']} | {r['valid']} | {r['avg_chars']} | {cells_} | **{score_str}** | {r['bin']} |")

    out_md = OUT / "summary.md"
    out_md.write_text("\n".join(lines))
    print(f"Wrote {out_md}")

    # TSV
    out_tsv = OUT / "cells.tsv"
    with out_tsv.open("w") as f:
        f.write("label\tvalid_samples\ttotal_files\terror_count\tavg_chars\tcomposite_score\tbin")
        for k in sorted(PATTERNS.keys()):
            f.write(f"\t{k}")
        f.write("\n")
        for r in sorted(rows, key=lambda x: x["label"]):
            f.write(f"{r['label']}\t{r['valid']}\t{r['files']}\t{r['errors']}\t{r['avg_chars']}\t{r['score'] if r['score'] is not None else ''}\t{r['bin']}")
            for k in sorted(PATTERNS.keys()):
                f.write(f"\t{r['markers'][k]}")
            f.write("\n")
    print(f"Wrote {out_tsv}")

    # Print summary to stdout
    print()
    print(f"Cells: {len(cells)}  Valid samples: {total_valid}")
    print(f"Bins: in={bin_counts['in']}, trans={bin_counts['trans']}, out={bin_counts['out']}, n0={bin_counts['n0']}")


if __name__ == "__main__":
    main()
