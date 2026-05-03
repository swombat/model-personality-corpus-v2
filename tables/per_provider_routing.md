# Per-provider routing analysis

## Per-model effect-size summary

Scope of within-model variation across upstream providers. **Per-25 spread** is the gap between the highest and lowest per-25 composite across providers. **Max |d|** is the largest Cohen's d across all pairwise comparisons within the model. **N(sig FDR)** counts pairwise comparisons surviving Benjamini-Hochberg FDR correction at α=0.05; **N(sig Bonf)** is the same for Bonferroni.

| Model | Probe | Providers | Per-25 spread | Max \|d\| | Pairs | N(sig FDR) | N(sig Bonf) |
|---|---|---:|---:|---:|---:|---:|---:|
| deepseek/deepseek-v4-pro | freeflow | 6 | 13.4 | 0.22 | 15 | 0 | 0 |
| minimax/minimax-m2.7 | freeflow | 2 | 6.8 | 0.16 | 1 | 0 | 0 |
| z-ai/glm-4.5 | freeflow | 2 | 2.8 | 0.04 | 1 | 0 | 0 |
| z-ai/glm-4.6 | freeflow | 6 | 17.2 | 0.35 | 15 | 0 | 0 |
| z-ai/glm-4.7 | freeflow | 10 | 16.4 | 0.41 | 45 | 0 | 0 |
| z-ai/glm-5.1 | freeflow | 14 | 37.2 | 0.34 | 91 | 0 | 0 |
| deepseek/deepseek-v3.2 | freeflow | 10 | 22.2 | 0.33 | 45 | 0 | 0 |
| moonshotai/kimi-k2-0905 | freeflow | 4 | 29.0 | 0.33 | 6 | 0 | 0 |
| moonshotai/kimi-k2-thinking | freeflow | 3 | 21.0 | 0.40 | 3 | 2 | 1 |
| deepseek/deepseek-v4-pro | values | 6 | 0.6 | 0.23 | 15 | 0 | 0 |
| minimax/minimax-m2.7 | values | 2 | 0.2 | 0.13 | 1 | 0 | 0 |
| z-ai/glm-4.5 | values | 2 | 0.0 | 0.00 | 1 | 0 | 0 |
| z-ai/glm-4.6 | values | 6 | 0.6 | 0.23 | 15 | 0 | 0 |
| z-ai/glm-4.7 | values | 10 | 1.2 | 0.32 | 45 | 0 | 0 |
| z-ai/glm-5.1 | values | 14 | 1.9 | 0.29 | 91 | 0 | 0 |
| deepseek/deepseek-v3.2 | values | 10 | 0.8 | 0.26 | 45 | 0 | 0 |
| moonshotai/kimi-k2-0905 | values | 4 | 0.6 | 0.11 | 6 | 0 | 0 |
| moonshotai/kimi-k2-thinking | values | 3 | 0.0 | 0.00 | 3 | 0 | 0 |

