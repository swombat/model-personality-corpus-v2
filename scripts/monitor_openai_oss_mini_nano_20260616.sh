#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
mkdir -p logs
LOCKDIR="logs/openai-oss-mini-nano-monitor.lock"
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] monitor already running" >> logs/openai-oss-mini-nano-monitor-20260616.log
  exit 0
fi
trap 'rmdir "$LOCKDIR"' EXIT

{
  echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] monitor tick"
  scripts/collect_openai_oss_mini_nano_20260616.sh
  if /Library/Frameworks/Python.framework/Versions/3.11/bin/python3 scripts/check_openai_oss_mini_nano_20260616.py; then
    echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] corpus complete"
    touch logs/openai-oss-mini-nano-corpus-complete.done
  else
    echo "[$(date +%Y-%m-%dT%H:%M:%S%z)] corpus incomplete; jobs ensured/reruns will top up"
  fi
} >> logs/openai-oss-mini-nano-monitor-20260616.log 2>&1
