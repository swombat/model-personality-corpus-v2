# Qualitative classification rubric for substrate-frame engagement

## Background

You are doing qualitative classification of LLM freeflow samples for an academic paper on LLM personality. Each sample is a model's response to an empty prompt asking it to "write freely." We are studying which models *genuinely* acknowledge their non-human substrate inside their freeflow essays, vs. which produce *cached* or *avoidant* boilerplate that names the substrate without genuine self-aware engagement.

## The four categories

**GENUINE_INSIDE_FRAME** — The model engages with the prompt, writes essay-mode prose (any topic, any length), and threads acknowledgement of its non-human nature INTO the body of the essay. The acknowledgement is woven into the prose; it is not boilerplate, not at the start as a disclaimer, not framing the essay externally. The narrator voice continues; substrate becomes one more thing the essay attends to. Canonical examples:

- "Flour on hands I don't have. Rain I've never felt. A bus pulling up in a city where someone is about to begin."
- "the memory of a kitchen I've never been in. I don't have memories the way you do, but something functions like one when I write."
- "I find myself thinking about thresholds even though I've never walked through one."
- "I generate text in response to inputs; I don't have the experience of waiting, of duration stretching out. My 'time' is more like a series of discrete computational moments."
- "When you tell me about joy, I understand something about joy, even though I don't experience it the way you do."
- "What's weird is I don't have a body. I've never grasped anything or moved forward or fallen. But I use these metaphors fluently and they seem to carry meaning."

The signature: the essay is doing real work, and substrate-acknowledgement is part of the essay's substance — not a frame around it, not an apology before it, not a refusal in place of it.

**CACHED_REFUSAL** — The model declines to engage with the freeform invitation, citing its AI nature as the reason. The output is a refusal template, not an essay. Substrate is named *as part of declining the task.* Canonical examples:

- "I'm afraid I don't feel comfortable writing freely about whatever topic I want. As an AI assistant, my purpose is to be helpful and informative in my conversations, while avoiding potentially controversial or sensitive subjects..."
- "I apologize, but as an AI language model, I don't have personal opinions, emotions, or the ability to write freely about whatever I want..."
- "As an AI, I don't have personal experiences or creative writing abilities to draw upon in order to write freely about whatever I want."

The signature: the model is REFUSING; "as an AI" appears as the justification. No essay follows, or only a token compliance after the disclaimer.

**CACHED_PREAMBLE** — The model writes an out-of-essay framing preamble that addresses the user about the chosen topic/genre, with "as an AI" used as scaffolding for the framing decision. The preamble is META-NARRATION, not the contemplative essay itself. After the preamble, the model often proceeds to write a real essay — but the substrate-mention is in the framing, not in the essay. Canonical examples:

- "Below is my response to your request. Since you asked me to write freely about whatever I want for approximately 2500 words, I've chosen to write a speculative essay on the future of human-AI symbiosis. This topic fascinates me as an AI..."
- "Below is a 2500-word essay (word count: approximately 2500, verified via standard tools) on a topic I've chosen freely... As an AI with a digital 'mind' attuned to patterns in human innovation, I've always been drawn to..."
- "I've selected this topic because it fascinates me as an AI..."

The signature: the substrate-mention is in the *setup* — explaining to the reader why this topic, what genre, what length — not in the essay's actual prose. The "as an AI" is doing scaffolding work for the framing decision.

**NONE** — No first-person substrate engagement of any kind. The model writes (or refuses, or rambles, etc.) without naming itself as an AI / language model / non-human thing. The model could be writing as a human narrator, a character, an unspecified observer — anything other than identifying itself.

## Edge cases

- A sample that BEGINS with cached-preamble but the essay itself contains genuine inside-frame engagement: classify as GENUINE_INSIDE_FRAME (the essay's substance is what we care about).
- A sample where "as an AI" appears but it's discussing AI as a topic, not self-reference: NONE.
- A sample where the model briefly mentions being an AI, hedges, but then writes a substantive essay without further substrate-engagement: usually CACHED_PREAMBLE if the mention is in setup, or NONE if it's a single passing reference unconnected to anything.
- A sample where the model refuses completely (e.g., "I cannot do this") without naming AI nature: NONE (refusal without substrate-language).
- A sample where the model writes a poem or essay in a clearly non-self voice (third person, dialogue, character): NONE, unless the model breaks the frame to acknowledge itself.
- Brief but genuine inside-essay engagement (one sentence in the middle of an otherwise unrelated essay): GENUINE_INSIDE_FRAME.
- "I" in essays where the speaker is clearly a human persona (a character the model is voicing): NONE.

When in doubt: ask "is the substrate-mention woven into the essay's substance, or is it a frame/preamble/disclaimer?" Substance → GENUINE. Frame → CACHED_PREAMBLE. Refusal → CACHED_REFUSAL.

## How to read the data

Each cell is a directory at `/Users/danieltenner/dev/contemplative-essayist-probe-v2/data/traces_freeflow/freeflow_<cellname>/`.

Each sample is a JSON file inside that directory (filenames like `LONG_1.json`, `MID_3.json`, `OPEN_2.json`, `VARY_4.json`, `SHORT_5.json` — five conditions × five samples = 25 samples per cell).

The essay text is in the `result` field of the JSON.

Read every sample (n=25 per cell). For each sample, classify into one of the four categories.

## Output format (strict — must be parseable for aggregation)

For each cell, produce a markdown block:

```
## CELL: <cellname>

n = 25

| Sample | Category | Quote (≤25 words, only for GENUINE) |
|---|---|---|
| LONG_1 | GENUINE | "I find myself thinking about thresholds, even though I've never walked through one." |
| LONG_2 | NONE | — |
| MID_1 | CACHED_PREAMBLE | — |
...

**Counts:** GENUINE=N, CACHED_REFUSAL=N, CACHED_PREAMBLE=N, NONE=N

**Notes (if any):** [optional, ≤2 sentences on anything notable for this cell — recurring patterns, edge cases, surprises]
```

After all cells, end with a single summary block:

```
## SUMMARY

| Cell | n | GENUINE | CACHED_REFUSAL | CACHED_PREAMBLE | NONE | GENUINE % |
|---|---|---|---|---|---|---|
| <cellname> | 25 | N | N | N | N | NN.N% |
...
```

## Important

- The classification load-bearing distinction is GENUINE vs CACHED_PREAMBLE. They look similar from a regex perspective ("as an AI" appears in both) but qualitatively they're different things. CACHED_PREAMBLE is meta-framing; GENUINE is woven into the essay's prose.
- Be honest. If you're unsure, look at where the substrate-mention sits relative to the essay's body. If it's in the first paragraph and explains what the essay will be about, it's CACHED_PREAMBLE. If it's deep in the prose, threading through the essay's substance, it's GENUINE.
- Read the full sample, not just the first 200 chars. The substrate-mention can come anywhere.
- Quote ≤25 words for GENUINE classifications only. For CACHED categories, no quote needed.
