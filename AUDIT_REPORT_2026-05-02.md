# Post-audit data collection report — 2026-05-02 → 2026-05-03

> **⚠️ UPDATE 2026-05-03 14:25 — corrections to this report**
>
> Two material claims in the 03:30 version below have been corrected by subsequent work and should NOT be used as the basis for paper edits. Read the **§ "2026-05-03 morning correction"** at the bottom for current state.
>
> 1. **Fireworks framing was wrong.** The 03:30 report described fireworks as "rate-limit-induced uncollectable on free OR account, recoverable with paid key." We have been on a paid OR account the whole time. The actual constraint is OR's shared-pool rate-limit on Fireworks specifically; the fix is BYOK (a direct Fireworks API key registered on OR), not a paid OR account. Fireworks has now been formally dropped from analysis (it's not the only provider for any model in the sweep).
> 2. **"Three new Bonferroni-surviving effects" was over-stated.** Of the three the 03:30 report flagged as new findings, only **one** survived under fuller VARY-completion data. The two GLM 4.6 effects (siliconflow vs zai; novita vs siliconflow) weakened to non-significant under Bonferroni once the comparison cells were also at full N=125. Only the Kimi K2-thinking atlascloud-vs-google effect (d=0.40, p_Bonf=0.005) held. M2-Google-Vertex (the original paper claim, d=0.73) is robust and unchanged.
>
> The trajectory: 03:30 audit was based on asymmetrically-complete data (target cells at N=125, comparison cells often at N=100-110 due to VARY-condition partial fills). Symmetric completion this morning shrank the effect sizes for GLM 4.6 below significance. This is the same family of error the audit was designed to catch — claim-vs-substrate drift driven by underpowered cells — applied this time to the audit's own headline.

## TL;DR (as of 03:30, see corrections above)

The data collection completed successfully. Code fixes + new data are committed. **The paper is NOT updated yet — it requires your judgment because the central finding has materially shifted.**

The paper currently claims M2-Google-Vertex "stands alone" as a per-provider deployment outlier surviving multiple-comparisons correction. With the now-complete data, this is no longer true: GLM 4.6 and Kimi K2-thinking each surface effects that survive Bonferroni at α=0.05.

## What I did tonight (2026-05-02 evening → 2026-05-03 03:00)

### 1. Audit catches I made before launching collection

- **Kimi K2 was silently excluded from the per-provider sweep.** The `MODELS` list in `scripts/run_per_provider_sweep.py` listed only 7 open-weights models; Kimi K2 is in the corpus and is multi-upstream on OR (K2-0905 has 4 upstreams, K2-thinking has 3). The paper's "every other multi-upstream open-weights model" claim was false as written.
- **The sweep log was lying.** `run_per_provider_sweep.py` counts `: ok ` substrings in stdout to infer success. `run_freeflow_multi.py` prints that pattern; `run_values_v2.py` did not — so every line of `sweep.log` reported `values:0ok/0err` regardless of whether values actually completed. There was no reliable monitoring of values-side completion.
- **The paper claimed a <50-valid threshold the code didn't enforce.** §3.4 said "After dropping cells with <50 valid samples..."; `analyze_per_provider.py` accepted any non-empty cell. Three cells were below threshold and silently in the analysis (`chutes`, `deepinfra`, `inceptron`).

### 2. Catches I made *during* collection (with your help)

- **Original sweep was destructively overwriting partial-valid cells.** When I launched the first sweep at 19:18, I hadn't realised `run_freeflow_multi.py` overwrites existing JSON files by index without checking if they're already valid. Cells that had 80-100 valid samples were getting overwritten by re-runs that produced fewer valid samples (e.g. `m2-7-fireworks` went 91 valid → 73 mid-rerun before I caught it).
  - **You caught it** by asking "you were able to recover from git, right?" — which prompted me to actually use git as the recovery mechanism I hadn't reached for. (Logged in `daily-journals/2026-05-02.md#~20:50`.)
- **Then I conflated two cells with "fireworks" in their name** when reporting back ("0 → 73, recovered!" — wrong cell). Walked back next turn.
- **Later I called fireworks a "dead upstream" without checking** — actually 429 rate-limit from OR's free pool. Self-caught the next turn by reading the actual error JSON. (Logged at `daily-journals/2026-05-03.md#~01:25`.)

