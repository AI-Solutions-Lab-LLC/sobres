# broker-execution — spec delta (0016)

## ADDED Requirements

### Requirement: Broker port and adapters

Execution SHALL go through a Sobres-owned broker protocol with owned request and
result models and declared capabilities. Vendor objects, enums and exceptions
SHALL NOT appear outside the vendor's adapter.

#### Scenario: Adapter replacement
- **WHEN** the preview → submit → partial fill → position → close → history workflow runs
- **THEN** it SHALL pass unchanged against the fake broker and against the Alpaca adapter on recorded payloads
- **AND** the shared conformance suite SHALL define the contract both satisfy

#### Scenario: Vendor stays in its adapter
- **WHEN** the source tree is scanned
- **THEN** only `data/brokers/alpaca.py` SHALL import or name the Alpaca API
- **AND** no shared module SHALL branch on a broker's name

#### Scenario: Unsupported capability fails before side effects
- **WHEN** a plan needs fractional shares from a broker that declares none
- **THEN** the command SHALL fail before any order is submitted
- **AND** SHALL NOT round silently to emulate the capability

### Requirement: Order sizing from a saved portfolio

`trade preview` SHALL turn a saved portfolio's weights and a budget into whole-share
orders against current holdings, pending orders and fresh quotes, with no side effects.

#### Scenario: Known allocation
- **WHEN** a saved 60/40 portfolio, a 1,000 budget, no holdings, no open orders and quotes of 100 and 50 are given
- **THEN** the preview SHALL be 6 and 8 shares with a 0.00 residual before costs
- **AND** SHALL show target weight, quantity, notional, quote timestamp, residual cash and drift

#### Scenario: Holdings and pending orders reduce the delta
- **WHEN** shares are already held or a buy is pending
- **THEN** their value SHALL count toward the target and only the difference SHALL be ordered
- **AND** a sell SHALL be produced when a holding exceeds its target

#### Scenario: Insufficient funds or unusable quote
- **WHEN** the budget exceeds available cash, a quote is missing, zero or older than the maximum age
- **THEN** the preview SHALL fail with a usage error naming the symbol or the limit
- **AND** nothing SHALL be submitted or recorded

### Requirement: Durable, non-duplicating execution

`trade execute` SHALL record its intent before any network call, submit each order
independently, and never label an unknown outcome as failed or filled.

#### Scenario: Plan must match
- **WHEN** `--plan` names a hash and the rebuilt plan differs (quotes moved, holdings changed)
- **THEN** execution SHALL be refused and a new preview requested

#### Scenario: Durable intent before submission
- **WHEN** execution starts
- **THEN** the intent (portfolio, run, account, environment, plan, hash) SHALL be persisted as confirmed before the first order leaves
- **AND** each order SHALL be persisted with its client order id beside the broker's id

#### Scenario: Duplicate confirmation is refused
- **WHEN** the same plan hash is executed twice
- **THEN** the second execution SHALL be refused because the intent already exists
- **AND** no second order SHALL be submitted

#### Scenario: Submission timeout leaves the order unresolved
- **WHEN** a submission raises after the request left
- **THEN** the order SHALL be recorded as `unresolved`, not failed, not filled
- **AND** `trade status` SHALL resolve it from the broker by client order id, or mark it failed only when the broker never saw it

#### Scenario: Partial fill is reported as observed
- **WHEN** the broker reports a partially filled order
- **THEN** positions, orders and history SHALL show the filled quantity and average price as reported
- **AND** a multi-order rebalance SHALL NOT be presented as atomic

### Requirement: Environments and enablement

Paper SHALL be the default. Live SHALL require the environment setting, the
enablement setting, the `--live` flag and a typed confirmation of the account id.

#### Scenario: Paper by default
- **WHEN** no environment is configured
- **THEN** preview and execute SHALL address the paper account and say so in every output

#### Scenario: Live requires setting, flag and confirmation
- **WHEN** `--live` is passed without `SOBRES_TRADING_LIVE_ENABLED=true` and `SOBRES_ALPACA_ENVIRONMENT=live`
- **THEN** the command SHALL exit 3 naming both settings
- **AND** with them set, execution SHALL still ask the operator to type the account id
- **AND** a paper intent SHALL never address a live account

#### Scenario: Credentials are secrets
- **WHEN** Alpaca credentials are configured
- **THEN** they SHALL live in the 0600 config file, be redacted in every output and log, and be browser-locked
- **AND** doctor SHALL report the broker's reachability and the missing-key fix

### Requirement: Positions, closing and history

Reads SHALL never submit orders. Closing SHALL preview, confirm and submit through
the same lifecycle. History SHALL survive restart and cache clearing.

#### Scenario: Positions are read without side effects
- **WHEN** `trade positions` runs
- **THEN** it SHALL list quantity, average cost, current price, market value and unrealized P&L as the broker reports them
- **AND** positions with no Sobres intent SHALL be marked external

#### Scenario: Close previews then submits a closing order
- **WHEN** `trade close AAPL --quantity 4` is confirmed
- **THEN** a sell of 4 shares SHALL be recorded as its own intent and submitted
- **AND** `--quantity` above the held quantity SHALL be refused

#### Scenario: Known P&L
- **WHEN** fills are buy 10 @ 100 and sell 4 @ 110 and the remaining 6 are marked at 105
- **THEN** realized P&L SHALL be 40 and unrealized 30 before fees
- **AND** a deposit SHALL change equity without counting as profit

#### Scenario: Durable history
- **WHEN** the process restarts or `sobres cache clear` runs
- **THEN** intents, orders and fills SHALL remain inspectable
- **AND** `db export` SHALL carry them

### Requirement: Surfaces

Trading commands SHALL be registry declarations. Financial mutations SHALL be terminal-only.

#### Scenario: Mutations are terminal-only
- **WHEN** `trade execute` or `trade close` is invoked over HTTP
- **THEN** it SHALL answer 400 before any side effect, naming the terminal command

#### Scenario: Reads are exposed
- **WHEN** `trade preview`, `positions`, `orders`, `status` or `history` is registered
- **THEN** the parity suite SHALL find its route, schema and view
