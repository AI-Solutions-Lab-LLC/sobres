---
change: 0016-broker-execution
milestone: v1.2
depends_on: [0002-portfolio-optimization, 0003-local-persistence, 0004-web-ui]
status: implemented
---

# 0016 — Broker execution: invest a saved portfolio through an adapter, paper first

## Outcome

A saved portfolio becomes real orders through a broker adapter, with the
review-before-anything discipline the rest of the tool has:

```
$ sobres trade preview --portfolio core --budget 1000
account paper PA3… (alpaca, paper): cash 100,000.00 USD, buying power 200,000.00 USD
plan 7c1e…: 2 orders, 1,000.00 USD budget, 0.00 USD residual; quotes as of 2026-09-16T19:59:58Z
  AAPL  buy  6 shares @ 100.00 = 600.00  (target 60%, held 0)
  MSFT  buy  8 shares @  50.00 = 400.00  (target 40%, held 0)
no side effects; to submit: sobres trade execute --portfolio core --budget 1000 --plan 7c1e…
```

`trade execute` records the intent durably, submits each order, and reports what
the broker actually said. `trade positions`, `trade orders`, `trade history`,
`trade status` (reconciliation) and `trade close` complete the loop. Paper trading
is the default; live trading needs a setting, a flag and a typed confirmation, and
CI never trades. Alpaca is the first adapter; the shared workflow, storage,
accounting and commands do not know its name.

Issue: [#22](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/22). This
change deliberately revises the scope statement in 0002 ("no live trading,
ever") and the roadmap exclusion: execution stays out of the optimizer, and
lives here, behind explicit enablement.

## Why

An optimizer whose output has to be retyped into a brokerage is half a tool.
The epic asks for the adapter pattern so the workflow survives a broker change,
and for honesty about what the broker reported versus what was intended.

## What changes

- **A Sobres-owned broker port** (`data/brokers/base.py`): account, positions,
  quotes, order submission/lookup/cancellation, fills, and a capability
  declaration (fractional shares, environments, close-position support). Owned
  request/result dataclasses and the shared error taxonomy; no vendor object
  crosses the boundary.
- **Two adapters:** `FakeBroker` (deterministic, in-memory, used by the
  conformance suite and every offline test) and `AlpacaBroker` (Trading API v2
  over `httpx`, paper and live base URLs, fixtures in the documented payload
  shape). A shared behavioral conformance suite runs both.
- **Pure accounting in `core/trading.py`:** whole-share order sizing from target
  weights, a budget, quotes, current holdings and pending orders; allocation
  drift; average-cost realized and unrealized P&L; deposit-aware equity
  attribution. Known answers: a 60/40 $1,000 plan at $100/$50 is 6 and 8
  shares with $0 residual; buy 10 @ 100, sell 4 @ 110, mark 6 @ 105 is $40
  realized and $30 unrealized.
- **Durable records** behind the storage port: trade intents (with the plan and
  its hash), orders (internal id beside the broker's), fills; migration v3;
  `cache clear` never touches them; `db export` carries them.
- **Commands** declared once in the registry: `trade preview`, `trade execute`,
  `trade positions`, `trade orders`, `trade status`, `trade history`,
  `trade close`. Reads have routes and forms like every command; `execute` and
  `close` refuse over HTTP (terminal-only, like `serve`).
- **Settings and doctor:** `SOBRES_ALPACA_KEY_ID`, `SOBRES_ALPACA_SECRET_KEY`
  (secrets, browser-locked), `SOBRES_ALPACA_ENVIRONMENT` (`paper` default),
  `SOBRES_TRADING_LIVE_ENABLED` (`false` default); an `alpaca` provider spec with
  a doctor check; the live-provider workflow reads the organization's paper
  credentials by name and skips without them.

## Non-goals

Autonomous or scheduled trading; multi-user hosting; account opening or
funding; options, crypto, shorting, leverage, FX trading; tax lots and tax
reporting; bulk liquidation; streaming trade updates (reconciliation is by
polling `trade status`); browser-initiated mutations. Live execution is
implemented but its real-money verification is the owner's separately
authorized step, with a bounded amount; this change does not perform it.

## Risks

A submission that times out is neither a failure nor a fill: the order stays
`unresolved` until `trade status` asks the broker. A partial rebalance is not
atomic; each order carries its own state. Recorded Alpaca fixtures are
synthesized from the documented API shape until an authorized paper recording
exists, and are labelled so.
