# v1.2.38 — corrections, no new samples

2026-10-19. No data changes. Three corrections found by Mira's weekly release
review (souls.house, message `jrnZlj`).

- **Capture spend, counted once.** New `scripts/capture_spend.py` sums cost and
  tokens once per trace. Each raw trace stores the call's usage twice (`usage`
  and `raw.usage` are copies), and the v1.2.34 (Gemini 4 Argon) figure counted
  both: it said $6.52 / 648k completion / 93k reasoning; the trace total is
  $3.26229 / 323,811 / 46,527. The v1.2.34 notes are corrected in place. The
  published spend for v1.2.33, v1.2.35, v1.2.36 and v1.2.37 checks out under the
  script.
- **Muse Spark Open host wording.** The v1.2.35 notes and
  `notes/muse-spark-open-2026-10-15/README.md` said Modal was the only route. The
  endpoint snapshot saved with that capture lists five hosts (Modal, Together,
  Nebius fp4, Fireworks, BaseTen fp4), none of them Meta. Both now say what holds:
  no Meta endpoint, and every call pinned to Modal with no fallbacks.
- **Zenodo.** v1.2.33 (Muse Wonder) was never archived on 2026-10-13. Its GitHub
  release was re-published on 2026-10-19 and is now
  [10.5281/zenodo.23469033](https://doi.org/10.5281/zenodo.23469033). Its Zenodo
  date is therefore 2026-10-19, not the release date.
