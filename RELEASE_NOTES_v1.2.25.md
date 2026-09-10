# Release notes — v1.2.25

Prepared 2026-09-10.

## DeepSeek V4.1 Flash and Inception Mercury 2.5

- Added 125 freeflow and 120 values samples for each model: 490 new responses.
- OpenRouter routes pinned to DeepSeek and Inception, with fallbacks disabled.
- Default reasoning retained: DeepSeek high, Mercury medium according to the live catalog.
- Exact catalog snapshots and default reasoning metadata recorded in the collection manifest.
- Strict audit checks exact sample identities, nonempty final answers, stop finish reasons, requested model, and actual upstream.
- Mercury OPEN_12 initially contained partial text with finish_reason=error; preserved under discarded/2026-09-10-mercury25-provider-error and replaced at identical settings. No error-finished output accepted as a valid sample.
- Companion analysis is phase34_deepseek41_mercury25_20260910. One DeepSeek posture classification remains explicitly ambiguous after independent adjudication; raw response is valid.
- Unrelated untracked collections are excluded from this release.
