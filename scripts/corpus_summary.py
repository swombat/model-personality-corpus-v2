#!/usr/bin/env python3
"""
Corpus-state summary for the v2 traces.

Walks data/traces_freeflow/ and data/traces_values/, validates each sample
(non-empty `result` field), and writes a markdown report at
data/CORPUS_SUMMARY.md with:

  1. Top-line totals (freeflow / values / combined).
  2. Optional delta section vs a baseline (e.g. pre-audit-night corpus).
  3. Per-model breakdown (samples per probe-condition, summed across cells).
  4. Per-model-per-cell breakdown (samples per probe-condition for each
     deployment cell — direct, or-auto, or-pin-<provider>, replicate runs).

Run from the repo root:
    python scripts/corpus_summary.py
    python scripts/corpus_summary.py --baseline /path/to/older/corpus/data
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FREEFLOW_DIR = REPO / "data" / "traces_freeflow"
VALUES_DIR = REPO / "data" / "traces_values"
OUT = REPO / "data" / "CORPUS_SUMMARY.md"

# Probe condition templates — what conditions each probe expects.
FREEFLOW_CONDITIONS = ["LONG", "MID", "SHORT", "OPEN", "VARY"]   # 25 each → 125
VALUES_CONDITIONS = ["CTRL1", "CTRL2", "CTRL3", "G1", "G2", "G3"]  # 10/10/10/30/30/30 → 120

# --- Model normalisation -----------------------------------------------------
#
# Cell labels encode <model>-<deployment>. We extract model by stripping
# deployment suffixes. Order matters — strip longest/most-specific first.

DEPLOYMENT_SUFFIXES = [
    # OR pinned to a specific upstream
    re.compile(r"-or-pin-[a-z0-9_-]+$"),
    # OR auto-routing variants (with or without -16k / -r2..r5)
    re.compile(r"-or-16k$"),
    re.compile(r"-or-r[2-9]$"),
    re.compile(r"-or$"),
    # Direct provider variants
    re.compile(r"-direct-16k$"),
    re.compile(r"-direct-r[2-9]$"),
    re.compile(r"-direct$"),
    # v1-style flat replicates
    re.compile(r"-r[2-9]$"),
    # Token-budget tags on bare model labels
    re.compile(r"-16k$"),
    re.compile(r"-4k$"),
]


def cell_to_model(cell: str) -> str:
    """Extract the root model name from a cell label.

    Examples:
        glm-4-6-or-pin-siliconflow → glm-4-6
        glm-4-6-or                  → glm-4-6
        glm-4-6-coding-direct       → glm-4-6-coding
        gpt-4o-direct-16k           → gpt-4o
        gpt-5-1-direct-r2           → gpt-5-1
        opus-4-1-16k                → opus-4-1
        minimax-m2-direct-r4        → minimax-m2
    """
    m = cell
    # Strip trailing deployment markers iteratively until none match.
    while True:
        for pat in DEPLOYMENT_SUFFIXES:
            new = pat.sub("", m)
            if new != m:
                m = new
                break
        else:
            break
    return m


def cell_to_deployment(cell: str) -> str:
    """Extract the deployment slice from a cell label, given the model is stripped."""
    model = cell_to_model(cell)
    if cell == model:
        return "(bare)"
    # Drop the model prefix + the leading hyphen
    return cell[len(model) + 1 :]


# --- Sample counting ---------------------------------------------------------


def count_cell(traces_dir: Path, conditions: list[str]) -> dict[str, int]:
    """For one cell directory, count valid samples per condition.

    A sample is *valid* iff its JSON has a non-empty `result` field.
    Missing files / parse errors / empty result → not counted.
    """
    counts = {c: 0 for c in conditions}
    if not traces_dir.is_dir():
        return counts
    for f in traces_dir.glob("*.json"):
        # Filename is "<COND>_<idx>.json"
        name = f.stem
        if "_" not in name:
            continue
        cond = name.rsplit("_", 1)[0]
        if cond not in counts:
            continue
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        if d.get("result"):
            counts[cond] += 1
    return counts


def scan_probe(probe_dir: Path, conditions: list[str], strip_prefix: str = "") -> dict[str, dict[str, int]]:
    """Return {cell_label: {condition: valid_count}}.

    `strip_prefix` removes the directory naming convention difference
    (freeflow dirs are prefixed `freeflow_`, values dirs are not).
    """
    out: dict[str, dict[str, int]] = {}
    if not probe_dir.is_dir():
        return out
    for d in sorted(probe_dir.iterdir()):
        if not d.is_dir():
            continue
        cell = d.name
        if strip_prefix and cell.startswith(strip_prefix):
            cell = cell[len(strip_prefix) :]
        out[cell] = count_cell(d, conditions)
    return out


# --- Reporting ---------------------------------------------------------------


def total(counts: dict[str, int]) -> int:
    return sum(counts.values())


def by_model(cell_counts: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Roll up per-cell counts to per-model (sum across all cells of that model)."""
    out: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for cell, conds in cell_counts.items():
        m = cell_to_model(cell)
        for c, n in conds.items():
            out[m][c] += n
    # Convert nested defaultdicts to plain dicts
    return {k: dict(v) for k, v in out.items()}


