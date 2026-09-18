# options-hosting — delta (0018)

## ADDED Requirements

### Requirement: Persistent inexpensive cloud profile

The POC SHALL serve the existing SPA/API in a restricted Cloud Run profile with
durable operational state and immutable artifacts, without Cloud SQL or an active
SQLite database on ephemeral storage or a Cloud Storage mount.

#### Scenario: OH1 Restart and revision replacement
- **WHEN** the web service scales to zero, restarts or is replaced with another image revision
- **THEN** acknowledged users/configuration, recommendations, model versions, paper positions, job state, subscriptions and outbox records SHALL survive
- **AND** no writable local SQLite fallback SHALL be used for hosted authoritative state

#### Scenario: OH2 Scoped adapter conformance
- **WHEN** the same new operational-repository contract suite runs against SQLite and Firestore
- **THEN** transactions, contention, rollback, version checks, pagination, schema upgrades and restoration SHALL satisfy the same domain behaviors
- **AND** selecting the hosted profile SHALL not imply Firestore implements unrelated Sobres portfolio/broker repositories

#### Scenario: OH3 Verified artifacts and protected data
- **WHEN** a worker publishes or a user requests an artifact
- **THEN** immutable IDs, schema/hash verification, private authorization and licensed retention SHALL be enforced
- **AND** an incomplete upload or hash mismatch SHALL prevent publication/use rather than fall back to an unverified file

### Requirement: Durable bounded work outside web requests

Hosted research and notification execution SHALL not depend on an in-process
background thread or CPU allocated after an HTTP response.

#### Scenario: OH4 Dispatch interruption and lease recovery
- **WHEN** dispatch fails after durable enqueue, executions overlap, or a worker dies mid-run
- **THEN** reconciliation SHALL restart pending/reclaimable work and fencing SHALL reject stale-worker writes
- **AND** polling SHALL show durable progress/failure while retries remain bounded and publication stays idempotent

#### Scenario: OH5 Delays, cancellation and application quotas
- **WHEN** a scheduled scan misses its freshness deadline, a job is cancelled or scan/API/SMS budgets exhaust
- **THEN** the website SHALL show stale/cancelled/paused status and suppress affected new actionable entries or outbound messages
- **AND** the worker SHALL stop at a bounded checkpoint without losing the last complete result or disabling opt-out processing

### Requirement: Authenticated, reproducible deployment

The cloud profile SHALL have tested identity/role isolation, declared settings,
runtime secrets, health checks and a reproducible immutable-image deployment.

#### Scenario: OH6 Fresh-browser access and callback isolation
- **WHEN** an allowlisted user logs in, an unlisted user attempts access, or a callback/internal request presents a forged identity/signature
- **THEN** the service SHALL validate identity/audience/expiry and roles, admit only authorized research actions and reject forged callbacks/internal requests
- **AND** browser sessions SHALL use secure cookie/CSRF controls without a local shared-token bypass

#### Scenario: OH7 Deploy and diagnose the actual image
- **WHEN** the generated deployment is applied with the chosen project, region, digest, port, secrets and cost limits
- **THEN** the HTTPS app SHALL become reachable with working readiness checks, and doctor SHALL diagnose missing cloud/provider/auth prerequisites actionably without printing secrets
- **AND** recorded acceptance SHALL include a browser journey, bounded provider probe and consenting-recipient SMS, not only a successful container build

### Requirement: Recoverable user state and honest costs

The deployment SHALL include tested consistent backups, safe restoration and
measured cost controls with separately budgeted data and messaging.

#### Scenario: OH8 Restore without replaying messages or consent
- **WHEN** a consistent backup is restored into a fresh namespace
- **THEN** all required operational records and artifact references SHALL pass integrity checks and the paper journey SHALL work
- **AND** SMS SHALL remain disabled until current opt-outs and previously submitted/unknown messages are reconciled, with demonstrated 24h RPO/4h RTO targets or explicit failures

#### Scenario: OH9 Workload and billing disclosure
- **WHEN** deployment preflight or the first-week usage review runs
- **THEN** it SHALL show workload limits and separate hosting, storage/build/logging, market data and SMS cost assumptions against approved budgets
- **AND** it SHALL explicitly distinguish application quotas from non-capping billing alerts and disclose already-consumed free-tier allowances
