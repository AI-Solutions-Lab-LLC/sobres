---
change: 0007-equity-factor-analysis
milestone: v1.3
depends_on: [0001-foundation-data-and-cli, 0002-portfolio-optimization, 0013-template-development-alignment, 0004-web-ui]
status: proposed
planning_depth: proposal + design + tasks + spec deltas; amended by 0013
---

# 0007 — Equity and factor analysis

## Outcome

```bash
sobres analyze stock NVDA
sobres analyze factors NVDA --model ff5 --start 2015-01-01
sobres analyze factors --tickers AAPL MSFT NVDA --model ff5+mom --format csv
```

A single-stock dashboard, and a Fama-French regression that answers the question the
whole thing exists for: **is this stock's excess return explained by known risk
factors, or is there alpha?** — with the t-statistic that says whether to believe it.

## Why

Factor analysis is the part of this tool that is genuinely hard to get elsewhere in
a usable form. The data (Ken French) lands in 0001, the returns and risk machinery
lands in 0002, so by this point the change is mostly regression plumbing and careful
statistics reporting.

It also feeds forward: factor exposures become a candidate expected-return estimator
for the optimizer, and factor-tilted portfolio construction becomes possible.

## What changes

- **New capability `equity-analysis`**: `core/factors.py` (CAPM, FF3, FF5,
  FF5+momentum, rolling betas) and a fundamentals summary built on yfinance.
- **New CLI group `sobres analyze`**: `stock`, `factors`.
- The amended design retains the candidate branch's numpy OLS/HAC implementation
  with independently verified answers; `statsmodels` stays in the `econ` extra
  and can serve as a development oracle. Base installation gains no regression dependency.

## Non-goals

- No DCF or intrinsic-value modeling. Its assumptions dominate its output; it would
  be false precision wearing a spreadsheet.
- No analyst estimates, earnings-call transcripts, or sentiment. Different data
  problem entirely.
- No point-in-time fundamentals. yfinance serves current values, so any
  fundamentals-based backtest would be survivorship- and restatement-biased. The
  spec states this limitation in the output rather than hiding it.
- No custom or proprietary factor construction. Ken French's published factors only.

## Risks

| Risk | Mitigation |
|---|---|
| Users read a positive alpha as a stock pick | Always report the t-statistic and p-value next to alpha; the spec requires stating explicitly when alpha is not statistically distinguishable from zero |
| Overlapping/autocorrelated residuals inflate significance | Newey-West (HAC) standard errors alongside OLS; report both |
| Short samples produce unstable betas | Enforce a minimum observation count; offer rolling-window betas so instability is visible rather than averaged away |
| Frequency mismatch (daily prices vs monthly factors) | Alignment is explicit via 0001's `align_frames`; monthly is the default for factor work, matching how the factors are published |

## Development alignment and review readiness (0013)

Keep OLS/HAC computation in `core/factors.py`, use cases in `application/commands/analyze.py` and vendor parsing in `adapters/providers/`. Carry forward the branch design of numpy-based regression with independent known-answer and statsmodels comparison tests; statsmodels stays out of base dependencies. Reconcile its cache changes with the corrected foundation.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #13 at `4a8a60d88f60dfe1fd1409b6c7890f9416f2f668` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge commit remains pending.
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#29](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/29).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. This plan is not yet merged.
