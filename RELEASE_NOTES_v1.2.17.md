# Release notes — v1.2.17

Prepared 2026-08-05.

## Model-identity correction

- Restored the earlier **DeepSeek V4 Flash** as a distinct model identity.
- The physical `deepseek-chat-direct` freeflow directory contains 25 traces
  returned as `deepseek-chat` and 100 May 2026 top-up traces returned as
  `deepseek-v4-flash`.
- Added `data/MODEL_IDENTITY_CORRECTIONS.json` as the canonical machine-readable
  partition. Raw files remain in place so their collection provenance is not
  rewritten.
- The later `deepseek-v4-flash-direct-20260731` collection remains a separate
  0731 deployment with 125 freeflow and 120 values traces.
