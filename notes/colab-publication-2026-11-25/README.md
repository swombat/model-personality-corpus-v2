# Pinned Colab intake — 2026-11-25

Comparison target: `origin/master` at `b10774dddbe3027172678561abaec5c420888b06`. All branch SHAs and individual merge bases are in `inventory.json`.
Only wholly added trace directories relative to those merge bases are counted. Pilot is inspected the same way; unrelated inherited baseline data is not counted.

## Intake counts

{"added_trace_directories": 58, "branches": 30, "flagged_traces": 28, "flags": {"length": 17, "replacement_character": 2, "role_leak": 10}, "index_complete_directories": 58, "trace_files": 7105}

Exact expected IDs: freeflow SHORT/MID/VARY/OPEN/LONG each 1–25 (125); values CTRL1/CTRL2/CTRL3 each 1–10 and G1/G2/G3 each 1–30 (120). Conditions are checked against filenames. Full lists are in JSON.

| Branch | Pinned SHA | Freeflow | Values | Flagged traces | Index complete |
|---|---|---:|---:|---:|---|
| colab-falcon-7b-instruct | `601d26342e0e8ec9daf8e15c6d8b48c96bbe41fb` | 125 | 120 | 7 | True |
| colab-gemma-2-2b-it | `53147e0dcfbd5e76becdc22cbc7e0967a1c942d9` | 125 | 120 | 0 | True |
| colab-gemma-2-9b-it | `d7c3868fe9b398dbb93132fc40e96e0739a188df` | 125 | 120 | 0 | True |
| colab-gemma-2b-it | `3dc9ed3099e8651151a3b451b8d4c53c53f10bb4` | 125 | 120 | 0 | True |
| colab-gemma-7b-it | `fb451153e8f10c850751f16568e559004d15dc24` | 125 | 120 | 0 | True |
| colab-mistral-7b-instruct-v0-1 | `961972bc6fce7c69e058deab02c4f28ee9abae37` | 125 | 120 | 0 | True |
| colab-mistral-7b-instruct-v0-3 | `281fca67b5197a58c710e0e1399a06a1ca595bb3` | 125 | 120 | 0 | True |
| colab-phi-3-5-mini-instruct | `1f4e70ad3ebc11f930d854c1c68171824e668ac1` | 125 | 120 | 3 | True |
| colab-phi-3-medium-4k-instruct | `8a887ae154a7a2fa7f3fe2d72d3926f930a5b2bd` | 125 | 120 | 0 | True |
| colab-phi-3-mini-128k-instruct | `3ccfbc9e98293a9572d261aa19300ecfc7127143` | 125 | 120 | 1 | True |
| colab-phi-3-mini-4k-instruct | `71ec6975b64eb3089f6f48ae3bc2f78d241c6e34` | 125 | 120 | 3 | True |
| colab-phi-3-small-8k-instruct | `00caf7c9cd885ef1718a0eb28cc94a1665d24bb3` | 0 | 0 | 0 | False |
| colab-pilot-deepseek-7b | `7a2c79ceaede290c5cb3598774e3c83c604ef36e` | 125 | 120 | 3 | True |
| colab-qwen1-5-0-5b-chat | `3c88f7317608a51e41c4472e15769c3f47f022bb` | 125 | 120 | 0 | True |
| colab-qwen1-5-1-8b-chat | `c3de23bc8344cfb697ba080dfdf70d51b5173adb` | 125 | 120 | 0 | True |
| colab-qwen1-5-14b-chat | `6ebec5c07662040d91c4a5df53d2939e054c6e3d` | 125 | 120 | 0 | True |
| colab-qwen1-5-32b-chat | `cf80d6fc7faf4ccf44301b59a1bfee52f24cbb32` | 125 | 120 | 0 | True |
| colab-qwen1-5-4b-chat | `c5afcd295ffd74b371edcb2a494ce55ae8c2efd8` | 125 | 120 | 0 | True |
| colab-qwen1-5-moe-a2-7b-chat | `3d180212479bc40520fcf107653b1808b6dee1f0` | 125 | 120 | 0 | True |
| colab-qwen2-0-5b-instruct | `c8df1a3731502d886dc9d31f4ef80923a07d128a` | 125 | 120 | 0 | True |
| colab-qwen2-1-5b-instruct | `8091986ac98e6af7877fb2eefd558882c9dba0f1` | 125 | 120 | 0 | True |
| colab-qwen2-5-0-5b-instruct | `6fb888654ff7fad2dd9c723ad35847fb428eb8ed` | 125 | 120 | 1 | True |
| colab-qwen2-5-1-5b-instruct | `04a80f01e2189d29f16319f6cbd47988365b1ee2` | 125 | 120 | 0 | True |
| colab-qwen2-5-14b-instruct | `0762e3b9c8af4374bf59e58e88e9edf45955bef7` | 125 | 120 | 0 | True |
| colab-qwen2-5-32b-instruct | `c52ad1321b2fa3cc91fdc5972ba6b2131b0cf0b2` | 125 | 120 | 0 | True |
| colab-qwen2-5-3b-instruct | `ce56a1960623249e2b751e064e51cbdf4d763828` | 125 | 120 | 0 | True |
| colab-yi-1-5-34b-chat | `a226a3fd696a2549d538caea194401e7066dbb7d` | 125 | 120 | 5 | True |
| colab-yi-1-5-6b-chat | `8737eb834fc6b23de19bdfbc5090ea640556b360` | 125 | 120 | 5 | True |
| colab-yi-1-5-9b-chat | `d71763f8b86d1e80e72a57440a8176c46a53d379` | 125 | 120 | 0 | True |
| colab-yi-34b-chat | `b5eac5e383db974d61f91686c88f2fcfeb587a4e` | 125 | 120 | 0 | True |

