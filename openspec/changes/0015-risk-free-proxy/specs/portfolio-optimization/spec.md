# Portfolio optimization

## MODIFIED Requirements

### Requirement: Risk metrics

The system SHALL compute a standard risk panel from a return series, using a sourced risk-free proxy.

#### Scenario: Sharpe ratio definition
- **WHEN** Sharpe is computed
- **THEN** it SHALL be `mean(period_excess) / sample_std(period_excess) * sqrt(periods_per_year)`
- **AND** `period_excess = simple_return - annual_simple_risk_free_proxy / periods_per_year`
- **AND** arithmetic annual return and geometric CAGR SHALL be reported separately
- **AND** a USD computation SHALL obtain a dated proxy: FRED DTB3 when a key is configured and usable, otherwise the Ken French daily `RF` series; an explicit annual decimal override SHALL take precedence over both
- **AND** no computation SHALL substitute an assumed constant for a missing proxy
- **AND** DTB3 bank-discount yields SHALL be converted using a stated 91-day bill approximation, a 360-day discount year and 365-day simple investment yield, never described as realized Treasury returns

## ADDED Requirements

### Requirement: Automatic risk-free selection is announced and bounded

When the proxy is selected automatically, the command SHALL say so, and SHALL fail rather than guess when no proxy applies.

#### Scenario: Selection is announced
- **WHEN** the risk-free proxy is selected automatically
- **THEN** stderr SHALL carry one line naming the source, currency, coverage and summary rate, at the default log level
- **AND** the provenance notes SHALL carry the same facts
- **AND** stdout SHALL be unchanged across log levels

#### Scenario: No proxy for the currency
- **WHEN** the analysis currency is not USD and `--risk-free` is not given
- **THEN** the command SHALL exit 2 naming the currency and the flag

#### Scenario: Source does not cover the window
- **WHEN** the selected source has no observation on or before `start`
- **THEN** the command SHALL exit 5 naming the first available date
- **AND** no return date SHALL receive a zero rate
