# earnings-options — delta (0018)

## ADDED Requirements

### Requirement: Explicit pre-announcement strategy

The initial strategy SHALL use the frozen ATM-straddle algorithm in `design.md`,
version every timing/selection/threshold change, and prohibit planned exposure
through earnings. Alternative structures SHALL remain unavailable until specified
and independently validated.

#### Scenario: EO1 Baseline entry and exit
- **WHEN** a confirmed event and standard pair pass every baseline data, IV, historical ramp, liquidity and macro gate
- **THEN** the simulation SHALL select the deterministic pair from pre-session information, enter T-10 at valid regular-session closing asks and schedule T-2 exit
- **AND** no same-close or later-published feature SHALL influence that entry decision

#### Scenario: EO2 Calendar boundaries
- **WHEN** the release is Tuesday BMO or AMC, Monday is a holiday, or a relevant session closes early
- **THEN** T offsets SHALL count actual exchange sessions strictly before the release's New York date
- **AND** T-1 SHALL be the preceding eligible session, closing fills SHALL honor the early close, and all scheduled exits SHALL precede the earliest plausible release

#### Scenario: EO3 Calendar revision after entry
- **WHEN** a release is moved earlier or a macro red day conflicts with a held pair's exit
- **THEN** the current recommendation SHALL be invalidated or moved to an earlier feasible exit with a recorded revision
- **AND** an impossible or already-missed exit SHALL be recorded as a breach/exit-unconfirmed state, never a retroactive safe fill

#### Scenario: EO4 No qualifying setup or no ramp
- **WHEN** entry inputs fail a gate or held-contract IV has not expanded by T-3
- **THEN** entry SHALL abstain with reason counts or the held trade SHALL retain an executable pre-event exit with a no-ramp reason
- **AND** neither condition SHALL cause a late entry, roll through earnings or directional/short-premium substitution

### Requirement: Comparable IV statistics

Rank/percentile and moving-average entry gates SHALL use the specified consistent
30-day ATM feature series; event-expiry IV SHALL remain separately identified.

#### Scenario: EO5 Rank, percentile and missing warmup
- **WHEN** trailing min/max are 0.20/0.60 and current IV is 0.30
- **THEN** IV rank SHALL be 25 and percentile SHALL be computed independently from the trailing empirical observations
- **AND** zero trailing range, insufficient 252-session history or missing expiry brackets SHALL make the rank gate unavailable, not eligible by default

### Requirement: Reserve-first, concurrent debit limits

The system SHALL enforce explicit sleeve cash, reserve, cohort, per-name and sector
limits for open positions and pending allocations, using whole contract quantities.

#### Scenario: EO6 Reserve and whole-pair sizing
- **WHEN** the sleeve is $50,000, reserve 20%, Week-2 weight 25%, per-name cap 25%, pair ask debit $1,200 and entry fee $1.30 per pair
- **THEN** cohort capacity SHALL be $10,000, per-name capacity $2,500 and quantity at most two pairs, further reduced by remaining cash/sector/global limits

#### Scenario: EO7 Competing reservations and overlapping weeks
- **WHEN** two workers reserve the same remaining capacity or a new earnings week starts with positions still open
- **THEN** allocation SHALL be atomic and keep every existing debit/reservation against its original cohort and global cash limit
- **AND** exited losses SHALL reduce reusable cash rather than reset the initial sleeve

### Requirement: Observed paper state

Recommendations SHALL not be represented as executed trades or confirmed exits.

#### Scenario: EO8 Exit deadline without confirmation
- **WHEN** the system recommends an exit but the user has not recorded paper closure by the deadline
- **THEN** the paper position SHALL remain open/overdue and continue to consume capacity
- **AND** the UI SHALL not claim that the account is flat or that a broker order was sent
