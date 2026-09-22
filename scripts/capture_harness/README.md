# Verified streaming capture harness

Runs on Python 3.11+ on macOS and Linux (including the Dell). Uses existing
`httpx` and the sibling analysis repository; inference is remote. SQLite,
subprocess supervision and file locks are in the standard library. Do not run
with Python `-O`: analysis validators intentionally use assertions.

## Contract

For **each model independently**:

```
freeflow sample -> raw verification -> BV1 -> BV1 QA ---------------------+
values sample  -> raw verification -> 3 content coders -> consensus     |
                 -> 3 posture coders -> consensus -> complete values   |
                 -> one preserved adjudication of initial splits -----+
                           all required samples -> synthesis/card/profile
```

There is **no batch-wide collection barrier**. Capture and analysis have
separate pools. Failed verification requeues the smallest affected unit;
exhausting its retry allowance blocks only descendants. Other models and probes
continue. Classification disagreement is evidence, not a retry trigger.

A raw success requires exact requested model and pinned upstream, canonical
prompt and condition, a nonempty final answer matching the raw completion,
`finish_reason=stop`, and no known role-delimiter/replacement-character damage.
A process exiting zero is not success: a separate validator must pass and output
hashes are checkpointed. On restart changed completed artifacts block their
subgraph; they are never silently trusted or overwritten.

Existing successful raw responses are verified and adopted before scheduling, so
local verification never waits behind slow API calls. The same conditional
pending-to-done adoption can safely run during a recovery; it never steals a
running task lease. Existing successful raw responses are reused. Legacy BV1/coder results require
an explicit source-verified import. Every rejected raw response and analysis
output is retained. Technical retries do not switch providers or alter prompts,
reasoning mode, sampling temperature, taxonomy, or agreement thresholds.

**Token limits:** each model declares an ordered cap schedule no higher than its
captured endpoint limit. A proven `length` finish advances to the next cap;
it does not keep rolling answers at the same insufficient cap. Request receipts
record the actual cap and the full policy. This introduces documented cap
heterogeneity when adopting earlier captures: do not describe them as a single
fixed-ceiling experiment. An exhausted cap escalates. Raw requests have six
queue attempts; analysis units four (existing coder adapters may themselves
make at most four HTTP attempts); adjudication and synthesis three technical
attempts. These are request/time bounds, **not a dollar budget guarantee**.

## Create and run

Create a manifest (IDs/pins/endpoint limit from a saved catalog snapshot):

```json
{
  "run_id": "20260922-example",
  "models": [{
    "provider": "openrouter", "model": "vendor/model", "or_provider": "Vendor",
    "label": "model-or-pin-vendor", "slug": "model", "family": "vendor",
    "route_max_tokens": 32768,
    "token_policy": {"freeflow": [16000, 32768], "values": [4000, 8000, 16000, 32768]}
  }],
  "pools": {"capture": 4, "analysis": 12, "local": 3, "synthesis": 1}
}
```

```sh
python3 scripts/capture_harness/build.py manifest.json \
  --run-dir logs/capture-harness/example --analysis-root ../model-personality-analysis-corpus
source scripts/source_sops_keys.sh
python3 scripts/capture_harness/service.py logs/capture-harness/example/spec.json \
  --state logs/capture-harness/example/state
```

Configuration is immutable after a run starts. Resume with the same command;
never rebuild to reset failed-task counters. The runner enforces one supervisor
per run and locks output resources across runs on the same host. Do not run old
collectors on those cells: legacy scripts do not participate in these locks.

`import_results.py RUN_DIR SOURCE_PHASE --old-writers-stopped` adopts existing
values annotations only when source trace hashes, IDs, prompts and responses
match. It explicitly records the prior BV1 source/output hashes. Stop all old
writers before import and before starting the service.

## Background service

`install_service.py` **generates** a wrapper and service file. It does not
silently install anything. Credentials stay in a private loader/environment;
never put them in a manifest, service definition, log or command line.

```sh
python3 scripts/capture_harness/install_service.py RUN_DIR/spec.json \
  --state RUN_DIR/state --output RUN_DIR/service --platform linux \
  --credential-loader /absolute/path/to/private-loader.sh
# Linux: copy generated unit to ~/.config/systemd/user/, then:
systemctl --user daemon-reload
systemctl --user enable --now mira-model-capture.service
# An unattended Dell user service needs login lingering enabled by its administrator.
```

