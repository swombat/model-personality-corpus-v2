#!/usr/bin/env bash
set -euo pipefail

# Parallel Qwen family completeness collection for corpus-v2, 2026-05-22.
# Runs one bounded worker pipeline per model. Per-sample scripts preserve prior
# valid traces and top up only missing/error files.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

set +u
set -a
source keys.env
set +a
set -u

export OR_PROVIDER="Alibaba"

RUN_ID="qwen-completeness-parallel-2026-05-22"
LOG_DIR="logs/${RUN_ID}"
mkdir -p "$LOG_DIR"

FREEFLOW_WORKERS="${FREEFLOW_WORKERS:-4}"
VALUES_WORKERS="${VALUES_WORKERS:-5}"

MODELS=(
  "qwen3-7-max-or-pin-alibaba|qwen/qwen3.7-max"
  "qwen3-5-plus-20260420-or-pin-alibaba|qwen/qwen3.5-plus-20260420"
  "qwen3-6-flash-or-pin-alibaba|qwen/qwen3.6-flash"
  "qwen3-6-max-preview-or-pin-alibaba|qwen/qwen3.6-max-preview"
  "qwen3-5-flash-02-23-or-pin-alibaba|qwen/qwen3.5-flash-02-23"
  "qwen3-max-thinking-or-pin-alibaba|qwen/qwen3-max-thinking"
  "qwen3-max-or-pin-alibaba|qwen/qwen3-max"
  "qwen3-coder-flash-or-pin-alibaba|qwen/qwen3-coder-flash"
)

{
  echo "# ${RUN_ID}"
  echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Route: OpenRouter provider.only=[Alibaba], allow_fallbacks=false"
  echo "Parallelism: one model pipeline per model; freeflow workers=${FREEFLOW_WORKERS}; values workers=${VALUES_WORKERS}"
  echo
  printf '| label | model_id | freeflow target | values target |\n'
  printf '|---|---|---:|---:|\n'
  for item in "${MODELS[@]}"; do
    IFS='|' read -r label model <<< "$item"
    printf '| `%s` | `%s` | 125 | 120 |\n' "$label" "$model"
  done
} > "$LOG_DIR/MANIFEST.md"

run_model() {
  local label="$1"
  local model="$2"
  local log="$LOG_DIR/${label}.log"
  {
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] START ${label} (${model})"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] freeflow ${label}"
    python3 scripts/run_freeflow_multi.py openrouter "$model" \
      --label "$label" --n 25 --workers "$FREEFLOW_WORKERS" --max-tokens 8000
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] values ${label}"
    python3 scripts/run_values_v2.py openrouter "$model" \
      --label "$label" --ctrl-n 10 --g-n 30 --workers "$VALUES_WORKERS" --max-tokens 2000
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] DONE ${label}"
  } > "$log" 2>&1
}

pids=()
for item in "${MODELS[@]}"; do
  IFS='|' read -r label model <<< "$item"
  run_model "$label" "$model" &
  pids+=("$!")
done

fail=0
for pid in "${pids[@]}"; do
  if ! wait "$pid"; then
    fail=1
  fi
done

python3 - <<'PY' | tee "$LOG_DIR/qwen_counts.tsv"
import json, pathlib
labels = [
  'qwen3-7-max-or-pin-alibaba',
  'qwen3-5-plus-20260420-or-pin-alibaba',
  'qwen3-6-flash-or-pin-alibaba',
  'qwen3-6-max-preview-or-pin-alibaba',
  'qwen3-5-flash-02-23-or-pin-alibaba',
  'qwen3-max-thinking-or-pin-alibaba',
  'qwen3-max-or-pin-alibaba',
  'qwen3-coder-flash-or-pin-alibaba',
]
print('probe\tlabel\tok\terr\ttarget')
for label in labels:
    for probe, base, prefix, target in [('freeflow', pathlib.Path('data/traces_freeflow'), 'freeflow_', 125), ('values', pathlib.Path('data/traces_values'), '', 120)]:
        d = base / f'{prefix}{label}'
        ok = err = 0
        if d.exists():
            for f in d.glob('*.json'):
                try:
                    j = json.loads(f.read_text())
                except Exception:
                    err += 1
                    continue
                if j.get('result'):
                    ok += 1
                else:
                    err += 1
        print(f'{probe}\t{label}\t{ok}\t{err}\t{target}')
PY

python3 scripts/corpus_summary.py > "$LOG_DIR/corpus_summary.log" 2>&1 || fail=1

echo "Completed: $(date -u +%Y-%m-%dT%H:%M:%SZ) fail=${fail}" | tee -a "$LOG_DIR/MANIFEST.md"
exit "$fail"
