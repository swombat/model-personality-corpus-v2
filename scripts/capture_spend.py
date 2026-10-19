#!/usr/bin/env python3
"""Capture spend for one model, counted once per trace.

Each raw trace stores the call's usage twice: top-level `usage` and
`raw.usage` are copies of the same OpenRouter response. A recursive walk
that sums every `cost` key therefore doubles the total (the Argon release,
v1.2.34, reported $6.52 / 648k / 93k for a capture that cost
$3.26229 / 323,811 / 46,527). This script reads one usage block per trace:
top-level `usage`, falling back to `raw.usage` only when it is absent.

Usage: scripts/capture_spend.py <slug-glob>   e.g.  '*gemini-4-argon*'
"""
import glob
import json
import sys


def usage_of(trace):
    u = trace.get("usage")
    if not u:
        u = (trace.get("raw") or {}).get("usage") or {}
    return u


def main(pattern):
    files = sorted(glob.glob(f"data/traces_*/{pattern}/*.json"))
    cost = completion = reasoning = 0
    missing = 0
    for f in files:
        u = usage_of(json.load(open(f)))
        if not u:
            missing += 1
            continue
        cost += u.get("cost") or 0
        completion += u.get("completion_tokens") or 0
        reasoning += (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0
    print(json.dumps({
        "traces": len(files),
        "traces_without_usage": missing,
        "cost_usd": round(cost, 5),
        "completion_tokens": completion,
        "reasoning_tokens": reasoning,
    }, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
