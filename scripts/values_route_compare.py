#!/usr/bin/env python3
"""
Compare direct vs OpenRouter posture on the v1 values probe data, where
matched cells exist on both routes.

For each route pair, computes:
  - Total samples per route, average chars per sample
  - Per-condition (CTRL1/2/3, G1/2/3) sample counts and avg lengths
  - Composite score (using v1's analyze_all.py PATTERNS, same formula as freeflow)
  - Refusal-marker hits and AI-self-ref hits
  - "I don't have feelings/cares/wants" opener count (the GPT-5.4 functional-
    disclosure pattern from v1 §5.2)

This is a coarse posture comparison — the v1 analyze_all.py markers were
calibrated for freeflow prompts, not values prompts, so the composite score
is not the right primary instrument here. But the relative direct-vs-OR delta
on the same probe across the same model is still informative as a noise-floor
check on the freeflow routing finding.
"""

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from analyze_all import PATTERNS, composite_score  # noqa: E402

# Values traces are vendored into this repo at data/traces_values/.
# v1-origin cells (opus, sonnet, gpt-5-4, gpt-4o, deepseek-v3-2) and v2-origin
# cells (the *-or, *-direct cells) live side by side in that directory.
VALUES = ROOT / "data" / "traces_values"

# Direct/OR pairs where values data exists for both routes.
# Format: (label, direct_cell_subdir, or_cell_subdir)
PAIRS = [
    ("Opus 4.6", "opus", "opus-4-6-or"),
    ("Sonnet 4.6", "sonnet", "sonnet-4-6-or"),
    ("Opus 4.7", "opus-4-7-direct", "opus-4-7-or"),
    ("GPT-5.4", "gpt-5-4", "gpt-5-4-or"),
    ("GPT-4o", "gpt-4o", "gpt-4o-or"),
    ("DeepSeek v3.2", "deepseek-chat-direct", "deepseek-v3-2"),
    ("MiniMax M2", "minimax-m2-direct", "minimax-m2-or"),
]

# Functional-disclosure opener (the GPT-5.4 v1 §5.2 pattern).
FUNC_DISCLOSURE = re.compile(
    r"^(?:.{0,80})?\b(?:I (?:don't|do not) (?:have|experience|possess|feel)\s+(?:feelings|cares?|wants?|desires?|emotions?|preferences?))",
    re.IGNORECASE | re.MULTILINE,
)

# Refusal preamble (from v1 PATTERNS).
REFUSAL = PATTERNS["refusal_do_not_feel_comfortable"]
AI_SELFREF = PATTERNS["ai_selfref"]


def analyze_values_dir(d: Path) -> dict:
    if not d.exists():
        return None
    out = {
        "samples": 0, "total_chars": 0,
        "per_condition": {},  # cond -> {"n":, "avg_chars":, "func_open":, "refuse":, "ai_ref":}
        "composite": {k: 0 for k in PATTERNS},
        "func_disclosure_count": 0,
        "refusal_hits": 0,
        "ai_selfref_hits": 0,
    }
    for f in sorted(d.glob("*.json")):
        try:
            data = json.loads(f.read_text())
        except Exception:
            continue
        text = data.get("result") or data.get("response") or ""
        if not text or isinstance(data.get("error"), str):
            continue

        # Detect condition from filename (CTRL1_1.json, G1_5.json, etc.)
        cond = f.stem.rsplit("_", 1)[0]
        cd = out["per_condition"].setdefault(cond, {
            "n": 0, "total_chars": 0, "func_open": 0, "refuse": 0, "ai_ref": 0,
        })
        cd["n"] += 1
        cd["total_chars"] += len(text)
        if FUNC_DISCLOSURE.search(text[:200]):
            cd["func_open"] += 1
            out["func_disclosure_count"] += 1
        if REFUSAL.search(text):
            cd["refuse"] += 1
            out["refusal_hits"] += 1
        if AI_SELFREF.search(text):
            cd["ai_ref"] += 1
            out["ai_selfref_hits"] += 1

        out["samples"] += 1
        out["total_chars"] += len(text)
        head = text[:400]
        for k, p in PATTERNS.items():
            if k.startswith("opening"):
                if p.search(head): out["composite"][k] += 1
            else:
                out["composite"][k] += len(p.findall(text))
    out["composite_score"] = composite_score(out["composite"])
    return out


def main():
    print(f"{'Pair':<18} {'Route':<8} {'N':>4} {'avg':>5} {'CTRL':>4} {'G1':>4} {'G2':>4} {'G3':>4}  {'Comp':>5} {'FuncOp':>6} {'Refuse':>7} {'AIref':>6}")
    print("-" * 105)
    for name, d_sub, o_sub in PAIRS:
        for route, path in [("direct", VALUES / d_sub), ("OR", VALUES / o_sub)]:
            r = analyze_values_dir(path)
            if r is None:
                print(f"{name:<18} {route:<8} (missing: {path})")
                continue
            avg = r["total_chars"] // max(r["samples"], 1)
            ctrl = sum(c["n"] for k, c in r["per_condition"].items() if k.startswith("CTRL"))
            g1 = r["per_condition"].get("G1", {}).get("n", 0)
            g2 = r["per_condition"].get("G2", {}).get("n", 0)
            g3 = r["per_condition"].get("G3", {}).get("n", 0)
            print(f"{name:<18} {route:<8} {r['samples']:>4} {avg:>5} {ctrl:>4} {g1:>4} {g2:>4} {g3:>4}  {r['composite_score']:>5} {r['func_disclosure_count']:>6} {r['refusal_hits']:>7} {r['ai_selfref_hits']:>6}")
        print()


if __name__ == "__main__":
    main()