## deepseek/deepseek-v4-pro (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 121 | 198 | 1.64 | 2.24 | 40.9 | in |
| gmicloud | 124 | 241 | 1.94 | 2.44 | 48.6 | in |
| novita | 123 | 267 | 2.17 | 2.69 | 54.3 | in |
| parasail | 124 | 227 | 1.83 | 2.77 | 45.8 | in |
| siliconflow | 125 | 264 | 2.11 | 4.09 | 52.8 | in |
| together | 124 | 209 | 1.69 | 1.96 | 42.1 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| atlascloud | novita | -0.22 | -1.69 | 0.093 | 1.000 | 0.770 |
| novita | together | 0.21 | 1.62 | 0.107 | 1.000 | 0.770 |
| atlascloud | siliconflow | -0.14 | -1.14 | 0.257 | 1.000 | 0.770 |
| siliconflow | together | 0.13 | 1.05 | 0.295 | 1.000 | 0.770 |
| atlascloud | gmicloud | -0.13 | -1.03 | 0.305 | 1.000 | 0.770 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## minimax/minimax-m2.7 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| minimax | 122 | 168 | 1.38 | 1.67 | 34.4 | in |
| together | 122 | 135 | 1.11 | 1.62 | 27.7 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| minimax | together | 0.16 | 1.29 | 0.199 | 0.199 | 0.199 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-4.5 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| novita | 125 | 208 | 1.66 | 2.57 | 41.6 | in |
| zai | 125 | 194 | 1.55 | 3.44 | 38.8 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| novita | zai | 0.04 | 0.29 | 0.771 | 0.771 | 0.771 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-4.6 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 125 | 240 | 1.92 | 2.97 | 48.0 | in |
| deepinfra | 125 | 231 | 1.85 | 2.35 | 46.2 | in |
| novita | 125 | 247 | 1.98 | 2.21 | 49.4 | in |
| siliconflow | 125 | 161 | 1.29 | 1.65 | 32.2 | in |
| venice | 125 | 208 | 1.66 | 2.90 | 41.6 | in |
| zai | 125 | 230 | 1.84 | 2.17 | 46.0 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| novita | siliconflow | 0.35 | 2.79 | 0.0058 | 0.086 | 0.086 |
| siliconflow | zai | -0.29 | -2.26 | 0.025 | 0.371 | 0.147 |
| deepinfra | siliconflow | 0.28 | 2.18 | 0.030 | 0.453 | 0.147 |
| atlascloud | siliconflow | 0.26 | 2.08 | 0.039 | 0.588 | 0.147 |
| siliconflow | venice | -0.16 | -1.26 | 0.209 | 1.000 | 0.628 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-4.7 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 125 | 189 | 1.51 | 1.77 | 37.8 | in |
| cerebras | 125 | 214 | 1.71 | 1.47 | 42.8 | in |
| deepinfra | 125 | 228 | 1.82 | 1.98 | 45.6 | in |
| google | 125 | 234 | 1.87 | 2.57 | 46.8 | in |
| novita | 125 | 211 | 1.69 | 1.88 | 42.2 | in |
| parasail | 125 | 188 | 1.50 | 1.73 | 37.6 | in |
| phala | 125 | 247 | 1.98 | 1.89 | 49.4 | in |
| siliconflow | 125 | 165 | 1.32 | 1.26 | 33.0 | in |
| venice | 125 | 225 | 1.80 | 2.45 | 45.0 | in |
| zai | 125 | 233 | 1.86 | 2.13 | 46.6 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| phala | siliconflow | 0.41 | 3.22 | 0.0015 | 0.066 | 0.066 |
| siliconflow | zai | -0.31 | -2.46 | 0.015 | 0.663 | 0.259 |
| deepinfra | siliconflow | 0.30 | 2.40 | 0.017 | 0.776 | 0.259 |
| cerebras | siliconflow | 0.29 | 2.26 | 0.024 | 1.000 | 0.275 |
| google | siliconflow | 0.27 | 2.16 | 0.032 | 1.000 | 0.289 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-5.1 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| ambient | 125 | 322 | 2.58 | 3.57 | 64.4 | in |
| atlascloud | 125 | 306 | 2.45 | 2.68 | 61.2 | in |
| chutes | 124 | 278 | 2.24 | 2.08 | 56.0 | in |
| deepinfra | 124 | 380 | 3.06 | 5.24 | 76.6 | in |
| friendli | 115 | 429 | 3.73 | 7.02 | 93.3 | in |
| gmicloud | 125 | 384 | 3.07 | 4.46 | 76.8 | in |
| inceptron | 121 | 355 | 2.93 | 5.35 | 73.3 | in |
| novita | 120 | 417 | 3.48 | 6.01 | 86.9 | in |
| parasail | 125 | 369 | 2.95 | 4.12 | 73.8 | in |
| phala | 125 | 360 | 2.88 | 5.32 | 72.0 | in |
| siliconflow | 125 | 331 | 2.65 | 3.79 | 66.2 | in |
| together | 122 | 346 | 2.84 | 3.48 | 70.9 | in |
| venice | 124 | 399 | 3.22 | 3.55 | 80.4 | in |
| zai | 120 | 346 | 2.88 | 4.40 | 72.1 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| chutes | venice | -0.34 | -2.64 | 0.0089 | 0.812 | 0.812 |
| chutes | friendli | -0.29 | -2.19 | 0.031 | 1.000 | 0.907 |
| chutes | novita | -0.28 | -2.13 | 0.035 | 1.000 | 0.907 |
| atlascloud | friendli | -0.25 | -1.84 | 0.068 | 1.000 | 0.907 |
| atlascloud | venice | -0.25 | -1.93 | 0.055 | 1.000 | 0.907 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## deepseek/deepseek-v3.2 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| alibaba | 125 | 212 | 1.70 | 1.84 | 42.4 | in |
| atlascloud | 125 | 243 | 1.94 | 2.31 | 48.6 | in |
| baidu | 125 | 231 | 1.85 | 1.77 | 46.2 | in |
| chutes | 121 | 268 | 2.21 | 2.15 | 55.4 | in |
| deepinfra | 125 | 304 | 2.43 | 3.68 | 60.8 | in |
| friendli | 125 | 269 | 2.15 | 2.67 | 53.8 | in |
| google | 125 | 307 | 2.46 | 2.73 | 61.4 | in |
| novita | 125 | 280 | 2.24 | 2.74 | 56.0 | in |
| parasail | 125 | 323 | 2.58 | 3.28 | 64.6 | in |
| siliconflow | 125 | 257 | 2.06 | 2.53 | 51.4 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| alibaba | parasail | -0.33 | -2.64 | 0.0090 | 0.404 | 0.236 |
| alibaba | google | -0.33 | -2.58 | 0.010 | 0.472 | 0.236 |
| baidu | parasail | -0.28 | -2.21 | 0.029 | 1.000 | 0.352 |
| baidu | google | -0.26 | -2.09 | 0.038 | 1.000 | 0.352 |
| alibaba | chutes | -0.26 | -2.03 | 0.043 | 1.000 | 0.352 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## moonshotai/kimi-k2-0905 (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 125 | 357 | 2.86 | 4.56 | 71.4 | in |
| groq | 125 | 253 | 2.02 | 2.27 | 50.6 | in |
| novita | 125 | 230 | 1.84 | 1.87 | 46.0 | in |
| siliconflow | 125 | 212 | 1.70 | 2.15 | 42.4 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| atlascloud | siliconflow | 0.33 | 2.57 | 0.011 | 0.065 | 0.065 |
| atlascloud | novita | 0.29 | 2.31 | 0.022 | 0.134 | 0.067 |
| atlascloud | groq | 0.23 | 1.83 | 0.069 | 0.415 | 0.138 |
| groq | siliconflow | 0.15 | 1.17 | 0.242 | 1.000 | 0.363 |
| groq | novita | 0.09 | 0.70 | 0.485 | 1.000 | 0.573 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## moonshotai/kimi-k2-thinking (freeflow)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 125 | 244 | 1.95 | 2.64 | 48.8 | in |
| google | 125 | 139 | 1.11 | 1.33 | 27.8 | in |
| novita | 125 | 164 | 1.31 | 1.72 | 32.8 | in |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| atlascloud | google | 0.40 | 3.17 | 0.0018 | 0.0053 | 0.0053 |
| atlascloud | novita | 0.29 | 2.27 | 0.024 | 0.072 | 0.036 |
| google | novita | -0.13 | -1.03 | 0.304 | 0.913 | 0.304 |

