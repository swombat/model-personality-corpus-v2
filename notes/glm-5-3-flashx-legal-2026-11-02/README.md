# GLM 5.3 FlashX Legal (z-ai/glm-5.3-flashx-legal), evidence snapshot

Retrieved 2026-11-03 by Lume (souls.house body, daily model-mapping rhythm).

- `announcement.html` / `announcement.md`: Z.ai's own documentation page
  https://docs.z.ai/guides/vlm/glm-5.3-flash (section "GLM-5.3-FlashX-Legal").
  It states the model "undergoes legal-domain mid-training and post-training"
  (reinforcement learning in legal task environments), so it is new weights on
  top of GLM-5.3-FlashX, not a serving variant. Mapped under the runbook rule.
- Release date 2026-11-02: the Legal section carries no visible date and the
  "New Released" page (docs.z.ai/release-notes/new-released) does not list it
  yet. The page's schema `dateModified` is 2026-11-02T10:33:58Z (HTTP
  last-modified Mon, 02 Nov 2026 19:04:07 GMT), the first appearance of the
  section we can see. OpenRouter's canonical slug `-20261102` agrees but is
  not used as evidence. Weaker than a visible date; marked as such.
- `endpoints.json`: OpenRouter endpoints at capture time. Single route Z.AI,
  fp8, max completion 131072, reasoning mandatory (default effort max).
