# persistence — spec delta (0003)

## ADDED Requirements

### Requirement: Versioned schema with forward-only migrations

The database SHALL carry a schema version and upgrade itself on open.

#### Scenario: Automatic upgrade
- **WHEN** a database at an older schema version is opened
- **THEN** pending migrations SHALL run in order inside a single transaction
- **AND** `schema_version` SHALL be updated only if every one succeeded

#### Scenario: Backup before migrating
- **WHEN** a migration is about to run against an existing database
- **THEN** a timestamped consistent backup SHALL be written beside it first, including committed WAL data
- **AND** the copy's path SHALL be reported on stderr

#### Scenario: Newer database than the installed tool
- **WHEN** the database's schema version is higher than the running code knows
- **THEN** the system SHALL exit 3 telling the user to upgrade sobres
- **AND** SHALL NOT open the database, downgrade it, or write to it

#### Scenario: Migrations are tested against real prior states
- **WHEN** the test suite runs
- **THEN** a fixture database at every previously shipped schema version SHALL be
  migrated to current and asserted intact

#### Scenario: Forward-only
- **WHEN** a migration is written
- **THEN** it SHALL NOT be edited after release; a correction SHALL be a new
  migration

### Requirement: Saved portfolios

The system SHALL persist named weighted or unweighted portfolios and validate them before writing.

#### Scenario: Save
- **WHEN** `sobres portfolio save core --tickers AAPL MSFT --weights 0.6 0.4` runs
- **THEN** the portfolio SHALL persist under that name with its holdings
- **AND** weights SHALL be validated as in 0002 before anything is written

#### Scenario: Weights are optional
- **WHEN** a portfolio is saved with tickers but no weights
- **THEN** it SHALL persist as an unweighted universe, usable as the input to an
  optimization that will determine the weights

#### Scenario: Use a saved portfolio anywhere tickers are accepted
- **WHEN** any analytical command is given `--portfolio core`
- **THEN** it SHALL resolve to that portfolio's tickers and weights
- **AND** supplying both `--portfolio` and `--tickers` SHALL raise `UsageError`

#### Scenario: Name collision
- **WHEN** a portfolio is saved under an existing name without `--force`
- **THEN** the system SHALL refuse and say which name is taken

#### Scenario: Listing and deletion
- **WHEN** `sobres portfolio list` runs
- **THEN** each portfolio's name, holding count, and last-modified time SHALL print
- **AND** `sobres portfolio delete <name>` SHALL require confirmation unless `--yes`

### Requirement: Watchlists and goals

The system SHALL persist watchlist membership and goal inputs without presenting stored results as current calculations.

#### Scenario: Watchlist
- **WHEN** `sobres watchlist add tech NVDA AMD` runs
- **THEN** those symbols SHALL be added to the named watchlist, creating it if absent
- **AND** adding a symbol already present SHALL be a no-op, not an error

#### Scenario: Saved goals
- **WHEN** a goal is saved (the goal parameters specified in 0008)
- **THEN** it SHALL persist with its target, horizon, and assumptions
- **AND** re-running it later SHALL recompute against current data rather than
  replay the stored result

### Requirement: Analysis run history

The system SHALL record resolved analysis inputs and results and support honest retrieval and comparison.

#### Scenario: Recording a run
- **WHEN** an analytical command is invoked with `--save-run`
- **THEN** a run record SHALL persist with the command, its resolved parameters,
  the estimators used, the data window, a timestamp, and the result

#### Scenario: Resolved parameters, not raw argv
- **WHEN** a run is recorded
- **THEN** the stored parameters SHALL be the values actually used after defaults
  and config were applied
- **AND** a run recorded today SHALL remain interpretable after a default changes

#### Scenario: Inspecting runs
- **WHEN** `sobres run list` runs
- **THEN** id, command, timestamp, and a one-line result summary SHALL print
- **AND** `sobres run show <id> --format json` SHALL emit the complete stored record

#### Scenario: Comparing runs
- **WHEN** `sobres run diff <id-a> <id-b>` runs on two runs of the same command
- **THEN** parameter and result differences SHALL be shown side by side
- **AND** comparing runs of different commands SHALL raise `UsageError`

#### Scenario: Runs are not promises of reproducibility
- **WHEN** a stored run is displayed
- **THEN** the output SHALL state that upstream data may have been revised since,
  rather than implying the result can be regenerated identically

### Requirement: Database administration

Database commands SHALL provide inspection, consistent export and non-destructive recovery while protecting user-authored rows.

#### Scenario: Inspect
- **WHEN** `sobres db info` runs
- **THEN** the file path, schema version, total size, and per-table row counts and
  sizes SHALL print

#### Scenario: Export
- **WHEN** `sobres db export --to <path>` runs
- **THEN** a consistent copy SHALL be written using SQLite's backup API, safe to
  run while the database is in use

#### Scenario: Cache and user data are never conflated
- **WHEN** `sobres cache clear` runs
- **THEN** only cached provider observations SHALL be removed
- **AND** portfolios, watchlists, goals and runs SHALL be untouched
- **AND** the command SHALL report what it removed and what it preserved

