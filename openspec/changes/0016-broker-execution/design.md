# 0016 — Design

## Boundary

```
core/trading.py            sizing, drift, average-cost P&L, equity attribution — pure
data/brokers/base.py       Broker protocol, owned models, BrokerCapabilities
data/brokers/fake.py       deterministic in-memory broker (tests, conformance, demos)
data/brokers/alpaca.py     LiveAlpacaSource (httpx) + AlpacaBroker (parser/mapper)
data/storage/base.py       TradeIntent / TradeOrder / TradeFill records, TradeRepository
data/storage/adapters/     migration v3 (trade_intent, trade_order, trade_fill)
cli/commands/trade.py      the seven commands; loads, confirms, persists, renders
```

The broker is selected by configuration (`SOBRES_BROKER`, only `alpaca` today;
`fake` is a test double reachable through `Context.sources`). No shared module
branches on the adapter's name; capability differences are declared on the port
and checked before any side effect.

## Owned models

`OrderRequest(client_order_id, symbol, side, quantity, order_type="market",
time_in_force="day")` — quantities are `Decimal`-free floats rounded to whole
shares unless the broker declares `fractional`. `BrokerOrder` carries the
broker's id, the client id, `status` in the owned vocabulary
(`new|accepted|partially_filled|filled|cancelled|rejected|expired|unresolved`),
filled quantity and average price, UTC timestamps, and the raw payload for
audit. `Fill(order_id, symbol, side, quantity, price, at, source)` with
`source` = `broker` or `external`. `Quote(symbol, price, as_of)`; a quote older
than `MAX_QUOTE_AGE` (5 minutes) is rejected at preview.

## Sizing (core)

For each symbol with target weight `w`, target value `w · budget`; current
value is held shares × quote plus pending buy notional minus pending sell
notional; delta = target − current; shares = `floor(|delta| / price)` toward
the sign of delta (`round` to the broker's fractional precision when supported).
Residual cash = budget − Σ buy notional + Σ sell notional (whole-share rounding
is reported, never hidden). Drift after the plan = resulting weight − target.
A budget above available cash, an unsupported asset, a missing quote or a zero
price is a usage error before anything is submitted.

## Execution lifecycle

1. `preview` builds the plan, hashes it (symbols, sides, quantities, quote
   timestamps, budget, account, environment) and prints the hash. No writes.
2. `execute --plan <hash>` rebuilds the plan and refuses if the hash differs
   (quotes moved, holdings changed): a new preview is required. It then writes a
   `TradeIntent(state=confirmed)` **before** any network call, then submits
   orders one by one; each `TradeOrder` is written as `submitted` with the
   broker's id, or `unresolved` when the submission raised after the request
   left (timeout). A second `execute` with the same hash is refused because the
   intent exists.
3. `status` asks the broker for every non-terminal order, updates states and
   appends fills. `unresolved` orders are looked up by client order id; if the
   broker has never seen them they become `failed`, otherwise their real state.
4. `close SYMBOL [--quantity]` previews a sell of the held quantity, confirms,
   and submits through the same path (its own intent).

## Environments and enablement

`SOBRES_ALPACA_ENVIRONMENT=paper` chooses the paper base URL and account. Live
needs all three: the environment setting `live`, `SOBRES_TRADING_LIVE_ENABLED=true`,
and `--live` on the command, which then asks for a typed confirmation of the
account id. Records are scoped by broker, account and environment; a paper
record cannot address a live account. Credentials are secrets (0600 file,
redacted, browser-locked); the environment and enablement flags are advanced
settings.

## Performance

Realized P&L uses average cost: each buy updates the average; each sell
realizes `(price − avg) × qty`. Unrealized is `(mark − avg) × held`. A deposit
or withdrawal appears in `history` as a cash flow and is excluded from profit;
period return is time-weighted between cash flows. Backtested and optimized
figures never mix with realized ones.

## Rejected

- Vendor SDK (`alpaca-py`): a large dependency whose objects would leak; the
  REST surface used here is small.
- Streaming (`trade_updates`): reconciliation by polling is enough for a single
  user and survives restarts by construction.
- Browser mutations: financial side effects stay in the terminal for now.
