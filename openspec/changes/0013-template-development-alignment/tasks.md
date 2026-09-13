# 0013 — Implementation tasks

All boxes are deliberately unchecked. This planning commit implements none of
these tasks. Each task is one coherent commit (≤2h); normally group 1–3 related
tasks per PR. Commands/test paths below are proposed proofs, not existing tests.
The issue and merged planning PR must be recorded before A1 begins.

## A — Foundation and local tooling

- [ ] **A1 (1h)** Record approved template/lake SHAs, local exceptions and actual
  source/package inventory in `template-manifest.toml` and `docs/architecture.md`.
  Proof: `tests/architecture/test_template_manifest.py`; confirm all pending
  milestones map to an owner and no proposed profile is labelled implemented.
- [ ] **A2 (2h)** Add repository-local uv/Python and Node/OpenSpec development
  manifests/locks plus idempotent `make install`, fresh-shell and Windows commands.
  Proof: `tests/integration/test_dev_setup.py` installs twice with no private lake;
  verify separate base-wheel consumer install needs none of these tools.
- [ ] **A3 (2h)** Align Black/isort 100, compatible Ruff lint, pre-commit and existing
  commit-gate scripts without unrelated source reformatting.
  Proof: `tests/architecture/test_formatting_policy.py`, formatter idempotence and
  pre-commit rejection of a deliberately misformatted scratch fixture.
- [ ] **A4 (2h)** Add fast affected-test and complete check/build/audit targets using
  explicit environment execution; retain 90% branch coverage and OS matrix.
  Proof: `tests/integration/test_dev_commands.py`; fresh shell selects clone-local
  tools; failed child check propagates nonzero; fast checks report partial coverage.
- [ ] **A5 (2h)** Add offline enforcement, strict OpenSpec and workflow lint to
  reusable CI without losing clean wheel/init/doctor/data or sdist checks.
  Proof: `tests/architecture/test_ci_contract.py`, unmarked external connection
  rejection and successful explicitly scoped loopback fixture server.

## B — Shared harness, context and policy

- [ ] **B1 (2h)** Consolidate shared AGENTS/rules/docs and Claude import; preserve
  every Sobres rule and versioned PR review procedure.
  Proof: `tests/architecture/test_instruction_sources.py` and manual rule inventory
  against pre-migration AGENTS/CLAUDE; no dropped currency or data-integrity rule.
- [ ] **B2 (2h)** Add shared skill/rule links and safe runtime-specific harness
  configuration; retain and adapt the existing commit gate.
  Proof: `tests/architecture/test_agent_links.py`, hook fixture tests, real installed
  agent discovery after restart; disclose unavailable agent separately.
- [ ] **B3 (2h)** Add optional reviewed context gitlink, local fallback standards,
  update/restore instructions and artifact exclusions.
  Proof: `tests/packaging/test_context_independence.py`, no-lake public clone and
  maintainer artifact build with dummy secret/state sentinels; no private fetch.
- [ ] **B4 (2h)** Add contribution guide, issue forms, standard PR template and
  issue/plan/task fields in propose/apply/ship procedures.
  Proof: `tests/architecture/test_contribution_contract.py`; walkthrough rejects
  starting implementation from an unmerged plan; local planning status stays explicit.
- [ ] **B5 (2h)** Implement trusted read-only issue/merged-plan metadata and ancestry
  validation, independent of a changed-spec-path heuristic.
  Proof: `tests/test_pr_gates.py` covers valid lineage, absent/wrong issue,
  wrong repo/base, unmerged plan, non-ancestor and missing metadata errors.
- [ ] **B6 (2h)** Add planning-only/semantic-amendment and scoped-maintenance checks,
  then integrate mandatory aggregation and optional review setup.
  Proof: `tests/test_pr_gates.py` covers code in planning, amended acceptance in
  implementation, blank reasons, fork-modified checker, unavailable API metadata
  failing closed, and skip/cancel/failure propagation. Read-only ruleset inspection
  identifies required statuses; any remote activation is a separate maintainer action.
- [ ] **B7 (2h)** Add reviewed template-update mechanism with downstream ownership
  exclusions and pin rollback. Start manual; do not enable auto-merge.
  Proof: `tests/integration/test_template_update.py` applies a synthetic upstream
  change in a temporary clone and refuses protected-path overwrite; revert is clean.

## C — Compatible application extraction (A and B first)

