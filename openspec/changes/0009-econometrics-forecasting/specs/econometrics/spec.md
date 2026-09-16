# econometrics — spec delta (0009)

This active delta replaces its former ARIMA requirement under the owner's
2026-09-13 scope amendment. It is not a claim that the candidate code has changed.
The versioned defaults and formulas in design.md and research.md are part of this
contract; later changes to them require a recorded preset/model version.

## ADDED Requirements

### Requirement: Multivariable forecasting scope

Equity forecasts SHALL use multiple informative series. Supported price-forecast
models SHALL be `var`, `bvar`, `elastic-net` and `boosted-trees`. Standalone AR,
ARMA, ARIMA, SARIMA and auto-ARIMA forecasts SHALL NOT remain in the active model
surface or act as fallbacks. VAR's joint lag dynamics and GARCH volatility remain.

#### Scenario: Default stock forecast
- **WHEN** `sobres econ forecast ticker:AAPL` runs with adequate supported data
- **THEN** it SHALL use the versioned `equity-basic` ridge VAR and a 20-target-session horizon
- **AND** SHALL state all selected predictors, transforms, lag order, penalty and price basis
- **AND** SHALL return a multivariable forecast with uncertainty and held-out baseline evidence

#### Scenario: Removed univariate selection
- **WHEN** an ARIMA-family model or removed order/auto-differencing flag is requested
- **THEN** the command SHALL exit 2 with an example of the new multivariable interface
- **AND** SHALL NOT silently choose VAR or modify a historical saved ARIMA run

### Requirement: Joint vector models

VAR/BVAR SHALL model a joint state using cross-variable lags and full residual
covariance, with bounded training-only selection and explicit stability guards.

#### Scenario: Cross-variable dynamics
- **WHEN** a known two-variable process has a nonzero cross-lag effect
- **THEN** the fitted joint model SHALL recover that relationship within justified tolerance
- **AND** a perturbation to the predictor's observed history SHALL affect the target forecast
- **AND** independent single-series fits SHALL NOT satisfy the scenario

#### Scenario: Shrinkage and prior are visible
- **WHEN** ridge VAR or BVAR is fitted
- **THEN** the normalized penalty or complete prior and selected hyperparameters SHALL be reported
- **AND** BVAR return-equation prior means SHALL NOT assume a unit-root price-level system
- **AND** scaling, prior scales and candidate selection SHALL use only the training/inner data

#### Scenario: Invalid system
- **WHEN** inputs duplicate a column, lack variation/history, exceed dimension bounds, or yield no stable candidate
- **THEN** the fit SHALL fail with the invalid inputs and an actionable next step
- **AND** SHALL NOT rescale explosive coefficients, insert a guessed predictor or fall back to a univariate model

### Requirement: Direct multivariable alternatives

Elastic-net and boosted trees SHALL forecast the requested cumulative log-price
return directly from multiple as-of predictors, under the same evaluation protocol.

#### Scenario: Horizon-specific direct forecast
- **WHEN** either direct model forecasts 20 sessions
- **THEN** its training labels SHALL be 20-session cumulative target log returns
- **AND** its lagged states/momentum inputs SHALL be known at each origin
- **AND** future predictor values or one-session labels SHALL NOT substitute for this target

#### Scenario: Comparable models
- **WHEN** `econ evaluate` compares VAR, BVAR and direct models
- **THEN** all SHALL be scored on identical complete outer dates and target conventions
- **AND** search spaces, losses and rejected candidates SHALL be visible
- **AND** neither outer test results nor random early-stopping splits SHALL tune any model

### Requirement: Researched and versioned predictors

The predictor catalog SHALL record economic rationale, formula, source, unit,
frequency, availability, staleness, role and evidence limitations for each input.
Research associations SHALL NOT be presented as universal or causal predictors.

#### Scenario: Keyless basic preset
- **WHEN** `equity-basic` runs for a supported USD US equity with complete provider data
- **THEN** it SHALL use target/SPY price returns, log realized volatility and change in log dollar-volume activity without an API key
- **AND** dollar volume SHALL use raw price and matching raw volume units
- **AND** the input manifest SHALL identify the exact windows and catalog version

#### Scenario: Sector or macro inputs
- **WHEN** a sector is supplied or `equity-macro` is selected
- **THEN** the named sector or DGS3MO/T10Y3M/VIXCLS inputs SHALL be included with their catalog transforms and available-at metadata
- **AND** missing credentials or required data SHALL fail visibly rather than revert to another preset
- **AND** current sector membership SHALL NOT silently determine a historical classification

