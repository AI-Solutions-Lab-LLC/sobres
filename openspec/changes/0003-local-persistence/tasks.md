# 0003 — Tasks

Planning amendment: source PR #9 at `20654c1249aa7de32e3c35dbaa346c6929ef5b1b`.
All tasks are unchecked because acceptance must be reverified on the new base.
Each unestimated task has a maximum 2h budget; split larger work before coding.
Each original task uses the named suite in its wave plus the R2 behavior checks.
No task authorizes publication; release activation remains a maintainer action.

Each task names the test that proves it.

## Alignment prerequisite — before the original waves

- [ ] **R0 (1h)** Verify the issue and merged planning ancestry, then reconcile the
  candidate branch with merged 0013 and its predecessor. Preserve the foundation's
  real recordings and fixes. Proof: source diff, merge-base and task/scenario ledger.
- [ ] **R1 (2h)** Apply this proposal's package/ownership amendment using 0013's
  shared services and ports; keep public commands and financial math compatible.
  Proof: `tests/architecture/test_layering.py` plus the existing capability's
  CLI/contract tests on the new base; no new use cases in legacy facades.
- [ ] **R2 (2h)** Re-run affected behavior through the installed package and any
  exposed API/UI, all formats, dummy-secret checks and relevant real integration.
  Proof: named tests below, full `make check`, `make build`, `make audit` and a
  scenario-to-assertion report. Source-only UI checks or synthetic vendor fixtures
  cannot establish browser behavior or live vendor truth.

## Wave A — schema and repositories

- [ ] **A1. Migration v2** — portfolio, watchlist, goal, run and job tables inside
      the portable type set; application-generated ids; UTC timestamps; JSON as text.
      → `tests/contracts/test_portability.py`, `tests/integration/storage/test_migrations.py`
- [ ] **A2. Prior-state fixtures** — `tests/fixtures/schema/v1.sql` recorded by
      `scripts/schema_fixture.py`; every shipped version migrates to current intact,
      after a backup, with each migration logged at INFO.
      → `tests/integration/storage/test_migrations.py::test_fixture_database_migrates_to_current_intact`
- [ ] **A3. Repository protocols** — `PortfolioRepository`, `WatchlistRepository`,
      `GoalRepository`, `RunRepository`, `JobRepository` in `ports/storage.py`,
      implemented only under `adapters/`.
      → `tests/architecture/test_layering.py::test_db_drivers_imported_only_in_adapters`
- [ ] **A4. Conformance coverage** — every new repository joins the shared suite.
      → `tests/contracts/storage_conformance.py::ApplicationStateConformance`

## Wave B — CLI

- [ ] **B1. `sobres portfolio save|list|show|delete`** — weights validated before any
      write; name collision refused without `--force`; delete confirms.
      → `tests/cli/test_persistence.py`
- [ ] **B2. `sobres watchlist add|remove|list|show|delete`** — adding a present symbol
      is a no-op.
- [ ] **B3. `--portfolio <name>`** wherever `--tickers` is accepted; both → `UsageError`.
      → `tests/cli/test_persistence.py::test_portfolio_substitutes_for_tickers`
- [ ] **B4. `--save-run`** on the analytical commands: resolved parameters, estimators,
      window, result and a one-line summary.
      → `tests/cli/test_persistence.py::test_save_run_records_resolved_parameters`
- [ ] **B5. `sobres run list|show|diff|delete`** — newest first; `diff` refuses runs of
      different commands; every display carries the revision note.
- [ ] **B6. `sobres db info|export|repair`** — export via SQLite's backup API; repair
      recovers into a new file and leaves the original.
      → `tests/cli/test_persistence.py::test_db_export_and_repair`
- [ ] **B7. Cache and user data never conflated** — `sobres cache clear` reports what it
      removed and what it preserved.
      → `tests/contracts/storage_conformance.py::test_cache_clear_never_touches_user_rows`

## Definition of done

- [ ] Every scenario in the spec delta has a test referencing it
- [ ] `mypy --strict` clean; `pytest -m "not network"` green offline
- [ ] No module outside `adapters/storage/` imports a database driver

## Additional persistence acceptance

- [ ] **R3 (2h)** Transaction failure, migration ownership and live-WAL backup.
  Proof: `tests/contracts/storage_conformance.py` and
  `tests/integration/storage/test_migrations.py`; assert rollback leaves no partial
  portfolio/run writes and restores committed WAL data with another connection open.