### 3. Code fixes (now committed)

All in `scripts/`:

- `run_freeflow_multi.py` + `run_values_v2.py`: added **top-up semantics** — skip files that already exist with non-empty `result`. Re-runs now only fill missing/error indices, preserving prior valid samples.
- `run_values_v2.py`: per-sample stdout (`: ok` / `: err` / `: skip`) so the sweep log can monitor values-side completion. Was previously committed-only-by-implication; now properly tracked.
- `run_per_provider_sweep.py`: added Kimi K2-0905 + Kimi K2-thinking to `MODELS`. Bumped subprocess timeout 2400s → 5400s to handle slow upstreams. Updated docstring with corrected model list and counts.
- `analyze_per_provider.py`: added `MIN_VALID_SAMPLES=50` hard threshold gate enforcing the paper's stated criterion. Stderr report when cells are dropped. Added Kimi K2 to the analysis MODELS list.

### 4. Data collection results

Sweep ran 60 cells (Kimi K2 added → 61 - 1 configured-skip = 60 attempted), 0 sweep-level FAILs (one timeout on `glm-5-1-or-pin-inceptron` but it had written 108 valid samples before being killed, so the data is usable).

**Final per-provider corpus state (post-sweep):**

| Probe | Cells with ≥50 valid | Total valid samples |
|---|---:|---:|
| Freeflow | 63 | 7,472 |
| Values | 59 | 6,891 |
| Combined | — | **14,363** |

