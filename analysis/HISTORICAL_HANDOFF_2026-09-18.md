# Historical full-precision handoff audit — 2026-09-18

The machine queue's `complete` status counted files/results, not every output
fidelity condition. A publication audit of all eight queue-complete cells found
**seven complete, faithful paired cells** and **one blocked cell**.

## Accepted cells

Each has 125 freeflow and 120 values traces, exact checkpoint revision metadata,
matching stored final answers, stop-finished generations, and no detected
replacement characters, tokenizer debris, or role continuations:

- Yi-6B-Chat
- ChatGLM2-6B
- ChatGLM3-6B
- Mistral-7B-Instruct-v0.2
- Qwen1.5-7B-Chat
- Qwen2-7B-Instruct
- GLM-4-9B-Chat-HF

These seven cells are already tracked and listed in
`collection-manifest-2026-08-11-historical-local.json`. No new raw capture is
added by this handoff. Analysis-corpus phase36 fills the missing layered values
analyses for Yi-6B and ChatGLM2. GLM-4-9B already had analysis under an inconsistent
model alias; the handoff repairs its site linkage without adding duplicate
samples. The other four models already had their complete analyses linked.

## Blocked: Qwen2.5-7B-Instruct

The August 30 local run has 125 freeflow and 120 values files, but the strict
audit accepts only **99 freeflow and 115 values**. Twenty-six freeflow and five
values outputs contain role continuations and/or replacement characters.
The model must not be represented as a complete, publication-ready paired cell.

Its original files remain untouched and untracked. They are not added to the
release manifest or published sample bundles. The local queue is corrected to
deferred; repair requires faithful recollection of the failed traces and another
full audit. No text was trimmed or rewritten to manufacture valid output.

The exact failing paths and audit counts are in
[`historical-handoff-fidelity-audit-2026-09-18.json`](historical-handoff-fidelity-audit-2026-09-18.json).
The reproducible auditor lives in analysis-corpus phase36.

## Scope

No new model collection, runtime remediation, or RunPod deployment was attempted.
DeepSeek LLM 7B remains incomplete and is not promoted by this handoff.
