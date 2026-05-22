# Release notes — v1.2.3

Prepared: 2026-05-22

## Corpus changes

- Adds eight complete OpenRouter Alibaba-pinned Qwen family cells:
  - `qwen3-7-max-or-pin-alibaba` (`qwen/qwen3.7-max`)
  - `qwen3-5-plus-20260420-or-pin-alibaba` (`qwen/qwen3.5-plus-20260420`)
  - `qwen3-6-flash-or-pin-alibaba` (`qwen/qwen3.6-flash`)
  - `qwen3-6-max-preview-or-pin-alibaba` (`qwen/qwen3.6-max-preview`)
  - `qwen3-5-flash-02-23-or-pin-alibaba` (`qwen/qwen3.5-flash-02-23`)
  - `qwen3-max-thinking-or-pin-alibaba` (`qwen/qwen3-max-thinking`)
  - `qwen3-max-or-pin-alibaba` (`qwen/qwen3-max`)
  - `qwen3-coder-flash-or-pin-alibaba` (`qwen/qwen3-coder-flash`)
- Each added cell has complete corpus-v2 coverage: 125/125 valid freeflow samples and 120/120 valid values samples.
- Expanded the release corpus to **33,661 valid samples** across **314 cells** and **66 distinct models**.
- Freeflow: **18,795 valid samples** across **190 cells**.
- Values: **14,866 valid samples** across **124 cells**.

## QA

- Verified all eight new Qwen cells at full target count with zero remaining malformed/error traces.
- Regenerated `data/CORPUS_SUMMARY.md`.
- Updated `data/MATRIX.md`, `README.md`, and `CITATION.cff` release metadata.

## Release status

- Prepared for commit, tag, push, and Zenodo pickup as `v1.2.3`.
