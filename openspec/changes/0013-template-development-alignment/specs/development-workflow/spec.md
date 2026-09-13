## Purpose

Give Sobres contributors a repeatable, shared development process that catches
contract and packaging failures locally before a change reaches review.

## ADDED Requirements

### Requirement: Reproducible contributor setup
The repository SHALL provide a documented installation and checking interface
using pinned development dependencies and explicit environment execution.

#### Scenario: Setup in a fresh shell
- **WHEN** a contributor clones without private context and runs the documented setup twice
- **THEN** both runs SHALL succeed without shell activation, private credentials or production configuration
- **AND** subsequent check commands SHALL use that clone's environment and the recorded tool versions

#### Scenario: Package consumer needs no development tooling
- **WHEN** a user installs the built wheel with base dependencies outside the checkout
- **THEN** version, offline init/doctor and fixture-backed keyless data commands SHALL work
- **AND** Node, Make, uv, agent software, Git and private context SHALL NOT be runtime requirements

### Requirement: One complete quality gate
Local full verification and reusable CI SHALL enforce the same mandatory checks,
including 90% branch coverage, strict specs, formatting, lint, typing and artifacts.

#### Scenario: Fast iteration followed by full verification
- **WHEN** a contributor runs the affected-test shortcut and then prepares a PR
- **THEN** the shortcut SHALL be identified as partial verification
- **AND** full checking, build/install smoke tests and the dependency audit SHALL still be required

#### Scenario: Python formatting is stable
- **WHEN** an edited Python file is formatted with Black line length 100 and isort Black profile line length 100
- **THEN** a second pass SHALL leave it unchanged and local hooks and CI SHALL accept the same formatting
- **AND** incompatible duplicate formatting/import-order rules SHALL NOT require alternating edits

#### Scenario: A mandatory job is skipped
- **WHEN** a required CI job fails, is cancelled or is skipped
- **THEN** the required aggregate check SHALL fail
- **AND** release verification SHALL inherit the same mandatory quality checks

#### Scenario: Offline tests attempt an external connection
- **WHEN** an unmarked test attempts provider or external network access in the ordinary suite
- **THEN** verification SHALL fail instead of silently reaching a vendor
- **AND** explicitly enabled local test servers and deliberately selected live tests SHALL be distinct from vendor access

### Requirement: Shared agent procedures without duplicated bodies
Supported agents SHALL discover one shared instruction entry and the same
procedure/rule bodies, while runtime controls remain specific to each agent.

#### Scenario: Linked procedures in a real checkout
- **WHEN** a contributor opens a checkout with working Git symlinks in either agent
- **THEN** each supported procedure SHALL resolve to one repository-owned body
- **AND** the link check SHALL reject broken, escaping or duplicate procedure targets

#### Scenario: Platform cannot preserve links
- **WHEN** a checkout converts a required link into a plain text file
- **THEN** setup SHALL report the unsupported harness state and the documented checkout remedy
- **AND** normal package installation SHALL remain independent of agent discovery

#### Scenario: Sobres rules survive consolidation
- **WHEN** the shared harness replaces the large current instruction file
- **THEN** the review workflow, core purity, data/currency integrity, secret redaction,
  mandatory Python formatting and installation verification rules SHALL remain discoverable
- **AND** agent runtime hooks SHALL NOT be represented as universal enforcement

### Requirement: Issue and merged planning traceability
Implementation SHALL follow a linked issue and a separately merged planning PR
in the same repository's default branch, with matching change and task identifiers.

#### Scenario: Local planning has no published issue
- **WHEN** the user requests a local planning branch and commit only
- **THEN** planning SHALL proceed with unpublished issue/PR status recorded explicitly
- **AND** the artifact SHALL NOT claim a merged plan or authorize implementation

#### Scenario: Valid implementation lineage
- **WHEN** implementation names an issue and a planning PR merged into default main
- **THEN** the gate SHALL verify repository, target branch, merge state, ancestry and matching approved scope
- **AND** implementation SHALL NOT need a token spec edit merely to satisfy a changed-path heuristic

#### Scenario: Invalid or changed plan
- **WHEN** the issue is absent, the plan is unmerged, belongs to another repository,
  targets another branch, is not an ancestor, or acceptance criteria change with implementation
- **THEN** the gate SHALL reject it with the specific missing planning step

#### Scenario: Production code bundled with a planning PR
- **WHEN** a PR declares itself planning but includes application feature implementation
- **THEN** the gate SHALL require the feature code to move to a later implementation PR

#### Scenario: Untrusted head edits the checker
- **WHEN** a fork changes its policy checker or PR metadata attempts to bypass validation
- **THEN** validation SHALL use trusted base policy and read-only metadata access
- **AND** no privileged credential SHALL execute code from the untrusted head

#### Scenario: Exception label without a reason
- **WHEN** a maintenance or template-sync PR supplies a bypass label alone
- **THEN** it SHALL NOT satisfy the planning exception requirement
- **AND** an exception SHALL require recorded maintainer-controlled scope and a substantive reason

### Requirement: Small review units and honest evidence
Tasks SHALL be sized at no more than approximately two hours with a named proof;
implementation PRs SHALL map coherent task commits to their tests and changelog.

#### Scenario: A capability spans multiple independent tasks
- **WHEN** work exceeds the usual one-to-three-task or roughly 300-line review target
- **THEN** the contributor SHALL split independent work or document an atomicity reason
- **AND** tests SHALL stay with their implementation

#### Scenario: An open branch reports completed tasks
- **WHEN** an existing stacked PR's tasks are reused in an amended plan
- **THEN** branch-local claims SHALL be distinguished from merged and reverified behavior
- **AND** new or changed acceptance obligations SHALL remain unchecked until tested on the new base

#### Scenario: Optional integration unavailable
- **WHEN** private lake access, an opted-out AI reviewer or an optional service is unavailable
- **THEN** its conformance check SHALL be reported unavailable or disabled explicitly
- **AND** mandatory public checks SHALL remain usable without that credential
