---
change: 0002-portfolio-optimization
milestone: v1 (part 2 of 2) — the v1.0.0 release
depends_on: [0001-foundation-data-and-cli, 0013-template-development-alignment]
status: proposed
---

# 0002 — Portfolio optimization

## Outcome

```bash
sobres optimize markowitz --tickers AAPL MSFT NVDA JNJ XOM GLD \
    --start 2015-01-01 --objective max-sharpe --max-weight 0.35

sobres optimize frontier --tickers ... --points 50 --format csv > frontier.csv

sobres optimize backtest --tickers ... --objective max-sharpe \
    --rebalance quarterly --lookback 36m --start 2015-01-01
```

Optimal weights with the risk/return profile that produced them, the full efficient
frontier, and an honest walk-forward backtest of the strategy.

## Why

This is the highest-value slice and the one that forces the hardest foundations.
Getting Markowitz right end-to-end requires returns handling, covariance estimation,
constrained optimization, and risk metrics — the same machinery 0007 (factor models)
and 0008 (goal planning) then reuse. Any other starting point would build a thinner
base.

The backtest ships **with** the optimizer, not after it, and that is deliberate.
In-sample mean-variance optimization produces beautiful, useless numbers: it
maximizes a Sharpe ratio on data it has already seen. Shipping the optimizer alone
would make the tool's flagship output actively misleading. `sobres optimize backtest` is
the honesty mechanism, so it is part of v1's definition of done.

## What changes

- **New capability `portfolio-optimization`**, spanning:
  - `core/returns.py` — price → simple/log returns, annualization, cumulative growth
  - `core/moments.py` — expected-return and covariance estimators, including
    Ledoit-Wolf shrinkage
  - `core/risk.py` — volatility, Sharpe, Sortino, max drawdown, VaR/CVaR, beta,
    correlation
  - `core/optimize.py` — min-variance, max-Sharpe, target-return/target-risk,
    risk parity, equal weight; the efficient frontier
  - `core/backtest.py` — walk-forward rebalancing with transaction costs
- **New CLI group `sobres optimize`** — `markowitz`, `frontier`, `backtest`, `risk`.
- Port this repository's own prior implementation
  (`legacy_code/Financial Portfolio Optimization.R`) to `core/optimize.py`, with its
  results as regression fixtures.

## Non-goals

- **No Black-Litterman in v1.** It needs a view-specification UX that deserves its
  own change; the plumbing (a pluggable expected-return estimator) is designed in.
- **No factor-model inputs to the optimizer.** That is 0007 → a later change.
- **No taxes, lot tracking, or wash sales.** Out of scope for the whole tool.
- **No live trading, broker connections, or order generation.** Ever.
- **No intraday data.** Daily bars throughout.
- **No currency analytics.** Multi-currency sets are converted to a stated base
  before estimation, per 0001; decomposing return into asset and currency
  components, and hedging, are 0010.
- **No CVaR/robust objectives in v1.** The `cvxpy` extra is wired so they can be
  added without restructuring.

## Risks

| Risk | Mitigation |
|---|---|
| **Mean-variance is famously unstable** — small changes in expected returns swing weights wildly | Ledoit-Wolf shrinkage is the *default* covariance estimator; a weight-concentration warning fires above a threshold; `frontier` shows the whole trade-off rather than a single point |
| Users read backtest output as a forecast | Backtest output states in-sample vs. out-of-sample explicitly; the disclaimer footer is mandatory; the docs carry a plain-language "why this number is optimistic" section |
| Optimizer returns a silently wrong answer on a non-PSD covariance matrix | Validate PSD before solving; repair via nearest-PSD projection and warn, or fail — never solve quietly on a broken matrix |
| Solver dependency weight (`cvxpy`) | SLSQP via `scipy` is the default and covers every v1 objective; `cvxpy` stays an opt-in extra |
| Annualization convention errors (252 vs 365, simple vs log) | One documented convention module; every conversion tested against a hand-computed fixture |

## Development alignment and review readiness (0013)

Keep returns/risk/optimization/backtest math in `core/`; orchestration and registry declarations go to `application/commands/optimize.py`, rendering to `adapters/cli/`. Use shared market/currency services and injected providers. R/textbook oracles and known review findings need fresh acceptance, not changed expected values.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #8 at `21724ce35c6a4b3f5d89db265517bf77a38d425f` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge commit remains pending.
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#24](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/24).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. This plan is not yet merged.
