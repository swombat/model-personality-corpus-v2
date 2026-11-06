#!/usr/bin/env python3
"""List OpenRouter text models from followed labs that the corpus has not mapped.

Daily model-mapping rhythm, step 2 (see docs/daily-mapping-runbook.md in this repo).

    python3 new_models.py            # candidates from the last 10 days, newest first
    python3 new_models.py --days 30
    python3 new_models.py --json

A candidate is: created within --days, id prefix in FOLLOWED_LABS, text output,
not a routing variant (:free, :batch, ...), not already a site model (the
openrouter ids in models.json plus MODEL_SLUGS in generate_data.py), and not in
decisions.json (mapped / skipped, with reason). Entries whose decision starts
with "queued" are always listed, whatever their age, until replaced by "mapped". Printing a candidate is not a
decision to map it: Pro/Prime/router/image variants still need judgement (RUNBOOK).
"""
from __future__ import annotations

import argparse
import os
import json
import re
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# The analysis repo checkout (swombat/model-personality-analysis-corpus); set MPAC_DIR if it is elsewhere.
ANALYSIS = Path(os.environ.get("MPAC_DIR", str(Path.home() / "work" / "mpac"))).expanduser()
# The one shared ledger: pull before reading it, commit + push before launching a capture.
DECISIONS = HERE / "decisions.json"

FOLLOWED_LABS = [
    "anthropic", "openai", "google", "qwen", "x-ai", "mistralai",
    "deepseek", "moonshotai", "z-ai", "minimax", "xiaomi", "meta-llama", "meta",
    "inception",  # added 2026-10-22: Mercury 2.5 was mapped by hand, Mercury 3 was missed (oewwDe)
]
SKIP_SUFFIXES = (":free", ":batch", ":beta", ":extended", ":thinking", ":online", ":nitro", ":floor")


def site_ids() -> set[str]:
    ids: set[str] = set()
    for m in json.loads((ANALYSIS / "website/src/generated/models.json").read_text()):
        o = m.get("openrouter") or {}
        if o.get("id"):
            ids.add(o["id"])
    gen = (ANALYSIS / "website/scripts/generate_data.py").read_text()
    ids |= set(re.findall(r'^\s*"[^"]+":\s*"([a-z0-9-]+/[^"]+)",', gen, re.M))
    return ids


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=10)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    data = json.load(urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=60))["data"]
    known = site_ids()
    # Any lab already on the site is followed too (2026-10-22: Mercury 3 was missed
    # because Inception had a site model but wasn't on the hand-kept list).
    followed = set(FOLLOWED_LABS) | {i.split("/")[0] for i in known if "/" in i}
    decided = json.loads(DECISIONS.read_text()) if DECISIONS.exists() else {}
    cut = time.time() - a.days * 86400
    out = []
    for m in sorted(data, key=lambda m: -m["created"]):
        mid = m["id"]
        queued = str(decided.get(mid, "")).startswith("queued")
        if not queued:
            if m["created"] < cut or mid.split("/")[0] not in followed or mid.endswith(SKIP_SUFFIXES):
                continue
            if "text" not in m["architecture"].get("output_modalities", []) or mid in known or mid in decided:
                continue
        p = m.get("pricing", {})
        out.append({
            "id": mid, "name": m.get("name"),
            "created": time.strftime("%Y-%m-%d", time.gmtime(m["created"])),
            "canonical_slug": m.get("canonical_slug"), "context": m.get("context_length"),
            "output_modalities": m["architecture"].get("output_modalities"),
            "usd_per_m_in": round(float(p.get("prompt", 0)) * 1e6, 4),
            "usd_per_m_out": round(float(p.get("completion", 0)) * 1e6, 4),
        })
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        for c in out:
            print(f"{c['created']}  {c['id']:42s} ${c['usd_per_m_in']}/${c['usd_per_m_out']} per M  {c['name']}")
        if not out:
            print("no new candidates")


if __name__ == "__main__":
    main()