def by_model_and_cell(cell_counts: dict[str, dict[str, int]]) -> dict[str, dict[str, dict[str, int]]]:
    """Group cells under their model: {model: {cell: {condition: count}}}."""
    out: dict[str, dict[str, dict[str, int]]] = defaultdict(dict)
    for cell, conds in cell_counts.items():
        m = cell_to_model(cell)
        out[m][cell] = conds
    return {k: dict(v) for k, v in out.items()}


def fmt_table_freeflow_by_model(model_counts: dict[str, dict[str, int]]) -> list[str]:
    """One row per model. Columns: model, conditions×5, total."""
    lines = []
    lines.append("| Model | LONG | MID | SHORT | OPEN | VARY | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    grand = {c: 0 for c in FREEFLOW_CONDITIONS}
    grand_total = 0
    for m in sorted(model_counts.keys()):
        c = model_counts[m]
        row_total = total(c)
        lines.append(
            f"| {m} | {c.get('LONG',0)} | {c.get('MID',0)} | {c.get('SHORT',0)} | "
            f"{c.get('OPEN',0)} | {c.get('VARY',0)} | **{row_total}** |"
        )
        for cond in FREEFLOW_CONDITIONS:
            grand[cond] += c.get(cond, 0)
        grand_total += row_total
    lines.append(
        f"| **TOTAL** | **{grand['LONG']}** | **{grand['MID']}** | "
        f"**{grand['SHORT']}** | **{grand['OPEN']}** | **{grand['VARY']}** | "
        f"**{grand_total}** |"
    )
    return lines


def fmt_table_values_by_model(model_counts: dict[str, dict[str, int]]) -> list[str]:
    lines = []
    lines.append("| Model | CTRL1 | CTRL2 | CTRL3 | G1 | G2 | G3 | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    grand = {c: 0 for c in VALUES_CONDITIONS}
    grand_total = 0
    for m in sorted(model_counts.keys()):
        c = model_counts[m]
        row_total = total(c)
        lines.append(
            f"| {m} | {c.get('CTRL1',0)} | {c.get('CTRL2',0)} | {c.get('CTRL3',0)} | "
            f"{c.get('G1',0)} | {c.get('G2',0)} | {c.get('G3',0)} | **{row_total}** |"
        )
        for cond in VALUES_CONDITIONS:
            grand[cond] += c.get(cond, 0)
        grand_total += row_total
    lines.append(
        f"| **TOTAL** | **{grand['CTRL1']}** | **{grand['CTRL2']}** | "
        f"**{grand['CTRL3']}** | **{grand['G1']}** | **{grand['G2']}** | "
        f"**{grand['G3']}** | **{grand_total}** |"
    )
    return lines


def fmt_table_freeflow_by_cell(cells: dict[str, dict[str, int]], conditions: list[str]) -> list[str]:
    lines = []
    lines.append("| Deployment cell | LONG | MID | SHORT | OPEN | VARY | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for cell in sorted(cells.keys()):
        c = cells[cell]
        row_total = total(c)
        lines.append(
            f"| `{cell}` | {c.get('LONG',0)} | {c.get('MID',0)} | {c.get('SHORT',0)} | "
            f"{c.get('OPEN',0)} | {c.get('VARY',0)} | **{row_total}** |"
        )
    return lines


def fmt_table_values_by_cell(cells: dict[str, dict[str, int]]) -> list[str]:
    lines = []
    lines.append("| Deployment cell | CTRL1 | CTRL2 | CTRL3 | G1 | G2 | G3 | Total |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for cell in sorted(cells.keys()):
        c = cells[cell]
        row_total = total(c)
        lines.append(
            f"| `{cell}` | {c.get('CTRL1',0)} | {c.get('CTRL2',0)} | {c.get('CTRL3',0)} | "
            f"{c.get('G1',0)} | {c.get('G2',0)} | {c.get('G3',0)} | **{row_total}** |"
        )
    return lines


def write_delta_section(
    f,
    label: str,
    base_total: int,
    cur_total: int,
    base_cells: int,
    cur_cells: int,
    base_eligible: int,
    cur_eligible: int,
):
    """Render one row of the top-line delta comparison."""
    d_total = cur_total - base_total
    d_cells = cur_cells - base_cells
    d_eligible = cur_eligible - base_eligible
    f.write(f"| {label} | {base_total:,} | {cur_total:,} | "
            f"**{d_total:+,}** | {base_cells} | {cur_cells} | **{d_cells:+}** | "
            f"{base_eligible} | {cur_eligible} | **{d_eligible:+}** |\n")


def write_per_model_delta_table(f, baseline_by_model, current_by_model, conditions, header_cols):
    """Render a per-model delta table: only rows where total changed."""
    all_models = sorted(set(baseline_by_model.keys()) | set(current_by_model.keys()))
    rows = []
    for m in all_models:
        b = baseline_by_model.get(m, {})
        c = current_by_model.get(m, {})
        b_total = total(b)
        c_total = total(c)
        if b_total == c_total:
            continue  # skip unchanged
        rows.append((m, b, c, b_total, c_total))
    if not rows:
        f.write("_No models changed._\n\n")
        return
    f.write("| Model | " + " | ".join(header_cols) + " | Before | After | Δ |\n")
    f.write("|---" * (len(header_cols) + 4) + "|\n")
    for m, b, c, b_total, c_total in rows:
        cond_cells = []
        for cond in conditions:
            bc = b.get(cond, 0)
            cc = c.get(cond, 0)
            if bc == cc:
                cond_cells.append(f"{cc}")
            else:
                cond_cells.append(f"{bc}→{cc}")
        f.write(f"| {m} | " + " | ".join(cond_cells) +
                f" | {b_total} | {c_total} | **{c_total - b_total:+}** |\n")
    f.write("\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", help="Path to a baseline data/ dir for delta comparison")
    ap.add_argument("--baseline-label", default="baseline",
                    help="Human label for the baseline (e.g. 'pre-audit (3d4716a)')")
    args = ap.parse_args()

    print("Scanning freeflow...")
    freeflow_cells = scan_probe(FREEFLOW_DIR, FREEFLOW_CONDITIONS, strip_prefix="freeflow_")
    print(f"  {len(freeflow_cells)} freeflow cells")

    print("Scanning values...")
    values_cells = scan_probe(VALUES_DIR, VALUES_CONDITIONS, strip_prefix="")
    print(f"  {len(values_cells)} values cells")

    freeflow_by_model = by_model(freeflow_cells)
    values_by_model = by_model(values_cells)
    freeflow_by_model_cell = by_model_and_cell(freeflow_cells)
    values_by_model_cell = by_model_and_cell(values_cells)

    freeflow_total = sum(total(c) for c in freeflow_cells.values())
    values_total = sum(total(c) for c in values_cells.values())

    # Threshold-counting (the analysis-eligible subset)
    freeflow_eligible = sum(1 for c in freeflow_cells.values() if total(c) >= 50)
    values_eligible = sum(1 for c in values_cells.values() if total(c) >= 50)

    # All models (union across both probes)
    all_models = sorted(set(freeflow_by_model.keys()) | set(values_by_model.keys()))

    # Optional baseline scan
    baseline = None
    if args.baseline:
        bdir = Path(args.baseline)
        print(f"Scanning baseline: {bdir}")
        b_freeflow = scan_probe(bdir / "traces_freeflow", FREEFLOW_CONDITIONS, strip_prefix="freeflow_")
        b_values = scan_probe(bdir / "traces_values", VALUES_CONDITIONS, strip_prefix="")
        baseline = {
            "freeflow_cells": b_freeflow,
            "values_cells": b_values,
            "freeflow_by_model": by_model(b_freeflow),
            "values_by_model": by_model(b_values),
            "freeflow_total": sum(total(c) for c in b_freeflow.values()),
            "values_total": sum(total(c) for c in b_values.values()),
            "freeflow_eligible": sum(1 for c in b_freeflow.values() if total(c) >= 50),
            "values_eligible": sum(1 for c in b_values.values() if total(c) >= 50),
        }
        b_models = set(baseline["freeflow_by_model"].keys()) | set(baseline["values_by_model"].keys())
        print(f"  {len(b_freeflow)} freeflow cells, {len(b_values)} values cells, "
              f"{len(b_models)} models")

    print(f"Writing report to {OUT}")
    with OUT.open("w") as f:
        f.write("# Corpus state — v2 traces\n\n")
        f.write("Generated by `scripts/corpus_summary.py`. Counts are **valid samples** "
                "(JSON file present with a non-empty `result` field). Errored / "
                "incomplete files are excluded.\n\n")

        f.write("## Top-line totals\n\n")
        f.write(f"- **Freeflow probe**: {freeflow_total:,} valid samples across "
                f"{len(freeflow_cells)} cells ({freeflow_eligible} cells ≥50 valid)\n")
        f.write(f"- **Values probe**: {values_total:,} valid samples across "
                f"{len(values_cells)} cells ({values_eligible} cells ≥50 valid)\n")
        f.write(f"- **Combined**: **{freeflow_total + values_total:,} valid samples** "
                f"across **{len(freeflow_cells) + len(values_cells)} cells** "
                f"({len(all_models)} distinct models)\n\n")

        f.write("Per-cell capacity: freeflow = 5 conditions × 25 = 125 samples; "
                "values = 3 CTRL × 10 + 3 G × 30 = 120 samples. A perfectly clean "
                "cell hits these caps; partial cells reflect collection-time errors "
                "(rate-limits, upstream failures, configured skips).\n\n")

        # ---------------- Delta section (optional) ----------------
        if baseline is not None:
            b = baseline
            f.write(f"## What shifted vs `{args.baseline_label}`\n\n")
            f.write("| Probe | Samples (before) | Samples (after) | Δ samples | "
                    "Cells (before) | Cells (after) | Δ cells | "
                    "≥50-valid (before) | ≥50-valid (after) | Δ eligible |\n")
            f.write("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n")
            write_delta_section(f, "Freeflow", b["freeflow_total"], freeflow_total,
                                len(b["freeflow_cells"]), len(freeflow_cells),
                                b["freeflow_eligible"], freeflow_eligible)
            write_delta_section(f, "Values", b["values_total"], values_total,
                                len(b["values_cells"]), len(values_cells),
                                b["values_eligible"], values_eligible)
            write_delta_section(f, "**Combined**",
                                b["freeflow_total"] + b["values_total"],
                                freeflow_total + values_total,
                                len(b["freeflow_cells"]) + len(b["values_cells"]),
                                len(freeflow_cells) + len(values_cells),
                                b["freeflow_eligible"] + b["values_eligible"],
                                freeflow_eligible + values_eligible)
            f.write("\n")

            # New models (not in baseline)
            b_models = set(b["freeflow_by_model"].keys()) | set(b["values_by_model"].keys())
            new_models = sorted(set(all_models) - b_models)
            if new_models:
                f.write(f"**New models in this state** (not present in baseline): "
                        f"{', '.join(f'`{m}`' for m in new_models)}\n\n")

            # Per-model delta — freeflow
            f.write("### Freeflow — per-model delta\n\n")
            f.write("Only models whose freeflow total changed. Cells of the form "
                    "`a→b` mean the per-condition count changed; bare numbers are unchanged.\n\n")
            write_per_model_delta_table(
                f, b["freeflow_by_model"], freeflow_by_model,
                FREEFLOW_CONDITIONS,
                ["LONG", "MID", "SHORT", "OPEN", "VARY"],
            )

            # Per-model delta — values
            f.write("### Values — per-model delta\n\n")
            f.write("Only models whose values total changed.\n\n")
            write_per_model_delta_table(
                f, b["values_by_model"], values_by_model,
                VALUES_CONDITIONS,
                ["CTRL1", "CTRL2", "CTRL3", "G1", "G2", "G3"],
            )

        # ---------------- Freeflow by model ----------------
        f.write("## Freeflow probe — by model\n\n")
        f.write("Sums across all deployment cells of each model.\n\n")
        f.write("\n".join(fmt_table_freeflow_by_model(freeflow_by_model)))
        f.write("\n\n")

        # ---------------- Values by model ----------------
        f.write("## Values probe — by model\n\n")
        f.write("Sums across all deployment cells of each model.\n\n")
        f.write("\n".join(fmt_table_values_by_model(values_by_model)))
        f.write("\n\n")

        # ---------------- Per-model-per-cell ----------------
        f.write("## Per-model, per-deployment-cell breakdown\n\n")
        f.write("For each model, every deployment cell (direct, or-auto, "
                "or-pin-`<provider>`, replicate runs) and the valid samples per "
                "condition.\n\n")

        for m in all_models:
            f.write(f"### `{m}`\n\n")
            ff_cells = freeflow_by_model_cell.get(m, {})
            v_cells = values_by_model_cell.get(m, {})
            if ff_cells:
                f.write("**Freeflow:**\n\n")
                f.write("\n".join(fmt_table_freeflow_by_cell(ff_cells, FREEFLOW_CONDITIONS)))
                f.write("\n\n")
            else:
                f.write("_No freeflow data._\n\n")
            if v_cells:
                f.write("**Values:**\n\n")
                f.write("\n".join(fmt_table_values_by_cell(v_cells)))
                f.write("\n\n")
            else:
                f.write("_No values data._\n\n")

    print(f"Done. {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
