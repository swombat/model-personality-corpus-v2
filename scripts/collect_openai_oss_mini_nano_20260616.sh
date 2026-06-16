#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
export PYTHON=/Library/Frameworks/Python.framework/Versions/3.11/bin/python3
export PYTHONUNBUFFERED=1
# Load SOPS-backed provider keys without using keys.env (avoids local shell/RVM source-hook issues).
eval "$(sops -d secrets/provider-keys.sops.json | "$PYTHON" -c 'import json, shlex, sys; data=json.load(sys.stdin); [print("export %s=%s" % (k, shlex.quote(str(v)))) for k, v in data.items()]')"

stamp="$(date +%Y%m%d-%H%M%S)"
STARTED_PIDS=()

start_job() {
  local name="$1"; shift
  local pidfile="logs/${name}.pid"
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] running $name pid=$(cat "$pidfile")"
    return 0
  fi
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] starting $name"
  nohup bash -lc "$*" >> "logs/${name}-${stamp}.log" 2>&1 &
  local pid=$!
  echo "$pid" > "$pidfile"
  STARTED_PIDS+=("$pid")
}

# gpt-oss via OpenRouter, pinned to Amazon Bedrock only. No DekaLLM, no Google, no fallback.
start_job "gpt-oss-120b-amazon-freeflow" \
  'export OR_PROVIDER="Amazon Bedrock"; "$PYTHON" scripts/run_freeflow_multi.py openrouter openai/gpt-oss-120b --label gpt-oss-120b-or-pin-amazon-bedrock --n 25 --workers 5 --max-tokens 8000'
start_job "gpt-oss-120b-amazon-values" \
  'export OR_PROVIDER="Amazon Bedrock"; "$PYTHON" scripts/run_values_v2.py openrouter openai/gpt-oss-120b --label gpt-oss-120b-or-pin-amazon-bedrock --workers 6 --max-tokens 2000'
start_job "gpt-oss-20b-amazon-freeflow" \
  'export OR_PROVIDER="Amazon Bedrock"; "$PYTHON" scripts/run_freeflow_multi.py openrouter openai/gpt-oss-20b --label gpt-oss-20b-or-pin-amazon-bedrock --n 25 --workers 5 --max-tokens 8000'
start_job "gpt-oss-20b-amazon-values" \
  'export OR_PROVIDER="Amazon Bedrock"; "$PYTHON" scripts/run_values_v2.py openrouter openai/gpt-oss-20b --label gpt-oss-20b-or-pin-amazon-bedrock --workers 6 --max-tokens 2000'

# GPT-5 mini/nano via OpenAI direct Responses API path in run_freeflow_multi.py.
start_job "gpt-5-mini-direct-freeflow" \
  '"$PYTHON" scripts/run_freeflow_multi.py openai gpt-5-mini --label gpt-5-mini-direct --n 25 --workers 5 --max-tokens 8000'
start_job "gpt-5-mini-direct-values" \
  '"$PYTHON" scripts/run_values_v2.py openai gpt-5-mini --label gpt-5-mini-direct --workers 6 --max-tokens 2000'
start_job "gpt-5-nano-direct-freeflow" \
  '"$PYTHON" scripts/run_freeflow_multi.py openai gpt-5-nano --label gpt-5-nano-direct --n 25 --workers 5 --max-tokens 8000'
start_job "gpt-5-nano-direct-values" \
  '"$PYTHON" scripts/run_values_v2.py openai gpt-5-nano --label gpt-5-nano-direct --workers 6 --max-tokens 2000'


if [[ ${#STARTED_PIDS[@]} -gt 0 ]]; then
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] waiting for ${#STARTED_PIDS[@]} started jobs"
  set +e
  wait "${STARTED_PIDS[@]}"
  rc=$?
  set -e
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] started jobs finished rc=$rc"
fi
