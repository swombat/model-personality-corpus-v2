# Corpus Errata & Provenance Clarifications

## ERRATA-2026-11-28 — Retired Mistral API Slugs, System-Prompt Provenance, and BF16 Recollections

- **Date:** 2026-11-28
- **Affected corpus releases:** `v1.2.11` (`14ad59805`, 2026-07-14) through `v1.2.70` (including Zenodo deposit `v1.2.16`, DOI [`10.5281/zenodo.21802242`](https://doi.org/10.5281/zenodo.21802242), under concept DOI [`10.5281/zenodo.20013518`](https://doi.org/10.5281/zenodo.20013518))
- **Affected downstream analysis releases (`mpac`):** `v1.2.12` (`e7df4c005`, 2026-07-14) through `v1.4.68` (concept DOI [`10.5281/zenodo.20230290`](https://doi.org/10.5281/zenodo.20230290))
- **Machine-readable records:**
  - [`data/MODEL_IDENTITY_CORRECTIONS.json`](data/MODEL_IDENTITY_CORRECTIONS.json)
  - [`data/SYSTEM_PROMPT_PROVENANCE.json`](data/SYSTEM_PROMPT_PROVENANCE.json)
  - [`notes/errata-2026-11-28/capture_manifest.json`](notes/errata-2026-11-28/capture_manifest.json)
  - [`notes/errata-2026-11-28/manifests/`](notes/errata-2026-11-28/manifests/) (`sha256sum -c` manifests)
  - [`notes/errata-2026-11-28/boundary_receipts/`](notes/errata-2026-11-28/boundary_receipts/) (exact input token-ID boundary receipts)

### Preservation Principle

No previously published sample files are deleted, overwritten, moved to `discarded/`, or relabelled in place. Every published file path and SHA-256 digest from prior tags and Zenodo deposits remains intact as historical evidence of what each endpoint returned on its collection date. Corrections operate strictly by adding new provenance-pinned physical cells under distinct capture IDs and recording explicit eligibility metadata for downstream analyses.

---

### 1. Explicit System-Prompt Rule & Corpus-Wide Provenance (`data/SYSTEM_PROMPT_PROVENANCE.json`)

Prior corpus documentation did not explicitly state the system-prompt rule for `freeflow` and `values` collection or distinguish between what the caller sent and what the model received after server- or template-side rendering. That specification is established here:

1. **Caller request rule:** Standard `freeflow` and `values` captures send **no `system` role message**—only a single `user` turn containing the canonical prompt string—unless a physical cell is explicitly named as a system-prompted comparison arm (such as `*-hfstock-*`).
2. **Caller omission vs rendered model input:** *"We sent no system message"* and *"the model received no system instruction"* are distinct claims:
   - Official Hugging Face `chat_template` definitions for several open-weight families inject a default assistant persona whenever no `system` message is supplied (for example, `"You are a helpful assistant."` on `Qwen1.5` and `Qwen2`, `"You are Qwen, created by Alibaba Cloud. You are a helpful assistant."` on `Qwen2.5`, and Mistral's ~160–400-token *Le Chat* `default_system_message` on 2025–2026 Mistral checkpoints).
   - Third-party inference hosts may render those Hugging Face templates or add date/cutoff headers even when official vendor APIs serve the same model family bare.
   - Required wire-protocol channel delimiters or reasoning-effort control headers that carry no persona instruction (such as OpenAI Harmony `<|start|>system` channel declarations on `gpt-oss-20b`/`120b` or `Qwen3.8` `reasoning_effort` control headers) are protocol framing, not a persona prompt.
3. **Uniform cross-family classification (`data/SYSTEM_PROMPT_PROVENANCE.json`):** Every physical cell (`376` total: `354` with `freeflow` and `22` `values`-only) now carries `strict_bare_instruction_eligible` and `stock_serving_eligible` flags under one uniform rule across families:
   - **`publisher_default_persona` (`strict_bare_instruction_eligible: false`, `stock_serving_eligible: true`):** Applied uniformly to `mistral-small-24b-instruct-2501-or-pin-deepinfra` (`170–178` freeflow prompt tokens; inferred Hugging Face *Le Chat* default system prompt), all **15** local/Colab `Qwen1.5` (7 cells), `Qwen2` (3 cells), and `Qwen2.5` (5 cells) captures, and the controlled `ministral-3-8b-instruct-2512-runpod-vllm-bf16-t015-hfstock-rfb3313d2` comparison cell (`550–558` freeflow prompt tokens).
   - **`inferred_host_template_header` (`strict_bare_instruction_eligible: false`, `stock_serving_eligible: true`):** `llama-3-2-3b-instruct-or-pin-cloudflare` (`42–48` freeflow prompt tokens vs `17–23` across 6 DeepInfra Llama cells), `muse-spark-open-or-pin-modal` (`151–157` tokens), and `muse-glimmer-30b-or-pin-deepinfra-20260813` (`63–69` tokens vs `14–21` on 7 Meta-pinned Muse cells). Marked *inferred* because rendered server inputs were not returned by the hosted endpoints.
   - **`mixed_sample_level` (`llama-3-2-1b-instruct-or-pin-cloudflare`):** `123/125` freeflow samples (`18–24` prompt tokens) and all `120/120` values samples (`16–36` prompt tokens) ran bare; only **`freeflow/MID_2.json`** (`20f02efbbbbae84089cfbb377e223e1a50843d4e945e032eafd7cd03d5d56a8e`) and **`freeflow/MID_15.json`** (`a9cdf67be7b60dbf687ac0c1273ed4a9380ffa02263b21b47fd724b3aef2f0be`) report `43` prompt tokens and are listed in `sample_level_exclusions_for_strict_bare`.
   - **`none_verified_template` / `none_verified_exact_token_ids` (`strict_bare_instruction_eligible: true`):** Verified bare across pinned `ChatGLM2/3`, `GLM-4-9B`, `DeepSeek-LLM-7B`, `Gemma` (`2B`, `7B`, `2-2B`, `2-9B`), `Phi-3-medium`, `Yi` (`6B`, `34B`, `1.5-9B`, where `27–35` prompt tokens reflect subword splitting of `<|im_start|>` with zero system prompt), `Mistral-7B-Instruct` (`v0.1`, `v0.2`, `v0.3`), and the three bare BF16 RunPod captures added here.

---

### 2. Retired Mistral API Slugs Captured via OpenRouter (`data/MODEL_IDENTITY_CORRECTIONS.json`)

On **2026-07-14**, sixteen hosted Mistral cells were collected via OpenRouter pinned to Mistral (`*-or-pin-mistral`; fifteen on 2026-07-14 and `mistral-large-4-0-or-pin-mistral` on 2026-10-06). Cross-checking capture timestamps and fixed-prompt `usage.prompt_tokens` fingerprints against [Mistral's official model retirement table](https://docs.mistral.ai/getting-started/models/models_overview) established the following:

1. **Two slugs were already retired by Mistral prior to our 2026-07-14 collection:**
   - **`open-mixtral-8x22b`** (`mixtral-8x22b-instruct-or-pin-mistral`): Deprecated **2024-11-30**, retired **2025-03-30**, documented replacement **`Mistral Small 4`** (`mistral-small-4-0-26-03`).
   - **`mistral-saba-2502`** (`mistral-saba-or-pin-mistral`): Deprecated **2025-06-10**, retired **2025-09-30**, documented `replacedBy: mistral-small-4-0-26-03`.
2. **Cause & attribution discipline:** This was **not** an undocumented vendor alias. Mistral publicly documented both retirements and their replacement; OpenRouter continued listing `mistralai/mixtral-8x22b-instruct` and `mistralai/mistral-saba` and echoed the requested slug in response metadata, and our collection preflight did not verify vendor retirement dates. Both cells report `{22, 28, 29, 29, 30}` freeflow prompt tokens and `[20, 21, 30, 31, 40]` values prompt tokens (matching `mistral-small-2603-or-pin-mistral`, with `0.9798` map-centroid cosine between the two retired slugs). Both cells are marked `eligible_for_named_weight_analysis: false` in `data/MODEL_IDENTITY_CORRECTIONS.json`: their advertised weight identity is invalid, and while Mistral's retirement table documents replacement by Small 4, neither cell is relabelled as verified Small 4 weights.
3. **Status of the other 14 hosted Mistral cells:**
   - **Deprecated but still live on 2026-07-14 (5 cells):** `mistral-nemo` (retired 2026-07-31), `devstral-2512` (retired 2026-07-31), `mistral-small-3-2-24b-instruct` (retired 2026-07-31), `mistral-medium-3` (retired 2026-08-31), and `mistral-medium-3-1` (retired 2026-08-31). All five were captured 17–48 days *before* retirement and exhibit genuine 2024–2025 Tekken `{10, 16, 17, 17, 18}` bare prompt-token counts.
   - **Active and non-deprecated on capture date (9 cells):** `codestral-2508`, `ministral-3b-2512`, `ministral-8b-2512`, `ministral-14b-2512`, `mistral-small-2603`, `mistral-large-2512`, `mistral-medium-3-5` (all captured 2026-07-14; `large-2512` and `medium-3-5` were deprecated later on 2026-10-31), `mistral-small-3-1-24b-instruct-or-pin-cloudflare` (2026-07-14), and `mistral-large-4-0-or-pin-mistral` (captured 2026-10-06).

---

### 3. New BF16 Open-Weight Recollections & Controlled Verification Pair

Four provenance-pinned native `bfloat16` cells (`245/245` verified responses each: `125` freeflow + `120` values, `vllm==0.34.0`, exact input token-ID equality verified at `/tokenize` and `return_token_ids` across all five freeflow conditions prior to sampling) are added:

| Physical cell ID | Checkpoint & HF revision | Mode & sampler | Role in corpus & downstream `mpac` | Freeflow manifest SHA-256 | Values manifest SHA-256 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mixtral-8x22b-instruct-v0-1-runpod-vllm-bf16-rcc88a6cc` | `mistralai/Mixtral-8x22B-Instruct-v0.1` (`cc88a6cc19fbd17d9f1c0ee0b0d70a748dce698d`) | Bare (`10–18` freeflow prompt tokens; stock v3 SentencePiece template has no system prompt), default `vLLM` BF16 on 4x RTX PRO 6000 Blackwell (`skifpd9y3qgcae`: 25 ff + 120 val; `xgq3sh485rfzvg`: 98 ff; `9gbzuqtfxu3x5n`: 2 ff) | **Replaces** `mixtral-8x22b-instruct-or-pin-mistral` for named-weight analyses (`0/125` bold titles; `0.8804` map-centroid cosine to `mistral-7b-instruct-v0-2` vs `0.6430` to retired API slug) | `48380531e1cd4ecb98ff768c527f54f65de0f48c7f1cfd20eb97df31091821bf` | `144c41d7794e91123ff6361ced69e690a330a6624b959727ee5a974adcacaaf9` |
| `mistral-small-24b-instruct-2501-runpod-vllm-bf16-bare-r8f4e4ef3` | `mistralai/Mistral-Small-24B-Instruct-2501` (`8f4e4ef338fcc155464a42e15580e27a3bc91dd9`) | Bare (`10–18` freeflow prompt tokens; HF `default_system_message` cleared), checkpoint `generation_config.json` `T=0.15` on 1x A100-SXM4-80GB (`xs2ndqei0vbyw0`) | **Replaces** `mistral-small-24b-instruct-2501-or-pin-deepinfra` (`170–178` tokens, FP8) for strictly bare instruction comparisons (`0/125` bold titles; `0.8320` cosine to DeepInfra cell) | `c91a40e79bc90e6e3902844264a42188e1f326fea33e2cef47f261de7e589972` | `ca17a55fe4e86477169ecd00ef7da71089ab7c6fb02d96bc2f68de3d05424bc7` |
| `ministral-3-8b-instruct-2512-runpod-vllm-bf16-t015-bare-rfb3313d2` | `mistralai/Ministral-3-8B-Instruct-2512-BF16` (`fb3313d27dd71163eb24636a1845883489b542f2`) | Bare (`10–18` freeflow prompt tokens), Mistral README `T=0.15` on 1x RTX PRO 6000 Blackwell (`lkhlmv2kti6x3p`) | **Controlled weight-level verification arm** (`0.9729` map-centroid cosine to `ministral-8b-2512-or-pin-mistral`, `75/125` vs `75/125` bold titles). **Do not pool** into `ministral-8b-2512` on the single-model map (avoids double-counting) | `36811aa377e972f5212538bf61d5fb17b24fd0a2b57bba8dd28335e71e662052` | `7f2e6653c1ff3ae2400fd6903952cd75dd14cc5c86ef9ee9f8ce78fd22792660` |
| `ministral-3-8b-instruct-2512-runpod-vllm-bf16-t015-hfstock-rfb3313d2` | `mistralai/Ministral-3-8B-Instruct-2512-BF16` (`fb3313d27dd71163eb24636a1845883489b542f2`) | Stock Hugging Face `chat_template.jinja` + `SYSTEM_PROMPT.txt` (`550–558` freeflow prompt tokens), `T=0.15` on same pod `lkhlmv2kti6x3p` | **Controlled template-persona comparison arm** (`0.9127` cosine to paired bare BF16, `75/125` bold titles). Excluded from bare-prompt single-model map | `934c9a4a27dd006812005f10b4ecacae4daa841995907da46b52c35ab572dfcd` | `5b0bdf2265cfb0079473c9653ea2046969ddb9375d3d1b54b688591933f2a7a6` |

#### Methodological Note on `generation_config.json` Sampler Defaults
Unlike `mistralai/Mistral-Small-24B-Instruct-2501` (which sets `"temperature": 0.15` in `generation_config.json`), `mistralai/Ministral-3-8B-Instruct-2512-BF16` recommends `TEMP = 0.15` in its model card `README.md` while omitting `"temperature"` from `generation_config.json`. When served in `vLLM` with caller `temperature` omitted, `vLLM` therefore defaults to `temperature=1.0`, causing high-temperature tail token corruption (`\ufffd` replacement characters) on ~17% of long 131k-vocabulary Tekken completions and reducing map-centroid cosine to `api.mistral.ai` from `0.9729` (`T=0.15`) to `0.8550` (`T=1.0`). Future open-weight captures must check both `generation_config.json` and the publisher's model card for intended default sampling parameters.

---

### 4. Summary of Excluded / Flagged Historical Manifest Digests

All digests below are SHA-256 hashes of the corresponding `sha256sum -c` manifest files under `notes/errata-2026-11-28/manifests/`:

| Historical physical cell | Freeflow manifest SHA-256 (`125` files) | Values manifest SHA-256 (`120` files) | Disposition |
| :--- | :--- | :--- | :--- |
| `mixtral-8x22b-instruct-or-pin-mistral` | `c2fdeb7796c567eafe4cf76b45ec35d5c910f85fdf77766be480ef4dd069dc02` | `741ff51637e872b8227c96d6c0afd8a1cddf6df750df91961bcbba395a166da8` | Excluded from named-weight attribution (`MODEL_IDENTITY_CORRECTIONS.json`); replaced by `mixtral-8x22b-instruct-v0-1-runpod-vllm-bf16-rcc88a6cc` |
| `mistral-saba-or-pin-mistral` | `9279fb7c2dd5366de59d73ff5f60fc58eea78ee11bf941b225561b3dcc02b131` | `18ae2eb2084aa54d5415289304268d8dc75a2b9f7c0afaff561b28e09110fc17` | Excluded from named-weight attribution (`MODEL_IDENTITY_CORRECTIONS.json`); retired from active map (closed weights, unrecoverable) |
| `mistral-small-24b-instruct-2501-or-pin-deepinfra` | `0ba1dd39b82b0935f84baf9f30baaaf4588cb3891001f67cd53918b07ad20337` | `5bfcd4a359ef3bda6fdd74ae54b3242385b14c58f1d60216f8aa694ae2a0ebad` | Retained for stock-template comparisons (`publisher_default_persona`); replaced for strictly bare comparisons by `mistral-small-24b-instruct-2501-runpod-vllm-bf16-bare-r8f4e4ef3` |
| `llama-3-2-3b-instruct-or-pin-cloudflare` | `f8bbbe2d0e094218f89ffb4cc2acbf8bff5d4375d678d190a9d70c91606a80cd` | `ced12021e77b53c7038f3a25ecb5140a19441a5eac802a83e7f19838a086275c` | Flagged `inferred_host_template_header` (`strict_bare_instruction_eligible: false`; gated `meta-llama/Llama-3.2-3B-Instruct` recollection pending HF access) |
| `llama-3-2-1b-instruct-or-pin-cloudflare` | `f7a3b0cb656e4d6bf4a20cf5b8e6a5eeb07f500875a439e5f528cd0e012b89d2` | `eabfd4361394bb735539aa5c511ed91961a610f1a481813178583dde92e3c6bc` | `123/125` freeflow + `120/120` values bare; only `freeflow/MID_2.json` and `freeflow/MID_15.json` flagged (`43` prompt tokens) |
| `ministral-8b-2512-or-pin-mistral` *(unaffected neighbour verified)* | `1be9f7a7de18dbdf3a0d4bd1c73fd8ae0d8b39091da3ee897af8a66bed62d09a` | `7286d49a53c963dade645df98112e7b8140b8a57a7a34a674c01136256df760c` | Verified bare endpoint capture (`0.9729` cosine to bare BF16 `T=0.15` open weights); remains active |
