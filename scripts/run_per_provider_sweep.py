#!/usr/bin/env python3
"""
Per-provider per-model sweep: for each open-weights model in the v2 corpus
that has multiple OR upstreams, collect freeflow + values traces pinned to
each upstream provider via OR's `provider.only` mechanism.

This is the data-collection script that produces the per-provider cells the
v2 routing paper needs to extend its open-weights case beyond N=1 (M2 alone).

Cells produced per (model, provider):
  - freeflow: 5 conditions × 25 samples = 125 samples
  - values:   3 CTRL × 10 + 3 G × 30 = 120 samples
  Total: 245 samples per cell.

Models covered (multi-provider on OR per the endpoints API, queried 2026-05-02):
  deepseek/deepseek-v4-pro    (7 providers, including DeepSeek themselves)
  minimax/minimax-m2.7        (4 providers)
  z-ai/glm-4.5                (2 providers)
  z-ai/glm-4.6                (6 providers)
  z-ai/glm-4.7                (11 providers)
  z-ai/glm-5.1                (15 providers)
  deepseek/deepseek-v3.2      (11 providers; no clean direct comparator
                               but cross-provider analysis still informative)
  moonshotai/kimi-k2-0905     (4 providers — added 2026-05-02 audit pass)
  moonshotai/kimi-k2-thinking (3 providers — added 2026-05-02 audit pass)

Excluded (single-provider on OR — per-provider analysis not possible):
  qwen/qwen3.6-plus           (Alibaba only)
  qwen/qwen3-coder-plus       (Alibaba only)
  moonshotai/kimi-k2          (Novita only)

Total cells: ~63. Total samples: ~63 × 245 = ~15,400.

Usage:
  source keys.env
  python scripts/run_per_provider_sweep.py [--max-parallel-cells 4] [--dry-run]
                                           [--only-model <model>]
"""

import argparse
import concurrent.futures
import os
import subprocess
import sys
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"
TRACES_FREEFLOW = REPO / "data" / "traces_freeflow"
TRACES_VALUES = REPO / "data" / "traces_values"

# Models to sweep: (OR alias, label-prefix used in cell directory names)
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


def slugify_provider(provider_name: str) -> str:
    """Match the convention used by the M2 cells (lowercase, simplify)."""
    s = provider_name.lower().replace(" ", "-").replace(".", "")
    # Map a couple of known forms to existing M2 conventions
    s = s.replace("/", "-")
    return s


def get_providers(or_alias: str) -> list[str]:
    """Return the list of upstream provider_name strings for an OR alias."""
    r = httpx.get(
        f"https://openrouter.ai/api/v1/models/{or_alias}/endpoints",
        timeout=15,
    )
    r.raise_for_status()
    eps = r.json().get("data", {}).get("endpoints", [])
    seen = []
    for e in eps:
        p = e.get("provider_name")
        if p and p not in seen:
            seen.append(p)
    return seen


def cell_label(label_prefix: str, provider: str) -> str:
    return f"{label_prefix}-or-pin-{slugify_provider(provider)}"


def _count_valid(d: Path) -> int:
    """Count JSON files in d that contain a non-empty `result` field
    (i.e. successful collections, not 429/error placeholders)."""
    if not d.is_dir():
        return 0
    valid = 0
    import json as _json
    for f in d.glob("*.json"):
        try:
            x = _json.loads(f.read_text())
        except Exception:
            continue
        if x.get("result"):
            valid += 1
    return valid


def freeflow_done(label: str) -> bool:
    # Require full fill (5 conds × 25 = 125). Top-up semantics in
    # run_freeflow_multi.py skip already-valid files at the per-sample level,
    # so re-invoking on a partial cell is cheap and only fills the gaps.
    # Previously this gated at ≥100 (80% of 125), which silently skipped
    # cells that were full in 4/5 conditions but missing a whole condition
    # (e.g. VARY-only failures). Bumped 2026-05-03 morning after the VARY
    # asymmetry was surfaced — see daily-journals/2026-05-03.md#07:27.
    return _count_valid(TRACES_FREEFLOW / f"freeflow_{label}") >= 125


def values_done(label: str) -> bool:
    # Require full fill (3 CTRL × 10 + 3 G × 30 = 120). Same rationale as
    # freeflow_done — let the per-file top-up handle skipping inside.
    return _count_valid(TRACES_VALUES / label) >= 120


