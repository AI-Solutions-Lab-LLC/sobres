# 0009 — Multivariable forecasting design

This design supersedes the candidate's ARIMA design. It is proposed behavior;
existing PR #15 code and tests are not evidence that it is implemented. Research
sources and their limits are recorded in [research.md](research.md).

## Target and price meaning

The default target is the future **split-only price log return**, not a raw
nonstationary price level, excess return, dividend-reinvested wealth index, or FX
rate. At origin `t`, define `y_(t,h) = log(P_(t+h) / P_t)` using prices in the
origin's share units. Historical split adjustments use only actions known by that
origin. Keep cash dividends separate: an adjusted-close total-return series must
not be passed off as the future quoted stock price. Price ingestion must expose
and test raw close, split actions, dividend flags and volume conventions.

From predictive log-return draws `z_b`, calculate `P_b = P_t * exp(z_b)`.
Report sample price mean, median and the 10/90 and 2.5/97.5 percentiles; do not call
`P_t * exp(mean(z_b))` the arithmetic expected price. Report the anchor, currency,
quote/sub-unit normalization, origin timestamp, target session, price basis and
future-corporate-action limitation. Historical evaluation uses the same origin
share basis. A total-return target, if later exposed, must have a separate name,
result type and wealth-index presentation.

Use the target exchange's completed sessions. A forecast created after close `t`
uses information available by its recorded cutoff; it is not a trade executable at
that already observed close. No future actual market, sector, macro, factor or
currency observations may enter its predictors or intervals. The default supports
USD US-listed equities; other markets require explicit benchmark/calendar/currency
configuration. Refuse mixed currencies rather than silently using SPY or projecting
an FX conversion. Preserve 0010's no-FX/PPP-forecast contract.

## Proposed defaults v1

Let `A = PERIODS_PER_YEAR["daily"]` from `core/conventions.py` (currently 252).
Window lengths for months/years derive from that convention; trading calendars
still determine actual forecast dates. These are testable product defaults, not
published estimates of optimal settings.

| Setting | Default and bounds |
|---|---|
| Model | `var`, ridge penalty on lag coefficients; unpenalized intercept |
| Preset | `equity-basic`: target return, SPY return, log 20-session realized volatility, change in log 20-session mean dollar volume |
| Frequency / horizon | Daily target-market sessions; `--horizon 20`; first implementation accepts 1, 5 or 20 sessions |
| Data request | Ten calendar years ending at the last completed session; explicit start/end override this, never silently extend an explicit requested start |
| Training | Trailing `5*A` usable sessions per origin; preprocessing warmup is additional; do not span missing-price sessions |
| Lag candidates | 1, 2, 5; requested fixed lag 1–5 permitted with the same guards |
| Ridge search | `lambda` in 0.01, 0.1, 1, 10 for the normalized objective below; choose on inner validation only |
| Dimension / samples | At least 2 distinct nonconstant series; default 4, maximum 12; every training fold needs `max(3*A, 10*(K*p+1))` usable rows |
| Evaluation | Last `A` sessions, at least 12 nonoverlapping complete horizon outcomes; three earlier inner validation blocks of `floor(A/4)` sessions within each outer training window |
| Simulation | Seed 0 by default, 1,000 predictive draws for VAR/BVAR, 200 bootstrap refits for VAR; explicit seed/draw overrides recorded with runtime limits |
| Missing observations | `--fill raise` default; explicit drop/ffill obey foundation gap rules and cannot fill unreleased data or bridge price gaps |
| Results | Model/preset versions, all candidates and losses, diagnostics, baseline comparison and mandatory 80%/95% prediction bounds in every format |

Use `--benchmark ticker:<symbol>` to override SPY explicitly.
If the target equals the benchmark, columns coincide, the history is too short,
volume is unavailable, or a preset variable is invalid, explain the problem and
request a valid explicit configuration. Do not invent a replacement ETF, zero-fill,
quietly drop a required series, or fall back to a univariate model. Explicit smaller
windows are allowed only above the stated sample guards; they must be labelled.
For evaluation, reserve enough data for warmup, outer origins and inner training.

## Inputs and timing

`equity-basic` requires no API key and uses repository-owned market data ports.
`--sector ticker:XLK` adds one joint sector-return series; no current-sector lookup
is treated as a historical classification. `equity-macro` adds changes in DGS3MO
and T10Y3M (percent quotes divided by 100) and log VIXCLS, using explicit FRED
sources and vintage/availability metadata. Missing FRED credentials are an exit-3
error with setup guidance, not a switch back to the basic preset. Unsupported
vintage history is a distinct data-capability error, not a reason to use final
revised values in a purported point-in-time evaluation.