#### Scenario: Destructive operations confirm
- **WHEN** any command would delete user-authored rows
- **THEN** it SHALL prompt for confirmation, with `--yes` for scripted use

#### Scenario: Repair
- **WHEN** `sobres db repair` runs on a database failing its integrity check
- **THEN** the system SHALL attempt recovery into a new file, leaving the original
  in place, and report what was and was not recovered

### Requirement: Repositories sit behind the storage port

User-state repositories SHALL expose domain operations through owned ports and common behavioral contracts.

#### Scenario: Backend-agnostic repositories
- **WHEN** a repository is defined for portfolios, watchlists, goals, runs, or jobs
- **THEN** it SHALL be a protocol in `ports/storage.py` with its
  implementation under `adapters/storage/`
- **AND** application/transport call sites SHALL NOT name a backend or construct a connection; composition SHALL select it

#### Scenario: New repositories join the conformance suite
- **WHEN** a repository is added
- **THEN** 0001's shared conformance suite SHALL gain coverage for it
- **AND** that coverage SHALL run against every registered adapter

#### Scenario: Portability guards apply to new tables
- **WHEN** a table is added for application state
- **THEN** it SHALL use only the portable type set, application-generated
  identifiers, explicit UTC timestamps, and JSON encoded as text

#### Scenario: Switching backends is configuration
- **WHEN** `SOBRES_DB_URL` names a different installed, supported operational backend
- **THEN** shared domain commands SHALL honor the same repository contracts
- **AND** engine-specific administration SHALL report supported operations explicitly
- **AND** the URL change SHALL NOT claim to transfer existing data; new adapters require
  conformance, migration, composition registration and dependency/doctor checks

### Requirement: Storage layer purity

Storage adapters SHALL perform persistence only, while financial core code SHALL remain independent of database I/O.

#### Scenario: Repositories perform no computation
- **WHEN** any module under `adapters/storage/` is reviewed
- **THEN** it SHALL contain persistence logic only
- **AND** SHALL NOT import financial computation functions from `sobres.core`; owned plain data types are permitted

#### Scenario: Core remains I/O-free
- **WHEN** any module under `core/` is reviewed
- **THEN** it SHALL NOT open a database connection or import `sqlite3`
- **AND** a test SHALL assert this by inspecting imports, so the rule is enforced
  rather than remembered

### Requirement: Observability of persistence

Persistence and migrations SHALL emit redacted diagnostic events through the shared adapter instrumentation.

#### Scenario: Operations are logged and spanned
- **WHEN** a repository operation runs
- **THEN** it SHALL emit a DEBUG record and a span carrying the operation, the
  entity, and the affected row count, per 0001's observability rules
- **AND** stored values SHALL be subject to the same redaction as any other
  logged data

#### Scenario: Migrations are visible
- **WHEN** a migration runs
- **THEN** each migration applied SHALL be logged at INFO with its version, and
  the backup path SHALL be logged at WARNING

### Requirement: Portability of the database file

A consistent SQLite backup SHALL preserve complete local application state across supported machines and containers.

#### Scenario: One file is the whole state
- **WHEN** a consistent SQLite backup is restored on another machine and
  `SOBRES_DB_URL` points at it
- **THEN** every saved portfolio, watchlist, goal, run and cached observation
  SHALL be available there

#### Scenario: The same file works in a container
- **WHEN** the file is mounted into the container built in 0005
- **THEN** it SHALL be used without conversion, and writes from the container
  SHALL be visible to the host CLI afterwards

### Requirement: Aligned development and application boundaries
This capability SHALL use the merged 0013 development contract and target
package ownership while preserving its domain scenarios and public CLI behavior.

#### Scenario: Capability resumes after the alignment migration
- **WHEN** implementation of this capability resumes on the aligned base
- **THEN** its use cases SHALL use shared application services and owned ports,
  with concrete I/O in adapters and financial computations in core
- **AND** its original scenarios and affected architecture/CLI checks SHALL pass
  against the installed package without private context access

#### Scenario: Capability is reviewed for another surface
- **WHEN** the capability is exposed through an API or UI
- **THEN** exposure SHALL be explicit and behavior SHALL use the same application
  service and validation contract as the CLI
- **AND** new settings/providers/dependencies SHALL include actionable doctor coverage

### Requirement: Adapter-owned migration and transaction semantics
Operational adapters SHALL own immutable migrations and expose explicit atomic
write behavior through the repository/unit-of-work contract.

#### Scenario: A multi-record write fails
- **WHEN** a unit of work fails after its first write but before commit
- **THEN** all its user-state writes SHALL roll back and a later operation SHALL remain usable
- **AND** the common suite SHALL assert resulting state, not adapter implementation details

#### Scenario: New engine versus existing SQLite lineage
- **WHEN** a future operational engine is introduced
- **THEN** existing SQLite migration IDs/content SHALL remain unchanged
- **AND** that engine's own migrations and data cutover SHALL require separate real-engine verification
