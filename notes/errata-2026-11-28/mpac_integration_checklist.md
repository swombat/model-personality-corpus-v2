# MPAC Downstream Integration & Cached-Derivative Checklist (`ERRATA-2026-11-28`)

Prepared to support eligibility/membership review across `mpac` (`website/`, `analysis/freeflow/`, and `analysis/values-probe/`):

1. **Prefix-matching pooling traps in `website/scripts/generate_data.py` (`model_from_cell` / `generate_samples`):**
   - Because superseded cells remain at their published `data/` paths in `model-personality-corpus-v2`:
     - `freeflow_mixtral-8x22b-instruct-or-pin-mistral` and `mixtral-8x22b-instruct-or-pin-mistral` match prefix `mixtral-8x22b-instruct-` alongside `mixtral-8x22b-instruct-v0-1-runpod-vllm-bf16-rcc88a6cc`. Gate out cells with `eligible_for_named_weight_analysis: false` in `data/MODEL_IDENTITY_CORRECTIONS.json` so `mixtral-8x22b-instruct.json` receives `125` freeflow + `120` values (not `250` + `240`).
     - `freeflow_mistral-small-24b-instruct-2501-or-pin-deepinfra` and `mistral-small-24b-instruct-2501-or-pin-deepinfra` match prefix `mistral-small-24b-instruct-2501-` alongside `mistral-small-24b-instruct-2501-runpod-vllm-bf16-bare-r8f4e4ef3`. Gate on `strict_bare_instruction_eligible` (or explicit cell selection) so `mistral-small-24b-instruct-2501.json` does not pool DeepInfra's 176-token FP8 cell with the bare BF16 cell.
     - `ministral-3-8b-instruct-2512-runpod-vllm-bf16-t015-bare-rfb3313d2` and `...-hfstock-rfb3313d2` use `ministral-3-8b-instruct-2512` (distinct from active map slug `ministral-8b-2512`); keep both out of `CELL_MODEL_ALIASES` for `ministral-8b-2512` so `ministral-8b-2512` stays at `125` freeflow + `120` values (`ministral-8b-2512-or-pin-mistral`).

2. **Cached derivatives to retire or regenerate in `mpac`:**
   - **`mistral-saba` (retire from active map & model index):**
     - `analysis/freeflow/personality-model-profiles/index.json` and `profiles/mistral-saba.md`
     - `analysis/freeflow/personality-model-cards/cards/mistral-saba.md`
     - `analysis/freeflow/personality-aggregates/manifest.json`
     - `analysis/values-probe/per-model/` & `analysis/values-probe/final/data/` (`source_map.jsonl`, tables, `curated_examples.json`)
     - `website/public/data/samples/mistral-saba.json` (`generate_map.py` globs `public/data/samples/*.json` filtered by `models.json` where `status != 'redirect'`; either set `status: 'redirect'` / retired notice or remove `mistral-saba.json` so stale bundle files cannot re-enter).
   - **`mixtral-8x22b-instruct` & `mistral-small-24b-instruct-2501` (re-evaluate before profile republish):**
     - Existing BV1 outputs (`analysis/freeflow/personality-eval-bv1/outputs/`), cards, profiles, straplines/banners, and values-probe rows for both slugs were derived from `mixtral-8x22b-instruct-or-pin-mistral` and `mistral-small-24b-instruct-2501-or-pin-deepinfra` (`v1.2.11` / `e7df4c005`, 2026-07-14) and must be replaced by fresh BV1-Luna + layered values coding on `mixtral-8x22b-instruct-v0-1-runpod-vllm-bf16-rcc88a6cc` and `mistral-small-24b-instruct-2501-runpod-vllm-bf16-bare-r8f4e4ef3`.

3. **Unaffected neighbour check:**
   - `ministral-8b-2512` (`ministral-8b-2512-or-pin-mistral`) and the other 9 non-retired `or-pin-mistral` island models (`ministral-3b-2512`, `ministral-14b-2512`, `mistral-small-3-2-24b-instruct`, `devstral-2512`, `codestral-2508`, `mistral-medium-3`, `mistral-medium-3-1`, `mistral-medium-3-5`, `mistral-large-2512`) plus mainland `mistral-nemo`, `mistral-small-3-1-24b-instruct`, `mistral-7b-instruct-v0-2`, and `mistral-large-4-0` remain active and unchanged at `125` freeflow + `120` values each.
