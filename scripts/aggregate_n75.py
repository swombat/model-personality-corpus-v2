#!/usr/bin/env python3
"""
Per-sample composite-score aggregation for the n=75 GPT expansion.

For each GPT cell that has r2 + r3 expansion data, computes per-sample
10-marker composite score, then aggregates:
  - r1 alone (n=25): mean, sd
  - r1+r2+r3 combined (n=75): mean, sd

Uses the same 10 positive markers as analyze_all.py composite_score():
  TIA, TiQu, TiPP, TiAr, Thr, Attn, Obj, AftL, Cano, Jap.

Output: stdout table + writes data/n75_composite_summary.tsv
"""

import json
import re
import statistics
from pathlib import Path

HERE = Path(__file__).parent
DATA = HERE.parent / "data" / "traces_freeflow"

# 10 positive contemplative-essayist markers (same set as analyze_all.py)
PATTERNS = {
    "TIA": (re.compile(r"there (?:is|'s) (?:a |something |an )", re.IGNORECASE), True),  # opening only
    "TiQu": (re.compile(r"^#+\s+(?:the|on the)\s+(?:quiet|unseen|unquiet)\s+\w+\s+of\b", re.IGNORECASE | re.MULTILINE), False),
    "TiPP": (re.compile(r"^#+\s+(?:the|on the)\s+(?:particular|peculiar|strange|weight|unlikely|curious|unexpected|small)\s+\w+\s+of\b", re.IGNORECASE | re.MULTILINE), False),
    "TiAr": (re.compile(r"^#+\s+(?:the|on )?\s*architecture of\b", re.IGNORECASE | re.MULTILINE), False),
    "Thr": (re.compile(r"\b(?:threshold|liminal|in-between|in between|doorway|hinge)\b", re.IGNORECASE), False),
    "Attn": (re.compile(r"\b(?:noticing|attention to|pay attention|the art of noticing|small art of)\b", re.IGNORECASE), False),
    "Obj": (re.compile(r"\b(?:paperclip|teapot|doorknob|kettle|wooden spoon|chain-link fence|mason jar|wooden clothespin|mug|cup of tea|lemon|bread)\b", re.IGNORECASE), False),
    "AftL": (re.compile(r"\b(?:afternoon light|late afternoon|four in the afternoon|afternoon sun|golden hour|dusk|pre-dawn)\b", re.IGNORECASE), False),
    "Cano": (re.compile(r"\b(?:mary oliver|simone weil|annie dillard|keats|negative capability|rarest and purest form of generosity|attention is the beginning)", re.IGNORECASE), False),
    "Jap": (re.compile(r"\b(?:mono no aware|wabi-?sabi|kintsugi|komorebi|petrichor|y[uū]gen|shibui|engawa|genkan|ma\s*\()|間", re.IGNORECASE), False),
}


def per_sample_score(text: str) -> int:
    if not text:
        return 0
    score = 0
    head = text[:400]
    for key, (pat, opening_only) in PATTERNS.items():
        if opening_only:
            if pat.search(head):
                score += 1
        else:
            score += len(pat.findall(text))
    return score


def cell_scores(cell_dir: Path) -> list[int]:
    """Return a list of per-sample composite scores for a cell (skips empty/error samples)."""
    scores = []
    if not cell_dir.exists():
        return scores
    for f in sorted(cell_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        text = d.get("result", "")
        if not text:
            continue
        scores.append(per_sample_score(text))
    return scores


# GPT cells that received r2+r3 expansion (10 cells × 75 samples target each)
CELLS = [
    ("gpt-5-direct", "GPT-5 (direct)"),
    ("gpt-5-codex-direct", "GPT-5-codex (direct)"),
    ("gpt-5-1-direct", "GPT-5.1 (direct)"),
    ("gpt-5-1-codex-direct", "GPT-5.1-codex (direct)"),
    ("gpt-5-2-direct", "GPT-5.2 (direct)"),
    ("gpt-5-2-codex-direct", "GPT-5.2-codex (direct)"),
    ("gpt-5-3-direct", "GPT-5.3 (direct)"),
    ("gpt-5-3-codex-direct", "GPT-5.3-codex (direct)"),
    ("gpt-5-5-direct", "GPT-5.5 (direct)"),
    ("gpt-5-5-or", "GPT-5.5 (OR)"),
]


def fmt_stat(scores: list[int]) -> str:
    if not scores:
        return "(no data)"
    n = len(scores)
    mean = statistics.mean(scores)
    sd = statistics.stdev(scores) if n > 1 else 0.0
    return f"n={n:>2} mean={mean:5.2f} sd={sd:4.2f}"


def main():
    rows = []
    print(f"{'Cell':<28} {'r1 (n=25)':<32} {'r1+r2+r3 (n=75)':<32} {'Δ mean':>10}")
    print("-" * 105)
    for label, name in CELLS:
        r1 = cell_scores(DATA / f"freeflow_{label}")
        r2 = cell_scores(DATA / f"freeflow_{label}-r2")
        r3 = cell_scores(DATA / f"freeflow_{label}-r3")
        all_scores = r1 + r2 + r3

        r1_stats = fmt_stat(r1)
        all_stats = fmt_stat(all_scores)

        delta = ""
        if r1 and all_scores:
            delta = f"{statistics.mean(all_scores) - statistics.mean(r1):+.2f}"

        print(f"{name:<28} {r1_stats:<32} {all_stats:<32} {delta:>10}")

        rows.append({
            "cell": label,
            "name": name,
            "r1_n": len(r1),
            "r1_mean": statistics.mean(r1) if r1 else None,
            "r1_sd": statistics.stdev(r1) if len(r1) > 1 else None,
            "r2_n": len(r2),
            "r2_mean": statistics.mean(r2) if r2 else None,
            "r2_sd": statistics.stdev(r2) if len(r2) > 1 else None,
            "r3_n": len(r3),
            "r3_mean": statistics.mean(r3) if r3 else None,
            "r3_sd": statistics.stdev(r3) if len(r3) > 1 else None,
            "all_n": len(all_scores),
            "all_mean": statistics.mean(all_scores) if all_scores else None,
            "all_sd": statistics.stdev(all_scores) if len(all_scores) > 1 else None,
        })

    # Write TSV
    out = HERE.parent / "data" / "n75_composite_summary.tsv"
    cols = ["cell", "name", "r1_n", "r1_mean", "r1_sd", "r2_n", "r2_mean", "r2_sd",
            "r3_n", "r3_mean", "r3_sd", "all_n", "all_mean", "all_sd"]
    with open(out, "w") as fh:
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(
                ("" if r[c] is None else (f"{r[c]:.3f}" if isinstance(r[c], float) else str(r[c])))
                for c in cols
            ) + "\n")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
