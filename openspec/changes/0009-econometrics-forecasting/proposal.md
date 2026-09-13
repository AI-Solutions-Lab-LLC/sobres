---
change: 0009-econometrics-forecasting
milestone: v1.5
depends_on: [0001-foundation-data-and-cli, 0002-portfolio-optimization, 0007-equity-factor-analysis, 0013-template-development-alignment, 0004-web-ui]
status: proposed
planning_depth: proposal + design + tasks + spec deltas; amended by 0013
---

# 0009 — Econometrics and forecasting

## Outcome

```bash
sobres econ forecast CPIAUCSL --model arima --horizon 12
sobres econ volatility SPY --model garch --horizon 30
sobres econ diagnose DGS10          # stationarity, ACF/PACF, structural breaks
sobres econ regress --y AAPL --x SPY DGS10 --robust hac
```

Time-series forecasting and regression diagnostics on the same data layer, with
honest uncertainty intervals.

## Why

Volatility forecasting feeds directly back into 0002: a GARCH-based covariance
estimator is a meaningfully better input to the optimizer than a rolling sample
window, particularly during regime shifts. Macro forecasting supports the real-return
assumptions in 0008.

It is last because it is the piece whose value depends most on everything below it
being trustworthy first.

## What changes

- **New capability `econometrics`**: `core/timeseries.py` (stationarity tests,
  differencing, ARIMA, GARCH, forecast intervals) and `core/regression.py` (OLS with
  robust standard errors, multicollinearity and residual diagnostics).
- **New CLI group `sobres econ`**: `forecast`, `volatility`, `diagnose`, `regress`.
- A GARCH-based covariance estimator registered into 0002's `core/moments.py`, which
  is why that module was built as a pluggable registry.
- Reuse: `espin086/Econometrics` for statsmodels patterns, `espin086/jjutils`
  `base_regression.py` for regression scaffolding, `espin086/NewsWaveMetrics` for
  its existing forecasting work.

## Non-goals

- No VAR, VECM, or cointegration analysis in this milestone.
- No machine-learning forecasters. A tool that ships an LSTM price predictor next to
  a Fama-French regression is telling the user something false about both.
- No causal inference (diff-in-diff, IV, RDD). `espin086/Econometrics` holds that
  work and it does not belong in an equity CLI.
- No automatic model selection presented as authoritative — see risks.

## Risks

| Risk | Mitigation |
|---|---|
| Point forecasts read as predictions | Prediction intervals are mandatory in every forecast output, never optional; the point forecast is never shown alone |
| Auto-ARIMA overfits and reads as objective | Report the selected order **and** the information criterion, plus the top 3 candidate models, so the choice is visible rather than authoritative |
| Non-stationary input silently produces nonsense | Stationarity is tested before fitting; non-stationary series either fail loudly or are differenced with the differencing order reported |
| `statsmodels` and `arch` dependency weight | Both stay in the opt-in `econ` extra; commands that need them exit 3 with an install hint |

## Development alignment and review readiness (0013)

Keep econometric math in `core/`, source resolution and use cases in `application/commands/econ.py`; providers remain adapters. Preserve the optional econ dependency/doctor contract and forecast intervals. Use explicit source prefixes or declared catalog entries, rejecting ambiguity instead of inferring a provider from symbol length.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #15 at `88df04e01a5993c24a0857ef387e0b03c24fbacc` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge commit remains pending.
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#31](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/31).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. This plan is not yet merged.
