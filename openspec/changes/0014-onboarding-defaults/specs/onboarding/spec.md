# Onboarding

## MODIFIED Requirements

### Requirement: `sobres init`

The installed CLI SHALL implement the specified onboarding behavior with actionable output and reliable process status. By default the guided walk SHALL cover only settings a user must supply themselves; every other declared setting SHALL remain reachable without a prompt.

#### Scenario: Guided, in the terminal
- **WHEN** `sobres init` runs in a TTY
- **THEN** it SHALL walk the non-advanced settings in registry order, showing each
  setting's description and where to obtain it, and prompt for a value
- **AND** it SHALL say how many advanced settings were not asked and how to set
  them
- **AND** secrets SHALL be entered without echo

#### Scenario: Advanced settings on request
- **WHEN** `sobres init --advanced` runs in a TTY
- **THEN** it SHALL walk every declared setting in registry order
- **AND** a setting given with `--set` SHALL be applied whether or not it is advanced

#### Scenario: Advanced settings survive a default run
- **WHEN** a configuration holds a value for an advanced setting and `sobres init`
  runs without `--advanced`
- **THEN** that value SHALL be neither prompted for nor changed

## ADDED Requirements

### Requirement: Settings declare a tier

Each declared setting SHALL state whether it is advanced. Exactly the settings a
new user cannot do without SHALL be non-advanced; in 0014 that is `fred_api_key`
alone.

#### Scenario: One essential setting
- **WHEN** the settings registry is inspected
- **THEN** exactly one setting SHALL be non-advanced, and it SHALL be `fred_api_key`