#### Scenario: Historical fundamentals and factors
- **WHEN** extended valuation, fundamental or factor inputs are requested for evaluation
- **THEN** only values/exposures available by each origin SHALL be eligible
- **AND** today's fundamentals or contemporaneous future-period factor returns SHALL NOT be backfilled
- **AND** absent supported history SHALL produce an actionable capability/data error

### Requirement: Point-in-time input alignment

Forecasting SHALL distinguish observation dates, publication availability, vintage
and retrieval time. A row dated in the past is not by itself point-in-time evidence.

#### Scenario: Delayed or revised macro release
- **WHEN** a macro observation is released or revised after an evaluated origin
- **THEN** the earlier origin SHALL retain only the value actually available then
- **AND** adding the later release or revision SHALL leave its forecast unchanged
- **AND** cache identity SHALL preserve distinct vintages rather than overwrite them

#### Scenario: Market revisions and gaps
- **WHEN** historical market data lacks archived as-of snapshots or includes missing sessions
- **THEN** evaluation SHALL disclose the revision limitation and exact missing-data policy
- **AND** SHALL NOT claim point-in-time tradability or bridge a missing price observation
- **AND** current-period macro data SHALL NOT be interpolated into unreleased daily values

#### Scenario: Unknown future covariates
- **WHEN** the forecast extends beyond its origin
- **THEN** VAR/BVAR SHALL simulate future states jointly and direct models SHALL use only origin-known inputs
- **AND** changing any actual future market, sector, macro or factor observation SHALL NOT change that origin's forecast

### Requirement: Explicit stock-price target

Price forecasts SHALL model split-only log-price returns and identify price/share
basis, currency, origin, horizon and corporate-action assumptions. Total-return
adjusted prices SHALL NOT masquerade as future quoted stock prices.

#### Scenario: Price reconstruction
- **WHEN** predictive log-return draws are converted into a stock-price distribution
- **THEN** each draw SHALL be compounded from the observed anchor in origin share units
- **AND** mean, median and bounds SHALL be calculated from the resulting price draws
- **AND** exponentiating the mean log return SHALL NOT be labelled arithmetic expected price

#### Scenario: Splits, dividends and unsupported currency
- **WHEN** data includes a split, cash dividend, sub-unit quote or mixed currency
- **THEN** split-only and dividend-reinvested series SHALL remain distinguishable and sub-units SHALL be normalized
- **AND** unsupported benchmark/currency combinations SHALL fail before fitting
- **AND** no forecast SHALL project an FX rate or PPP convergence to manufacture a stock-price output

### Requirement: Chronological evaluation and baselines

Every forecast SHALL include a time-ordered held-out evaluation using design.md's
window, fold and sample guards. Evaluation SHALL remain distinct from model tuning.

#### Scenario: Fold-local training
- **WHEN** a fold is fitted and selected
- **THEN** transformations, feature selection, scaling, priors and calibration SHALL exclude later observations
- **AND** training labels crossing the validation boundary SHALL be purged
- **AND** altering later data SHALL NOT change an earlier fold's fitted choices or prediction

#### Scenario: Honest skill report
- **WHEN** an outer evaluation completes
- **THEN** price/return RMSE and MAE, direction accuracy, baseline-relative R², interval coverage/width and sample counts SHALL be reported
- **AND** no-change-price and training-only historical-mean-return controls SHALL use identical dates
- **AND** negative skill SHALL remain visible; zero-denominator statistics SHALL be explicitly undefined

#### Scenario: Insufficient evaluation history
- **WHEN** there are too few complete training, calibration or outer outcomes
- **THEN** the command SHALL report counts and the required window/next step
- **AND** SHALL NOT replace held-out evidence with training accuracy or silently reduce the evaluation period

#### Scenario: Optional economic evaluation
- **WHEN** a user requests a strategy diagnostic
- **THEN** the signal rule SHALL be fixed before outer scoring and execute no earlier than the next tradable session
- **AND** costs, turnover, exposure and net metrics SHALL be reported using 0002 conventions
- **AND** forecasts SHALL NOT automatically change optimizer assumptions, goal projections or place orders

### Requirement: Forecast uncertainty and provenance

Every forecast format SHALL include 80% and 95% future-observation prediction
bounds, the point statistic's meaning, method/assumptions and reproducibility data.

#### Scenario: Intervals are mandatory
- **WHEN** a price or return forecast is rendered as table, JSON or CSV
- **THEN** its point, 80% bounds and 95% bounds SHALL all be present and correctly ordered
- **AND** coefficient confidence intervals SHALL NOT be substituted for prediction intervals

#### Scenario: Joint and direct uncertainty
- **WHEN** VAR, BVAR or a direct model computes intervals
- **THEN** it SHALL use the design's joint bootstrap, posterior-predictive or horizon-specific validation-residual method respectively
- **AND** SHALL state omitted uncertainty, overlap/effective calibration count and regime limitations
- **AND** failed draws or missing calibration evidence SHALL NOT be silently discarded beyond the declared guard

