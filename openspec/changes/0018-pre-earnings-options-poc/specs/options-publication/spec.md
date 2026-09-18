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
durable revision pointers and alert intents only after evidence artifacts exist.

#### Scenario: OP3 Publish, promote and roll back
- **WHEN** an owner promotes a passing evaluated version or rolls back to a previously passing compatible version
- **THEN** the system SHALL pin the exact model/data/config evidence, record the actor/reason and create one logical model-change event
- **AND** a retraining run alone SHALL neither promote the model nor send a model-change alert

#### Scenario: OP4 Revision, expiry and stale inputs
- **WHEN** a recommendation changes materially, expires, loses required fresh inputs or is invalidated by an event revision
- **THEN** its current link SHALL show the latest state and retained revision history
- **AND** expired/stale candidates SHALL not appear actionable, and eligible subscribers SHALL receive the corresponding configured state-change intent

#### Scenario: OP5 Crash during publication
- **WHEN** a process dies after artifact upload or after committing a revision but before notification dispatch
- **THEN** readers SHALL see either the prior complete revision or the new complete revision, never a pointer to unverified content
- **AND** orphan cleanup and outbox replay SHALL recover without duplicate logical publication events

### Requirement: Consented and bounded SMS

SMS SHALL require verified recipient consent, a permitted registered sender,
subscription preferences, and an enforced application segment budget.

#### Scenario: OP6 Recipient subscribes or opts out
- **WHEN** a verified recipient opts in or a signed STOP/opt-out callback arrives
- **THEN** consent provenance/preferences SHALL be stored durably, STOP SHALL cancel queued sends and prevent subsequent dispatch, and any resubscription SHALL require fresh consent
- **AND** provider-managed opt-out confirmation MAY follow the provider's policy without re-enabling research messages

#### Scenario: OP7 Duplicate, uncertain or failed send
- **WHEN** workers race, a provider callback repeats, or a submission times out after the provider may have accepted it
- **THEN** transactional claims SHALL prevent duplicate local submissions, callbacks SHALL be idempotent, and uncertain sends SHALL stay unknown pending reconciliation
- **AND** the system SHALL not blindly resend an uncertain non-idempotent submission or claim delivered without delivery evidence

#### Scenario: OP8 Notification meaning and cost ceiling
- **WHEN** a new eligible recommendation, material revision, exit reminder or promoted-model event matches a subscription
- **THEN** the text SHALL identify the event/model and as-of state with a link to full evidence, honor recipient quiet-hour/digest preferences and show delivery status in the app
- **AND** duplicate/no-change scans SHALL create no new message; exhausted segment budgets SHALL suppress additional sends with a visible reason while preserving opt-out processing

#### Scenario: OP9 Secret and recipient privacy
- **WHEN** commands, jobs, callbacks or failures run at any supported log level
- **THEN** dummy sentinel credentials, full phone numbers and private message bodies SHALL not appear in results, logs, traces or downloadable shared reports
- **AND** recipient access SHALL be restricted to the authorized owner and recipient workflow
