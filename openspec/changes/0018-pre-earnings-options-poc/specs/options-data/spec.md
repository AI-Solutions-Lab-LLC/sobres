# options-data — delta (0018)

## ADDED Requirements

### Requirement: Entitled point-in-time inputs

The system SHALL admit data for strategy validation only when its contract fields,
historical coverage, timestamps and usage rights are recorded and verified.

#### Scenario: OD1 Cheap data without historical quotes
- **WHEN** a configured plan provides aggregate prices or current IV but lacks historical bid/ask
- **THEN** validation SHALL report the missing capability and prohibit execution-quality backtests with that source
- **AND** available data MAY support clearly labelled parser/demo research without a profitability claim

#### Scenario: OD2 Replaying event and feature availability
- **WHEN** earnings timing or a feature is revised or first collected after a historical decision cutoff
- **THEN** replay SHALL use only the version available at that cutoff
- **AND** unprovable historical confirmation SHALL be excluded with a reason and counted in coverage

#### Scenario: OD3 Imported data and provider failure
- **WHEN** an entitled file import or API request is ingested, retried, rate-limited or denied
- **THEN** the adapter SHALL preserve provider identity, licensing/entitlement metadata, timestamps and content hashes, deduplicate safely, and expose actionable retry/credential errors
- **AND** cached and refreshed runs over the same pinned revision SHALL produce equivalent normalized observations without replacing missing values silently

### Requirement: Contract and observation fidelity

The system SHALL preserve option identity, quote quality, currency, corporate actions
and missingness independently from requested date coverage.

#### Scenario: OD4 Adjusted or illiquid contract
- **WHEN** a pair has an adjusted deliverable, unsupported exercise/settlement convention, non-USD quote, zero/crossed/stale bid, unknown multiplier or insufficient displayed size
- **THEN** the baseline SHALL reject it with the specific reason rather than assume a standard usable contract

#### Scenario: OD5 Held pair survives an ATM change
- **WHEN** the underlying moves so another strike becomes ATM during a backtest
- **THEN** holdings and realized P&L SHALL continue to use the original call/put IDs
- **AND** feature-surface re-centering SHALL be identified separately from position valuation

#### Scenario: OD6 Optional feature unavailable
- **WHEN** a social, news, skew, VIXEQ or all-time-high feature is unavailable, unlicensed, stale or lacks history
- **THEN** it SHALL be marked unavailable, never zero or fabricated
- **AND** a model requiring that feature SHALL abstain while an independently validated compatible baseline MAY still run

### Requirement: Reproducible input manifests

Every research run SHALL pin the data, calendar, model, configuration, code and
normalization versions needed to reproduce its output.

#### Scenario: OD7 Dataset later changes
- **WHEN** a vendor revises history after a saved run
- **THEN** replay with the original manifest SHALL resolve the original retained inputs and reproduce the original numerical output
- **AND** a new revision SHALL create a distinct manifest with explicit differences

#### Scenario: OD8 IV cannot be computed honestly
- **WHEN** an IV solver lacks dividend/rate/exercise inputs, violates price bounds or fails to converge
- **THEN** the result SHALL be unavailable with a diagnostic, not a zero/default IV
- **AND** its provider or solver convention SHALL remain visible in every dependent feature