For macOS use `--platform macos`, copy the generated plist to
`~/Library/LaunchAgents/`, and `launchctl bootstrap gui/$(id -u) PATH.plist`.
Both managers restart unexpected failures; the persisted queue decides what
can run again. Network failures never erase prior work. `systemd` kills the
whole unit's process tree on stop. The macOS supervisor tracks and stops worker
process groups; an ungraceful supervisor crash leaves surviving child locks in
place until their own deadlines expire.

## Escalation / observability

`state/status.json`, `STATUS.md`, `state.sqlite` (events + attempts), per-attempt
logs and `outbox/*.json` provide explicit custody. Status timestamps distinguish
fresh work from stale receipts. The service drains alerts independently of the
chat and of ordinary collection. An optional `notify_command` argv array in the
manifest receives a bounded checkpoint prompt as its last argument. Configure
it to invoke **Mira's own** runtime, never Lume's. It is called once per model
escalation/completion; failed delivery retries at most three times and remains
visibly failed. No notifier configured means an undelivered outbox, **not** a
claim that Mira was alerted. No provider credentials or corpus text go into the
notification prompt. Escalation diagnoses the problem; it never silently raises
budgets or rewrites the experiment.

## Completion boundary (important)

This version's final receipt is `ANALYSIS_READY.json`:
**verified raw + all sample analyses + adjudication provenance + overall
freeflow synthesis/personality card/profile**. It explicitly says
`analysis_complete_awaiting_publication`, not published. Shared final-values
integration, website/map generation, editorial assets, release metadata, and
commit/push/tag/deploy are distinct publication work. The harness does not
mislabel that boundary as a completed public release.

## Portability and tests

No macOS automation APIs in the engine/worker. The service generator is the only
OS-specific component. Model/analysis paths are provided at build time; the raw
repository is located relative to the script. An existing compiled run contains
absolute checkpoint paths: do not just launch a Mac spec on Linux. Stop the old
host first and transfer repositories + artifacts; create a host-local run and
explicitly import verified artifacts. Do not reset exhausted budgets to evade a
blocker. Full live cross-host checkpoint migration is not yet implemented.

```sh
python3 -m unittest discover -s scripts/capture_harness/tests -v
```

Tests simulate failure/retry, zero-exit malformed artifacts, timeouts, restart,
artifact tampering, model isolation, streaming dependencies, alert delivery and
delivery failure without making API calls. Production success still requires a
live canary through the actual analysis scripts.

## Operational limits

- Transport is at-least-once, not exactly-once billing: a crash after a provider
  accepts a request but before the response is saved can cost a duplicate call.
  Atomic results, output locks and preserved attempt counters bound that risk.
- A bounded escalation is a separate Mira checkpoint, not a guarantee that the
  original interactive conversation will spontaneously resume. Its response and
  nonce-bound JSON acknowledgement and delivery receipt remain in the outbox.
  Exit code zero alone is never delivery: Mira must write the dedicated receipt,
  which survives the journal reflex replacing the CLI final text.
- macOS uses launchd Standard scheduling (Background severely throttles SQLite
  fsync and Python startup) and prevents idle sleep while the service works.
- Standard sample coding is light local work; API inference is remote. Future
  whole-corpus similarity-map regeneration is a separate CPU/memory-heavy stage,
  not something to multiply by the sample worker count.

## Model metadata and release dates

New runs include a model-local metadata task before synthesis. Supply optional
`release_date` (YYYY-MM-DD) and **required when dated** `release_date_source` in
each model entry. The worker writes `model_metadata.json` and merges the exact
slug into the website's `model-release-dates.json` with a separate source registry.
Conflicting existing dates/sources fail closed. Missing dates stay explicitly
unknown: OpenRouter's `created` timestamp is a listing date, not automatically a
model release date. Endpoint/provider/quantization metadata remains in the record.
This does not build/deploy the website or fill its other routing/pricing registries.
For already-compiled runs use `metadata.py SUPPLEMENT_CONFIG.json` without
changing the immutable run configuration; preserve that explicit supplement.

## Explicit repair after escalation

`recover_blocked.py SPEC --state STATE --authorization AUTHORITY_ID --limit 2 JOB_ID...`
executes only explicitly selected blocked roots under the normal output lock,
validator and deadline. Its separate SQLite allowance survives restart; original
attempt counts, prompts and settings are unchanged. Successful repair releases
only dependency-blocked descendants. A repair is an intervention, **not** evidence
that the initial unattended trial succeeded. Never mint a new authorization ID
merely to refill an exhausted allowance. A terminal engine must be resumed after
repair if it has already exited; an active engine picks up dependencies normally.
