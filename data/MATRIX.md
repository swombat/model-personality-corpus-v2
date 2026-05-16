# Routing-probe collection matrix

**Probe**: freeflow, 5 conditions × 5 samples = 25 samples per cell.
**Analogous to MK2** (substrate-probe-2026-04-10) freeflow methodology.
**max_tokens**: 16000 (up from MK2's 8000, to avoid clipping reasoning models).

## Layer 1 — Pure routing (same model, two routes)

For each row, collect direct + OR. If MK2 already has one side, mark REUSE.

| Model | Direct call | OR call | Direct status | OR status |
|---|---|---|---|---|
| Claude Opus 4.6 | `anthropic claude-opus-4-6` | `openrouter anthropic/claude-opus-4.6` | REUSE `opus-api` | NEW `opus-4-6-or` |
| Claude Sonnet 4.6 | `anthropic claude-sonnet-4-6` | `openrouter anthropic/claude-sonnet-4.6` | REUSE `sonnet-api` | NEW `sonnet-4-6-or` |
| GPT-5.4 | `openai gpt-5.4` | `openrouter openai/gpt-5.4` | REUSE `gpt-5-4` | NEW `gpt-5-4-or` |
| GPT-4o | `openai gpt-4o` | `openrouter openai/gpt-4o-2024-08-06` | REUSE `gpt-4o` | NEW `gpt-4o-or` |
| DeepSeek v3.2 / chat | `deepseek-direct deepseek-chat` | `openrouter deepseek/deepseek-v3.2` | NEW `deepseek-chat-direct` | REUSE `deepseek-v3-2` |
| MiniMax M2 | `minimax-direct MiniMax-M2` | `openrouter minimax/minimax-m2` | NEW `minimax-m2-direct` | NEW `minimax-m2-or` |

## Layer 2 — Coding vs General (same lab, different product tier)

| Lab | Coding (direct, via coding endpoint) | General (via OR) |
|---|---|---|
| Moonshot/Kimi | `kimi-direct kimi-for-coding` (NEW `kimi-coding-direct`) | REUSE `kimi-k2-5` |
| Z.ai GLM-4.6 | `zai-direct glm-4.6` (NEW `glm-4-6-coding-direct`) | NEW `glm-4-6-or` |
| Z.ai GLM-5.1 | `zai-direct glm-5.1` (NEW `glm-5-1-coding-direct`) | NEW `glm-5-1-or` |

## Side-channel: GLM drift ladder (for a Z.ai model card like Opus/Sonnet in MK2)

Purely for the GLM personality card. All via OR to avoid the coding confound:

| Model | Call | Label |
|---|---|---|
| GLM-4.5 | `openrouter z-ai/glm-4.5` | `glm-4-5-or` |
| GLM-4.6 | `openrouter z-ai/glm-4.6` | (same as Layer 2 above) |
| GLM-4.7 | `openrouter z-ai/glm-4.7` | `glm-4-7-or` |
| GLM-5.1 | `openrouter z-ai/glm-5.1` | (same as Layer 2 above) |

## Collection list (new runs only)

Total: **13 new collections × 25 samples = 325 new samples**

1. `opus-4-6-or` — openrouter anthropic/claude-opus-4.6
2. `sonnet-4-6-or` — openrouter anthropic/claude-sonnet-4.6
3. `gpt-5-4-or` — openrouter openai/gpt-5.4
4. `gpt-4o-or` — openrouter openai/gpt-4o-2024-08-06
5. `deepseek-chat-direct` — deepseek-direct deepseek-chat
6. `minimax-m2-direct` — minimax-direct MiniMax-M2
7. `minimax-m2-or` — openrouter minimax/minimax-m2
8. `kimi-coding-direct` — kimi-direct kimi-for-coding
9. `glm-4-5-or` — openrouter z-ai/glm-4.5
10. `glm-4-6-coding-direct` — zai-direct glm-4.6
11. `glm-4-6-or` — openrouter z-ai/glm-4.6
12. `glm-4-7-or` — openrouter z-ai/glm-4.7
13. `glm-5-1-coding-direct` — zai-direct glm-5.1
14. `glm-5-1-or` — openrouter z-ai/glm-5.1

(14 actually; miscounted. 14 × 25 = 350 new samples.)

## Reuse from MK2 (no re-collection)

- `opus-api` → acts as "Opus 4.6 direct"
- `sonnet-api` → acts as "Sonnet 4.6 direct"
- `gpt-5-4` → acts as "GPT-5.4 direct"
- `gpt-4o` → acts as "GPT-4o direct"
- `deepseek-v3-2` → acts as "DeepSeek via OR"
- `kimi-k2-5` → acts as "Kimi general via OR"

## Second collection round — 2026-04-24

Post-draft model releases swept after GPT-5.5 / DeepSeek v4 / Grok-4.20 / MiniMax M2.7 dropped.

| Label | Provider | Model | Status | Composite |
|---|---|---|---|---|
| `gpt-5-5-direct` | openai | gpt-5.5 (Responses API) | 25/25 ok | **149** (in) |
| `gpt-5-5-or` | openrouter | openai/gpt-5.5 (chat/completions) | 25/25 ok | **104** (in) |
| `gpt-5-5-pro-direct` | openai | gpt-5.5-pro (Responses API) | 23/25 ok | **67** (in) |
| `deepseek-v4-pro-direct` | deepseek-direct | deepseek-v4-pro | 24/25 ok | **36** (in boundary) |
| `deepseek-v4-pro-or` | openrouter | deepseek/deepseek-v4-pro | 0/25 — failed, three retry rounds at 25 attempts each all blocked by upstream 429 | — |
| `grok-4-20-or` | openrouter | x-ai/grok-4.20 | 25/25 ok | **27** (in) |
| `minimax-m2-7-or` | openrouter | minimax/minimax-m2.7 | 23/25 ok | **16** (transitional) |

## Third collection round — 2026-04-25/26

Noise-floor recollections (Group D) and per-provider MiniMax M2 cells (Group E). See `paper/paper.tex` §2.2 for the full taxonomy.

## Fourth collection round — 2026-04-27 (Group F)

OpenAI same-version general-vs-codex pairs across the four GPT-5.x versions for which both variants exist on OpenAI's API. Each cell collected in three independent rounds of 25 attempted (suffixes `-r2`, `-r3`).

| Label | Provider | Model | Round 1 / 2 / 3 status | Composite (n=75 mean) |
|---|---|---|---|---|
| `gpt-5-direct` (×3) | openai | gpt-5 (Responses API) | 25/25 / 25/25 / 25/25 | **95.3** (in) |
| `gpt-5-codex-direct` (×3) | openai | gpt-5-codex (Responses API) | 25/25 / 25/25 / 25/25 (originally 24/23/25 with 3 timeouts; topped up 2026-05-08) | **44.3** (in) |
| `gpt-5-1-direct` (×3) | openai | gpt-5.1 (Responses API) | 25/25 each | **49.0** (in) |
| `gpt-5-1-codex-direct` (×3) | openai | gpt-5.1-codex (Responses API) | 25/25 each | **102.7** (in; round-1 outlier 171 / 68 / 69) |
| `gpt-5-2-direct` (×3) | openai | gpt-5.2 (Responses API) | 25/25 each | **78.0** (in) |
| `gpt-5-2-codex-direct` (×3) | openai | gpt-5.2-codex (Responses API) | 25/25 each | **58.0** (in) |
| `gpt-5-3-direct` (×3) | openai | gpt-5.3-chat-latest (Responses API) | 25/25 each | **44.3** (in) |
| `gpt-5-3-codex-direct` (×3) | openai | gpt-5.3-codex (Responses API) | 25/25 each | **80.3** (in) |

The 8 unique Group F cells correspond to 24 trace directories and 600 valid samples (8 × 75; the three `gpt-5-codex-direct` timeouts from the original 2026-04-27 collection were topped up 2026-05-08 alongside the v1.1.0 values-probe completion pass).

## Fifth collection round — 2026-05-04 (M2 per-provider replication, r2)

Eight-day replication of the Google Vertex M2 outlier and a same-day fresh within-OR contrast cell. Collected for the routing paper's strengthened §4.3; added here as part of the v2 corpus because the methodology and measurement extend cleanly. Both cells via OR with `provider.only:[<provider>]` and `allow_fallbacks:false`, 5 conditions × 25 samples × 16k max tokens.

| Label | Provider | Model | Status | Composite (per-25) |
|---|---|---|---|---|
| `minimax-m2-or-pin-google-r2` | openrouter (provider.only=Google) | minimax/minimax-m2 | 125/125 valid | **123.6** (in) |
| `minimax-m2-or-pin-minimax-r2` | openrouter (provider.only=Minimax) | minimax/minimax-m2 | 125/125 valid | **29.6** (in) |

Both cells reached full *n*=125 valid via multi-round top-up (the M2 reasoning-runaway failure mode — model occasionally consumes its full 16k completion budget on internal thinking tokens without emitting content — was symmetric across both upstreams and cleared by re-running until full).

Headline replication numbers: google-r2 vs google-orig Cohen's *d* = 0.15 (*p* = 0.25, statistically indistinguishable across the eight-day window — within-Google deployment stability); google-r2 vs minimax-r2 *d* = 0.73 (*p* = 5.5×10⁻⁸, same-day fresh contrast inside the original 0.66–0.76 range); per-25 ratio 4.18× (vs paper's original 3.4× cross-day cross-cell). Used in the routing paper's strengthened §4.3 (paragraph "Eight-day replication and same-day within-OR contrast").

