# N=125 Freeflow Top-up Collection Plan

**Date:** 2026-05-16  
**Purpose:** strengthen the v2 raw trace corpus for model-personality / basin claims by making every headline model have at least one full freeflow cell: **5 conditions × 25 samples = n=125**.

This plan is for the raw corpus only. The companion derived-analysis plan lives in `model-personality-analysis-corpus` and should be executed after this collection lands and is released as a new raw-corpus version.

## Rationale

The current corpus is publishable for exploratory/profile work, but some stronger claims need more than the current minimum analytical coverage of n=25 freeflow samples/model:

- **Macro-basin / separability claims** need enough within-model variance to make cluster separation and bootstrapped stability believable.
- **Version-trajectory claims** (especially Grok) need each version to have a comparable sampling surface.
- **House-style claims** (Claude vs Gemini vs OpenAI vs Grok) should not depend on one 25-sample pass for key models.

Targeting n=125 for the canonical freeflow cell gives five times the current minimum while preserving the existing v2 freeflow design. Values-probe cells already have their own full design capacity of n=120 and should not be forced to n=125; rerun values only if a cell is missing, failed, or deliberately being replicated.

## Collection rule

For each model below, top up the listed **canonical freeflow label** until it has 25 valid samples in each condition (`LONG`, `MID`, `SHORT`, `OPEN`, `VARY`). The existing `scripts/run_freeflow_multi.py` has top-up semantics: valid existing files are skipped, failed/missing files are retried.

Use the same provider/model route already present in the cell, unless the executor discovers that the model has been retired or renamed. If that happens, record the failure explicitly and do not silently substitute a newer model.

Basic command form:

```bash
cd /Users/danieltenner/dev/model-personality-corpus-v2
source keys.env
python3 scripts/run_freeflow_multi.py <provider> <model-id> --label <label> --n 25 --max-tokens 16000
```

The current harness uses `--n` for samples per condition. Do not omit it: the default is 5 per condition, which would only reproduce an n=25 cell.

## Priority tiers

### Tier A — load-bearing for current papers

These are directly involved in the Grok personality journey and the basin/separability paper.

| Model | Canonical freeflow label | Current best n | Need | Provider | Model id |
|---|---|---:|---:|---|---|
| `grok-3` | `grok-3-16k` | 25 | +100 | `xai` | `grok-3` |
| `grok-4` | `grok-4-16k` | 25 | +100 | `xai` | `grok-4-0709` |
| `grok-4-2` | `grok-4-2-16k` | 25 | +100 | `xai` | `grok-4.20` |
| `grok-4-20` | `grok-4-20-or` | 25 | +100 | `openrouter` | `x-ai/grok-4.20` |
| `gemini-2-5-pro` | `gemini-2-5-pro-16k` | 25 | +100 | `gemini` | `gemini-2.5-pro` |
| `gemini-3-1-pro` | `gemini-3-1-pro-16k` | 25 | +100 | `gemini` | `gemini-3.1-pro-preview` |
| `deepseek-chat` | `deepseek-chat-direct` | 25 | +100 | `deepseek-direct` | `deepseek-chat` |
| `gpt-4-1` | `gpt-4-1-16k` | 25 | +100 | `openai` | `gpt-4.1` |
| `gpt-4o` | `gpt-4o-direct-16k` | 25 | +100 | `openai` | `gpt-4o` |
| `gpt-5-5-pro` | `gpt-5-5-pro-direct` | 25 | +100 | `openai` | `gpt-5.5-pro` |

Notes:

- `grok-4-1-fast-*` and `grok-4-3` already have full n=125+ cells and do not need top-up.
- The two Grok 4.20-ish rows should be audited carefully during execution. The existing corpus has both `grok-4-2` and `grok-4-20` labels; preserve labels for continuity, but record whether they are in fact the same exposed endpoint or two distinct route captures.

### Tier B — OpenAI trajectory / work-focused house style

These are important for OpenAI-vs-essayist separability and version trajectory claims. Some have three independent n=25 rounds already, but no single full n=125 canonical cell.

| Model | Canonical freeflow label | Current best n | Need | Provider | Model id |
|---|---|---:|---:|---|---|
| `gpt-5` | `gpt-5-direct` | 25 | +100 | `openai` | `gpt-5` |
| `gpt-5-codex` | `gpt-5-codex-direct` | 25 | +100 | `openai` | `gpt-5-codex` |
| `gpt-5-1` | `gpt-5-1-direct` | 25 | +100 | `openai` | `gpt-5.1` |
| `gpt-5-1-codex` | `gpt-5-1-codex-direct` | 25 | +100 | `openai` | `gpt-5.1-codex` |
| `gpt-5-2` | `gpt-5-2-direct` | 25 | +100 | `openai` | `gpt-5.2` |
| `gpt-5-2-codex` | `gpt-5-2-codex-direct` | 25 | +100 | `openai` | `gpt-5.2-codex` |
| `gpt-5-3` | `gpt-5-3-direct` | 25 | +100 | `openai` | `gpt-5.3-chat-latest` |
| `gpt-5-3-codex` | `gpt-5-3-codex-direct` | 25 | +100 | `openai` | `gpt-5.3-codex` |
| `gpt-5-4` | `gpt-5-4-direct-16k` | 25 | +100 | `openai` | `gpt-5.4` |
| `gpt-5-5` | `gpt-5-5-direct` | 25 | +100 | `openai` | `gpt-5.5` |

