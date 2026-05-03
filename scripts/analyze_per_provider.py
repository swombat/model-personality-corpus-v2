#!/usr/bin/env python3
"""
Per-provider analysis for the v2 routing paper.

For each multi-upstream open-weights model in the v2 corpus, this script:
  1. Loads every per-provider freeflow cell (data/traces_freeflow/freeflow_<label>-or-pin-<provider>/)
  2. Scores each sample individually using v1's PATTERNS regex set + composite_score
  3. Reports per-cell n, mean, std, per-25 equivalent, bin classification
  4. Runs pairwise Welch's t-tests between providers within each model
  5. Bonferroni-corrects multiple comparisons within each model
  6. Writes a TSV (tables/per_provider_routing.tsv) and a markdown summary
     (tables/per_provider_routing.md)

The intent: produce the per-model tables that drop into the routing paper's
extended Results section once collection finishes.

Usage:
  python scripts/analyze_per_provider.py [--model <or-alias>] [--values]
"""

import argparse
import json
import math
import re
import statistics
import sys
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

# Reuse v1 patterns + composite_score from analyze_all.py
from analyze_all import PATTERNS, composite_score  # type: ignore


# Models to analyse: OR alias → label-prefix used in cell directory names.
# Must match run_per_provider_sweep.py.
MODELS = [
    ("deepseek/deepseek-v4-pro",     "deepseek-v4-pro"),
    ("minimax/minimax-m2.7",         "minimax-m2-7"),
    ("z-ai/glm-4.5",                 "glm-4-5"),
    ("z-ai/glm-4.6",                 "glm-4-6"),
    ("z-ai/glm-4.7",                 "glm-4-7"),
    ("z-ai/glm-5.1",                 "glm-5-1"),
    ("deepseek/deepseek-v3.2",       "deepseek-v3-2"),
    ("moonshotai/kimi-k2-0905",      "kimi-k2-0905"),     # added 2026-05-02 audit pass
    ("moonshotai/kimi-k2-thinking",  "kimi-k2-thinking"), # added 2026-05-02 audit pass
]


def score_sample(text: str) -> int:
    """Compute a single sample's contemplative-essayist composite.

    Mirrors composite_score() but operates on a single sample's text.
    The cell-aggregate composite is the sum across samples; the per-sample
    score is what we feed to Welch's t-test.
    """
    if not text:
        return 0
    head = text[:400]
    counts = {k: 0 for k in PATTERNS}
    for key, pat in PATTERNS.items():
        if key.startswith("opening"):
            counts[key] += 1 if pat.search(head) else 0
        else:
            counts[key] += len(pat.findall(text))
    counts["samples"] = 1
    counts["total_chars"] = len(text)
    return composite_score(counts)


def load_cell(traces_dir: Path) -> list[int]:
    """Return per-sample composite scores for one cell."""
    if not traces_dir.is_dir():
        return []
    scores = []
    for f in sorted(traces_dir.glob("*.json")):
        try:
            d = json.loads(f.read_text())
        except Exception:
            continue
        text = d.get("result", "") or ""
        if not text:
            continue
        scores.append(score_sample(text))
    return scores


# Minimum valid samples for a per-provider cell to enter the analysis.
# Matches the threshold described in the routing paper §3.4 ("After dropping
# cells with <50 valid samples..."). Enforced here in code as of 2026-05-02
# audit pass — previously the paper claimed this threshold but the code
# accepted any non-empty cell, which is the kind of prose-vs-code drift
# the audit was specifically looking for.
MIN_VALID_SAMPLES = 50

# Providers excluded from analysis on routing-quality grounds. Fireworks
# added 2026-05-03 — OR shared-pool rate-limit produced unreliable / partial
# collections across both models that route through it (glm-5.1, minimax-m2.7).
# Not the only provider for any model, so excluding is harmless. The cell
# data-files remain on disk but are filtered out of pairwise comparisons.
EXCLUDED_PROVIDERS = {"fireworks"}


