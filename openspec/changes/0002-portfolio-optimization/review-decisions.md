# Review corrections and acceptance decisions

Implements the authorized PR #8 report corrections. Foundation corrections and recorded
fixtures are integrated from local main. The original report remains an historical review.

1. Decision inputs use only dated observations strictly before a rebalance. FRED's
   latest historical data is not a point-in-time vintage database; outputs disclose that
   limitation. A constant risk-free override is explicit. Non-USD universes default to
   a disclosed zero proxy rather than silently borrowing a USD Treasury rate.
2. DTB3 is converted from bank-discount yield using a stated 91-day bill approximation,
   360-day discount basis, and 365-day annual simple investment-yield basis. Per-period
   excess returns subtract this annual simple proxy divided by the convention table.
3. Sharpe uses arithmetic mean excess return / sample excess-return deviation,
   annualized. CAGR remains a separate reported return and is used for Calmar.
   Sortino uses arithmetic excess return / root-mean-square below-target shortfall
   over all observations; the target is a per-period decimal, default zero.
4. Drawdown includes initial wealth 1.0. A null peak date denotes initial capital
   immediately before the first recorded return; it is never assigned a fabricated date.
5. Price gaps are handled on the original index before invalid return intervals are
   dropped. Every dropped return date is reported. Public analytics require finite
   inputs; callers must explicitly resolve missing data first.
6. CAPM accepts an explicit benchmark ticker, converted to the portfolio currency and
   aligned before estimation. Every rebalance slices the benchmark along with assets.
   Both target objectives accept a validated target in Markowitz and backtest.
7. Public optimization conditions covariance, verifies the final weights/targets, and
   returns conditioning/solver provenance. SciPy is behind a repository-owned protocol;
   differentiable objectives supply analytic derivatives. Frontier supports progress.
8. A frontier contains exactly N portfolios including named extrema. Coincident named
   extrema share one row. N=2 prioritizes min variance and max Sharpe; N>=3 also includes
   maximum return where distinct. A degenerate universe can contain repeated identical
   portfolios to satisfy the requested sample count, with each name flagged once.
9. The default fee is 10 bps per unit of one-way turnover, not 10 bps per trade side.
   Turnover includes cash, making initial full investment one unit. Total cost is actual
   fees divided by initial capital; the sum of fee fractions is reported separately.
10. Group constraints, true R execution parity, further solver backends, parallel
    provider acquisition and Homebrew distribution are explicitly deferred. The CLI
    work limit is 100 assets and 500 frontier points, with bounded dates/lookbacks.
    PyPI workflow corrections are included; #21 remains open for upload verification
    and activation. Publication is a later release action.

Validation includes hand-computed math, future-price/rate perturbation through the CLI
adapter, actual generated option parsing, typed table/JSON/CSV output, a clean wheel,
strict OpenSpec validation, CI checks, and bounded live-provider runs where available.
