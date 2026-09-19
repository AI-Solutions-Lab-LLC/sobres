# options-hosting — delta (0018)

## ADDED Requirements

### Requirement: Persistent inexpensive cloud profile

The POC SHALL serve the existing SPA/API in a restricted Cloud Run profile with
durable operational state and immutable artifacts, without Cloud SQL or an active
SQLite database on ephemeral storage or a Cloud Storage mount.

#### Scenario: OH1 Restart and revision replacement
- **WHEN** the web service scales to zero, restarts or is replaced with another image revision
- **THEN** acknowledged users/configuration, recommendations, model versions, paper positions and job state SHALL survive
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

Hosted research execution SHALL not depend on an in-process
background thread or CPU allocated after an HTTP response.

#### Scenario: OH4 Dispatch interruption and lease recovery
- **WHEN** dispatch fails after durable enqueue, executions overlap, or a worker dies mid-run
- **THEN** reconciliation SHALL restart pending/reclaimable work and fencing SHALL reject stale-worker writes
- **AND** polling SHALL show durable progress/failure while retries remain bounded and publication stays idempotent

#### Scenario: OH5 Delays, cancellation and application quotas
- **WHEN** a scheduled scan misses its freshness deadline, a job is cancelled or scan/API budgets exhaust
- **THEN** the website SHALL show stale/cancelled/paused status and suppress affected new actionable entries
- **AND** the worker SHALL stop at a bounded checkpoint without losing the last complete result

### Requirement: Authenticated, reproducible deployment

The cloud profile SHALL have tested identity/role isolation, declared settings,
runtime secrets, health checks and a reproducible immutable-image deployment.

#### Scenario: OH6 Fresh-browser access and internal-request isolation
- **WHEN** an allowlisted user logs in, an unlisted user attempts access, or an internal request presents a forged identity/signature
- **THEN** the service SHALL validate identity/audience/expiry and roles, admit only authorized research actions and reject forged internal requests
- **AND** browser sessions SHALL use secure cookie/CSRF controls without a local shared-token bypass

#### Scenario: OH7 Deploy and diagnose the actual image
- **WHEN** the saved Terraform plan is applied through `deploy cloud-run apply` with the chosen project, region, digest, port, secret names and cost limits
- **THEN** the HTTPS app SHALL become reachable with working readiness checks, and doctor SHALL diagnose missing cloud/provider/auth prerequisites actionably without printing secrets
- **AND** recorded acceptance SHALL include a browser journey and bounded provider probe, not only a successful container build

### Requirement: Recoverable user state and honest costs

The deployment SHALL include tested consistent backups, safe restoration and
measured cost controls with separately budgeted market data.

#### Scenario: OH8 Restore into a fresh namespace
- **WHEN** a consistent backup is restored into a fresh namespace
- **THEN** all required operational records and artifact references SHALL pass integrity checks and the paper journey SHALL work
- **AND** the restoration SHALL demonstrate the 24h RPO/4h RTO targets or report explicit failures

#### Scenario: OH9 Workload and billing disclosure
- **WHEN** deployment preflight or the first-week usage review runs
- **THEN** it SHALL show workload limits and separate hosting, storage/build/logging and market data cost assumptions against approved budgets
- **AND** it SHALL explicitly distinguish application quotas from non-capping billing alerts and disclose already-consumed free-tier allowances

### Requirement: Terraform-managed infrastructure through the CLI

Hosted resources SHALL be created, changed and destroyed only by Terraform invoked
from the terminal-only `deploy cloud-run` commands, with `gcloud` and Terraform
prerequisites diagnosed before any plan runs and secret values never handled by
the CLI or by Terraform.

#### Scenario: OH10 Plan then apply the saved plan
- **WHEN** an operator runs `deploy cloud-run plan` and then `deploy cloud-run apply`
- **THEN** the CLI SHALL first verify `gcloud` authentication, project, the pinned Terraform version and the remote state bucket, write a saved plan with a resource summary, and apply exactly that plan
- **AND** an apply without a saved plan, with a stale plan, against local state, or issued through HTTP SHALL be refused with an actionable reason

#### Scenario: OH11 Destroy through the CLI protects data
- **WHEN** an operator runs `deploy cloud-run destroy` for an environment
- **THEN** the CLI SHALL print every resource the destroy plan removes, require the project ID typed back, and leave the artifact bucket, backup bucket, Firestore database and state bucket in place
- **AND** those data resources SHALL be removed only with `--include-data`, a second typed confirmation and a recorded verified export, after which a further plan SHALL report nothing left to destroy

#### Scenario: OH12 Secrets by name only
- **WHEN** doctor, plan or apply runs with a required Secret Manager secret missing, or with one present whose value was added by the owner through `gcloud secrets`
- **THEN** the missing secret SHALL be reported with the exact `gcloud secrets create` and `versions add` commands as its fix, and the present secret SHALL be referenced by name in Terraform and the runtime binding
- **AND** no secret value SHALL be read, printed, placed in Terraform variables, outputs or state, or accepted as a CLI argument