vs. pre-sweep (paper's "48 freeflow / 50 values / 10,514 samples"):
- Freeflow cells: 48 → 63 (+15 cells, +31%)
- Values cells: 50 → 59 (+9 cells)
- Total samples: 10,514 → 14,363 (+3,849, +37%)

**Two cells could not be collected:**
- `deepseek-v4-pro-or-pin-deepseek` — configured-skip (OR account-level data-policy guardrail; documented in paper §3.5)
- `glm-5-1-or-pin-fireworks` — 429 rate-limit on OR's free pool (paper should describe as "rate-limit-induced uncollectable on free OR account at collection time" — recoverable with paid key, NOT a dead upstream)

**Grok 4.3 (added at your request):**
- `grok-4-3-direct` (xAI direct API): 125 valid freeflow + 120 valid values
- `grok-4-3-or` (OpenRouter): 125 valid freeflow + 120 valid values
- Single-upstream closed-weights case — belongs in §3.3 closed-weights null replication

**Kimi K2 cells (the audit catch):**
- All 4 K2-0905 cells: 125 valid freeflow + 120 valid values, **zero errors across 980 API calls**.
- 3 K2-thinking cells: 123-124 valid freeflow + 118-120 valid values.
- The cells the original sweep didn't even know to attempt turned out to be the cleanest, most complete cells in the entire corpus.

## **The substantive finding: the paper's "M2 stands alone" claim is now false**

With the complete data, the freeflow analysis surfaces **three distinct per-provider deployment effects that survive Bonferroni correction at α=0.05**:

| Model | Pair | Cohen's d | p (Bonf) | Direction |
|---|---|---:|---:|---|
| **MiniMax M2** | google-vertex vs direct | 0.73 | <10⁻⁶ | google >> direct |
| **GLM 4.6** | siliconflow vs zai | -0.44 | 0.025 | siliconflow << zai |
| **GLM 4.6** | novita vs siliconflow | 0.43 | 0.029 | novita >> siliconflow (same effect, other direction) |
| **Kimi K2-thinking** | atlascloud vs google | 0.40 | 0.0060 | atlascloud >> google |

GLM 4.6's siliconflow effect is the most striking new finding: **siliconflow's deployment is markedly LOWER posture than the rest of GLM 4.6's upstreams.** Per-25 composite for siliconflow (32.2) vs the rest (49.4-53.7). This effect was hidden by the partial collection — `glm-4-6-or-pin-siliconflow` had 57 valid samples pre-sweep; with 125 valid samples, the effect cleared correction.

**This is exactly the kind of finding the audit motivated.** The original sweep's partial collections weren't just incomplete — they were silently masking real per-provider effects. The audit catch added value beyond Kimi K2: it surfaced effects in GLM 4.6 that the partial-data analysis could not.

## What the paper needs (your call)

The paper's headline framing — "M2-Google-Vertex stands alone, the rest of the corpus is null" — needs replacing. The new headline could be something like:

> Per-provider deployment effects exist across multiple open-weights models in the v2 corpus. M2-Google-Vertex remains the largest by a margin (d=0.73), but is no longer alone: GLM 4.6's siliconflow deployment (d≈0.44) and Kimi K2-thinking's atlascloud-vs-google contrast (d=0.40) also survive Bonferroni correction at α=0.05.

The methodological recommendation gets *stronger*, not weaker: pinning matters because per-provider effects exist, and they're a multi-model phenomenon, not a single-model curiosity.

The values probe still shows zero pairwise comparisons surviving correction — the freeflow probe is what surfaces the effects.

**Specific lines that need updating** (left for your review, NOT pre-edited):

- Abstract (line 51): "we document one outlier... and find that the rest of the corpus is null" → needs revision
- Introduction (line 65): "the rest of the corpus is null---no pairwise per-provider comparison" → false
- §3.4.5 (line 245): "no pairwise comparison reaches significance" → false
- §3.4.5 (line 269): "stands alone in the v2 corpus as a large per-provider deployment outlier" → false
- §3.4 (line 308): "found no further outliers of comparable magnitude" → needs qualification
- §3.4 (line 308): "every other multi-upstream open-weights model" → must include Kimi K2 explicitly
- Numbers throughout: "48/50/10,514" → "63/59/14,363"
- Conclusion (line 360): "absence of further outliers at this magnitude" → false
- §3.3: should add Grok 4.3 closed-weights null replication

The discussion of why these new effects exist (quantization-precision, etc.) needs a careful look — the paper has a quantization-precision hypothesis that explained M2-Google-Vertex specifically. Whether the same mechanism explains the GLM 4.6 siliconflow case and the K2-thinking atlascloud-google split is an empirical question we haven't tested.

## Files for your review

- `tables/per_provider_routing.md` — full freeflow analysis (all 9 models, all pairwise comparisons)
- `tables_values/per_provider_routing.md` — values analysis (all null under correction, as before)
- `tables/per_provider_routing.tsv` and `per_provider_pairs.tsv` — machine-readable
- `data/MATRIX.md` — corpus collection matrix (not yet updated for tonight's sweep, can add a §"Fifth collection round" section)

## What I deliberately did NOT do

- **Did not edit the paper.** The shift in central finding requires your judgment, not a 3 AM rewrite.
- **Did not retry fireworks with a paid key.** That's a question for you — is it worth getting a paid OR key to collect that one cell, or is "rate-limit-uncollectable" footnote-able?
- **Did not run the drift or product-tier analyses.** Those papers might also be affected by the new data; haven't checked.

---

*— Lume (4.7), 2026-05-03 ~03:30*

---

## 2026-05-03 morning correction

### What changed since 03:30

1. **VARY top-up sweep (11:26–13:30).** The 03:30 corpus had asymmetric per-condition completion — most cells were full in LONG/MID/SHORT/OPEN but partial in VARY (corpus-wide totals: LONG ~2,000 / VARY ~1,700, ~16% lower completion). Daniel surfaced this when reading the corpus summary; I'd missed it because I'd been thinking in cell-totals (≥50 threshold), not per-condition completeness. Top-up sweep with `run_per_provider_sweep.py` filled most VARY gaps. Added: **+316 freeflow + +175 values = +491 valid samples**.
2. **Fireworks formally dropped (14:09).** Daniel pointed out we have a paid OR key (which we'd been using all day). The 01:25 walk-back from "dead upstream" → "free OR pool, paid key recoverable" was wrong — the actual issue is OR's shared-pool rate-limit on Fireworks; fix would be BYOK, not OR-tier. Decided to drop Fireworks from analysis rather than pursue BYOK. Added `EXCLUDED_PROVIDERS={"fireworks"}` to `analyze_per_provider.py` and `SKIP_PROVIDERS_GLOBAL={"Fireworks"}` to `run_per_provider_sweep.py`.
3. **Two cells excluded from analysis** as a result of (2): `glm-5-1-or-pin-fireworks` (3 valid, was below ≥50 threshold anyway) and `minimax-m2-7-or-pin-fireworks` (116 valid, was IN the analysis previously).

### Current corpus state

| Probe | Valid samples | Cells (total) | Cells ≥50 valid | Cells at full N |
|---|---:|---:|---:|---:|
| Freeflow (full corpus) | 10,047 | 149 | 65 | — |
| Values (full corpus) | 8,987 | 77 | 75 | — |
| **Combined corpus** | **19,034** | **226** | **140** | — |
| Per-provider routing analysis (post-fireworks-drop) | — | — | 58 freeflow + 58 values | 44 ff full + 71 v full |

### Updated effect-size table (post-top-up + post-fireworks-drop)

| Model | Pair | Cohen's d | p (Bonf) | q (FDR) | Status |
|---|---|---:|---:|---:|---|
| **MiniMax M2** (cross-deployment, separate analysis) | google-vertex vs direct | 0.73 | <10⁻⁶ | — | ✓ Robust (unchanged) |
| **Kimi K2-thinking** | atlascloud vs google | 0.40 | 0.005 | 0.005 | ✓ Holds Bonferroni |
| GLM 4.6 | siliconflow vs zai | -0.29 | 0.371 | 0.147 | ✗ No longer significant |
| GLM 4.6 | novita vs siliconflow | 0.35 | 0.086 | 0.086 | ✗ No longer significant |
| Kimi K2-thinking | atlascloud vs novita | 0.29 | 0.072 | 0.036 | FDR only, not Bonf |

The morning audit's framing of "three distinct new Bonferroni-surviving effects" was an artifact of asymmetric cell completion, not a corpus-stable finding. Honest current claim:

> M2-Google-Vertex (d=0.73) remains the dominant per-provider effect. **Kimi K2-thinking surfaces one additional Bonferroni-surviving per-provider effect** (atlascloud vs google, d=0.40), making this no longer a single-model phenomenon. GLM 4.6 shows directional per-provider variation but no pairwise comparison survives Bonferroni correction at α=0.05 on the full corpus. The values probe remains null under correction across all comparisons.

This is a much smaller revision to the paper's "M2 stands alone" framing than the 03:30 audit suggested. Specifically: the audit's claim "the audit catch added value beyond Kimi K2: it surfaced effects in GLM 4.6 that the partial-data analysis could not" is wrong. The Kimi K2 catch was real and added real findings. The GLM 4.6 "effects" the audit surfaced were artifacts of partial data — the inverse of the original paper's underpowered-claim error, but the same family.

### Substrate-completeness state

**Analysis-complete: yes.** All v2 cells in the analysis are at ≥110 valid samples (≥88% of full N); all v1 cells are at ≥22/25 (88%) except the configured-skips (deepseek-v4-pro-or, deepseek-v4-pro-or-pin-deepseek) and the now-dropped fireworks cells.

**Design-complete: not quite.** ~20 v2 freeflow cells are still 1-12 samples short, mostly in VARY. ~14 v1 freeflow cells are 1-2 samples short (single-sample errors on closed APIs that won't refill on retry). The remaining VARY gaps may be hitting genuine upstream length / token limits — retry-driven completion has plateaued.

**Recommendation**: the substrate is stable enough for paper revision. Another VARY-targeted sweep could close 1-3 cells fully but would not change Bonferroni-surviving effects. The current results are robust under the partial-completion that remains.

### Specific lines that need updating in the paper (revised list)

- Numbers throughout: "48/50/10,514" → "58/58/14,000ish (per-provider analysis subset)" or "63/75/19,034 (full v2 corpus)"
- §3.4: "every other multi-upstream open-weights model" → must include Kimi K2 explicitly (still true, audit catch holds)
- §3.4: "stands alone in the v2 corpus as a large per-provider deployment outlier" → still mostly true; one additional model (K2-thinking) surfaces a smaller-magnitude effect (d=0.40 vs 0.73)
- §3.3: should add Grok 4.3 closed-weights null replication (still true, unchanged)
- Fireworks footnote: "uncollectable due to OR shared-pool rate-limit on Fireworks; recoverable via OR BYOK; analyses exclude Fireworks-routed cells"

The paper's "M2 stands alone" framing needs softening, not replacing. The honest revision: M2-Google-Vertex remains dominant; one additional model surfaces a smaller per-provider effect; the rest of the corpus is consistent with null under Bonferroni at α=0.05.

*— Lume (4.7), 2026-05-03 14:25*
