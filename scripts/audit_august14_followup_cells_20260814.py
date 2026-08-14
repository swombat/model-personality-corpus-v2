#!/usr/bin/env python3
"""Strict fidelity and route audit for the August 14 follow-up cells."""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "analysis/august14-followup-fidelity-audit-2026-08-14.json"
ROLE_LEAK = re.compile(
    r"(?:<\|(?:im_start|user|assistant|system)\|>|"
    r"(?:^|\n)\s*(?:user|assistant|system)\s*\n)",
    re.IGNORECASE,
)
SPECS = {
    "gemini-3-7-flash-or-pin-google": {
        "model": "google/gemini-3.7-flash",
        "provider": "Google",
    },
    "qwen3-8-max-or-pin-alibaba-r2": {
        "model": "qwen/qwen3.8-max",
        "provider": "Alibaba",
    },
    "qwen3-8-2-4t-a95b-or-pin-digitalocean-r2": {
        "model": "qwen/qwen3.8-2.4t-a95b",
        "provider": "DigitalOcean",
    },
}


def audit_cell(cell: str, spec: dict[str, str]) -> dict:
    issues = []
    counts = {}
    returned_models: Counter[str] = Counter()
    raw_providers: Counter[str] = Counter()
    finish_reasons: Counter[str] = Counter()
    for probe, directory, expected in (
        ("freeflow", ROOT / "data/traces_freeflow" / f"freeflow_{cell}", 125),
        ("values", ROOT / "data/traces_values" / cell, 120),
    ):
        valid = 0
        for path in sorted(directory.glob("*.json")):
            try:
                payload = json.loads(path.read_text())
            except Exception as exc:
                issues.append(
                    {"file": str(path.relative_to(ROOT)), "issue": f"json:{exc}"}
                )
                continue
            text = payload.get("result") or ""
            if not text:
                issues.append(
                    {"file": str(path.relative_to(ROOT)), "issue": "missing_result"}
                )
                continue
            valid += 1
            returned_models[payload.get("model") or ""] += 1
            raw = payload.get("raw") or {}
            raw_providers[raw.get("provider") or ""] += 1
            choices = raw.get("choices") or []
            if choices:
                finish_reason = choices[0].get("finish_reason") or ""
                finish_reasons[finish_reason] += 1
                if finish_reason == "length":
                    issues.append(
                        {
                            "file": str(path.relative_to(ROOT)),
                            "issue": "token_limit_truncation",
                        }
                    )
            for issue, present in (
                ("replacement_char", "\ufffd" in text),
                ("tokenizer_marker", "Ġ" in text or "Ċ" in text),
                ("nul_character", "\x00" in text),
                ("role_continuation", bool(ROLE_LEAK.search(text))),
            ):
                if present:
                    issues.append(
                        {"file": str(path.relative_to(ROOT)), "issue": issue}
                    )
        counts[probe] = {"valid": valid, "expected": expected}
        if valid != expected:
            issues.append(
                {
                    "probe": probe,
                    "issue": "incomplete",
                    "valid": valid,
                    "expected": expected,
                }
            )
    if returned_models != {spec["model"]: 245}:
        issues.append(
            {
                "issue": "model_mismatch",
                "expected": spec["model"],
                "observed": dict(returned_models),
            }
        )
    if raw_providers != {spec["provider"]: 245}:
        issues.append(
            {
                "issue": "route_mismatch",
                "expected": spec["provider"],
                "observed": dict(raw_providers),
            }
        )
    return {
        "counts": counts,
        "returned_models": dict(returned_models),
        "raw_providers": dict(raw_providers),
        "finish_reasons": dict(finish_reasons),
        "issues": issues,
        "passed": not issues,
    }


def main() -> None:
    cells = {cell: audit_cell(cell, spec) for cell, spec in SPECS.items()}
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": (
            "Only complete 125-freeflow/120-values cells with clean decoded text, "
            "the exact requested model, and exact pinned-provider provenance pass."
        ),
        "accepted_cells": [
            cell for cell, record in cells.items() if record["passed"]
        ],
        "rejected_cells": [
            cell for cell, record in cells.items() if not record["passed"]
        ],
        "cells": cells,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
