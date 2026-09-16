# CLI shell

## MODIFIED Requirements

### Requirement: Error handling and exit codes

Failures SHALL exit with the documented code and SHALL tell the user what to do next. A usage error on a command that declares an example SHALL show that example.

#### Scenario: Exit code contract
- **WHEN** a command fails
- **THEN** the exit code SHALL be: `1` unexpected internal error, `2` bad usage,
  `3` missing configuration or credential, `4` provider/network failure,
  `5` insufficient data for the requested computation

#### Scenario: Actionable messages
- **WHEN** any error with code 3, 4, or 5 is raised
- **THEN** the message SHALL state what failed and the next action to take

#### Scenario: Usage errors show a worked example
- **WHEN** parameter validation fails for a command that declares an example
- **THEN** the hint SHALL begin with `try: sobres <example>` and still name `--help`

## ADDED Requirements

### Requirement: Commands with required parameters declare an example

Every registered command with at least one required parameter SHALL declare a
runnable example beginning with its own CLI name.

#### Scenario: Declaration is enforced
- **WHEN** the registry is inspected
- **THEN** every command with a required parameter SHALL have a non-empty example
  whose leading words are the command's CLI name

### Requirement: Opinionated date windows

Every command that accepts `--start` and `--end` SHALL run without either.

#### Scenario: Default window
- **WHEN** a window-taking command runs without `--start`
- **THEN** `start` SHALL be five years before `end`, and `end` SHALL default to
  today
- **AND** 29 February SHALL clamp to 28 February in a non-leap target year
- **AND** the resolved `start` and `end` SHALL appear in the result's provenance

#### Scenario: Explicit dates are untouched
- **WHEN** `--start` is given
- **THEN** no default SHALL apply and `end` before `start` SHALL remain a usage error