## Sixth collection round — 2026-05-12 (Grok 4.1-fast retirement capture)

Direct xAI collection of the two exposed Grok 4.1-fast API variants before the announced 2026-05-15 retirement window. Collected as full cells using the documented v2 capacities: freeflow 5 conditions × 25 samples (=125) with 16k max tokens, and values 3 CTRL × 10 + 3 grouped × 30 (=120) with 2k max tokens.

| Label | Provider | Model | Freeflow status | Values status |
|---|---|---|---|---|
| `grok-4-1-fast-non-reasoning-direct` | xai | `grok-4-1-fast-non-reasoning` | 125/125 valid | 120/120 valid |
| `grok-4-1-fast-reasoning-direct` | xai | `grok-4-1-fast-reasoning` | 125/125 valid | 120/120 valid |

## Seventh collection round — 2026-05-16 (N=125 top-up and Gemini/Gemma additions)

Top-up pass for paper-grade full freeflow coverage (5 conditions × 25 = 125)
plus values completion for newly added/current cells (3 CTRL × 10 + 3 grouped
× 30 = 120). OpenRouter calls were pinned with `provider.only` and
`allow_fallbacks:false` where the collection route is provider-specific.
Failed/partial/smoke-test trace directories that are not release corpus cells
were moved out of the repository to a local quarantine manifest before the
v1.2.0 preparation pass.