#### Scenario: Reproducible run
- **WHEN** input snapshots, catalog/model versions, configuration and seed are identical
- **THEN** predictions, intervals and evaluation choices SHALL be reproducible within the documented numeric/platform contract
- **AND** the run SHALL record source hashes/vintages, boundaries, transforms, settings, candidate losses and seed
- **AND** logging/tracing SHALL NOT alter results or expose secrets

### Requirement: Stationarity diagnostics

Econometric diagnostics SHALL report complementary stationarity tests and lag
correlations, including disagreement. ACF/PACF are diagnostics, not AR forecasters.

#### Scenario: Tests reported
- **WHEN** `sobres econ diagnose <series>` runs
- **THEN** ADF and KPSS statistics, p-values, lags and conclusions SHALL be reported
- **AND** disagreement SHALL be stated rather than resolved silently

#### Scenario: ACF and PACF
- **WHEN** diagnostics run
- **THEN** ACF/PACF through lag 20 SHALL be reported with significance bounds

### Requirement: Volatility forecasting

Volatility forecasts SHALL retain GARCH(1,1), EGARCH and EWMA with conditional
uncertainty, convention-based annualization and optimizer covariance guarantees.

#### Scenario: GARCH fit
- **WHEN** `sobres econ volatility ticker:SPY --model garch` runs
- **THEN** a GARCH(1,1) return-volatility model SHALL provide seeded conditional forecast bands
- **AND** `egarch` and `ewma` SHALL remain available without an ARIMA mean forecaster

#### Scenario: Annualized output
- **WHEN** volatility is reported
- **THEN** annualization SHALL use the conventions table and be labelled
- **AND** a collapsed known one-step conditional band SHALL be explained

#### Scenario: Feeds the optimizer
- **WHEN** `covariance(returns, method="garch")` runs
- **THEN** CCC-GARCH covariance SHALL satisfy the existing PSD/finite-value contract
- **AND** superiority over other covariance estimators SHALL NOT be asserted without evidence

### Requirement: Regression with robust inference

Regression output SHALL preserve robust inference, collinearity and residual
diagnostics without treating an explanatory fit as forecasting evidence.

#### Scenario: Robust standard errors
- **WHEN** `sobres econ regress --robust <kind>` runs
- **THEN** hac, hc0–hc3 and none SHALL remain accepted and identified

#### Scenario: Multicollinearity
- **WHEN** multiple regressors are supplied
- **THEN** VIF SHALL be reported per regressor and values above 10 flagged

#### Scenario: Diagnostics reported
- **WHEN** regression completes
- **THEN** R², adjusted R², F with p-value, Durbin-Watson and a heteroskedasticity test SHALL be reported

### Requirement: Dependency gating and source resolution

Optional engines and data sources SHALL have explicit configuration, owned ports
and actionable errors. Source inference by symbol length/digits SHALL NOT be used.

#### Scenario: Missing extra
- **WHEN** an econ operation lacks its required optional dependency
- **THEN** it SHALL exit 3 with `This command needs the econ extra. Install it with: pip install 'sobres[econ]'`
- **AND** base package imports and command discovery SHALL still work without traceback

#### Scenario: Ambiguous source
- **WHEN** a bare symbol lacks unambiguous catalog metadata or a source flag
- **THEN** the command SHALL exit 2 with a `fred:` or `ticker:` example before network access

#### Scenario: Named source
- **WHEN** `fred:CPIAUCSL` or `ticker:SPY` is supplied
- **THEN** only the named provider SHALL supply that input and its transform SHALL be stated

### Requirement: Aligned application boundaries and migration

This capability SHALL follow implemented 0013 ownership and explicit surface
exposure, preserving unaffected public behavior and historical user state.

#### Scenario: Capability resumes after the alignment migration
- **WHEN** revised 0009 implementation resumes
- **THEN** the amended plan's merged ancestry and implemented prerequisites SHALL be recorded
- **AND** pure math SHALL remain in core, shared orchestration in application, protocols in ports and concrete I/O/library adapters in adapters
- **AND** conformance and installed-package checks SHALL run without private context

#### Scenario: Capability is reviewed for another surface
- **WHEN** forecasting or evaluation is exposed in API/UI
- **THEN** exposure SHALL be explicit with shared validation, intervals, provenance, progress and cancellation
- **AND** generated schemas/forms SHALL reflect removal of ARIMA choices without corrupting stored old runs
- **AND** settings, new sources and optional dependencies SHALL have doctor coverage