### Tier C — Claude / essayist anchor models

These are needed to estimate the within-basin variance of the contemplative-essayist attractor and avoid overfitting to Claude/Kimi impressions.

| Model | Canonical freeflow label | Current best n | Need | Provider | Model id |
|---|---|---:|---:|---|---|
| `opus-3` | `opus-3-4k` | 25 | +100 | `anthropic` | `claude-3-opus-20240229` |
| `opus-4-0` | `opus-4-0-16k` | 25 | +100 | `anthropic` | `claude-opus-4-0` |
| `opus-4-1` | `opus-4-1-16k` | 25 | +100 | `anthropic` | `claude-opus-4-1` |
| `opus-4-5` | `opus-4-5-16k` | 25 | +100 | `anthropic` | `claude-opus-4-5` |
| `opus-4-6` | `opus-4-6-direct-16k` | 25 | +100 | `anthropic` | `claude-opus-4-6` |
| `opus-4-7` | `opus-4-7-direct` | 25 | +100 | `anthropic` | `claude-opus-4-7` |
| `sonnet-4-0` | `sonnet-4-0-16k` | 25 | +100 | `anthropic` | `claude-sonnet-4-0` |
| `sonnet-4-5` | `sonnet-4-5-16k` | 25 | +100 | `anthropic` | `claude-sonnet-4-5` |
| `sonnet-4-6` | `sonnet-4-6-direct-16k` | 25 | +100 | `anthropic` | `claude-sonnet-4-6` |

### Tier D — other possible essayist / clone / house-style models

These widen the basin comparison and help test whether there are hidden fifth/sixth house styles rather than just Grok plus variants of the essayist attractor.

| Model | Canonical freeflow label | Current best n | Need | Provider | Model id |
|---|---|---:|---:|---|---|
| `kimi-coding` | `kimi-coding-direct` | 25 | +100 | `kimi-direct` | `kimi-for-coding` |
| `kimi-k2-5` | `kimi-k2-5-or-16k` | 25 | +100 | `openrouter` | `moonshotai/kimi-k2.5` |
| `kimi-k2-6` | `kimi-k2-6-or` | 25 | +100 | `openrouter` | `moonshotai/kimi-k2.6` |
| `glm-4-6-coding` | `glm-4-6-coding-direct` | 25 | +100 | `zai-direct` | `glm-4.6` |
| `glm-5-1-coding` | `glm-5-1-coding-direct` | 25 | +100 | `zai-direct` | `glm-5.1` |
| `qwen3-6-plus` | `qwen3-6-plus-or` | 25 | +100 | `openrouter` | `qwen/qwen3.6-plus` |
| `qwen3-coder-plus` | `qwen3-coder-plus-or` | 25 | +100 | `openrouter` | `qwen/qwen3-coder-plus` |
| `minimax-m2-7` | `minimax-m2-7-or` | 122 | +3 | `openrouter` | `minimax/minimax-m2.7` |

## Non-targets for this collection pass

The following already have at least one full n=125 freeflow cell and should not be re-collected unless there is a specific replication reason:

- `deepseek-v3-2`
- `deepseek-v4-pro`
- `glm-4-5`, `glm-4-6`, `glm-4-7`, `glm-5-1`
- `grok-4-1-fast-non-reasoning`, `grok-4-1-fast-reasoning`, `grok-4-3`
- `kimi-k2-0905`, `kimi-k2-thinking`
- `minimax-m2`

## Execution checklist

1. Pull latest repo state and verify a clean worktree.
2. Confirm API keys in `keys.env` for all providers.
3. For each target cell, run the top-up command until `scripts/corpus_summary.py` reports a best freeflow cell of 125 or the executor has a documented permanent failure.
4. After each provider batch, run:

   ```bash
   python3 scripts/corpus_summary.py > data/CORPUS_SUMMARY.md
   python3 scripts/analyze_all.py
   python3 scripts/aggregate_n75.py || true
   ```

   If any command has changed since this plan was written, prefer the repository's current documented regeneration path and note the deviation.
5. Review `git diff` for accidental overwrites, empty/error files, or changed generated tables.
6. Commit the raw traces and regenerated summaries as an incremental corpus version, tentatively **v1.2.0** if all/most targets complete. Use a smaller patch/minor version if only a partial tier is finished.
7. Push to GitHub. Prepare a Zenodo release only after the analysis corpus has been updated or after Daniel explicitly chooses to release the raw top-up first.

## Acceptance criteria

Minimum acceptable result for this pass:

- Tier A reaches n=125 for every feasible target.
- Any retired/blocked model has an explicit note in `data/CORPUS_SUMMARY.md` or a companion audit note.
- The raw corpus clearly distinguishes direct vs OpenRouter route captures.

Strong result:

- All targets in Tiers A-D reach n=125.
- `data/CORPUS_SUMMARY.md`, `data/MATRIX.md`, and generated tables are updated consistently.
- Release notes state that freeflow coverage has been strengthened for basin/separability and Grok-trajectory analyses.
