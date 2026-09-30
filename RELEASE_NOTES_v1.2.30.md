# v1.2.30 — Local evidence preserved; GLM-5.3 LONG repair

2026-09-30. Companion analysis release: v1.4.21.

- Commit 625 previously local-only freeflow trace files across MiMo-V2.5-Pro,
  Qwen3.8-27B medium, Ternary Bonsai2-27B medium, original Bonsai, and local
  DeepSeek-LLM-7B. The first three cells are complete. Original Bonsai has
  111 stop-finished responses plus 14 token-capped LONG attempts (13 empty);
  local DeepSeek has 94 nonempty successful responses plus 31 failed traces.
  Neither incomplete cell is presented as a completed personality analysis.
- Commit the 15 September 22 GLM-5.3 LONG replacements. The companion aggregate,
  card and profile were resynthesised on September 30. Preserve mixed-date,
  mixed-budget provenance and the archived originals.
- Preserve historical collection manifests, repair scripts, fidelity notes and
  133 previously untracked discarded-attempt files.
- Make credential loading fail closed; regression tests use fake credentials.
- Refresh the summary and front matter: 62,767 nonempty samples, 552 probe cells,
  176 model identities. These are nonempty-result counts, not strict raw QA.

No source samples were recollected or semantic disagreements rerolled during
this cleanup. See `notes/cleanup-2026-09-30.md` for recovery details and limits.
