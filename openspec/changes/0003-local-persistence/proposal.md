---
change: 0003-local-persistence
milestone: v1.1
depends_on: [0001-foundation-data-and-cli, 0002-portfolio-optimization, 0013-template-development-alignment]
status: proposed
---

# 0003 — Local persistence

## Outcome

Work stops being disposable. Portfolios, watchlists, goals and every analysis run
are saved and recallable, from the CLI now and from the UI in 0004:

```bash
sobres portfolio save core --tickers AAPL MSFT NVDA JNJ --weights 0.3 0.3 0.2 0.2
sobres optimize markowitz --portfolio core --save-run
sobres run list --limit 20
sobres run show 42 --format json
sobres db info
sobres db export --to ~/backups/sobres-2026-09-12.sqlite
```

## Why

0002 makes the tool useful; this makes it *cumulative*. Re-typing eight tickers
and a constraint set on every invocation is the difference between a demo and
something used weekly.

It is also the prerequisite for everything after it. The UI in 0004 needs saved
state to show and a job table to report progress from; the Docker deployment in
0005 needs exactly one thing to mount as a volume. Building those on ad-hoc files
would mean two storage stories to reconcile later.

0001 already established the single SQLite file. This change turns it from a
cache into a database: schema versioning, migrations, and the application tables.

## What changes

- **New capability `persistence`.**
- `adapters/storage/migrations/` retains SQLite's forward-only migration lineage,
  keyed on `schema_version` and applied by its adapter. Future operational engines
  own their migration implementation and must satisfy the same behavioral contracts.
- `ports/storage.py` gains repository protocols for portfolios, watchlists, goals,
  analysis runs and job records, behind 0001's storage port. Plain data in, plain
  data out; no math, and no driver import outside the adapters.
- The conformance suite from 0001 grows to cover the new repositories, so a
  future backend is still proven by one shared suite rather than by inspection.
- **New CLI groups** `sobres portfolio`, `sobres watchlist`, `sobres run`, and `sobres db`.
- `--save-run` on the analytical commands; `--portfolio <name>` accepted wherever
  `--tickers` is, so saved state substitutes for typing.

## Non-goals

- **No multi-user data model.** One database is one person's data. Adding a
  `user_id` column "just in case" would shape every query for a use case that is
  explicitly out of scope (see 0004's access model).
- **No second backend is implemented here either.** 0001 ships the port, the
  registry, and the conformance suite; this change adds repositories behind them.
  A PostgreSQL operational adapter remains a later change requiring real-engine
  conformance, migration and cutover/rollback evidence. DuckDB is a separate
  analytical capability, not a substitute for transactional application state.
- No cloud sync. Running against a remote backend becomes possible through the
  port, but nothing in this change assumes or requires it.
- No ORM. SQLAlchemy Core sits below the repositories as the dialect layer; object
  mapping would hide the migration story that has to stay legible.
- No automatic scheduled refresh of saved portfolios. That is a cron job the user
  writes with the CLI they already have.
- No encryption at rest. The file holds public market data and the user's own
  ticker lists; a keyed database would add a lost-password failure mode for no
  real confidentiality gain. API keys stay in the config file at mode `0600`,
  never in the database.

## Risks

| Risk | Mitigation |
|---|---|
| A migration corrupts real user data | Forward-only, tested against fixture databases at every prior schema version; automatic timestamped backup before any migration; `sobres db export` for a manual copy first |
| Schema churn during 0004 and 0005 makes migrations painful early | Version from the first release; treat every shipped schema as immutable even pre-1.0, since the cost of the discipline is far below the cost of a user's lost portfolios |
| CLI and server write concurrently and one wedges | WAL plus a busy timeout from 0001; writes are short transactions; the job table is the only hot row and is written by a single worker |
| The database grows without bound as price history accumulates | `sobres db info` reports size by table; `sobres cache clear` prunes cached observations while leaving user-authored rows untouched — the two must never be conflated |
| Repositories accrete SQLite-shaped assumptions now that there is real application state | Every repository is added to the shared conformance suite as it is written, and the portability guards from 0001 (portable types, application-generated ids, explicit UTC, JSON as text) apply to every new table |
| Saved runs reference market data that later gets revised | A run records the inputs and the resolved parameters it used, so it stays interpretable; it is a record of an analysis, not a promise of reproducibility against a mutable index |

## Development alignment and review readiness (0013)

Define user-state ports in `ports/storage.py`, use cases in `application/`, and concrete SQLite migrations/repositories in `adapters/storage/`. Preserve immutable migration IDs, WAL-safe backup and transaction rollback. PostgreSQL needs its own later real-engine and data-cutover plan; DuckDB is analytics, not an operational substitute.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #9 at `20654c1249aa7de32e3c35dbaa346c6929ef5b1b` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge is PR #33 (`b9792d7`).
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#25](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/25).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. The plan merged in PR #33 at `b9792d72dad7217f7bb642c0c90a668afc501087`;
the 0013 package migration remains unimplemented.
