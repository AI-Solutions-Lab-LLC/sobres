# 0007 — Design

Proposed design carried forward from PR #13; statements about tests or
behavior describe that branch's intent and claims, not verified acceptance here.
Reconcile through R0/R1/R2 and this amendment before implementation.

## Regression on numpy, HAC by hand

`statsmodels` stays in the `econ` extra. The OLS fit, classical standard errors
and the Newey-West (Bartlett kernel) covariance are ~40 lines of numpy in
`core/factors.py`, with the formulas cited in the module docstring. The test
suite checks them against a hand-worked two-variable closed form and, as an
independent implementation, against `statsmodels` HAC (`tests/core/test_factors.py`)
— the reference is used by the tests, not by the product, so the base install
gains no dependency. The lag length defaults to the Newey & West (1994) rule
`floor(4 (n/100)^(2/9))` and is always stated in the output.

## Excess returns, monthly by default

The dependent variable is `r - RF` with `RF` from the same Ken French file — not
the FRED bill used elsewhere — so an asset's alpha is measured against the
factors' own zero. Monthly is the default frequency because that is how the
factors are published: daily prices are resampled to month-end and simple
monthly returns taken before alignment (`core/factors.py::to_monthly_returns`).
`--frequency daily` uses the daily factor files.

## Alpha, twice, and never alone

Every term carries OLS and HAC standard errors, t and p. The significance
statement uses the HAC p-value (the conservative one); when it exceeds 0.05
the output says alpha is not statistically distinguishable from zero and that
the point estimate should not be read on its own. The comparison table marks
significant alphas with `*` and says what the absence of a mark means.

## Fundamentals at the provider boundary

`YahooSource` gains `fundamentals(ticker)` returning the vendor's `info`
document (or None for ETFs, funds and indexes); `YFinanceProvider.get_fundamentals`
parses the documented keys into a `Fundamentals` dataclass. Fundamentals are
current values and are never cached as observations. The recorded fixture is
`tests/fixtures/yfinance/fundamentals.json`, in the vendor's key names.

## A cache bug this change found

Cached factor frames came back with an empty `Mkt-RF` column: the observation
cache upper-cased symbols before asking the provider, and the provider's
mixed-case column was never stored. The cache now asks in the caller's casing,
stores keys upper-cased, and restores the caller's casing on the way out
(`tests/data/test_cache.py::test_mixed_case_symbols_round_trip_with_their_casing`).

## Rejected

| Choice | Rejected | Why |
|---|---|---|
| numpy OLS + HAC | `statsmodels` in the base install | ~80 MB of dependency for one covariance formula; the tests still use it as the oracle |
| `RF` from the factor file | FRED bill | Would mix two risk-free series in one regression |
| Monthly default | Daily default | Factors are monthly; daily fits over-weight microstructure noise |
| Fundamentals uncached | Cache as observations | They are not time-series observations; caching would imply point-in-time values they are not |

## Alignment amendment (0013)

Keep OLS/HAC computation in `core/factors.py`, use cases in `application/commands/analyze.py` and vendor parsing in `adapters/providers/`. Carry forward the branch design of numpy-based regression with independent known-answer and statsmodels comparison tests; statsmodels stays out of base dependencies. Reconcile its cache changes with the corrected foundation.

The [common package map](../0013-template-development-alignment/design.md) is authoritative
for future locations. This amendment does not accept proposed cloud profiles.
Use named task proofs, installed-artifact checks and explicit rollback: revert
application wiring with compatibility facades intact; never rewrite a released
schema migration or delete user state to roll back a module move.
