# Qwen2.5 targeted fidelity repair

The 2026-09-18 historical handoff audit rejected 26 freeflow and five values
traces from the pinned official Qwen2.5-7B-Instruct local BF16 cell. This archive
preserves those originals, rather than deleting them or editing their prose.

`manifest.json` records the target paths, rejection reasons, and pre-repair
SHA256 hashes of all 245 samples. The 214 non-target samples must remain
byte-identical. `originals/` contains exact copies of the rejected files.

Repair uses the same checkpoint revision, official template, sampling settings,
and token budgets. Unlike the older runtime, decoding does not trim incomplete
terminal byte tokens. `attempts/` retains every new response plus generated
token IDs, decoding with special tokens, and fidelity-check results. A maximum
of three attempts per target is permitted; only the first passing draw replaces
its canonical file. Selection is by the pre-existing technical fidelity audit,
not answer meaning or analytical scores. This repair/selection history matters
when interpreting the resulting cell.

Operational state and the final full-cell audit live in
`.local-runtime/runs/qwen25-repair-20260918/`. The existence of this archive is
not evidence of completed collection, analysis, or publication.
