#!/usr/bin/env bash
# Source this file to export corpus collection provider keys from SOPS:
#   source scripts/source_sops_keys.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SECRETS="$ROOT/secrets/provider-keys.sops.json"
if ! command -v sops >/dev/null 2>&1; then
  echo "sops not found in PATH" >&2
  return 1 2>/dev/null || exit 1
fi
# A failed command substitution inside eval otherwise becomes a successful
# empty eval and starts workers without credentials.
if ! _corpus_exports="$(sops -d "$SECRETS" | python3 -c 'import json, shlex, sys; data=json.load(sys.stdin); [print("export %s=%s" % (k, shlex.quote(str(v)))) for k, v in data.items()]')"; then
  unset _corpus_exports
  echo "Corpus credential loading failed; refusing to start workers" >&2
  return 1 2>/dev/null || exit 1
fi
eval "$_corpus_exports"
unset _corpus_exports
