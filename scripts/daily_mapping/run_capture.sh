#!/bin/bash
# Usage: run_capture.sh RUN_ID            start/resume the capture harness for a run (detached-safe)
#        run_capture.sh RUN_ID --repair AUTHZ ID...   repair-lane exhausted raw tasks (2 extra tries), then resume
# Logs: <this repo>/logs/capture-harness/RUN_ID/{service.out,STATUS.md,state/}
#
# Body-neutral. Key: uses OPENROUTER_API_KEY if already set (Mira: run under
# corpus-ops/with_keys.py); otherwise sources $OR_KEY_LOADER, default the house
# body's ~/state/lume/or-key-loader.sh. Python: $MPC_PY, default the house
# body's ~/state/tools/mpc-py/bin/python, else python3.
set -u
RUN=$1; shift
cd "$(dirname "$(readlink -f "$0")")/../.."
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  LOADER=${OR_KEY_LOADER:-$HOME/state/lume/or-key-loader.sh}
  [ -f "$LOADER" ] && source "$LOADER"
fi
[ -n "${OPENROUTER_API_KEY:-}" ] || { echo "no OpenRouter key"; exit 9; }
R=logs/capture-harness/$RUN
PY=${MPC_PY:-$HOME/state/tools/mpc-py/bin/python}
[ -x "$PY" ] || PY=$(command -v python3)
if [ "${1:-}" = "--repair" ]; then
  AUTH=$2; shift 2
  (cd scripts/capture_harness && $PY recover_blocked.py ../../$R/spec.json --state ../../$R/state --authorization "$AUTH" --limit 2 "$@"); echo "repair exit $?"
fi
exec $PY scripts/capture_harness/service.py $R/spec.json --state $R/state