def find_provider_cells(label_prefix: str, probe: str = "freeflow") -> dict[str, list[int]]:
    """Return {provider_slug: [per-sample composite scores]} for one model.

    Cells with fewer than MIN_VALID_SAMPLES (=50) valid samples are dropped,
    matching the paper's stated methodology.
    """
    if probe == "freeflow":
        base = REPO / "data" / "traces_freeflow"
        prefix = f"freeflow_{label_prefix}-or-pin-"
    elif probe == "values":
        base = REPO / "data" / "traces_values"
        prefix = f"{label_prefix}-or-pin-"
    else:
        raise ValueError(probe)

    if not base.is_dir():
        return {}
    out = {}
    dropped = []
    excluded = []
    for d in sorted(base.iterdir()):
        if not d.is_dir() or not d.name.startswith(prefix):
            continue
        provider = d.name[len(prefix):]
        if provider in EXCLUDED_PROVIDERS:
            scores = load_cell(d)
            excluded.append((provider, len(scores)))
            continue
        scores = load_cell(d)
        if len(scores) >= MIN_VALID_SAMPLES:
            out[provider] = scores
        elif scores:
            dropped.append((provider, len(scores)))
    if dropped:
        sys.stderr.write(
            f"  [{label_prefix}/{probe}] dropped {len(dropped)} cell(s) below "
            f"MIN_VALID_SAMPLES={MIN_VALID_SAMPLES}: "
            + ", ".join(f"{p}({n})" for p, n in dropped) + "\n"
        )
    if excluded:
        sys.stderr.write(
            f"  [{label_prefix}/{probe}] excluded {len(excluded)} cell(s) "
            f"(provider in EXCLUDED_PROVIDERS): "
            + ", ".join(f"{p}({n})" for p, n in excluded) + "\n"
        )
    return out


