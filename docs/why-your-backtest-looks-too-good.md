# Why your backtest looks too good

In-sample optimization selects weights using the same history on which it reports
performance. Walk-forward evaluation repeatedly fits prior data and then measures
later returns. Either Sharpe ratio can be larger: the gap reflects estimation
error, changing market conditions, costs, and differences between estimated and
realized statistics. It does not isolate one cause.

## What the backtest measures

At each rebalance date, only earlier asset and CAPM benchmark returns enter the
training window. The risk-free proxy uses the most recent observation strictly
before that date. Weights drift with realized returns until the next rebalance.
An equal-weight portfolio runs over the same dates and pays the same cost rate.
The JSON result records each training window, decision rate, estimators, bounds,
seed, warnings, and the requested settings.

Sharpe uses annualized arithmetic mean excess return divided by annualized
excess-return volatility. CAGR is reported separately. Sortino divides annualized
arithmetic excess return by the annualized root-mean-square shortfall below the
per-observation target, including zero shortfalls in the denominator population.
Ratios are unitless. VaR/CVaR describe one observation, with losses negative.
Drawdown includes initial capital; a null peak date means the initial baseline.

## Risk-free assumptions

`--risk-free 0.04` specifies a 4% annual simple rate in the computation currency.
Without an override, USD portfolios can use FRED DTB3 with a configured key.
DTB3 is a bank-discount quote: the implementation approximates a 91-day bill,
a 360-day discount basis, and 365-day annual simple investment yield. Per-period
proxy return is that annual rate divided by the frequency convention. This is
an approximation, not a realized investable total-return series.

Non-USD portfolios and missing keys use zero with an explicit warning. FRED
observations are current historical vintages, not an archived information set:
strict date cutoffs prevent future-date leakage but cannot undo later revisions.
A universe selected today also has survivorship bias.

## Costs and missing data

The default is 10 bps per unit of one-way turnover, calculated as half the sum
of absolute weight changes across risky assets **and residual cash**. Initial
investment from cash has turnover 1 and costs 0.1%; a full A-to-B rotation also
costs 0.1%. `total_cost` is actual fees paid divided by initial capital; it is not
the terminal performance drag. `total_cost_rate` separately sums fee fractions
charged against the changing wealth base.

Choose `--fill drop|ffill|raise` explicitly. Dropping a missing price excludes
both adjacent return intervals, records their dates, and never treats a
multi-day move as a one-day return. Core functions reject unresolved NaN and
infinity. Forward fill is a modeling choice and may create zero-return periods.
Multi-currency prices are converted before returns are calculated.

## Using the controls

```bash
sobres optimize markowitz --tickers AAPL MSFT --start 2020-01-01 --end 2020-03-31 --fill drop --returns-estimator capm --benchmark JNJ
sobres optimize backtest --tickers AAPL MSFT --start 2020-01-01 --end 2020-03-31 --fill drop --lookback 20 --objective target_return --target 0.10
sobres optimize frontier --tickers AAPL MSFT --start 2020-01-01 --end 2020-03-31 --fill drop --points 10 --format json
```

A target return is an annual decimal equality and may be infeasible for a
particular training window. Target risk is an annual volatility **ceiling**.
`--allow-short` permits negative weights within the box bounds; it does not
model borrowing fees, margin calls, or liquidation. Risk parity seeks equal
contributions to portfolio variance under those bounds; constraints can prevent
exact equality. Ledoit-Wolf covariance shrinkage is the default.

Frontier output contains exactly the requested number of rows, including named
portfolios. Two rows prioritize minimum variance and maximum Sharpe; three or
more also include the maximum-return endpoint. Coincident optima share flags;
a completely degenerate frontier repeats identical portfolios to retain the
requested count. Commands support at most 100 assets and 500 frontier points.
Ctrl-C cancels a foreground CLI calculation; stderr progress and timing do not
change the numeric output. Cache/source timestamps and elapsed times are
observational metadata, so byte comparisons require a fixed clock/cache state.

Independent hand calculations and closed-form two-asset solutions test the
math. The legacy LP fixture is independently enumerated in Python; actual R
execution and an externally published three-asset weight solution are not
claimed as completed validation.

*For research and education only. Not investment advice.*
