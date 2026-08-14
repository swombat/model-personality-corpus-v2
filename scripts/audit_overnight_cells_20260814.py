#!/usr/bin/env python3
"""Strict completeness, text-fidelity, and route audit for the overnight batch."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/overnight-fidelity-audit-2026-08-14.json"
ROLE_LEAK = re.compile(
    r"(?:<\|(?:im_start|user|assistant|system)\|>|"
    r"(?:^|\n)\s*(?:user|assistant|system)\s*\n)",
    re.IGNORECASE,
)
CELLS = [
    "chatglm3-6b-local-transformers-mps-float16-re9e0406d",
    "deepseek-llm-7b-chat-local-transformers-mps-auto-rafbda8b3",
    "mistral-7b-instruct-v0-2-local-transformers-mps-auto-r63a8b081",
    "qwen1-5-7b-chat-local-transformers-mps-auto-r5f4f5e69",
    "qwen2-7b-instruct-local-transformers-mps-auto-rf2826a00",
    "qwen2-5-7b-instruct-local-transformers-mps-auto-ra09a3545",
    "glm-4-9b-chat-hf-local-transformers-mps-auto-r8599336f",
    "grok-4-6-or-pin-xai-20260813",
    "deepseek-v4-pro-0813-direct-20260813",
    "qwen3-8-2-4t-a95b-or-pin-digitalocean",
]
EXPECTED_PROVIDERS = {
    "grok-4-6-or-pin-xai-20260813": "xAI",
    "qwen3-8-2-4t-a95b-or-pin-digitalocean": "DigitalOcean",
}


def audit_cell(cell: str) -> dict:
    issues = []
    counts = {}
    returned_models = Counter()
    raw_providers = Counter()
    for probe, directory, expected in (
        ("freeflow", ROOT / "data/traces_freeflow" / f"freeflow_{cell}", 125),
        ("values", ROOT / "data/traces_values" / cell, 120),
    ):
        valid = 0
        if not directory.is_dir():
            issues.append({"probe": probe, "issue": "missing_directory"})
            counts[probe] = {"valid": 0, "expected": expected}
            continue
        for path in sorted(directory.glob("*.json")):
            try:
                payload = json.loads(path.read_text())
            except Exception as exc:
                issues.append({"file": str(path.relative_to(ROOT)), "issue": f"json:{exc}"})
                continue
            text = payload.get("result") or ""
            if not text:
                issues.append({"file": str(path.relative_to(ROOT)), "issue": "missing_result"})
                continue
            valid += 1
            returned_models[payload.get("model") or payload.get("model_requested") or ""] += 1
            raw_provider = (payload.get("raw") or {}).get("provider")
            if raw_provider:
                raw_providers[raw_provider] += 1
            for issue, present in (
                ("replacement_char", "\ufffd" in text),
                ("tokenizer_marker", "Ġ" in text or "Ċ" in text),
                ("nul_character", "\x00" in text),
                ("role_continuation", bool(ROLE_LEAK.search(text))),
            ):
                if present:
                    issues.append({"file": str(path.relative_to(ROOT)), "issue": issue})
        counts[probe] = {"valid": valid, "expected": expected}
        if valid != expected:
            issues.append({"probe": probe, "issue": "incomplete", "valid": valid, "expected": expected})
    expected_provider = EXPECTED_PROVIDERS.get(cell)
    if expected_provider and raw_providers != {expected_provider: 245}:
        issues.append({
            "issue": "route_mismatch",
            "expected_provider": expected_provider,
            "observed": dict(raw_providers),
        })
    return {
        "counts": counts,
        "returned_models": dict(returned_models),
        "raw_providers": dict(raw_providers),
        "issues": issues,
        "passed": not issues,
    }


def main() -> None:
    records = {cell: audit_cell(cell) for cell in CELLS}
    accepted = [cell for cell, record in records.items() if record["passed"]]
    rejected = [cell for cell, record in records.items() if not record["passed"]]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": (
            "Only complete 125-freeflow/120-values cells with clean decoded text "
            "and, where applicable, exact pinned-provider provenance are accepted."
        ),
        "accepted_cells": accepted,
        "rejected_cells": rejected,
        "cells": records,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({"accepted": accepted, "rejected": rejected}, indent=2))


if __name__ == "__main__":
    main()