The extended catalog includes inflation/activity, dated fundamentals and factor
states. Each entry declares provider/field, units, transform, frequency, lookback,
release-availability policy, maximum staleness, role and evidence. None is enabled
by spelling a ticker that happens to resemble a macro ID. Sources use `ticker:` /
`fred:` or an unambiguous catalog ID. Future-input scenarios are out of scope.

As-of joins use both observation period and `available_at`; macro values with
only a release date become usable on the next target session, never retroactively
on the period they describe. For daily market-derived FRED series require a
published value no older than five target sessions. Monthly entries require the
latest actually released period and fail after 62 calendar days without a release.
Report carried values and age. Do not interpolate macro releases into fictitious
daily observations. FRED realtime/vintage dates are part of the cache key; repeated
requests for different origins must not overwrite one another's vintage.

For keyless historical market data, persist hashes, fetch time and corporate-action
basis. Unless true archived snapshots exist, label evaluation `revised-market-data`
and do not claim point-in-time tradability. Macro presets require historical
vintages for their backtest, even when the market leg remains revision-limited.
Current fundamentals cannot populate a historical panel. Live recording/fixture
redistribution must respect each source's terms; synthetic fixtures prove formulas
and leakage checks only, not vendor truth.

## Model contracts

### Joint VAR and BVAR

Fit `s_t = c + sum(A_l s_(t-l), l=1..p) + e_t`. All preset state columns are jointly
modeled; independent univariate fits do not satisfy this contract. VAR minimizes
`||Y - X B||_F^2 / n + lambda * ||B_lags||_F^2` on training-standardized columns.
Candidate selection minimizes mean squared cumulative log-return error across
complete inner-validation outcomes at the requested horizon. For ties within
relative tolerance 1e-12, choose stronger shrinkage then fewer lags; direct-model
ties choose the simpler model (fewer nonzero coefficients or shallower/fewer trees),
then stable catalog order. Outer metrics cannot break ties.
Scaler means/standard deviations come from that fold only, with zero-variance
columns rejected. Estimate and report the full residual covariance. The diagnostic
unregularized option requires full column rank and the same sample guards.

BVAR uses a documented conjugate normal–inverse-Wishart, Minnesota-style shrinkage
prior: zero lag-coefficient means for these stationary/transformed variables,
lag-decaying prior variance, training-only scale estimates and a proper diffuse
intercept prior. Do not apply the own-first-lag mean of one used for persistent level
systems to returns. Tightness candidates are 0.1, 0.2, 0.5; only inner data can select them.
For standardized K-column states, fix `B0=0`, `nu0=K+2`, and
`S0=(nu0-K-1)*diag(training state variances)` using sample variances (ddof 1).
Use `Sigma ~ IW(S0,nu0)` with `E[Sigma]=S0/(nu0-K-1)` and
`B | Sigma ~ MatrixNormal(B0,V0,Sigma)`. The diagonal of `V0` is 1e6 for the
intercept and `lambda^2 / (lag^2 * variance_of_predictor)` for each lag coefficient.
This is a precisely specified Minnesota-style prior, not a claim to replicate
every hyperprior in the ECB paper.

Posterior: `Vn=(V0^-1 + X'X)^-1`, `Bn=Vn*(V0^-1*B0 + X'Y)`,
`nun=nu0+n`, `Sn=S0+Y'Y+B0'*V0^-1*B0-Bn'*Vn^-1*Bn`.
Use stable factorizations rather than literal inverse operations. Task M3 verifies
the parameterization against an independent small known-answer oracle before M4
codes posterior sampling. All prior values and the posterior-predictive method
are visible in results.

Check per-series ADF/KPSS (including conflicting conclusions), system rank,
conditioning, companion-matrix spectral radius and multivariate residual whiteness.
A rejected unit-root/stability assumption must be visible. Price/rate transforms
are catalog decisions rather than an unbounded auto-differencing search. Do not
silently re-scale explosive coefficients. Stable VAR fits require spectral radius
strictly below one; if no candidate passes, return an actionable insufficient-data/
model-fit error. Report rejected posterior/bootstrap draws and fail if fewer than
90% of requested draws are usable. State all numerical tolerances in formula tests.

Generate unknown future states recursively from joint innovations, preserving
cross-series covariance; never supply future actual SPY/sector returns or macro
releases. Modeled volatility/activity states are reduced-form predictors, not a
separate GARCH forecast or an accounting identity guaranteed by a VAR. For the
price result, accumulate only the target-return coordinate over the horizon.

### Direct multivariable alternatives

`elastic-net` and `boosted-trees` predict `y_(t,h)` directly for the requested
horizon, from the same as-of state plus the catalog's 12-minus-1-month momentum and
one-month return. Optional sector, beta and liquidity inputs are explicit. Fit a
separate horizon-specific model; do not supply future predictors or call a
one-step estimate a 20-session cumulative return. They have one target and multiple
predictors, unlike VAR's joint multiple equations.