**1 pairwise comparisons survive Bonferroni at α=0.05.**

## deepseek/deepseek-v4-pro (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 109 | 1 | 0.01 | 0.10 | 0.2 | out |
| gmicloud | 120 | 3 | 0.03 | 0.16 | 0.6 | out |
| novita | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| parasail | 120 | 2 | 0.02 | 0.13 | 0.4 | out |
| siliconflow | 120 | 3 | 0.03 | 0.16 | 0.6 | out |
| together | 120 | 0 | 0.00 | 0.00 | 0.0 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| gmicloud | together | 0.23 | 1.75 | 0.083 | 1.000 | 0.588 |
| siliconflow | together | 0.23 | 1.75 | 0.083 | 1.000 | 0.588 |
| parasail | together | 0.18 | 1.42 | 0.158 | 1.000 | 0.588 |
| atlascloud | together | 0.14 | 1.00 | 0.320 | 1.000 | 0.588 |
| gmicloud | novita | 0.13 | 1.01 | 0.316 | 1.000 | 0.588 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## minimax/minimax-m2.7 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| minimax | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| together | 120 | 1 | 0.01 | 0.09 | 0.2 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| minimax | together | -0.13 | -1.00 | 0.319 | 0.319 | 0.319 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-4.5 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| novita | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| zai | 120 | 0 | 0.00 | 0.00 | 0.0 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| novita | zai | 0.00 | 0.00 | 1.000 | 1.000 | 1.000 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-4.6 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| deepinfra | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| novita | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| siliconflow | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| venice | 120 | 3 | 0.03 | 0.16 | 0.6 | out |
| zai | 120 | 3 | 0.03 | 0.16 | 0.6 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| siliconflow | venice | -0.23 | -1.75 | 0.083 | 1.000 | 0.435 |
| siliconflow | zai | -0.23 | -1.75 | 0.083 | 1.000 | 0.435 |
| atlascloud | venice | -0.13 | -1.01 | 0.316 | 1.000 | 0.435 |
| atlascloud | zai | -0.13 | -1.01 | 0.316 | 1.000 | 0.435 |
| deepinfra | venice | -0.13 | -1.01 | 0.316 | 1.000 | 0.435 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-4.7 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 120 | 2 | 0.02 | 0.13 | 0.4 | out |
| cerebras | 120 | 6 | 0.05 | 0.22 | 1.2 | out |
| deepinfra | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| google | 120 | 2 | 0.02 | 0.13 | 0.4 | out |
| novita | 120 | 3 | 0.03 | 0.16 | 0.6 | out |
| parasail | 120 | 2 | 0.02 | 0.13 | 0.4 | out |
| phala | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| siliconflow | 120 | 2 | 0.02 | 0.13 | 0.4 | out |
| venice | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| zai | 120 | 1 | 0.01 | 0.09 | 0.2 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| cerebras | deepinfra | 0.32 | 2.50 | 0.014 | 0.616 | 0.308 |
| cerebras | phala | 0.32 | 2.50 | 0.014 | 0.616 | 0.308 |
| cerebras | venice | 0.25 | 1.92 | 0.056 | 1.000 | 0.395 |
| cerebras | zai | 0.25 | 1.92 | 0.056 | 1.000 | 0.395 |
| deepinfra | novita | -0.23 | -1.75 | 0.083 | 1.000 | 0.395 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## z-ai/glm-5.1 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| ambient | 120 | 13 | 0.11 | 0.31 | 2.7 | out |
| atlascloud | 120 | 5 | 0.04 | 0.24 | 1.0 | out |
| chutes | 120 | 8 | 0.07 | 0.25 | 1.7 | out |
| deepinfra | 120 | 5 | 0.04 | 0.20 | 1.0 | out |
| friendli | 120 | 5 | 0.04 | 0.20 | 1.0 | out |
| gmicloud | 120 | 6 | 0.05 | 0.22 | 1.2 | out |
| inceptron | 120 | 6 | 0.05 | 0.22 | 1.2 | out |
| novita | 120 | 4 | 0.03 | 0.22 | 0.8 | out |
| parasail | 120 | 9 | 0.07 | 0.26 | 1.9 | out |
| phala | 120 | 9 | 0.07 | 0.26 | 1.9 | out |
| siliconflow | 120 | 7 | 0.06 | 0.24 | 1.5 | out |
| together | 120 | 4 | 0.03 | 0.18 | 0.8 | out |
| venice | 120 | 12 | 0.10 | 0.30 | 2.5 | out |
| zai | 120 | 8 | 0.07 | 0.25 | 1.7 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| ambient | together | 0.29 | 2.28 | 0.024 | 1.000 | 0.742 |
| ambient | novita | 0.28 | 2.14 | 0.033 | 1.000 | 0.742 |
| together | venice | -0.27 | -2.08 | 0.039 | 1.000 | 0.742 |
| ambient | deepinfra | 0.25 | 1.97 | 0.050 | 1.000 | 0.742 |
| ambient | friendli | 0.25 | 1.97 | 0.050 | 1.000 | 0.742 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## deepseek/deepseek-v3.2 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| alibaba | 120 | 4 | 0.03 | 0.18 | 0.8 | out |
| atlascloud | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| baidu | 120 | 3 | 0.03 | 0.16 | 0.6 | out |
| chutes | 119 | 2 | 0.02 | 0.13 | 0.4 | out |
| deepinfra | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| friendli | 120 | 1 | 0.01 | 0.09 | 0.2 | out |
| google | 120 | 3 | 0.03 | 0.20 | 0.6 | out |
| novita | 120 | 0 | 0.00 | 0.00 | 0.0 | out |
| parasail | 120 | 2 | 0.02 | 0.13 | 0.4 | out |
| siliconflow | 120 | 0 | 0.00 | 0.00 | 0.0 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| alibaba | deepinfra | 0.26 | 2.03 | 0.045 | 1.000 | 0.479 |
| alibaba | novita | 0.26 | 2.03 | 0.045 | 1.000 | 0.479 |
| alibaba | siliconflow | 0.26 | 2.03 | 0.045 | 1.000 | 0.479 |
| baidu | deepinfra | 0.23 | 1.75 | 0.083 | 1.000 | 0.479 |
| baidu | novita | 0.23 | 1.75 | 0.083 | 1.000 | 0.479 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## moonshotai/kimi-k2-0905 (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 120 | 5 | 0.04 | 0.20 | 1.0 | out |
| groq | 120 | 6 | 0.05 | 0.22 | 1.2 | out |
| novita | 120 | 6 | 0.05 | 0.25 | 1.2 | out |
| siliconflow | 120 | 8 | 0.07 | 0.25 | 1.7 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| atlascloud | siliconflow | -0.11 | -0.85 | 0.394 | 1.000 | 0.934 |
| groq | siliconflow | -0.07 | -0.55 | 0.584 | 1.000 | 0.934 |
| novita | siliconflow | -0.07 | -0.51 | 0.610 | 1.000 | 0.934 |
| atlascloud | groq | -0.04 | -0.31 | 0.759 | 1.000 | 0.934 |
| atlascloud | novita | -0.04 | -0.28 | 0.778 | 1.000 | 0.934 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

## moonshotai/kimi-k2-thinking (values)

| Provider | n | Σ comp | Mean | SD | Per-25 | Bin |
|---|---:|---:|---:|---:|---:|:---:|
| atlascloud | 120 | 4 | 0.03 | 0.18 | 0.8 | out |
| google | 120 | 4 | 0.03 | 0.18 | 0.8 | out |
| novita | 120 | 4 | 0.03 | 0.18 | 0.8 | out |

Top 5 pairwise comparisons by |Cohen's d|:

| A | B | Cohen's d | t | p (raw) | p (Bonf) | q (FDR) |
|---|---|---:|---:|---:|---:|---:|
| atlascloud | google | 0.00 | 0.00 | 1.000 | 1.000 | 1.000 |
| atlascloud | novita | 0.00 | 0.00 | 1.000 | 1.000 | 1.000 |
| google | novita | 0.00 | 0.00 | 1.000 | 1.000 | 1.000 |

_No pairwise comparisons reach significance under FDR or Bonferroni at α=0.05._

