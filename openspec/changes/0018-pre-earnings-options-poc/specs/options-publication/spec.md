# options-publication — delta (0018)

## ADDED Requirements

### Requirement: Shared research interface and explicit permissions

Commands SHALL be declared once and exposed through profile-aware CLI/API/UI
projections using the same model validation, numerical results and reason codes.

#### Scenario: OP1 Candidate evidence across surfaces
- **WHEN** a user inspects a candidate or recommendation via CLI table/json/csv or the authenticated website
- **THEN** event/session, contracts, quote as-of/delay, straddle mid, heuristic implied move, completed earnings-move history, IV/regime/technical features, eligibility reasons, max debit/loss, exit deadline, model version and historical evidence SHALL agree across surfaces
- **AND** unavailable inputs and stale/unvalidated status SHALL remain visible, with a research disclaimer that does not corrupt machine-readable formats

#### Scenario: OP2 Hosted exposure and role enforcement
- **WHEN** a viewer or unauthenticated caller guesses a promotion, deployment, broker, full settings or unsupported local-only route
- **THEN** the hosted profile SHALL reject the request before any side effect, credential disclosure or local database creation
- **AND** schemas/forms SHALL expose only the caller's permitted profile capabilities

### Requirement: Durable versioned publication

Recommendation publication and owner model promotion SHALL atomically update
durable revision pointers only after evidence artifacts exist.

#### Scenario: OP3 Publish, promote and roll back
- **WHEN** an owner promotes a passing evaluated version or rolls back to a previously passing compatible version
- **THEN** the system SHALL pin the exact model/data/config evidence, record the actor/reason and create one logical model-change event
- **AND** a retraining run alone SHALL neither promote the model nor create a model-change event

#### Scenario: OP4 Revision, expiry and stale inputs
- **WHEN** a recommendation changes materially, expires, loses required fresh inputs or is invalidated by an event revision
- **THEN** its current link SHALL show the latest state and retained revision history
- **AND** expired/stale candidates SHALL not appear actionable, and the state change SHALL appear in the recommendation's retained history

#### Scenario: OP5 Crash during publication
- **WHEN** a process dies after artifact upload but before the revision pointer commits
- **THEN** readers SHALL see either the prior complete revision or the new complete revision, never a pointer to unverified content
- **AND** orphan cleanup SHALL recover without duplicate logical publication events

### Requirement: Secret privacy

Credentials SHALL never appear in results, logs, traces or shared reports at any
supported log level.

#### Scenario: OP6 Secret privacy
- **WHEN** commands, jobs or failures run at any supported log level
- **THEN** dummy sentinel credentials SHALL not appear in results, logs, traces or downloadable shared reports
- **AND** evidence downloads SHALL be restricted to authorized workspace members