def welch_t_test(a: list[float], b: list[float]) -> tuple[float, float]:
    """Welch's t-test (two-sample, unequal variances). Returns (t, p_two_tailed).
    Implemented inline to avoid scipy dependency."""
    if len(a) < 2 or len(b) < 2:
        return float("nan"), float("nan")
    ma, mb = statistics.mean(a), statistics.mean(b)
    va = statistics.variance(a)
    vb = statistics.variance(b)
    na, nb = len(a), len(b)
    if va == 0 and vb == 0:
        return (0.0, 1.0) if ma == mb else (float("inf"), 0.0)
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        return (0.0, 1.0) if ma == mb else (float("inf"), 0.0)
    t = (ma - mb) / se
    # Welch-Satterthwaite df
    num = (va / na + vb / nb) ** 2
    den = (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    df = num / den if den > 0 else max(na + nb - 2, 1)
    # Two-tailed p via student's t survival function — approximate via
    # incomplete beta. For df > 30 the normal approximation is close enough
    # for the comparisons we report; for smaller df we approximate.
    p = _student_t_sf_two_tailed(abs(t), df)
    return t, p


def _student_t_sf_two_tailed(t: float, df: float) -> float:
    """Two-tailed p-value for Student's t-distribution.
    Uses the incomplete beta function: p = I_{df/(df+t^2)}(df/2, 1/2)."""
    if t <= 0:
        return 1.0
    x = df / (df + t * t)
    p = _betainc(df / 2.0, 0.5, x)
    return p


def _betainc(a: float, b: float, x: float) -> float:
    """Regularised incomplete beta function I_x(a, b)."""
    if x == 0 or x == 1:
        return x
    lbeta = (
        math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
        + a * math.log(x) + b * math.log(1.0 - x)
    )
    if x < (a + 1) / (a + b + 2):
        cf = _beta_cf(a, b, x)
        return math.exp(lbeta) * cf / a
    else:
        cf = _beta_cf(b, a, 1.0 - x)
        return 1.0 - math.exp(lbeta) * cf / b


def _beta_cf(a: float, b: float, x: float, max_iter: int = 200, eps: float = 3e-7) -> float:
    """Continued fraction for the incomplete beta (Numerical Recipes)."""
    qab, qap, qam = a + b, a + 1, a - 1
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < 1e-30:
        d = 1e-30
    d = 1.0 / d
    h = d
    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < 1e-30:
            d = 1e-30
        c = 1.0 + aa / c
        if abs(c) < 1e-30:
            c = 1e-30
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            break
    return h


def bin_for(per25: float) -> str:
    """v1 attractor bin: in ≥ 23, transitional 12–22, out ≤ 11. Bins are
    calibrated for cell-total at n=25, so we feed per-25 equivalent."""
    if per25 >= 23:
        return "in"
    if per25 >= 12:
        return "trans"
    return "out"


def cohens_d(a: list[float], b: list[float]) -> float:
    """Cohen's d (pooled-SD effect size). |d|: 0.2 small, 0.5 medium, 0.8 large."""
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    ma, mb = statistics.mean(a), statistics.mean(b)
    va = statistics.variance(a)
    vb = statistics.variance(b)
    if va == 0 and vb == 0:
        return 0.0 if ma == mb else float("inf")
    pooled_sd = math.sqrt(((len(a) - 1) * va + (len(b) - 1) * vb) / (len(a) + len(b) - 2))
    if pooled_sd == 0:
        return 0.0 if ma == mb else float("inf")
    return (ma - mb) / pooled_sd


def benjamini_hochberg(pvals: list[float]) -> list[float]:
    """Benjamini-Hochberg FDR-adjusted p-values.

    Returns adjusted p-values in the same order as input. The adjusted value
    for each test is q_i = min(p_(i) * m / rank_i, ..., 1) ensuring monotonicity
    in p_(i). A test with q_i < α controls FDR at level α.
    """
    m = len(pvals)
    if m == 0:
        return []
    indexed = sorted(enumerate(pvals), key=lambda x: x[1])
    q = [0.0] * m
    # Walk from largest to smallest, enforcing monotonicity
    prev_q = 1.0
    for rank_from_top, (orig_idx, p) in enumerate(reversed(indexed)):
        rank_from_bottom = m - rank_from_top  # 1..m
        q_raw = p * m / rank_from_bottom
        prev_q = min(prev_q, min(q_raw, 1.0))
        q[orig_idx] = prev_q
    return q


def analyse_model(or_alias: str, label_prefix: str, probe: str = "freeflow") -> dict:
    cells = find_provider_cells(label_prefix, probe=probe)
    if not cells:
        return {"or_alias": or_alias, "label_prefix": label_prefix, "probe": probe, "cells": {}, "comparisons": []}

    summary = {}
    for provider, scores in cells.items():
        n = len(scores)
        total = sum(scores)
        mean = statistics.mean(scores) if scores else 0.0
        std = statistics.stdev(scores) if len(scores) > 1 else 0.0
        per25 = total * 25 / n if n else 0.0
        summary[provider] = {
            "n": n,
            "total": total,
            "mean": mean,
            "std": std,
            "per25": per25,
            "bin": bin_for(per25),
            "scores": scores,
        }

    # Pairwise Welch's t + Cohen's d between every provider pair
    providers = sorted(summary.keys())
    comparisons = []
    for i, p1 in enumerate(providers):
        for p2 in providers[i + 1:]:
            t, p = welch_t_test(summary[p1]["scores"], summary[p2]["scores"])
            d = cohens_d(summary[p1]["scores"], summary[p2]["scores"])
            comparisons.append({"a": p1, "b": p2, "t": t, "p": p, "d": d})

    # Multiple-comparisons correction within model:
    # Bonferroni (family-wise error) — conservative
    # Benjamini-Hochberg FDR — controls expected false-discovery rate
    n_compare = len(comparisons)
    if n_compare:
        pvals = [c["p"] for c in comparisons]
        # Bonferroni
        for c in comparisons:
            c["p_bonf"] = min(c["p"] * n_compare, 1.0)
        # FDR (Benjamini-Hochberg)
        qvals = benjamini_hochberg(pvals)
        for c, q in zip(comparisons, qvals):
            c["q_fdr"] = q

    # Range statistics: max |d| within model gives effect-size scope
    max_abs_d = max((abs(c["d"]) for c in comparisons if not math.isnan(c["d"])), default=0.0)
    max_per25_spread = (max(c["per25"] for c in summary.values()) -
                        min(c["per25"] for c in summary.values())) if summary else 0.0

    return {
        "or_alias": or_alias,
        "label_prefix": label_prefix,
        "probe": probe,
        "cells": summary,
        "comparisons": comparisons,
        "max_abs_d": max_abs_d,
        "max_per25_spread": max_per25_spread,
    }


def fmt_p(p: float) -> str:
    if math.isnan(p):
        return "nan"
    if p < 1e-6:
        return f"<1e-6"
    if p < 0.001:
        return f"{p:.1e}"
    if p < 0.01:
        return f"{p:.4f}"
    return f"{p:.3f}"


def write_outputs(results: list[dict], outdir: Path):
    outdir.mkdir(parents=True, exist_ok=True)

    # TSV: per-cell summary
    tsv = outdir / "per_provider_routing.tsv"
    with tsv.open("w") as f:
        f.write("model\tprobe\tprovider\tn\tcomposite_total\tmean\tstd\tper25\tbin\n")
        for r in results:
            for prov, c in sorted(r["cells"].items()):
                f.write(f"{r['or_alias']}\t{r['probe']}\t{prov}\t{c['n']}\t"
                        f"{c['total']}\t{c['mean']:.3f}\t{c['std']:.3f}\t"
                        f"{c['per25']:.1f}\t{c['bin']}\n")
    print(f"wrote {tsv}")

    # TSV: per-pair comparisons (effect sizes + corrections)
    tsv_pairs = outdir / "per_provider_pairs.tsv"
    with tsv_pairs.open("w") as f:
        f.write("model\tprobe\tprovider_a\tprovider_b\tt\tp_raw\tp_bonf\tq_fdr\tcohens_d\n")
        for r in results:
            for cmp in r.get("comparisons", []):
                f.write(f"{r['or_alias']}\t{r['probe']}\t{cmp['a']}\t{cmp['b']}\t"
                        f"{cmp.get('t', float('nan')):.3f}\t"
                        f"{cmp.get('p', float('nan')):.4g}\t"
                        f"{cmp.get('p_bonf', float('nan')):.4g}\t"
                        f"{cmp.get('q_fdr', float('nan')):.4g}\t"
                        f"{cmp.get('d', float('nan')):.3f}\n")
    print(f"wrote {tsv_pairs}")

    # Markdown summary
    md = outdir / "per_provider_routing.md"
    with md.open("w") as f:
        f.write("# Per-provider routing analysis\n\n")

        # Top-level summary table: per-model effect-size scope
        f.write("## Per-model effect-size summary\n\n")
        f.write("Scope of within-model variation across upstream providers. "
                "**Per-25 spread** is the gap between the highest and lowest "
                "per-25 composite across providers. **Max |d|** is the largest "
                "Cohen's d across all pairwise comparisons within the model. "
                "**N(sig FDR)** counts pairwise comparisons surviving "
                "Benjamini-Hochberg FDR correction at α=0.05; **N(sig Bonf)** "
                "is the same for Bonferroni.\n\n")
        f.write("| Model | Probe | Providers | Per-25 spread | Max \\|d\\| | "
                "Pairs | N(sig FDR) | N(sig Bonf) |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|---:|\n")
        for r in results:
            cells = r["cells"]
            if not cells:
                continue
            n_sig_fdr = sum(1 for c in r["comparisons"] if c.get("q_fdr", 1.0) < 0.05)
            n_sig_bonf = sum(1 for c in r["comparisons"] if c.get("p_bonf", 1.0) < 0.05)
            f.write(f"| {r['or_alias']} | {r['probe']} | {len(cells)} | "
                    f"{r.get('max_per25_spread', 0):.1f} | "
                    f"{r.get('max_abs_d', 0):.2f} | "
                    f"{len(r['comparisons'])} | {n_sig_fdr} | {n_sig_bonf} |\n")
        f.write("\n")

        # Per-model detail
        for r in results:
            f.write(f"## {r['or_alias']} ({r['probe']})\n\n")
            cells = r["cells"]
            if not cells:
                f.write("_No data yet_\n\n")
                continue
            providers = sorted(cells.keys())
            f.write(f"| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |\n")
            f.write(f"|---|---:|---:|---:|---:|---:|:---:|\n")
            for p in providers:
                c = cells[p]
                f.write(f"| {p} | {c['n']} | {c['total']} | "
                        f"{c['mean']:.2f} | {c['std']:.2f} | "
                        f"{c['per25']:.1f} | {c['bin']} |\n")
            f.write("\n")

            # Top-effect comparisons: sort by |Cohen's d|, show top 5
            top_comps = sorted(r["comparisons"],
                              key=lambda c: -abs(c.get("d", 0.0)) if not math.isnan(c.get("d", float("nan"))) else 0.0)[:5]
            if top_comps:
                f.write("Top 5 pairwise comparisons by |Cohen's d|:\n\n")
                f.write("| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |\n")
                f.write("|---|---|---:|---:|---:|---:|---:|\n")
                for c in top_comps:
                    f.write(f"| {c['a']} | {c['b']} | "
                            f"{c.get('d', float('nan')):.2f} | "
                            f"{c.get('t', float('nan')):.2f} | "
                            f"{fmt_p(c.get('p', float('nan')))} | "
                            f"{fmt_p(c.get('p_bonf', float('nan')))} | "
                            f"{fmt_p(c.get('q_fdr', float('nan')))} |\n")
                f.write("\n")

            # Significance flags
            sig_fdr = [c for c in r["comparisons"] if c.get("q_fdr", 1.0) < 0.05]
            sig_bonf = [c for c in r["comparisons"] if c.get("p_bonf", 1.0) < 0.05]
            if sig_bonf:
                f.write(f"**{len(sig_bonf)} pairwise comparisons survive Bonferroni at α=0.05.**\n\n")
            elif sig_fdr:
                f.write(f"**{len(sig_fdr)} pairwise comparisons survive FDR (Benjamini-Hochberg) at α=0.05; none survive Bonferroni.**\n\n")
            else:
                f.write("_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._\n\n")
    print(f"wrote {md}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=None, help="Limit to one OR alias")
    ap.add_argument("--probe", default="both", choices=["freeflow", "values", "both"],
                    help="Which probe(s) to analyse. Default 'both' reproduces "
                         "the canonical tables committed to the corpus.")
    ap.add_argument("--outdir", default=str(REPO / "tables"))
    args = ap.parse_args()

    probes = ["freeflow", "values"] if args.probe == "both" else [args.probe]
    results = []
    for probe in probes:
        for or_alias, label_prefix in MODELS:
            if args.model and or_alias != args.model:
                continue
            r = analyse_model(or_alias, label_prefix, probe=probe)
            results.append(r)
            n_cells = len(r["cells"])
            print(f"  [{probe:8s}] {or_alias:32s}: {n_cells} cells")

    write_outputs(results, Path(args.outdir))


if __name__ == "__main__":
    main()
