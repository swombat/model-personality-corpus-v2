#!/usr/bin/env python3
"""Replace vague August historical-local provenance with exact metadata."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "collection-manifest-2026-08-11-historical-local.json"
PATCH_SUFFIX = "; fidelity stop-token and complete-byte decode patch 2026-08-13"

CELLS = {
    "chatglm3-6b-local-transformers-mps-float16-re9e0406d": {
        "model": "zai-org/chatglm3-6b",
        "revision": "e9e0406d062cdb887444fe5bd546833920abd4ac",
        "runtime": "transformers-mps-custom-chatglm3",
        "runtime_version": "transformers 4.30.2; torch 2.13.0",
        "weight_precision": "FP16 (explicit torch.float16 load of official safetensors)",
    },
    "mistral-7b-instruct-v0-2-local-transformers-mps-auto-r63a8b081": {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "revision": "63a8b081895390a26e140280378bc85ec8bce07a",
        "runtime": "transformers-mps-generic-official-checkpoint",
        "runtime_version": "transformers 5.14.1; torch 2.13.0",
        "weight_precision": "BF16 (official safetensors; checkpoint dtype via auto)",
    },
    "qwen1-5-7b-chat-local-transformers-mps-auto-r5f4f5e69": {
        "model": "Qwen/Qwen1.5-7B-Chat",
        "revision": "5f4f5e69ac7f1d508f8369e977de208b4803444b",
        "runtime": "transformers-mps-generic-official-checkpoint",
        "runtime_version": "transformers 5.14.1; torch 2.13.0",
        "weight_precision": "BF16 (official safetensors; checkpoint dtype via auto)",
    },
    "qwen2-7b-instruct-local-transformers-mps-auto-rf2826a00": {
        "model": "Qwen/Qwen2-7B-Instruct",
        "revision": "f2826a00ceef68f0f2b946d945ecc0477ce4450c",
        "runtime": "transformers-mps-generic-official-checkpoint",
        "runtime_version": "transformers 5.14.1; torch 2.13.0",
        "weight_precision": "BF16 (official safetensors; checkpoint dtype via auto)",
    },
    "glm-4-9b-chat-hf-local-transformers-mps-auto-r8599336f": {
        "model": "zai-org/glm-4-9b-chat-hf",
        "revision": "8599336fc6c125203efb2360bfaf4c80eef1d1bf",
        "runtime": "transformers-mps-generic-official-checkpoint",
        "runtime_version": "transformers 5.14.1; torch 2.13.0",
        "weight_precision": "BF16 (official safetensors; checkpoint dtype via auto)",
    },
}


def sample_paths(cell: str) -> list[Path]:
    freeflow = ROOT / "data/traces_freeflow" / f"freeflow_{cell}"
    values = ROOT / "data/traces_values" / cell
    paths = sorted(freeflow.glob("*.json")) + sorted(values.glob("*.json"))
    if len(paths) != 245:
        raise RuntimeError(f"{cell}: expected 245 samples, found {len(paths)}")
    return paths


def correct_samples() -> dict[str, list[str]]:
    recollections: dict[str, list[str]] = {}
    for cell, expected in CELLS.items():
        patched = []
        for path in sample_paths(cell):
            original = path.read_text()
            payload = json.loads(original)
            if payload.get("model") != expected["model"]:
                raise RuntimeError(f"{path}: unexpected model {payload.get('model')!r}")
            deployment = payload.get("local_deployment")
            if not isinstance(deployment, dict):
                raise RuntimeError(f"{path}: missing local_deployment")
            if deployment.get("model_revision") != expected["revision"]:
                raise RuntimeError(f"{path}: unexpected revision")
            runtime_version = deployment.get("runtime_version", "")
            if runtime_version.endswith(PATCH_SUFFIX):
                patched.append(str(path.relative_to(ROOT)))
            elif runtime_version != expected["runtime_version"]:
                raise RuntimeError(f"{path}: unexpected runtime_version {runtime_version!r}")
            replacements = {
                deployment["runtime"]: expected["runtime"],
                deployment["weight_precision"]: expected["weight_precision"],
            }
            corrected = original
            for old, new in replacements.items():
                if old == new:
                    continue
                quoted_old = json.dumps(old)
                quoted_new = json.dumps(new)
                if corrected.count(quoted_old) != 1:
                    raise RuntimeError(
                        f"{path}: expected exactly one occurrence of {quoted_old}"
                    )
                corrected = corrected.replace(quoted_old, quoted_new)
            path.write_text(corrected)
        recollections[cell] = patched
    return recollections


def update_manifest(recollections: dict[str, list[str]]) -> None:
    manifest = json.loads(MANIFEST.read_text())
    manifest["name"] = "2026-08-09 to 2026-08-14 historical local full-precision capture"
    existing = {entry["label"]: entry for entry in manifest["models"]}
    for cell, metadata in CELLS.items():
        entry = {
            "provider": "local-openai",
            "model": metadata["model"],
            "revision": metadata["revision"],
            "label": cell,
            "runtime": metadata["runtime"],
            "runtime_version": metadata["runtime_version"],
            "weight_precision": metadata["weight_precision"],
            "weight_format": "official safetensors",
            "freeflow_valid": 125,
            "values_valid": 120,
        }
        if recollections[cell]:
            entry["fidelity_recollections"] = recollections[cell]
            entry["recollection_runtime_version"] = (
                metadata["runtime_version"] + PATCH_SUFFIX
            )
        existing[cell] = entry
    manifest["models"] = list(existing.values())
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")


def main() -> None:
    recollections = correct_samples()
    update_manifest(recollections)
    print(
        json.dumps(
            {
                "corrected_cells": list(CELLS),
                "corrected_samples": sum(len(sample_paths(cell)) for cell in CELLS),
                "fidelity_recollections": recollections,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