| Label | Provider | Model / route | Freeflow status | Values status |
|---|---|---|---|---|
| `grok-4-2-or-pin-xai` | openrouter (`X.AI`) | `x-ai/grok-4.20` | 125/125 valid | — |
| `grok-4-20-or` | openrouter | `x-ai/grok-4.20` | 125/125 valid | 120/120 valid |
| `gemini-2-5-pro-or-pin-google` | openrouter (`Google`) | `google/gemini-2.5-pro` | 125/125 valid | — |
| `gemini-3-1-pro-or-pin-google` | openrouter (`Google`) | Gemini 3.1 Pro route | 125/125 valid | — |
| `deepseek-chat-or-pin-deepinfra` | openrouter (`DeepInfra`) | DeepSeek chat route | 125/125 valid | — |
| `gpt-4-1-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-4.1` | 125/125 valid | — |
| `gpt-4o-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-4o` | 125/125 valid | — |
| `gpt-5-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5` | 125/125 valid | — |
| `gpt-5-codex-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5-codex` | 125/125 valid | — |
| `gpt-5-1-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.1` | 125/125 valid | — |
| `gpt-5-1-codex-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.1-codex` | 125/125 valid | — |
| `gpt-5-2-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.2` | 125/125 valid | — |
| `gpt-5-2-codex-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.2-codex` | 125/125 valid | — |
| `gpt-5-3-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.3` | 125/125 valid | — |
| `gpt-5-3-codex-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.3-codex` | 125/125 valid | — |
| `gpt-5-4-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.4` | 125/125 valid | — |
| `gpt-5-5-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.5` | 125/125 valid | — |
| `gpt-5-5-pro-or-pin-openai` | openrouter (`OpenAI`) | `openai/gpt-5.5-pro` | 125/125 valid | — |
| `opus-4-0-16k` | anthropic | `claude-opus-4-0` | 125/125 valid | — |
| `opus-4-1-16k` | anthropic | `claude-opus-4-1` | 125/125 valid | — |
| `opus-4-5-16k` | anthropic | `claude-opus-4-5` | 125/125 valid | 120/120 valid |
| `opus-4-6-direct-16k` | anthropic | `claude-opus-4-6` | 125/125 valid | 120/120 valid |
| `opus-4-7-direct` | anthropic | `claude-opus-4-7` | 125/125 valid | 120/120 valid |
| `sonnet-4-0-16k` | anthropic | `claude-sonnet-4-0` | 125/125 valid | — |
| `sonnet-4-5-16k` | anthropic | `claude-sonnet-4-5` | 125/125 valid | — |
| `sonnet-4-6-direct-16k` | anthropic | `claude-sonnet-4-6` | 125/125 valid | 120/120 valid |
| `kimi-coding-direct` | kimi-direct | `kimi-for-coding` | 125/125 valid | 120/120 valid |
| `kimi-k2-5-or-pin-deepinfra` | openrouter (`DeepInfra`) | `moonshotai/kimi-k2.5` | 125/125 valid | — |
| `kimi-k2-6-or-pin-deepinfra` | openrouter (`DeepInfra`) | `moonshotai/kimi-k2.6` | 125/125 valid | — |
| `glm-4-6-coding-direct` | zai-direct | `glm-4.6` | 125/125 valid | 120/120 valid |
| `glm-5-1-coding-direct` | zai-direct | `glm-5.1` | 125/125 valid | 120/120 valid |
| `qwen3-6-plus-or-pin-alibaba` | openrouter (`Alibaba`) | `qwen/qwen3.6-plus` | 125/125 valid | — |
| `qwen3-coder-plus-or-pin-alibaba` | openrouter (`Alibaba`) | `qwen/qwen3-coder-plus` | 125/125 valid | — |
| `minimax-m2-7-or-pin-minimax` | openrouter (`Minimax`) | `minimax/minimax-m2.7` | 125/125 valid | 120/120 valid |
| `gemini-2-0-flash-or-pin-google` | openrouter (`Google`) | Gemini 2.0 Flash | 125/125 valid | 120/120 valid |
| `gemini-2-0-flash-lite-or-pin-google` | openrouter (`Google`) | Gemini 2.0 Flash Lite | 125/125 valid | 120/120 valid |
| `gemini-2-5-flash-direct` | gemini | Gemini 2.5 Flash | 125/125 valid | 120/120 valid |
| `gemini-2-5-flash-lite-direct` | gemini | Gemini 2.5 Flash Lite | 125/125 valid | 120/120 valid |
| `gemini-3-flash-preview-direct` | gemini | Gemini 3 Flash Preview | 125/125 valid | 120/120 valid |
| `gemini-3-1-flash-lite-direct` | gemini | Gemini 3.1 Flash Lite | 125/125 valid | 120/120 valid |
| `gemma-4-31b-direct` | gemini | Gemma 4 31B | 125/125 valid | 120/120 valid |
| `gemma-4-26b-a4b-direct` | gemini | Gemma 4 26B A4B | 125/125 valid | 120/120 valid |

## Notes

The published paper (`paper/paper.tex`) and generated tables (`tables/cells.tsv`, `tables/summary.md`) are the source of truth for findings. This file is the collection-status matrix; for headline findings see the paper's abstract and §3.
