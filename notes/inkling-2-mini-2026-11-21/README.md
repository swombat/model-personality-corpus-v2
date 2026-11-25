# Inkling 2 Mini (Thinking Machines) — release evidence

- Release date 2026-11-20: Thinking Machines' post "Introducing Inkling 2 Mini"
  (https://thinkingmachines.ai/news/inkling-2-mini/, schema.org datePublished
  2026-11-20T00:00:00+00:00, visible "Nov 20, 2026"; dateModified 2026-11-24),
  saved as `announcement.html` (retrieved 2026-11-25). Open weights on Hugging
  Face and on Tinker at launch.
- OpenRouter listing (created 1795227585, ~21 Nov) is not release evidence.
- `endpoints-2026-11-21.json`: first snapshot, PrimeIntellect fp4 only.
  `endpoints.json` = `endpoints-2026-11-25.json`: PrimeIntellect fp4 (three
  price tiers), DeepInfra fp4, Io Net nvfp4. No Thinking Machines route.
- Precision: the post's "NVFP4 and low-bit quantization" section says the model
  was trained with NVFP4 expert layers (final 4 layers MXFP8) and "Inkling 2
  Mini's weights are deployed in the same numeric precision they were trained
  on ... so there is no conversion loss from quantization." So OpenRouter's
  `fp4` label is the native release precision, not a post-hoc quantization.
  We held this from 21 to 25 Nov waiting for a non-fp4 host; that host does not
  exist in the lab's own terms.
- Pinned to DeepInfra (fp4), a THIRD-PARTY host, under Daniel's standing
  delegation of host choice for this family (YZxogj, 2026-11-13, "Pin to
  whatever seems sensible"). DeepInfra over PrimeIntellect: one endpoint rather
  than three price tiers behind one provider name, and a 943,718-token max
  completion. Both answered a pinned smoke test (HTTP 200) on 2026-11-25.
  Siblings Inkling (v1) and Inkling 2 Small ran on Together, which does not
  list this model.
