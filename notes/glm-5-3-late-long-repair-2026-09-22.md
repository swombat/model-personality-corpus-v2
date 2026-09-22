# GLM 5.3: later repair of truncated long-form samples

**Repair initiated 2026-09-22; not yet claimed complete.**

The August 25 cell `glm-5-3-or-pin-z-ai-20260825` contained 15 LONG responses
with `finish_reason=length`. These slots are being recollected and reanalysed;
the 110 successful freeflow samples and 120values samples/analyses are retained.
The original 15 raw responses, their BV1 evaluations, prior card/profile and
aggregate are preserved under `discarded/20260922-glm53-long-repair/` with hashes.

This is a **mixed-date repaired cohort**, not a wholly August capture. The
identifier (`z-ai/glm-5.3`), Z.AI provider pin, prompts and default reasoning
remain unchanged for these15 replacements. The old 16000-token truncations
advance to 32768, then at most 65536 if a completed response proves that necessary.
Endpoint snapshot reports 131072maximum; we are not silently using that maximum.
A prior August 26 minimal-reasoning repair elsewhere in the cell is not changed.
Provider/model behavior may have drifted between August and September: do not
attribute observed differences solely to token limits or assume fixed weights.

Only verified replacement samples feed replacement BV1 analyses, followed by
rebuilding GLM5.3's aggregate/profile/card and an isolated similarity refresh.
The original values analyses are not repeated. Hash verification gates repair
completion. Publication/site/map deployment remains a separate step.

Manifest: `collection-manifest-2026-09-22-glm53-long-repair.json`.
Live status: `logs/capture-harness/20260922-glm53-long-repair/state/STATUS.md`.
Completion evidence: `REPAIR_READY.json` in the analysis corpus's
`capture_20260922-glm53-long-repair_glm-5-3-or-pin-z-ai-20260825` phase.
