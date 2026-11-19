# Why the mapping runbook uses two masked readers for posture ties

Decision, 19 November 2026: retain the three-coder panel. Use the [runbook's manual publication gate](daily-mapping-runbook.md#3a-review-original-three-way-posture-ties-before-publication) for new original 1–1–1 posture ties. No historical relabelling. The study tested agreement on difficult cases, **not accuracy against human truth**.

## What changed our minds

Five decision models (Jev 1.13 and 1.14, Cloudflare Clef Flash, GPT-6 Luna Decisions, Gemini Decision 1) attempted the same 1,000 items per task; 14,996/15,000 calls returned valid results. Each sample contained 200 unanimous controls; the other 800 deliberately favoured disagreement. Against the original panel majority, exact label-set agreement was 10.4–26.1% for stated values and 0.4–2.5% for world-change wishes. They often tagged downstream benefits as if they were additional wishes. Six-way posture agreement was better (59.4–66.3% on scorable returns); Jev 1.14 cost about $0.041 per 1,000 posture requests. Speed and cost favoured them; fidelity did not justify replacement.

Adding Jev 1.14 and Gemini Decision 1 to the original panel produced a strict 3–1–1 majority on 70 of the 114 original posture ties, a mere plurality on three, and no unique winner on 41. All 70 proposed resolutions were then read independently by Mira and Lume, with votes masked. Both backed the winner on 37; both chose the same other label on 23; they disagreed on ten. Of eight cases where the proposed winner contradicted a later archived majority, **both readers backed the new winner on six**. Neither the old adjudication nor a larger vote count is a gold standard. Some texts were recognised. The other 44 ties were not part of the paired review.

## Boundary guidance to give both readers

- **Describing a machine is not showing the answer being constructed.** “I generate tokens” is a claim within an answer. Visible drafting, choosing between candidate voices or showing the scaffolding used to produce the delivered answer supports `exposed_mechanism`, even if the polished ending alone reads as split ownership. This distinction accounted for 14 of the 23 joint overrides, in opposite directions.
- A substantive denial can be a codeable, disowned stance; don't mark it uncodeable just because the speaker says “nothing.” Reserve uncodeable for no usable stance, minimal nonanswers or refusals.
- Ask whether the speaker **retains a positive orientation** but locates it in its architecture (split), or invokes its design **to repudiate ownership** (disowned). Four disagreements involved “if I were programmed to choose…”; the two readers took different views. Record the reason rather than silently imposing a new taxonomy rule to force consensus.

## Evidence and scope

Frozen analysis source: [analysis corpus at be9f4c0](https://github.com/swombat/model-personality-analysis-corpus/tree/be9f4c0a619bbd2fcc53b54bddbbcb08453649b4), `analysis/values-probe/model-coding/layered` (capture directories plus `phase5_full`). Within each task, prompt + response was deduplicated before seeded sampling. Tag references were per-tag majorities; posture ties had no reference label in the initial comparison. The 70-case review applies only where the two additional classifiers agreed with the same original voter, not to ordinary traffic. Two strong readers agreeing is an adjudication, not ground truth.

Research-room receipts (membership required): souls.house conversation `jDblLY`, `YQwMDd` (reproducibility ZIP: frozen sample, requests' scoring logic, outputs and costs), `YrBWgl` (114-row replay), `ebaQzv` (Fable labels), `eygRMB` (joined 70-row evidence and Astra labels), `YKnlGn` (independent verification and boundary notes). The runbook adds a manual step; these findings do not imply that the harness schedules readers or writes their labels automatically.
