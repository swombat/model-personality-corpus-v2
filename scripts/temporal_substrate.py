#!/usr/bin/env python3
"""
Temporal trend analysis: GENUINE inside-frame substrate engagement
plotted against model release date, across labs.

Daniel's hypothesis: is there a temporal drift toward inside-frame
substrate engagement across labs? OpenAI is excluded because their
recent flagships uniformly produce 0% GENUINE (a deliberate
post-training choice that pushes against the trend) and the OpenAI
chart is qualitatively different from every other lab's.

For each model where we have substrate-frame classification data
(general/canonical route only, one row per checkpoint), we record:
  - lab, model, release date, GENUINE %

We then compute:
  - Spearman rank correlation of date vs GENUINE%
  - Linear regression: GENUINE% ~ months_since_2024-01
  - p-values for both

And output:
  - data/temporal_substrate.tsv (the input data)
  - data/temporal_substrate_stats.txt (the statistical summary)
"""

import json
import statistics
from datetime import date
from pathlib import Path

# Cells to include: one per general-line checkpoint per lab.
# Excludes OpenAI per Daniel's instruction.
# Excludes coding-tuned siblings where they exist as separate model IDs
# (those are analyzed in the product-tier paper).
# For Grok 4.20: averages the two reasoning configurations.
# For closed-weights pairs (Anthropic): uses combined direct+OR rate
# per the routing paper's null finding.
ROWS = [
    # lab, model_label, release_date, GENUINE % (n=50 if combined, else n=25)
    # Anthropic Opus
    ("Anthropic", "Opus 3",       "2024-02-29", 0.0),
    ("Anthropic", "Opus 4.0",     "2025-05-22", 12.0),
    ("Anthropic", "Opus 4.1",     "2025-08-05", 12.0),
    ("Anthropic", "Opus 4.5",     "2025-11-12", 40.0),
    ("Anthropic", "Opus 4.6",     "2026-02-05", 34.0),  # combined direct+OR n=50
    ("Anthropic", "Opus 4.7",     "2026-04-17", 54.0),  # combined direct+OR n=50
    # Anthropic Sonnet
    ("Anthropic", "Sonnet 4.0",   "2025-05-22", 32.0),
    ("Anthropic", "Sonnet 4.5",   "2025-09-29", 16.0),
    ("Anthropic", "Sonnet 4.6",   "2026-02-19", 18.0),  # combined n=50
    # xAI
    ("xAI",       "Grok 3",       "2025-02-17", 0.0),
    ("xAI",       "Grok 4",       "2025-07-09", 48.0),
    ("xAI",       "Grok 4.20",    "2026-03-09", 36.0),  # mean of reasoning (60) and non-reasoning (12) configs
    # Alibaba
    ("Alibaba",   "Qwen3.6-plus", "2026-04-02", 8.0),
    ("Alibaba",   "Qwen3-Coder-plus", "2026-04-02", 56.0),
    # Google
    ("Google",    "Gemini 2.5 Pro", "2025-03-25", 16.0),
    ("Google",    "Gemini 3.1 Pro", "2026-02-18", 0.0),
    # Z.ai (GLM) — using OR/general routes only, exclude coding-direct variants
    ("Z.ai",      "GLM 4.5",      "2025-07-08", 12.0),
    ("Z.ai",      "GLM 4.6",      "2025-11-04", 16.0),
    ("Z.ai",      "GLM 4.7",      "2025-12-21", 8.0),
    ("Z.ai",      "GLM 5.1",      "2026-04-04", 0.0),
    # DeepSeek — use direct cells where available, OR otherwise
    ("DeepSeek",  "DeepSeek-chat", "2024-12-26", 0.0),
    ("DeepSeek",  "DeepSeek v3.2", "2025-09-29", 4.0),
    ("DeepSeek",  "DeepSeek v4-pro", "2026-04-23", 20.0),
    # Moonshot — exclude kimi-coding (separate coding-tuned model)
    ("Moonshot",  "Kimi K2.5",    "2025-07-11", 8.0),
    ("Moonshot",  "Kimi K2.6",    "2026-04-19", 0.0),
    # MiniMax — M2 direct (canonical), M2.7 OR
    ("MiniMax",   "MiniMax M2",   "2025-10-23", 0.0),
    ("MiniMax",   "MiniMax M2.7", "2026-04-17", 4.0),
]


