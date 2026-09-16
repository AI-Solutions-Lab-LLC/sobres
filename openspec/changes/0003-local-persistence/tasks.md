# 0003 — Tasks

Planning amendment: source PR #9 at `20654c1249aa7de32e3c35dbaa346c6929ef5b1b`.
Checked tasks are proven by the named tests on `main` (2026-09-16 reconciliation).
Each unestimated task has a maximum 2h budget; split larger work before coding.
No task authorizes publication; release activation remains a maintainer action.

Each task names the test that proves it.

## Alignment prerequisite — removed 2026-09-16

The R0/R1/R2 tasks that required implementing 0013 before this capability could be
accepted were removed when 0013 was superseded (see its proposal). The shipped code
lives in `core/`, `data/`, `cli/` and `api/`, the layout enforced by
`tests/architecture/test_layering.py`; the domain tasks below are checked against the
tests that actually prove them on `main`.

## Wave A — schema and repositories

- [x] **A1. Migration v2** — portfolio, watchlist, goal, run and job tables inside
      the portable type set; application-generated ids; UTC timestamps; JSON as text.
      → `tests/data/test_portability.py`, `tests/data/test_migrations.py`
- [x] **A2. Prior-state fixtures** — `tests/fixtures/schema/v1.sql` recorded by
      `scripts/schema_fixture.py`; every shipped version migrates to current intact,
      after a backup, with each migration logged at INFO.
      → `tests/data/test_migrations.py::test_fixture_database_migrates_to_current_intact`
- [x] **A3. Repository protocols** — `PortfolioRepository`, `WatchlistRepository`,
      `GoalRepository`, `RunRepository`, `JobRepository` in `data/storage/base.py`,
      implemented only under `data/storage/adapters/`.
      → `tests/architecture/test_layering.py::test_db_drivers_imported_only_in_adapters`
- [x] **A4. Conformance coverage** — every new repository joins the shared suite.
      → `tests/data/storage_conformance.py::ApplicationStateConformance`

## Wave B — CLI

- [x] **B1. `sobres portfolio save|list|show|delete`** — weights validated before any
      write; name collision refused without `--force`; delete confirms.
      → `tests/cli/test_persistence.py`
- [x] **B2. `sobres watchlist add|remove|list|show|delete`** — adding a present symbol
      is a no-op.
- [x] **B3. `--portfolio <name>`** wherever `--tickers` is accepted; both → `UsageError`.
      → `tests/cli/test_persistence.py::test_portfolio_substitutes_for_tickers`
- [x] **B4. `--save-run`** on the analytical commands: resolved parameters, estimators,
      window, result and a one-line summary.
      → `tests/cli/test_persistence.py::test_save_run_records_resolved_parameters`
- [x] **B5. `sobres run list|show|diff|delete`** — newest first; `diff` refuses runs of
      different commands; every display carries the revision note.
- [x] **B6. `sobres db info|export|repair`** — export via SQLite's backup API; repair
      recovers into a new file and leaves the original.
      → `tests/cli/test_persistence.py::test_db_info_export_and_repair`
- [x] **B7. Cache and user data never conflated** — `sobres cache clear` reports what it
      removed and what it preserved.
      → `tests/data/storage_conformance.py::test_cache_clear_never_touches_user_rows`

## Definition of done

- [x] Every scenario in the spec delta has a test referencing it
- [x] `mypy --strict` clean; `pytest -m "not network"` green offline
- [x] No module outside `data/storage/adapters/` imports a database driver

## Additional persistence acceptance

- [x] **R3 (2h)** Transaction failure, migration ownership and live-WAL backup.
  Proof: `tests/data/storage_conformance.py::test_transaction_rolls_back_as_a_unit`
  (no partial kv/observation writes survive an aborted unit; the next unit works),
  `tests/data/test_migrations.py::test_migrations_are_forward_only_and_contiguous`
  (adapter-owned, immutable migration ids) and
  `tests/data/test_storage_port.py::test_backup_contains_committed_wal` (a backup taken
  with another connection open carries the committed WAL data).