- [ ] **C1 (2h)** Split neutral registry declarations from Typer generation and
  introduce explicit disabled-by-default HTTP/UI exposure metadata.
  Proof: `tests/cli/test_registry.py`, `tests/architecture/test_registry_neutrality.py`;
  all existing CLI names/aliases/defaults/booleans/list options remain identical.
- [ ] **C2 (2h)** Introduce owned provider/storage ports and plain market types with
  compatibility re-exports; relocate conformance tests without duplicate collection.
  Proof: `tests/contracts/`, `tests/packaging/test_legacy_imports.py`; no driver
  types exposed and one collected instance per conformance case.
- [ ] **C3 (2h)** Move the SQLite adapter/schema/migration implementation behind the
  new adapter boundary with original migration contents/IDs and data locations.
  Proof: `tests/integration/storage/` includes WAL backup, transaction failure,
  previous-schema read/restore and unsupported backend errors.
- [ ] **C4 (2h)** Move Yahoo/FRED providers and fixture wiring with forwarding imports.
  Proof: `tests/integration/providers/` and recorded cold/warm cache parity;
  no synthetic replacement of recorded payloads.
- [ ] **C5 (2h)** Move Ken French/ECB providers and pure alignment/gap types/rules.
  Proof: provider fixtures, missing/closure/listing distinctions, mixed-case factors,
  currency normalization and single-currency no-FX tests.
- [ ] **C6 (2h)** Extract cache/currency service orchestration and composition context
  from CLI context; inject clock, settings, providers, repositories and progress.
  Proof: `tests/application/test_market_services.py`, cache TTL/refresh/revision
  tests and `tests/architecture/test_layering.py` prohibit concrete adapters in services.
- [ ] **C7 (2h)** Migrate data/cache declarations and handlers into application use
  cases; keep CLI parsing/rendering and error mapping in adapters.
  Proof: `tests/application/test_data_commands.py`, `tests/cli/test_data_commands.py`,
  all format/log-level invariants with fixed time/cache metadata policy.
- [ ] **C8 (2h)** Migrate config/doctor/init application work, separating secret
  settings I/O and terminal prompts through owned boundaries.
  Proof: `tests/cli/test_config_commands.py`, `test_doctor.py`, `test_init.py`;
  real TTY optional-key skip and idempotent offline setup in an isolated config/DB.
- [ ] **C9 (2h)** Migrate upgrade/introspection and finish CLI entry-point facades;
  remove migration allowlist entries now replaced by facades.
  Proof: upgrade installer cases, complete registry exactly once, old imports and
  generated help/version/format/exit-code parity in an installed wheel.

## D — Final compatibility and milestone handoff

- [ ] **D1 (2h)** Run current and migrated builds from separate fresh environments
  against the same recorded inputs and isolated state, compare values/units/errors,
  record full gate/build/audit results and cross-platform CI.
  Proof: `tests/packaging/test_migration_compatibility.py`; parse JSON/CSV, compare
  table semantics and verify explicit allowed time/cache metadata differences only.
- [ ] **D2 (2h)** Verify no-lake and populated-checkout wheel/sdist contents and clean
  consumer onboarding; exercise rollback of harness/pins/package moves.
  Proof: `tests/packaging/`, `tests/integration/test_template_update.py`; config/data
  locations and released migration identities unchanged after rollback.
- [ ] **D3 (2h)** Prepare the stack migration ledger: reconcile PR #8 first, then
  #9–#16 in order, mapping old task IDs to amended tasks and new merge prerequisites.
  Proof: diff/ancestry and scenario/task audit for every branch; no branch is marked
  ready based on stale checkboxes or source-only UI assertions. Actual feature
  restacking, fixes and testing stay in each owning milestone's R0/R1/R2 tasks.
- [ ] **D4 (2h)** Sync/archive completed baseline specs with preserved scenario
  coverage, then refresh local docs and re-run strict validation of the full set.
  Proof: disposable archive dry run, canonical requirement comparison and existing
  `tests/architecture/test_scenarios.py`; no implemented scope dropped or newly
  proposed requirement accidentally labelled shipped.

## Verification discipline

Use explicit temporary `SOBRES_CONFIG_FILE` and `SOBRES_DB_URL`; never repurpose
`HOME`. Live provider checks are a separately selected, bounded supplement with
recorded skips. No cloud or release credential is needed for 0013 acceptance.
Black and isort run after every implementation Python edit. Formatting, spec and
link validation alone cannot prove the financial, UI or storage behavior.