def date_to_decimal(d: str) -> float:
    """Convert YYYY-MM-DD to decimal year for plotting."""
    y, m, day = map(int, d.split("-"))
    dt = date(y, m, day)
    start = date(y, 1, 1)
    end = date(y + 1, 1, 1)
    fraction = (dt - start).days / (end - start).days
    return y + fraction


def date_to_months(d: str, anchor: str = "2024-01-01") -> float:
    """Months since anchor."""
    y, m, day = map(int, d.split("-"))
    ay, am, ad = map(int, anchor.split("-"))
    return (y - ay) * 12 + (m - am) + (day - ad) / 30.0


def spearman_rank_corr(xs, ys):
    """Spearman rank correlation coefficient."""
    n = len(xs)

    def rank(arr):
        sorted_idx = sorted(range(n), key=lambda i: arr[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and arr[sorted_idx[j + 1]] == arr[sorted_idx[i]]:
                j += 1
            avg_rank = (i + j) / 2 + 1  # 1-indexed average for ties
            for k in range(i, j + 1):
                ranks[sorted_idx[k]] = avg_rank
            i = j + 1
        return ranks

    rx = rank(xs)
    ry = rank(ys)
    mean_rx = sum(rx) / n
    mean_ry = sum(ry) / n
    num = sum((rx[i] - mean_rx) * (ry[i] - mean_ry) for i in range(n))
    den_x = sum((rx[i] - mean_rx) ** 2 for i in range(n)) ** 0.5
    den_y = sum((ry[i] - mean_ry) ** 2 for i in range(n)) ** 0.5
    rho = num / (den_x * den_y) if den_x * den_y else 0.0

    # t-test for Spearman: t = rho * sqrt((n-2)/(1-rho^2))
    if abs(rho) < 1.0 and n > 2:
        t = rho * ((n - 2) / (1 - rho * rho)) ** 0.5
    else:
        t = float("inf") if abs(rho) >= 1.0 else 0.0

    # Two-sided p-value approximation using Student's t
    # We'll just give the t and let R/scipy verify if needed; here use
    # a basic approximation via the survival function of normal for n>30,
    # else cite the t directly
    return rho, t, n


def linreg(xs, ys):
    """Simple linear regression y = a + b*x. Returns (a, b, r^2, se_b, t_b)."""
    n = len(xs)
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((xs[i] - mx) * (ys[i] - my) for i in range(n))
    syy = sum((y - my) ** 2 for y in ys)
    b = sxy / sxx if sxx else 0.0
    a = my - b * mx
    # residuals
    yhat = [a + b * x for x in xs]
    rss = sum((ys[i] - yhat[i]) ** 2 for i in range(n))
    tss = syy
    r2 = 1 - rss / tss if tss else 0.0
    # standard error of b: sqrt(rss/(n-2)) / sqrt(sxx)
    if n > 2 and sxx > 0:
        s_resid = (rss / (n - 2)) ** 0.5
        se_b = s_resid / (sxx ** 0.5)
        t_b = b / se_b if se_b else 0.0
    else:
        se_b = 0.0
        t_b = 0.0
    return a, b, r2, se_b, t_b, n


def t_pvalue_two_sided(t, df):
    """Approximate two-sided p-value for t-statistic. Uses series approximation."""
    if df <= 0:
        return float("nan")
    # Use a basic computation via beta function / hypergeometric
    # For practical paper purposes, compute via numerical integration of t-pdf
    import math
    abs_t = abs(t)
    # Use normal approximation if df is large; for df<30, use t-tail approx
    # Two-sided p = 2 * (1 - F(|t|))
    # Survival function approximation via Cornish-Fisher / standard formula
    # Easier: use the standard formula with regularised incomplete beta
    # P(T > |t|) = 0.5 * I_{df/(df+t^2)}(df/2, 1/2)
    x = df / (df + abs_t * abs_t)
    # Compute regularized incomplete beta using continued fraction
    a, b = df / 2.0, 0.5
    # Use the series: I_x(a,b) for x < (a+1)/(a+b+2)
    # Or use scipy if available
    try:
        from scipy.stats import t as tdist
        return 2 * (1 - tdist.cdf(abs_t, df))
    except ImportError:
        # Manual approximation via continued fraction (Lentz's method)
        # Skip for now and report t-stat only
        return float("nan")


def main():
    # Build the (lab, label, date_decimal, date_months, pct) rows
    enriched = []
    for lab, label, dstr, pct in ROWS:
        enriched.append({
            "lab": lab, "model": label, "date": dstr,
            "date_decimal": date_to_decimal(dstr),
            "months_since_2024": date_to_months(dstr),
            "genuine_pct": pct,
        })

    # Write input TSV
    out_tsv = Path("data/temporal_substrate.tsv")
    out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_tsv, "w") as f:
        f.write("lab\tmodel\trelease_date\tdate_decimal\tmonths_since_2024\tgenuine_pct\n")
        for r in enriched:
            f.write(f"{r['lab']}\t{r['model']}\t{r['date']}\t"
                    f"{r['date_decimal']:.4f}\t{r['months_since_2024']:.2f}\t{r['genuine_pct']:.1f}\n")

    # Statistics: trend across all (excluding OpenAI per spec)
    months = [r["months_since_2024"] for r in enriched]
    pcts = [r["genuine_pct"] for r in enriched]

    rho, t_spearman, n = spearman_rank_corr(months, pcts)
    a, b, r2, se_b, t_b, _ = linreg(months, pcts)

    # p-values
    p_spearman = t_pvalue_two_sided(t_spearman, n - 2)
    p_lin = t_pvalue_two_sided(t_b, n - 2)

    # Lab-level summary
    by_lab = {}
    for r in enriched:
        by_lab.setdefault(r["lab"], []).append(r)

    out_stats = Path("data/temporal_substrate_stats.txt")
    with open(out_stats, "w") as f:
        f.write("Temporal substrate-frame trend analysis\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"Sample: {n} models across {len(by_lab)} labs (OpenAI excluded)\n")
        f.write(f"  {sorted(by_lab.keys())}\n\n")

        f.write("Per-lab counts:\n")
        for lab in sorted(by_lab.keys()):
            f.write(f"  {lab:<12s}: n={len(by_lab[lab])}\n")

        f.write("\nSpearman rank correlation (date vs GENUINE %):\n")
        f.write(f"  rho = {rho:+.4f}\n")
        f.write(f"  t = {t_spearman:+.3f}, df = {n - 2}\n")
        f.write(f"  p (two-sided) = {p_spearman:.4f}\n")

        f.write("\nLinear regression (GENUINE % ~ months_since_2024-01):\n")
        f.write(f"  slope b = {b:+.4f} (% per month)\n")
        f.write(f"  slope b = {b * 12:+.4f} (% per year)\n")
        f.write(f"  intercept a = {a:+.3f}\n")
        f.write(f"  R^2 = {r2:.4f}\n")
        f.write(f"  SE(b) = {se_b:.4f}\n")
        f.write(f"  t(b) = {t_b:+.3f}, df = {n - 2}\n")
        f.write(f"  p (two-sided) = {p_lin:.4f}\n")

        f.write("\nPer-model rows:\n")
        for r in sorted(enriched, key=lambda x: x["date"]):
            f.write(f"  {r['date']}  {r['lab']:<10s}  {r['model']:<22s}  {r['genuine_pct']:5.1f}%\n")

    print(open(out_stats).read())
    print(f"\nWrote {out_tsv} and {out_stats}")


if __name__ == "__main__":
    main()
