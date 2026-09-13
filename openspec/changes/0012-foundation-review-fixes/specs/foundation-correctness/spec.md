# Foundation correctness

## ADDED Requirements

### Requirement: Secret-valued config logging

A generic config command containing a declared secret SHALL redact its value in
every diagnostic sink, using the setting's secret declaration.

#### Scenario: Secret-valued config logging
- **WHEN** a secret is passed to `config set` at INFO or DEBUG
- **THEN** the full secret SHALL be absent from stderr and the log file
- **AND** nonsensitive setting values SHALL remain useful in diagnostics

### Requirement: Opaque cached factor identifiers

Shared caches SHALL preserve dataset identifiers exactly.

#### Scenario: Opaque cached factor identifiers
- **WHEN** FF3, FF5, or FF5+MOM factors are read directly and through cold/warm caches
- **THEN** every column and value SHALL match, including `Mkt-RF`
- **AND** caching SHALL NOT introduce missing values

### Requirement: Consistent migration backup

A pre-migration backup SHALL restore all committed rows, including data in WAL.

#### Scenario: Consistent migration backup
- **WHEN** another connection has committed rows in WAL and a backup is created
- **THEN** opening the standalone backup SHALL return those rows without requiring
  any original sidecar

### Requirement: Base install price dependency

The base distribution SHALL include all dependencies needed for keyless prices.

#### Scenario: Base install price dependency
- **WHEN** the built wheel is installed without optional extras
- **THEN** the Yahoo client SHALL import and the normal live price path SHALL be
  available without another installation

### Requirement: Empty optional wizard input

The real terminal wizard SHALL accept empty answers for optional settings.

#### Scenario: Empty optional wizard input
- **WHEN** a user presses Enter at an optional setting with no stored value
- **THEN** the wizard SHALL advance without forcing a key or repeating the prompt

### Requirement: Missing observation replacement

The cache SHALL preserve explicit missing dates and replace withdrawn values
within a fetched interval. Missing values SHALL remain missing, never filled by
the cache.

#### Scenario: Missing observation replacement
- **WHEN** a refresh changes a number to NaN or omits a previously stored date
- **THEN** the old number SHALL NOT survive
- **AND** missing dates SHALL remain distinguishable
- **AND** unrelated intervals SHALL remain unchanged

### Requirement: Empty calendar tail reuse

A validated ticker with no observations in a calendar interval SHALL NOT become
an unknown symbol. An unvalidated empty response SHALL remain a provider failure.

#### Scenario: Empty calendar tail reuse
- **WHEN** cached weekday prices are extended through a weekend or holiday
- **THEN** existing weekday data SHALL be returned
- **AND** a repeated empty-tail request SHALL use the fetch log without another fetch
- **AND** metadata from the cached history SHALL be retained

### Requirement: Complete conversion metadata

Conversion SHALL validate every column's currency before its no-conversion shortcut.

#### Scenario: Complete conversion metadata
- **WHEN** currency metadata is absent or omits any column
- **THEN** conversion SHALL raise a domain error
- **AND** SHALL NOT relabel unknown units as the requested currency

### Requirement: Init health status propagation

Initialization SHALL repair config permissions and return the closing doctor
failure status to the process.

#### Scenario: Init health status propagation
- **WHEN** initialization finds insecure config permissions or a failing health check
- **THEN** config permissions SHALL become 0600 on POSIX
- **AND** the process exit SHALL match the reported closing doctor failure status

### Requirement: Negative boolean options

Generated boolean parameters SHALL allow both selections and preserve their default.

#### Scenario: Negative boolean options
- **WHEN** `init --no-verify --offline` is parsed
- **THEN** verification SHALL be disabled
- **AND** the command SHALL NOT fail with an unknown option
