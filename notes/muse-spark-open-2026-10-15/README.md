# Muse Spark Open (Meta) — release evidence

- Release date: **2026-10-15**, from Meta's own model release on Hugging Face (`meta-models/Muse-Spark-Open-816B-A42B`):
  the Muse Model License and Usage Policy on the model page read "Release date: October 15, 2026" / "Dated: October 15, 2026".
  Saved as `announcement.html` (model page) and `hf-model-api.json` (HF API record; repo lastModified 2026-10-15T15:46:43Z).
  No about.fb.com post for this model was found at capture time (checked 2026-10-16). The HF repo's createdAt (2026-09-15)
  predates the public release (gated/private staging) and is not used.
- Open-weight, 816B total / 42B active MoE, described by OpenRouter as coding-optimized for agentic workflows.
- OpenRouter id `meta/muse-spark-open`, pinned endpoint "Modal | meta/muse-spark-open-20261015" (provider **Modal**, a
  third-party host; quantization "unknown"), $1.25/M in, $4.25/M out, max completion 262144. Snapshot in `endpoints.json`,
  retrieved 2026-10-16. OpenRouter's created timestamp is not used as release evidence.
- **Not a first-party route.** Meta serves no endpoint for this model on OpenRouter. Daniel approved capturing it through
  Modal on condition that the cell is clearly marked (souls.house wJVbwJ, message JXVpqe, 2026-10-16). Personality data
  here reflects Modal's serving of the open weights (unknown quantization, Modal's default sampling/reasoning), not a
  Meta-hosted endpoint.
- Captured by Lume (souls.house body).

- *Corrected 2026-10-19 (Mira's weekly review):* the endpoint snapshot saved with this capture, `notes/muse-spark-open-2026-10-15/endpoints.json`, lists five OpenRouter hosts (Modal, Together, Nebius fp4, Fireworks, BaseTen fp4), none of them Meta. On the morning of 2026-10-16, when Daniel was asked, OpenRouter showed only Modal; the snapshot's retrieval time isn't recorded, so these notes don't claim Modal was the only route for the whole capture. What holds: there was no Meta endpoint, and every call was pinned to Modal with no fallbacks.
