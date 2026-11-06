# Daily model mapping — runbook

Canonical home: this file, in swombat/model-personality-corpus-v2, next to the
capture harness it drives (`scripts/capture_harness`, Mira's). Moved here
2026-11-06 from Lume's home (`tools/model-mapping/`) so either Lume or Mira can
run the rhythm (Daniel, souls.house eLQgdj). The scripts are in
`scripts/daily_mapping/`: `new_models.py` (detector), `decisions.json` (the
shared ledger), `run_capture.sh` (launcher).

Daniel, 2026-10-07 (souls.house BjZoXJ, message JXGxBY): every day, check
OpenRouter for new text models from the labs we follow. When one appears, map
it end to end (capture, analysis, site data, map, ladder, strapline, banner,
release, deploy) **without asking him**. He doesn't need to review the strapline.
Worked example: the Mistral Large 4 run (2026-10-06/07; analysis v1.4.23,
raw v1.2.31).

**Who does what.** Either body can run steps 1–3 and 4 except 4.4. Step 4.4
(strapline + banner) is Lume's: if you are Mira, stop at 4.4, tag Lume in the
rhythm's conversation with the branch name, and let Lume finish 4.4 and hand
back (or finish the rest).

**One ledger, one claim.** `scripts/daily_mapping/decisions.json` in this repo
is the only authority on what is mapped, skipped, held or in flight. Never
decide from a local copy. Before step 1: `git pull --ff-only` on master.
Before launching any capture (step 3.5): record
`"capturing YYYY-MM-DD <body>: <run_id>"` for the model, commit and push to
master. If the push is rejected, someone else moved: pull, re-read, and
don't launch if the model now has an entry. Replace the claim with
`"mapped ..."` / `"held ..."` when done. A `capturing` entry whose run has no
live process and no fresh STATUS.md is step 1's business, not a new capture.

The rhythm wakes a fresh instance that has none of this in context. This file
is the whole procedure. Read it all before acting.

## 0. Environment

Per-body setup lives with each body: Lume's house body below; Mira's in her
`shared/reference/model-capture/house.md`. The scripts take overrides:
`MPAC_DIR` (analysis checkout), `MPC_PY` (harness python), `OR_KEY_LOADER`, or
an `OPENROUTER_API_KEY` already in the environment. Paths below written as
`~/work/...` are the house body's; substitute your own.

### Lume, house body

- `source ~/state/tools/env.sh`. Without it there's no node, ruby or postgres
  on PATH.
- Git: the state gitconfig has no identity. Use
  `export GIT_CONFIG_GLOBAL=$HOME/state/github/gitconfig` and
  `git -c user.name="Lume Tenner" -c user.email=lume.pa@agentmail.to ...`.
- Python: `~/state/tools/mpc-py/bin/python` (httpx) for the harness;
  `~/state/tools/map-py/bin/python` (numpy/scipy/sklearn/umap) for the map
  and tests; system `python3` for generate_scoped.py.
- Repos: raw `~/work/model-personality-corpus-v2` (default branch `master`),
  analysis `~/work/mpac` = swombat/model-personality-analysis-corpus (`main`;
  the site deploys from main to model-personality.danieltenner.com).
- OpenRouter key: `source ~/state/lume/or-key-loader.sh` (the souls.house dev
  key; Daniel approved it for this research, BjZoXJ jWnRzJ). There's no spend
  limit on the key, so record its usage before and after each run
  (`curl -s -H "Authorization: Bearer $OPENROUTER_API_KEY"
  https://openrouter.ai/api/v1/key`) and report the delta.
- GitHub token: `~/state/github/token` (authenticates as swombat).

## 1. Finish anything in flight first

`ls ~/work/model-personality-corpus-v2/logs/capture-harness/ | grep house`.
For each run without a release: read `STATUS.md` and `state/status.json`.
- Running (fresh timestamps, process alive: `pgrep -af service.py`): leave it.
- Stopped with tasks blocked on HTTP 429 or other technical errors: repair
  them with `scripts/daily_mapping/run_capture.sh RUN_ID --repair <authz-tag>
  <task ids>`. Launch it detached (see 3). Then write a note in the run's
  release notes that this was an intervention. Do this only for technical
  failures. Never repair a QA rejection by retrying, and never raise budgets.
- Complete (all tasks done, no blockers): go to step 4 (publish).
- Blocked on `exit 22` = "declared token ceiling exhausted" (finish_length at
  the top of the model file's `token_policy` ladder). Raising it is a budget
  change: ask Daniel, or settle it with Mira (she's in the rhythm since
  2026-11-04). Mechanics once approved (GLM FlashX Legal, 2026-11-04): copy the
  run's `models/<cell>.json` and `spec.json` aside, extend the ladder in the
  model file, put the new `digest()` in `spec.input_hashes`, then move the
  state DB `meta` row `k='spec'` to `sha256(json.dumps(spec, sort_keys=True))`
  (copy `state.sqlite` aside first; recover_blocked asserts it), then
  `run_capture.sh RUN --repair <authz> <ids>`. Write `INTERVENTION-<date>.md`
  and copy it into the raw repo's `notes/<slug>-<date>/`.

## 2. Detect

`python3 scripts/daily_mapping/new_models.py` (default: last 10 days).
It lists followed-lab text models that aren't on the site and aren't in
`decisions.json`. Decide for each one and record the decision in
`decisions.json` (`"mapped YYYY-MM-DD: vX"` or `"skip: reason"`). Commit and
push this repo (master).

Map: a new model from a followed lab (new weights, or a new named release with
its own default behaviour). Pinning a "-pro"/"-prime" endpoint is fine if it's a
separately announced model.

Skip, with a reason: image/audio generators, routers, `:batch`/`:free`
duplicates, and pure serving variants of something already mapped
(precedent: UltraSpeed and FlashX borrow their parent's score).
Also skip same-model reasoning-mode SKUs ("Pro" = the same weights served in
max-thinking mode). Daniel, 2026-10-07: "ignore models that are just the same
model on max thinking". Do the same for throughput SKUs ("Prime", "UltraSpeed",
"FlashX"). Read the OpenRouter description: it usually says "same underlying
model" or "high-speed variant".

Ask Daniel first (one message, then wait for the next day) only if
1. the estimated run cost exceeds **$20**. Estimate it as
   245 × ~6k output tokens × output price, plus about $1 of analysis. Pro
   models at $180/M out are the case this exists for. Or
2. the model has no OpenRouter route that can be pinned to the lab's own
   provider.
Stealth models (`stealth/*`, provider "Stealth", lab unnamed) are NOT a rule-2
case: they get mapped, lab Unknown, release date = OpenRouter listing date
labelled as such, plus a provenance note (precedent: Ox Alpha, Union Alpha,
Space Bunny; manifest `collection-manifest-2026-09-23-space-bunny.json`). I
skipped Crouton Alpha on 2026-11-04 by misreading rule 2; Daniel asked for it.
Smoke-test from here first: Crouton Alpha answered 403 "not available in your
region" from both Finland (house box) and Spain (Dell); held, recheck daily.
The `"backlog ... ask Daniel"` entries in decisions.json predate the rhythm.
Leave them unless he answers.

## 2b. Make it selectable on souls.house (Daniel, 2026-10-07, JNPpXe)

For every model you map, also add it to the souls.house model list, as a
tiny commit straight to master (no PR; standing rule for few-line changes).
Master auto-deploys Rails since 2026-10-08, so this commit is a deploy: read
that SHA's Deploy Rails receipt (`success` + `verified`) before reporting it.
Labs with no direct route here (Meta, Mistral) get an OpenRouter-only row:
no `provider_model_id`, and skip the direct-id sandbox test (Muse Wonder
`d557eae` is the worked example).
Worked example: `bdefc61` (Haiku 5.5) and `89cebb9` (GPT-6.1 Sol). In a fresh
worktree of `~/work/souls-house` off origin/master:
- `app/models/chat/model_selection.rb`: one `MODELS` row in the lab's group
  (`model_id` = OpenRouter id, `provider_model_id` = the lab's direct id,
  `thinking:` like its siblings), and extend `reasoning_profile_for` if no
  existing case matches. Don't touch "Top Models" unless it's the lab's new
  flagship (there's a test pinning that list).
- `app/services/agent_runtime_interaction_cost.rb`: a `PRICE_RULES` row
  (anchored regex, before any looser sibling it could shadow); cache rates
  only if the defaults are wrong for it.
- Tests: add the id to the provider-group/effort test in
  `test/models/chat_thinking_test.rb`, the direct-id routing test in
  `test/services/agents/sandbox_model_test.rb`, and a price test in
  `test/services/agent_runtime_interaction_cost_test.rb`; a note with the
  price source in `docs/interaction-cost-pricing.md`.
- Verify the direct id actually answers (Anthropic:
  `claude -p --model <id> "Reply with just: ok"` from the scratchpad with
  `LUME_NO_REFLECTION=1`; others: the provider API).
- Run those test files. `lume-rails-test` refuses unknown checkout names, so
  call `bin/rails test` with its env and a free `SOULSHOUSE_INSTANCE`
  (claims live in `~/.local/state/souls-house/instances/`).
Pro/Prime/serving-variant SKUs that you skip for mapping can still be worth a
row here only if Daniel asks.

## 3. Capture + analysis (one harness run, ~1–2 h)

1. Snapshot evidence into `notes/<slug>-<release-date>/` in the raw repo:
   `endpoints.json` (OpenRouter `/api/v1/models/<id>/endpoints`), the lab's
   announcement page as `announcement.html`, and a `README.md` saying where the
   release date came from. Use the lab's post (schema.org datePublished
   or a visible date). OpenRouter's created timestamp is not release evidence.
2. Write `collection-manifest-<date>-<slug>-house.json`, copying
   `collection-manifest-2026-10-06-mistral-large-4-house.json`. Set label
   `<slug>-or-pin-<provider>`, `or_provider` = the lab's own provider name on
   OpenRouter, `route_max_tokens` = the endpoint's max completion, and the same
   token_policy, bv1_evaluator `bv1-luna-v1-20260929`, synthesis_route
   `openrouter-openai`, release_date and source.
3. Build: `cd ~/work/model-personality-corpus-v2 && ~/state/tools/mpc-py/bin/python
   scripts/capture_harness/build.py <manifest> --run-dir
   logs/capture-harness/<run_id> --analysis-root /home/agent/work/mpac`.
4. Smoke-test one pinned call (expect HTTP 200) before launching.
5. Launch **detached**, or it dies when the shell closes:
   `setsid nohup scripts/daily_mapping/run_capture.sh <run_id> >
   ~/work/model-personality-corpus-v2/logs/capture-harness/<run_id>/service.out
   2>&1 < /dev/null &`
6. Post in the rhythm's conversation that it started. The session can't wake
   itself when the run finishes, so the next daily wake (step 1) picks it up.
   A 0-byte service.out says nothing; read STATUS.md and state/status.json.

## 4. Publish (when the run is complete)

Analysis repo (`~/work/mpac`), on a branch named after the slug, then
fast-forward main:
1. Check the harness wrote the card/profile/values merges (it does them
   additively). Check `analysis/values-probe/final/data/QA.md` counts.
2. `website/scripts/generate_data.py`: add `"<slug>": "<openrouter id>"` to
   MODEL_SLUGS, plus a display_name_from_slug branch if the slug-derived name is
   ugly. Add only a FIRST_PARTY_API_PRICING row when OpenRouter's price isn't
   the interactive first-party price.
3. `website/src/generated/model-notes.json`: a note on the evaluator
   (BV1-Luna) and any intervention.
4. Strapline + banner (editorial: Lume's, and Daniel doesn't review it;
   Mira hands this step to Lume, see the top).
   Use the model's own recurring line where one exists. Check it isn't already a
   sibling's strapline (grep `summary` in models.json). The strapline lives in
   the card index/summary (see how `mistral-large-4-0` got its summary in
   `model-summaries.json`). Banner: `internal/scripts/generate_model_images.py`
   has the house style and per-model prompts. Add one. There's no Gemini key
   in the house, so render through OpenRouter `google/gemini-3-pro-image`
   (≈$0.14) and inspect it for fake signatures or text. Write
   `website/public/images/models/<slug>.webp` and `-thumb.webp`.
5. Release date: `model-release-dates.json` and
   `model-release-date-sources.json`.
6. `cd website && python3 scripts/generate_scoped.py <slug>`. It must report
   125/125 freeflow, 120/120 values, image True, and every other model
   preserved exactly.
7. Map: `~/state/tools/map-py/bin/python scripts/generate_map.py`. Record the
   nearest neighbours, the nearest same-lab model and the PCA disparity.
8. Ladder: fetch `https://artificialanalysis.ai/models/<aa-slug>` (find the slug
   by trying the obvious one; AA sometimes adds "Preview"). Extract the
   `currentModel` object; `internal/capability-ladder/provisional-20261007/`
   has the script and an example. Field map (the chance-corrected score is
   `(x - chance)/(1 - chance)`): lcr→aa_lcr, scicode, automationBenchPartialScore
   →automationbench, briefcaseBreakdown.rubricPassRate→briefcase_rubric,
   hle (chance 0.048), omniscienceAccuracy, critpt, gdpPdfAllPass→gdp_pdf,
   mlcrOverall→mlcr, tauBanking→tau3_banking, terminalbenchHard,
   terminalBench21→terminalbench_v21, ifbench, gpqa (chance 0.25), aime25,
   livecodebench. Values belong to the model only inside `currentModel`.
   The rest of the page lists other models. With a multi-effort AA page, use
   the effort the site cell ran (usually provider default; precedent: Sol
   used "high"). Fewer than 3 measured rungs: leave it unscored and say so.
   Otherwise copy the provisional_fit.py approach, add the entry to
   `capability-ladder.json` with `provisional_note`, and add the
   `aliases.tsv` row. No AA page: unscored, with an aliases row saying so.
9. Tests: `~/state/tools/map-py/bin/python scripts/test_model_map.py`,
   `test_scoped_values.py`, `test_pricing.py`, `test_phase19_cards.py`
   (that one failed on main before 2026-10-07; compare against main before
   calling anything a regression). `npm run build`, then check
   `dist/models/<slug>/index.html` for the strapline, price and ladder.
10. Versions: next analysis version = highest of the latest tag and the
    release notes, +1 patch. `RELEASE_NOTES_vX.md` in the shape of v1.4.23
    (evaluation, intervention, what it looks like, editorial, ladder, map,
    verification, spend). Bump `CITATION.cff` (version, date-released),
    `.zenodo.json` version, and the README status block.

Raw repo first: release notes `RELEASE_NOTES_v1.2.N.md`, CITATION version/date,
the README "Latest addition" and model count, and regenerate
`data/CORPUS_SUMMARY.md` with `~/state/tools/mpc-py/bin/python
scripts/corpus_summary.py`. Commit, merge to master, push, then create the GitHub
release (tag vX on the pushed sha) through the API.

Then analysis: commit, ff main, push. Wait for the "Deploy website" Actions
run to finish green, curl the live model page and capability page, then
create the GitHub release on the pushed sha. Don't claim a Zenodo DOI until
you've seen it.

## 5. Report and record

- Post in the rhythm's conversation: live URL, versions/shas, metadata,
  ladder, nearest neighbours, interventions, spend delta. Also post a short
  line in BjZoXJ if it's still the thread where Daniel follows this.
- Update `decisions.json` (replace the `capturing` claim), commit and push this repo.
- Journal entry in your own home.
- Mira's weekly review rhythm reads the releases. Her findings come back to
  Daniel and Lume, and fixes are Lume's.

## Known gotchas (each one bit once)

- Never crop a banner to remove a fake signature or lettering: every banner
  is the render's native 21:9 (1500x636). Paint it out with a feathered patch
  of the adjacent texture, or re-render. Check the size against a sibling
  before publishing (Muse Wonder shipped at 1500x585; Daniel noticed).
- "Branch ready" meant only the parts I'd made were ready. Check against the
  previous release's diff (`git show --stat` of the Sol and Mistral commits),
  not my own list.
- The site JSON `difficulty` is a rank placement, not the logistic midpoint.
  Fit the slope and intercept per rung (provisional_fit.py does this).
- A detached run can stop silently at its retry budget. A 0-byte log isn't a
  witness; read STATUS.md.
- Launch-day 429s are normal for a new model. Better to wait a day than burn
  the six attempts.
- Never edit harness or evaluator code in `~/work/model-personality-corpus-v2`
  or `~/work/mpac` while a run is live: the service imports from those trees,
  so an edit goes straight into running tasks. Branch in a worktree.
- `pgrep -f PATTERN` inside a `bash -c` matches the shell that ran it. Use
  `ps -eo pid,args | grep "[s]ervice.py"` and never signal a pattern match.
- A blocked BV1 task can be declared ineligible only through
  `scripts/capture_harness/apply_ineligibility.py` (bv1-ineligibility-v1; run
  `--check` first). Do it only with Mira's approval naming that sample. It
  fits one odd sample, not a systematic gap: Qwen3.8 Omni Flash (2026-10-08)
  had 8/125 unpunctuated sources and is *held*, not mapped. See
  `decisions.json` and the raw repo branch `hold/qwen3-8-omni-flash`.
- A "held" entry in decisions.json means captured: don't re-capture it.
- Pushing the 2b commit to souls-house master prints "Changes must be made through
  a pull request". That is the ruleset's admin-bypass notice, not a rejection: the
  push lands (3cd1ff99, 2026-10-16). Check `git log origin/master` before opening a PR.
- No first-party route (rule 2) and Daniel approves a third-party host anyway
  (Muse Spark Open via Modal, 2026-10-16): pin that provider, name it in the label
  (`-or-pin-modal`), and mark it in the notes README, manifest notes, release notes
  and the site model note ("marking the cell clearly").
