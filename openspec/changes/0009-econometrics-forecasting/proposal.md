---
change: 0009-econometrics-forecasting
milestone: v1.5
depends_on: [0001-foundation-data-and-cli, 0002-portfolio-optimization, 0007-equity-factor-analysis, 0013-template-development-alignment, 0004-web-ui]
status: proposed
planning_depth: proposal + research + design + tasks + spec deltas; multivariable amendment 2026-09-13
---

# 0009 — Multivariable equity forecasting and volatility

## Outcome

Forecast a stock's future price distribution using several economically relevant
series, with understandable defaults and evidence from unseen dates. Retain GARCH
volatility and robust regression diagnostics. These are **proposed interfaces**:

```bash
sobres econ forecast ticker:AAPL --model var --preset equity-basic --horizon 20
sobres econ forecast ticker:AAPL --model bvar --sector ticker:XLK
sobres econ forecast ticker:AAPL --model elastic-net --preset equity-macro
sobres econ forecast ticker:AAPL --model boosted-trees --preset equity-basic
sobres econ evaluate ticker:AAPL --models var bvar elastic-net boosted-trees --horizon 20
sobres econ volatility ticker:SPY --model garch --horizon 30
sobres econ diagnose fred:DGS10
sobres econ regress --y ticker:AAPL --x ticker:SPY fred:DGS10 --robust hac
```

## Decision and evidence

The owner's 2026-09-13 instruction supersedes the original ARIMA forecasting
scope. Remove standalone AR, ARMA, ARIMA, SARIMA and auto-ARIMA price/macro
forecasters from this milestone. VAR/BVAR explicitly retain their joint lagged
relationships across variables; the instruction does not remove those lags or
GARCH's volatility dynamics. Diagnostic ACF/PACF also remain useful.

[Research and predictor decisions](research.md) cover influential econometric and
asset-pricing work plus 2025–2026 forecasting models/benchmarks, checked on
2026-09-13. They motivate shrinkage, multiple predictors and chronological
validation; they do **not** prove that any preset will predict this stock well.
Cross-sectional monthly return evidence is not direct evidence for a single-stock
daily price model. Daily defaults below are engineering choices to be tested.

## What changes

- A genuine joint VAR, regularized by default; optional Bayesian VAR with a
  documented shrinkage prior. No relabelled independent ARIMA fits.
- Direct multivariable elastic-net and gradient-boosted-tree forecasts, evaluated
  with the same available information, horizons and outer dates as VAR/BVAR.
- A versioned predictor catalog: a small keyless equity preset; optional sector,
  momentum, liquidity, macro and point-in-time fundamental/factor inputs. Each
  entry specifies its economic rationale, formula, unit, source and availability.
- Default daily horizon 20 target-market sessions, five-year training window,
  bounded tuning, mandatory 80%/95% price and return intervals, and benchmarks.
- Split-only price semantics, dividend/total-return distinctions, realistic
  publication/vintage alignment, fold-local preprocessing and seeded uncertainty.
- `econ evaluate` for held-out skill, calibration and optional costed strategy
  diagnostics; no automatic forecast handoff into goals, expected returns or trades.
- Retain `diagnose`, robust `regress`, GARCH(1,1)/EGARCH/EWMA and CCC-GARCH covariance.
  Volatility modeling is separate from directional price forecasting; superiority
  over sample covariance must be measured, not asserted.

## Non-goals

Univariate forecasting; FX or PPP forecasts; causal interpretations of VAR or
feature importance; live trading; automatic changes to 0008 goal assumptions;
training a large cross-sectional model on a single ticker. FAVAR/PCR, VECM,
DCC-GARCH and pretrained neural/foundation models are explicitly deferred, with
promotion conditions in research.md. No new cloud service or paid data dependency
is necessary for the basic preset.

## Status, compatibility and dependencies

PR #15 at `6a1f12dc7ab3a70ad84fc4ef2ef8fe4c96cb3620` contains the synchronized
**older ARIMA implementation**. This amendment changes planning artifacts only;
its existing green tests do not satisfy the new forecasting contract. Do not
merge/release that candidate as a completed implementation of revised 0009.
Implementation tasks remain unchecked. The old ARIMA requirement is replaced in
this active delta, not retained as an alternative acceptance path.

PR #33 (`b9792d72dad7217f7bb642c0c90a668afc501087`) merged the earlier plan and
0013 alignment proposal; it did not merge this amendment or implement the package
migration. Resume implementation only after this amendment is accepted/merged and
0013 plus the listed predecessors are implemented. Follow the shared application,
ports and adapters map in [0013](../0013-template-development-alignment/design.md),
its [workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and the [revision-pinned decision audit](../0013-template-development-alignment/alignment-audit.md).
Public work must not depend on private context.

The candidate's ARIMA flags/results must receive an explicit migration error and
updated CLI/API/UI schema; they must not silently select VAR. Preserve stored old
runs as historical records. If a public release actually included that interface,
apply the repository's major-version/deprecation contract before removal. Preserve
all unaffected commands, public core imports, settings/doctor and storage behavior.

## Risks and acceptance

Overfitting is addressed through shrinkage, a fixed search budget and nested time
splits. Data revisions and unavailable future predictors are addressed through
availability metadata and vintage-aware joins. Price-level accuracy alone is
insufficient: include return error, baseline-relative skill and interval coverage.
A negative result is valid output, not a reason to change test dates or defaults.
Missing required predictors must fail visibly rather than silently reduce the model.

Tracker: [#31](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/31);
Candidate PR: [#15](https://github.com/AI-Solutions-Lab-LLC/sobres/pull/15).
The docs-only planning PR against main is linked from #31; merge that amendment
independently before replacing the older candidate implementation.
Carry this amended contract into dependent #16. New source/extra dependencies need
settings and doctor coverage. #36 separately owns automatic risk-free policy;
ordinary price returns here are not excess returns, and the macro short-rate
predictor must not redefine that policy.
