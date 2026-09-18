# options-backtesting — delta (0018)

## ADDED Requirements

### Requirement: Executable returns and failure accounting

Backtests SHALL produce an auditable event ledger and chronological cash/position
ledger with observed quotes, commissions, spreads, missingness and overlap limits.

#### Scenario: OB1 Independently known P&L
- **WHEN** two pairs enter at asks 6+6, exit at bids 7+6, have multiplier 100 and commission $0.65 per contract-side
- **THEN** conservative gross P&L SHALL be $200 and net P&L $194.80
- **AND** if each leg-side spread is $0.20, additional half-spread stress SHALL yield $114.80 net, without charging the baseline spread twice

#### Scenario: OB2 Missing exit or halted position
- **WHEN** an entered pair lacks an executable pre-event exit, including a halt or unexpected announcement
- **THEN** the run SHALL retain that event as unresolved/breached, include its full-debit-loss downside bound, and block promotion
- **AND** it SHALL not delete the loss, forward-fill a fictional execution, or substitute a post-announcement price as a successful pre-event exit

#### Scenario: OB3 Overlapping portfolio and cost comparisons
- **WHEN** multiple events compete for capital or the report compares midpoint, ask-to-bid and adverse half-spread fills
- **THEN** each result SHALL identify its execution/cost assumptions and apply the same deterministic allocations and fee rules appropriate to that variant
- **AND** portfolio returns/drawdown SHALL include idle cash, open liquidation values and blocked trades, separate from equal-unit event returns

### Requirement: Leakage-resistant model evaluation

Every promotable strategy, overlay or learned model SHALL have chronological
out-of-sample evaluation with fixed trial records and uncertainty estimates.

#### Scenario: OB4 Purged season evaluation
- **WHEN** strategy thresholds, scalers, ridge penalties or overlays are chosen
- **THEN** selection SHALL use training/inner-validation data only, purge overlapping holding/label intervals, apply the declared embargo and preserve an untouched final block
- **AND** all attempted variants and train/validation/test boundaries SHALL be persisted

#### Scenario: OB5 Overlay fails to add value
- **WHEN** an overlay is redundant, unavailable, unstable across two seasons or fails the same-event conservative comparison
- **THEN** the report SHALL retain its failed result and prohibit promoting it as an improvement
- **AND** no sentiment or regression output SHALL override timing, liquidity, budget or event-confirmation gates

#### Scenario: OB6 Insufficient or negative evidence
- **WHEN** any frozen promotion gate fails, including sample size, unresolved exits, positive conservative confidence bound, stress result, season consistency or drawdown
- **THEN** evidence SHALL be published as rejected/inconclusive with failing gates
- **AND** actionable recommendation publication SHALL remain disabled for that version, while research/demo views stay usable

### Requirement: Reproducible complete reporting

Reports SHALL expose sample exclusions, uncertainty, baselines, drawdowns and worst
events, rather than only favorable summary returns.

#### Scenario: OB7 Complete evidence and replay
- **WHEN** a backtest finishes or is replayed with its pinned manifest and seed
- **THEN** it SHALL provide the same numerical ledgers, uncertainty calculations and evaluation partitions, with runtime metadata separated
- **AND** include attempted/filled/resolved counts, exclusion reasons, cash baseline, conservative/mid/stress and T-1/T-2 comparisons, worst ten events and IVR/VIX/correlation/high-low/attention segments with sample sizes

#### Scenario: OB8 Correct annualization and learning labels
- **WHEN** annualized portfolio statistics or learned return forecasts are displayed
- **THEN** annualization SHALL use daily equity and shared conventions, and forecasts SHALL show held-out error/calibration and prediction uncertainty
- **AND** training performance, synthetic fixtures and retrospective event discovery SHALL never be labelled validated live or out-of-sample evidence