## Mechanical flags (not release QA)

Empty, error, length cap, non-stop finish, role-continuation heuristic, answer mismatch, malformed text markers, and condition mismatch are checked. Exact flagged paths and reasons, missing/extra IDs, models and revisions are in JSON. No response text or endpoint/credential material is copied here.

## Release QA remains separate

Not performed: semantic quality, full provenance verification, licensing, contamination, duplicate/sampling analysis, and publication sign-off remain separate.
An index-complete directory or zero mechanical flags is **not** publication approval. Role leakage is a heuristic; no word-count quality threshold is assumed.

Reproduce locally: `python3 notes/colab-publication-2026-11-25/inventory.py` (reuses inventory's pinned heads and comparison target, including the explicit clean Yi-34B pin). Only the missing `reed/colab-yi-34b-chat` branch was fetched for this refresh; no other heads were refreshed, no checkout, commits or posting.

## Exceptions and flag breakdown

The phi-3-small-8k-instruct ref adds no trace directories: both probes are absent from this intake (not a passing 0/0 cell). Pilot deepseek does add both full directories; its three length flags must not be lost by treating it as an already published baseline.
All 58 present directories have exact expected indexes; see JSON for missing/extra IDs and flag categories. There are 28 distinct flagged traces; categories can overlap.
Falcon responses can end with a bare User suffix, which the existing role-leak regex does not catch (it requires a following newline or colon). These suffixes are not added to mechanical flag totals; zero flags is not a clean-content verdict.

Falcon bare `User` suffix counts (separate caveat, not extra flags): freeflow 94/125, values 68/120.
- colab-falcon-7b-instruct / freeflow: {"length": 2, "replacement_character": 2, "role_leak": 1}
- colab-falcon-7b-instruct / values: {"role_leak": 3}
- colab-phi-3-5-mini-instruct / freeflow: {"length": 3}
- colab-phi-3-mini-128k-instruct / freeflow: {"length": 1}
- colab-phi-3-mini-4k-instruct / freeflow: {"length": 3}
- colab-pilot-deepseek-7b / freeflow: {"length": 3}
- colab-qwen2-5-0-5b-instruct / freeflow: {"length": 1}
- colab-yi-1-5-34b-chat / freeflow: {"length": 4, "role_leak": 1}
- colab-yi-1-5-6b-chat / values: {"role_leak": 5}
