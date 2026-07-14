#!/usr/bin/env python3
"""Durable, restartable corpus collection from a JSON manifest.

The runner delegates actual sample creation to the canonical freeflow and
values scripts. It adds:

* non-canonical smoke tests for every route;
* per-model/provider pinning through OR_PROVIDER;
* bounded top-up rounds;
* an atomically updated state file suitable for unattended monitoring; and
* append-only logs.

Models that fail smoke testing are recorded as blocked and skipped by the full
run rather than creating 245 error files in the canonical data tree.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
FREEFLOW = HERE / "run_freeflow_multi.py"
VALUES = HERE / "run_values_v2.py"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def save_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    tmp.replace(path)


def valid_count(probe: str, label: str) -> int:
    if probe == "freeflow":
        directory = REPO / "data" / "traces_freeflow" / f"freeflow_{label}"
    else:
        directory = REPO / "data" / "traces_values" / label
    if not directory.is_dir():
        return 0
    count = 0
    for path in directory.glob("*.json"):
        try:
            if json.loads(path.read_text()).get("result"):
                count += 1
        except Exception:
            pass
    return count


@contextmanager
def provider_pin(pin: str | None):
    previous = os.environ.get("OR_PROVIDER")
    try:
        if pin:
            os.environ["OR_PROVIDER"] = pin
        else:
            os.environ.pop("OR_PROVIDER", None)
        yield
    finally:
        if previous is None:
            os.environ.pop("OR_PROVIDER", None)
        else:
            os.environ["OR_PROVIDER"] = previous


def smoke_test(item: dict, smoke_dir: Path) -> dict:
    sys.path.insert(0, str(HERE))
    from run_freeflow_multi import PROVIDERS

    started = time.time()
    try:
        with provider_pin(item.get("or_provider")):
            result = PROVIDERS[item["provider"]](
                item["model"],
                "Write one short sentence about rain.",
                max_tokens=128,
            )
        text = (result.get("result") or "").strip()
        if not text:
            raise RuntimeError("empty result")
        record = {
            "status": "ok",
            "at": now(),
            "duration_ms": int((time.time() - started) * 1000),
            "result_preview": text[:300],
            "model_returned": result.get("model"),
            "usage": result.get("usage", {}),
            "raw_provider": (result.get("raw") or {}).get("provider"),
        }
    except Exception as exc:
        record = {
            "status": "failed",
            "at": now(),
            "duration_ms": int((time.time() - started) * 1000),
            "error": repr(exc),
        }
        response = getattr(exc, "response", None)
        if response is not None:
            record["http_status"] = response.status_code
            record["http_body"] = response.text[:2000]
    smoke_dir.mkdir(parents=True, exist_ok=True)
    save_json(smoke_dir / f"{item['label']}.json", record)
    return record


def run_command(command: list[str], env: dict[str, str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a") as log:
        log.write(f"\n\n===== {now()} =====\n$ {' '.join(command)}\n")
        log.flush()
        process = subprocess.Popen(
            command,
            cwd=REPO,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        return process.wait()


def run_probe(item: dict, probe: str, log_dir: Path, rounds: int) -> dict:
    target = 125 if probe == "freeflow" else 120
    env = os.environ.copy()
    if item.get("or_provider"):
        env["OR_PROVIDER"] = item["or_provider"]
    else:
        env.pop("OR_PROVIDER", None)

    workers = str(item.get("workers", 5))
    if probe == "freeflow":
        command = [
            sys.executable,
            str(FREEFLOW),
            item["provider"],
            item["model"],
            "--label",
            item["label"],
            "--n",
            "25",
            "--workers",
            workers,
            "--max-tokens",
            str(item.get("freeflow_max_tokens", 16000)),
        ]
    else:
        command = [
            sys.executable,
            str(VALUES),
            item["provider"],
            item["model"],
            "--label",
            item["label"],
            "--ctrl-n",
            "10",
            "--g-n",
            "30",
            "--workers",
            workers,
            "--max-tokens",
            str(item.get("values_max_tokens", 2000)),
        ]

    history = []
    previous = valid_count(probe, item["label"])
    for round_number in range(1, rounds + 1):
        if previous >= target:
            break
        rc = run_command(
            command,
            env,
            log_dir / f"{item['label']}-{probe}.log",
        )
        current = valid_count(probe, item["label"])
        history.append(
            {
                "round": round_number,
                "returncode": rc,
                "before": previous,
                "after": current,
                "at": now(),
            }
        )
        if current >= target:
            previous = current
            break
        if current <= previous:
            previous = current
            break
        previous = current

    return {
        "status": "complete" if previous >= target else "partial",
        "valid": previous,
        "target": target,
        "history": history,
        "updated_at": now(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--log-dir", type=Path, required=True)
    parser.add_argument("--smoke-dir", type=Path, required=True)
    parser.add_argument("--smoke-only", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--max-topup-rounds", type=int, default=5)
    parser.add_argument("--labels", nargs="*")
    args = parser.parse_args()

    manifest = load_json(args.manifest, {})
    items = manifest.get("models", [])
    if args.labels:
        wanted = set(args.labels)
        items = [item for item in items if item["label"] in wanted]

    state = load_json(
        args.state,
        {
            "manifest": str(args.manifest),
            "created_at": now(),
            "updated_at": now(),
            "models": {},
        },
    )

    for index, item in enumerate(items, 1):
        label = item["label"]
        entry = state["models"].setdefault(label, {})
        entry.update(
            {
                "provider": item["provider"],
                "model": item["model"],
                "or_provider": item.get("or_provider"),
                "ordinal": index,
                "total": len(items),
            }
        )

        if not args.skip_smoke and entry.get("smoke", {}).get("status") != "ok":
            entry["stage"] = "smoke"
            entry["updated_at"] = now()
            state["updated_at"] = now()
            save_json(args.state, state)
            entry["smoke"] = smoke_test(item, args.smoke_dir)
            entry["updated_at"] = now()
            state["updated_at"] = now()
            save_json(args.state, state)

        if entry.get("smoke", {}).get("status") != "ok" and not args.skip_smoke:
            entry["stage"] = "blocked"
            entry["updated_at"] = now()
            state["updated_at"] = now()
            save_json(args.state, state)
            continue

        if args.smoke_only:
            entry["stage"] = "smoke-complete"
            save_json(args.state, state)
            continue

        for probe in ("freeflow", "values"):
            if entry.get(probe, {}).get("status") == "complete":
                continue
            entry["stage"] = probe
            entry["updated_at"] = now()
            state["updated_at"] = now()
            save_json(args.state, state)
            entry[probe] = run_probe(
                item,
                probe,
                args.log_dir,
                args.max_topup_rounds,
            )
            entry["updated_at"] = now()
            state["updated_at"] = now()
            save_json(args.state, state)

        if (
            entry.get("freeflow", {}).get("status") == "complete"
            and entry.get("values", {}).get("status") == "complete"
        ):
            entry["stage"] = "complete"
        else:
            entry["stage"] = "partial"
        entry["updated_at"] = now()
        state["updated_at"] = now()
        save_json(args.state, state)

    state["finished_at"] = now()
    state["updated_at"] = now()
    save_json(args.state, state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
