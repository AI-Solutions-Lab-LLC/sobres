# Implementation plan and proof map

**Planning only. All implementation tasks remain unchecked.** Each task below is
one intended coherent commit of approximately 1–2 hours; if an adapter or research
run exceeds that, split by contract/scenario before implementation rather than
claiming a whole platform fits in two hours. Data procurement, long backfills,
vendor registration and empirical paper observation have separate elapsed time.
Each row is one proposed implementation PR containing 1–3 related tasks.

Before any implementation: verify this planning PR is merged and an ancestor of
the implementation branch; resolve applicable Q decisions; keep new scenarios
`proposed` until their assertions and observed behavior pass. Scenario references
below are future proof locations, not tests that exist today.

## Human-gated tasks (owner)

Defined in [hosting.md](hosting.md#human-gated-prerequisites). They are owner
actions, never CI or agent work, and the tasks they unblock stay open until the
owner records them as done.

- [ ] **H1** — API keys or complete API documentation for at least two options/earnings vendors, with sample data confirmed to carry historical bid/ask, timestamps, contract identity and earnings confirmation times (Q12). Unblocks A2.
- [ ] **H2** — GCP project/billing, authenticated `gcloud` CLI and Terraform at pinned versions, bootstrap state bucket, secrets created and their values added through `gcloud secrets`. Unblocks D4.
- [ ] **H3** — Approved hosting, data and one-time history budgets and alert recipients. Unblocks B6 and D4.

## Wave A — data feasibility before platform spend

### A1 Contract and entitlement

- [ ] Record Q1–Q6 decisions, frozen thresholds and full entitlement/cost/rights matrix.
- [ ] Implement owned event/quote/manifest models and synthetic fixtures clearly labelled.

Proof: `tests/data/test_options_contracts.py`: OD1, OD2, OD4; real sample field/rights report; no purchase without owner-selected budget

### A2 Imported and provider observations (blocked by H1)

- [ ] Implement licensed file import with idempotent hashes and actionable quality errors.
- [ ] Design the owned options/earnings ports and capability declarations against at least two vendors' documented payloads, and build the recorded-fixture conformance suite that every adapter must pass.
- [ ] Implement the selected bounded vendor adapters and rate-limit/retry behavior.
- [ ] Add provider settings/doctor and recorded payload fixtures.

Proof: `tests/data/test_options_providers.py`: OD3, OD6, OD9; shared fake/recorded-provider contract over every adapter; bounded live sample separately recorded

### A3 Events, sessions and revisions

- [ ] Implement confirmed event versions and calendar ingestion.
- [ ] Implement as-of joins and immutable data manifests.

Proof: `tests/data/test_earnings_versions.py`: OD2, OD7; `tests/core/test_options_calendar.py`: EO2, EO3; BMO/AMC/holiday/early-close/DST and revised-date fixtures


## Wave B — math and reproducible evidence

### B1 Features and IV

- [ ] Implement consistent-maturity IV/IVR/IVP and historical-ramp math.
- [ ] Wrap a documented vendor/solver convention behind a pure pricing protocol and validate failure modes.

Proof: `tests/core/test_options_features.py`: EO5, OD8; hand-computed rank/percentile/interpolated total variance; independently verified American-option fixtures

### B2 Strategy and sizing

- [ ] Implement frozen pair selection, entry/exit and macro gates.
- [ ] Implement reserve/cohort/cash/sector sizing with deterministic ordering.

Proof: `tests/core/test_options_strategy.py`: EO1, EO4, OD5; `test_options_sizing.py`: EO6, EO7; perturb future data and assert unchanged prior decisions

### B3 Ledger and execution

- [ ] Implement observed ask/bid and midpoint/stress event ledger with fees.
- [ ] Implement chronological portfolio ledger, unresolved exits and adverse bounds.

Proof: `tests/core/test_options_backtest.py`: OB1–OB3, OD4, OD5; exact $194.80/$114.80 cases, overlapping cap/loss cases, halt/missing-exit accounting

### B4 Evaluation and reports

- [ ] Implement purged chronological partitions, trial manifests and seeded block bootstrap.
- [ ] Implement baseline/sensitivity/segment reports and frozen promotion gates.

Proof: `tests/core/test_options_evaluation.py`: OB4, OB6–OB8; deterministic split/interval known cases; no training/test overlap; report includes failures

### B5 Overlay and challenger experiments

- [ ] Implement predeclared VIX/technical overlay features and ablation runner.
- [ ] Implement bounded ridge challenger with inner-only penalty selection and uncertainty.
- [ ] Add optional licensed news/social feature experiment or record unavailable scope.

Proof: `tests/core/test_options_models.py`: OB4, OB5, OB8, OD6; same-event comparisons and redundant-cut detection; unavailable inputs cannot become zeros

### B6 Actual historical evidence

- [ ] Acquire approved bounded history, run frozen baseline and all declared variants, save manifests and data-quality report.
- [ ] Publish full held-out report and promotion decision, including inconclusive/rejected outcome if gates fail.

Proof: Re-run command + data hashes + event/portfolio CSV + report; OD7, OB1–OB8. Acquisition/run time is external to the 1–2h orchestration commits; no fabricated metrics


## Wave C — usable local research workflow

### C1 New operational repositories

- [ ] Define domain transactions and implement SQLite migrations/repositories for models, recommendations and paper allocations.
- [ ] Add job repositories with leases/fencing and WAL-safe export coverage.

Proof: `tests/data/test_options_storage.py` and shared conformance: EO7–EO8, OP3–OP5; transactions, stale leases, rollback, cache-clear preservation and committed-WAL backup

### C2 Registry and research UI

- [ ] Declare typed options commands/results, settings/checks and profile exposure metadata.
- [ ] Add SPA candidate/evidence/model/paper-position views and registry parity assertions.
- [ ] Add stale/revised/overdue/empty-result states and typed user actions.

Proof: `tests/cli/test_options.py`, `tests/api/test_options.py`, browser assertions: OP1–OP4, EO8; all formats/log levels and cross-field validators; actual rendered journey

### C3 Publication

- [ ] Implement artifact-first publication, promotion audit and retained revision history.

Proof: `tests/data/test_options_publication.py`: OP3–OP6; crash between upload and pointer commit, orphan cleanup, rollback audit, redaction at every log level


## Wave D — cloud profile and deployment

### D1 Scoped Firestore storage

- [ ] Implement new operational ports in Firestore with schema/version/error translation.
- [ ] Run the shared conformance suite against emulator and a bounded real-project namespace.

Proof: OH1, OH2, EO7, OP5; adapter work split further per domain if necessary; never claim generic `Storage` support

### D2 Artifacts and cloud jobs

- [ ] Add GCS immutable artifact adapter and checksums/retention.
- [ ] Add durable Cloud Run Job dispatch/reconciliation, fencing, cancellation and quota controls.

Proof: `tests/data/test_cloud_artifacts.py`, `tests/api/test_cloud_jobs.py`: OH3–OH5, OP5; dispatch-crash and stale-worker races

### D3 Identity and hosted profile

- [ ] Implement allowlisted Google identity/roles and secure session/CSRF boundary.
- [ ] Construct restricted registry/UI/startup profile without default SQLite or thread-worker initialization.

Proof: `tests/api/test_hosted_options.py`: OP2, OP6, OH1, OH6; browser access and guessed-route probes; no auto-generated token disclosure

### D4 Deployment and recovery (blocked by H2, H3)

- [ ] Add the Terraform root and bootstrap modules (pinned versions, GCS remote state, least-privilege service accounts, protected data resources, labels, digest-pinned images) with `terraform fmt -check` and `validate` in CI.
- [ ] Add registry-declared `deploy cloud-run check|plan|apply|destroy` wrapping the `terraform` and `gcloud` binaries, plus doctor checks for `gcloud` authentication, Terraform version, state bucket and named secrets.
- [ ] Add fenced logical backup and isolated restore runbook.
- [ ] Run the complete hosted acceptance journey, including destroy of the smoke environment, and record URL, image digest, Terraform outputs and measured cost evidence.

Proof: `tests/cli/test_deploy_cloud_run.py` with fake `terraform`/`gcloud` binaries: OH10–OH12; OH7–OH9 and all `hosting.md` runbook steps; abrupt termination, revision rollback, restore, no live trading; external account setup billed separately from commit work


## Required implementation gates

- Offline known-answer/conformance/property tests must reference their actual
  scenario titles and assert outputs, errors and state transitions.
- Follow reviewed CI: non-network suite with 90% branch coverage, Ruff lint/format,
  mypy, architecture/parity/secret checks, wheel/sdist build and strict Twine check;
  frontend build/client drift, container quickstart, workflow lint and dependency
  audit where affected. Run Black 100 and isort Black-profile 100 on every Python
  edit as required by AGENTS.md. No unrelated reformatting.
- New cloud/data extras must not break base-wheel keyless init/doctor or
  existing local/Compose paths. Test base wheel in a fresh environment.
- Live provider and Google cloud evidence requires actual configured access
  and bounded owner-approved spend. Fixtures prove code behavior only.
- Terraform plan, apply and destroy run only from a human's terminal through the
  CLI; CI validates the module without credentials and never applies. Secret
  values enter Google Cloud only through the owner's `gcloud` session (H2).
- Do not mark the change implemented until every required POC scenario and
  deployment journey is demonstrated. Optional/deferred structures or unavailable
  social experiments remain explicitly out of promoted scope.