Elastic-net uses training-standardized inputs, unpenalized intercept, L1 ratios
0.1/0.5/0.9 and normalized penalty candidates 0.001/0.01/0.1. Boosted trees use
squared-error regression, depth 2/3, learning rate 0.05, 100/300 iterations and a
minimum leaf of 20 observations. No random validation split or library-default
random early stopping. Select bounded candidates on the same inner folds. Report
feature definitions and optionally chronological block-permutation importance;
importance is neither causality nor proof of future skill. No full-data feature
ranking or PCA before splitting.

### Retained volatility and regression

Keep GARCH(1,1), EGARCH and EWMA in `econ volatility`, fitted to returns with a
constant/zero mean component, not a new ARIMA mean model. Show seeded simulated
80%/95% volatility bands and convention-based annualization. A known one-step
conditional variance may have a collapsed conditional band; label the conditioning.
CCC-GARCH covariance uses conditional diagonal variances and a declared sample
correlation estimate with the existing PSD guards. It is not automatically better
than every other covariance estimator. Retain OLS, HAC/HC0–HC3, VIF and residual
inference in `regress`; an explanatory fit is not held-out forecasting evidence.

## Validation and uncertainty

For each outer forecast origin, use only completed training outcomes before that
origin. Inside its trailing training window, tune on three forward validation
blocks, purging any fit sample whose horizon label crosses a validation boundary.
In direct models, purge at least `h` session positions at each boundary. Feature
construction, scaling, variable selection and any calibration never access later
rows. Validation histories may roll forward through observed covariates, never
unobserved outcomes. Record exact train/validation/test boundaries and effective
sample counts. Outer evaluation origins are spaced by `h` sessions, and each final
outcome must exist; do not random-shuffle time or score incomplete labels.

Always report a no-change-price/zero-log-return baseline and a historical mean
log-return baseline estimated from that origin's training data. These are control
forecasts, not reinstated standalone AR models. Score all models on identical outer
dates; report return RMSE/MAE, price RMSE/MAE, direction accuracy and baseline-relative
out-of-sample R² (undefined denominators explicitly null), 80%/95% empirical coverage,
interval width and sample count. The requested model stays visible even if it loses.
Outer results never choose/tune a winner and are never relabelled training data.

VAR uses joint residual moving-block bootstrap (block length `max(5,h)`) with
parameter refits and recursive paths; BVAR uses posterior-predictive draws with
joint innovations. Direct models use horizon-specific rolling-validation residual
quantiles (10/90 and 2.5/97.5) around the point prediction, requiring at least 100
completed residuals from inner validation, recording overlap/effective count and
an explicit lack of guaranteed nominal coverage under regime change. Use the same
interval-evaluation metrics across methods; do not substitute parameter confidence
intervals for future-observation prediction intervals. Report conditional assumptions
and any uncertainty component omitted by the selected method.

If an optional economic evaluation is requested, fix the mapping from signal to
positions before looking at the outer test, execute no earlier than the next
tradable session, and report transaction costs, turnover, exposure, net return,
Sharpe and drawdown through 0002 conventions. Statistical accuracy, profitability
and calibration are separate. No live order, automatic optimizer expected-return
change, or goal projection is part of this command.

## Implementation ownership and compatibility

Follow 0013: pure target transforms, linear algebra, feature formulas, metrics and
result types in `core/`; `application/commands/econ.py` coordinates availability,
ports and evaluation; concrete data/library adapters live in `adapters/`. A
repository-owned forecasting protocol returns owned arrays/results, not statsmodels,
arch or sklearn result objects. Shared conformance proves horizon semantics,
reproducibility, errors and uncertainty for each engine. Bootstrap composes adapters.
No I/O, settings reads, logging or tracing in core; preserve public existing imports.

Keep statsmodels/arch optional in `econ`; add scikit-learn there for direct models,
with doctor and dependency-audit coverage. Base installs still import/register the
commands and give exit 3 plus `pip install 'sobres[econ]'` when an engine is missing.
Do not add remote inference, GPU packages or new secrets to the default install.
Registry declarations generate CLI and explicitly exposed API/UI. Include progress,
cancellation and run provenance for longer evaluation jobs without changing math.

Remove ARIMA from the active forecast model enum, help, generated client and current
examples during implementation. Removed flags (`--order`, `--auto`, differencing /
AIC-only forecast choices) fail with a migration example; do not map them silently
to different mathematics. Keep old saved runs readable with their original labels.
An actually released interface requires the repository's compatibility/version gate.
The plan amendment itself does not edit runtime code, claim the new CLI is shipped,
or trigger a version bump/release. Existing `diagnose`, `regress`, `volatility`,
0002 risk-free conventions, 0008 assumptions and 0010 FX prohibitions stay intact.
