## Purpose

Keep Sobres aligned with a reviewed AISL template revision while preserving its
public interfaces, data integrity and ability to work without private services.

## ADDED Requirements

### Requirement: Auditable template adoption
Every template adoption SHALL record exact source revisions, implemented versus
proposed capabilities, project exceptions and impacts on active OpenSpecs.

#### Scenario: A proposed blueprint differs from the implemented template
- **WHEN** a package layout or hosted profile exists only in context proposals
- **THEN** its adoption SHALL be identified as a local proposed decision with an owner and tests
- **AND** it SHALL NOT be advertised as inherited working template functionality

#### Scenario: Pending milestones reference retired paths
- **WHEN** the common layout is amended before a pending milestone resumes
- **THEN** its proposal, design, tasks and scenarios SHALL agree on the new ownership and dependencies
- **AND** the impact inventory SHALL cover every open milestone and distinguish merged history

### Requirement: Compatible shared application boundary
The reorganized package SHALL preserve CLI names, aliases, defaults, validation,
results and supported imports while sharing application behavior across transports.

#### Scenario: Existing CLI after package migration
- **WHEN** the same command runs against identical fixtures, explicit clock/cache state and seed before and after migration
- **THEN** parsed values, units, ordering, exit code and state changes SHALL agree in all supported output formats
- **AND** only explicitly documented time/cache metadata differences SHALL be permitted

#### Scenario: Existing import after package migration
- **WHEN** a caller uses an established entry point or import path from the migrated foundation
- **THEN** it SHALL reach the same implementation through a compatibility facade
- **AND** no second implementation or duplicated command registration SHALL be created

#### Scenario: Framework-free application use
- **WHEN** a use case or neutral command declaration is imported without CLI/API adapters
- **THEN** it SHALL depend on owned interfaces and plain validated data, not transport contexts or concrete drivers
- **AND** architecture verification SHALL reject new adapter imports in core, ports or application code

#### Scenario: Administrative command has no HTTP exposure
- **WHEN** a local-only command is added to the registry
- **THEN** HTTP/UI exposure SHALL default to disabled
- **AND** future route generation SHALL require explicit approved exposure metadata

### Requirement: State preserved by structural migration
A package path migration SHALL NOT relocate user state, revise released schema
steps or weaken transaction, backup, currency or cache semantics.

#### Scenario: Existing SQLite state including WAL
- **WHEN** the reorganized foundation opens an existing database with committed WAL data
- **THEN** cached values and all user-authored state present in its schema SHALL remain intact
- **AND** backup/restore and cache-clear contracts SHALL preserve that user-authored state

#### Scenario: An unsupported backend is selected
- **WHEN** configuration names an adapter whose dependencies or implementation are unavailable
- **THEN** setup SHALL fail actionably without silently choosing SQLite or claiming data was migrated

#### Scenario: Another operational backend is proposed
- **WHEN** PostgreSQL or another operational engine is introduced later
- **THEN** its plan SHALL require real-engine behavioral contracts and data cutover/rollback evidence
- **AND** analytics, cache and vector capabilities SHALL NOT be assumed to satisfy operational transactions

### Requirement: Optional private context with public independence
The context lake SHALL be an optional pinned maintainer input. Normal builds,
checks, installation and artifact use SHALL work without private context access.

#### Scenario: Public clone omits the lake
- **WHEN** a clone has no initialized context submodule or credentials
- **THEN** documented setup, mandatory CI and package builds SHALL succeed using local standards
- **AND** context conformance SHALL be reported unverified without an automatic private fetch

#### Scenario: Maintainer updates the pin
- **WHEN** a maintainer explicitly updates context
- **THEN** the update SHALL select a reachable reviewed full commit and describe affected decisions
- **AND** reverting the pin SHALL restore the previous context without rewriting source history

#### Scenario: Artifact build from a populated maintainer checkout
- **WHEN** wheel, sdist, container or site artifacts are built with private context and dummy local state present
- **THEN** their content SHALL exclude private context bodies, credentials, databases, WAL files and derived indexes

### Requirement: Downstream ownership survives template updates
Template updates SHALL be reviewable changes that preserve Sobres-owned source,
specs, fixtures, identity, local rules and context pins.

#### Scenario: Template sync attempts to overwrite local policy
- **WHEN** an upstream update conflicts with the Sobres coverage threshold, review skill, OpenSpec config or package paths
- **THEN** the update SHALL require explicit reconciliation and SHALL NOT overwrite or auto-merge those files
- **AND** the resulting diff SHALL identify the template revision and project overrides

#### Scenario: Adoption rollback
- **WHEN** an infrastructure adoption is reverted
- **THEN** the prior development interface and pins SHALL be recoverable
- **AND** user databases, configuration and immutable released migrations SHALL remain untouched

### Requirement: Honest optional delivery profiles
Container, site, cloud and enterprise capabilities SHALL be owned by explicit
milestones and activated only after their applicable implementation and checks.

#### Scenario: Local development alignment is complete
- **WHEN** 0013's harness and package migration pass acceptance
- **THEN** Docker remains owned by 0005, the home page by 0006, and hosted profiles by later plans
- **AND** alignment SHALL NOT imply tenancy, a hosted SLA, cloud provisioning or publication