def run_cell(or_alias: str, provider: str, label: str, dry_run: bool = False) -> tuple[str, str]:
    """Collect both freeflow and values for one (model, provider) cell.
    Returns (status, message).
    """
    env = os.environ.copy()
    env["OR_PROVIDER"] = provider

    results = []

    # Freeflow: --n 25 per condition → 125 samples per cell
    if freeflow_done(label):
        results.append(f"freeflow:skip(exists)")
    else:
        cmd = [
            sys.executable,
            str(SCRIPTS / "run_freeflow_multi.py"),
            "openrouter",
            or_alias,
            "--label", label,
            "--n", "25",
            "--max-tokens", "16000",
            "--workers", "3",
        ]
        if dry_run:
            results.append(f"freeflow:DRY {' '.join(cmd)}")
        else:
            try:
                r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5400)
                ok_count = r.stdout.count(": ok ")
                err_count = r.stdout.count(": err ")
                results.append(f"freeflow:{ok_count}ok/{err_count}err")
            except Exception as e:
                results.append(f"freeflow:FAIL({e})")

    # Values probe: 3 CTRL × 10 + 3 G × 30 = 120 samples per cell
    if values_done(label):
        results.append(f"values:skip(exists)")
    else:
        cmd = [
            sys.executable,
            str(SCRIPTS / "run_values_v2.py"),
            "openrouter",
            or_alias,
            "--label", label,
            "--ctrl-n", "10",
            "--g-n", "30",
            "--workers", "3",
        ]
        if dry_run:
            results.append(f"values:DRY {' '.join(cmd)}")
        else:
            try:
                r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=5400)
                ok_count = r.stdout.count(": ok ")
                err_count = r.stdout.count(": err ")
                results.append(f"values:{ok_count}ok/{err_count}err")
            except Exception as e:
                results.append(f"values:FAIL({e})")

    return label, " ".join(results)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-parallel-cells", type=int, default=4,
                    help="Max cells running concurrently (default 4)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print commands without running")
    ap.add_argument("--only-model", type=str, default=None,
                    help="Limit sweep to one OR alias (e.g. z-ai/glm-4.6)")
    args = ap.parse_args()

    if "OPENROUTER_API_KEY" not in os.environ:
        sys.exit("ERROR: OPENROUTER_API_KEY not in environment. Source keys.env first.")

    # Provider/model combinations to skip (blocked by OR account guardrails
    # that we have decided not to flip, or providers we've decided to drop).
    # Each entry: (or_alias, provider_name).
    SKIP = {
        ("deepseek/deepseek-v4-pro", "DeepSeek"),  # blocked by OR data-policy guardrail
    }
    # Providers to skip across ALL models. Fireworks added 2026-05-03 — its
    # OR shared-pool rate-limit produces unreliable / partial collections (the
    # glm-5.1 cell came back 3ok/122err on retries, the m2.7 cell is partially
    # filled). Not the only provider for any model in the sweep, so dropping
    # is harmless. Recoverable in future via OR BYOK if Daniel chooses.
    SKIP_PROVIDERS_GLOBAL = {"Fireworks"}

    # Build full plan
    plan = []
    for or_alias, label_prefix in MODELS:
        if args.only_model and or_alias != args.only_model:
            continue
        try:
            providers = get_providers(or_alias)
        except Exception as e:
            print(f"  [{or_alias}] ERROR fetching providers: {e}", file=sys.stderr)
            continue
        for p in providers:
            if (or_alias, p) in SKIP:
                print(f"  [skip] {or_alias} via {p} (configured skip)", file=sys.stderr)
                continue
            if p in SKIP_PROVIDERS_GLOBAL:
                print(f"  [skip] {or_alias} via {p} (provider globally skipped)", file=sys.stderr)
                continue
            label = cell_label(label_prefix, p)
            plan.append((or_alias, p, label))

    print(f"Plan: {len(plan)} cells across {len({p[0] for p in plan})} models")
    for or_alias, p, label in plan:
        ff = "✓" if freeflow_done(label) else "·"
        vv = "✓" if values_done(label) else "·"
        print(f"  [{ff}{vv}] {or_alias:<32} via {p:<22} → {label}")

    if args.dry_run:
        print("\n(dry-run; no collections will be launched)")
        return

    print(f"\nLaunching with max-parallel-cells={args.max_parallel_cells}\n")

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_parallel_cells) as ex:
        futures = {
            ex.submit(run_cell, or_alias, provider, label): label
            for (or_alias, provider, label) in plan
        }
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            label, msg = fut.result()
            done += 1
            print(f"[{done}/{len(plan)}] {label}: {msg}")


if __name__ == "__main__":
    main()
