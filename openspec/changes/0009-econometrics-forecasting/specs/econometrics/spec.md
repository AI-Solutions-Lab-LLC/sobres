# econometrics — spec delta (0009)

This delta is the shipped contract of the 2026-09-13 multivariable amendment as
implemented on 2026-09-16: a regularized joint VAR and a Minnesota-prior BVAR
over the keyless `equity-basic` state, with chronological held-out evaluation
and mandatory intervals. The direct elastic-net and boosted-tree models, the
FRED macro preset with vintage joins, the extended fundamentals/factor catalog
and the optional strategy diagnostic are **deferred** to a follow-up change
(tracked as an issue); their scenarios are not part of this contract. The
versioned defaults and formulas in design.md are part of it.

## ADDED Requirements

### Requirement: Multivariable forecasting scope

Equity forecasts SHALL use multiple informative series. Supported price-forecast
models SHALL be `var` and `bvar`. Standalone AR, ARMA, ARIMA, SARIMA and
auto-ARIMA forecasts SHALL NOT remain in the active model surface or act as
fallbacks. VAR's joint lag dynamics and GARCH volatility remain.

#### Scenario: Default stock forecast
- **WHEN** `sobres econ forecast ticker:AAPL` runs with adequate supported data
- **THEN** it SHALL use the versioned `equity-basic` ridge VAR and a 20-target-session horizon
- **AND** SHALL state all selected predictors, transforms, lag order, penalty and price basis
- **AND** SHALL return a multivariable forecast with uncertainty and held-out baseline evidence

#### Scenario: Removed univariate selection
- **WHEN** an ARIMA-family model is requested with `--model`
- **THEN** the command SHALL exit 2 naming the removal and an example of the multivariable interface
- **AND** the removed order/auto-differencing flags SHALL be unknown options (exit 2), never mapped to VAR
- **AND** a historical saved ARIMA run SHALL remain readable with its original labels

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

#### Scenario: Comparable models
- **WHEN** `econ evaluate` compares VAR and BVAR
- **THEN** both SHALL be scored on identical complete outer dates and target conventions
- **AND** per-origin selections SHALL be visible and the controls SHALL share those dates
- **AND** outer test results SHALL NOT tune or choose either model

### Requirement: Researched and versioned predictors

The predictor catalog SHALL record role, formula, window and source for each
input, under a catalog version. Research associations SHALL NOT be presented as
universal or causal predictors.

#### Scenario: Keyless basic preset
- **WHEN** `equity-basic` runs for a supported USD US equity with complete provider data
- **THEN** it SHALL use target/SPY price returns, log realized volatility and change in log dollar-volume activity without an API key
- **AND** dollar volume SHALL use raw price and matching raw volume units
- **AND** the input manifest SHALL identify the exact windows and catalog version

#### Scenario: Sector input
- **WHEN** `--sector ticker:<symbol>` is supplied
- **THEN** that one sector return SHALL join the joint state with its catalog transform
- **AND** a sector equal to the target or the benchmark SHALL be refused before any fit
- **AND** current sector membership SHALL NOT be inferred; only an explicit series is used

### Requirement: Point-in-time input alignment

Forecasting SHALL distinguish observation dates from retrieval time and SHALL
never let a future observation enter an earlier origin's forecast.

#### Scenario: Market revisions and gaps
- **WHEN** historical market data lacks archived as-of snapshots or includes missing sessions
- **THEN** the output SHALL disclose the revision limitation and the exact missing-data policy
- **AND** SHALL NOT claim point-in-time tradability or bridge a missing price observation

#### Scenario: Unknown future covariates
- **WHEN** the forecast extends beyond its origin
- **THEN** VAR/BVAR SHALL simulate future states jointly from the origin's information only
- **AND** changing any later market, sector or activity observation SHALL NOT change that origin's forecast

### Requirement: Explicit stock-price target

Price forecasts SHALL model split-only log-price returns and identify price
basis, currency, origin, horizon and corporate-action assumptions. Total-return
adjusted prices SHALL NOT masquerade as future quoted stock prices.

#### Scenario: Price reconstruction
- **WHEN** predictive log-return draws are converted into a stock-price distribution
- **THEN** each draw SHALL be compounded from the observed anchor in origin share units
- **AND** the point SHALL be the median price draw, with the mean price reported separately
- **AND** exponentiating the mean log return SHALL NOT be labelled arithmetic expected price

#### Scenario: Splits, dividends and unsupported currency
- **WHEN** the target, benchmark or sector are quoted in different currencies
- **THEN** the command SHALL fail before fitting and SHALL NOT project an exchange rate
- **AND** the split-only close SHALL be the price basis, distinct from the dividend-reinvested series

### Requirement: Chronological evaluation and baselines

Every forecast SHALL include a time-ordered held-out evaluation using design.md's
window, fold and sample guards. Evaluation SHALL remain distinct from model tuning.

#### Scenario: Fold-local training
- **WHEN** a fold is fitted and selected
- **THEN** scaling, priors and candidate selection SHALL exclude later observations
- **AND** training labels crossing the validation boundary SHALL be purged
- **AND** altering later data SHALL NOT change an earlier fold's fitted choices or prediction

#### Scenario: Honest skill report
- **WHEN** an outer evaluation completes
- **THEN** return and price RMSE/MAE, direction accuracy, out-of-sample R² versus no-change, interval coverage/width and sample counts SHALL be reported
- **AND** no-change and training-only historical-mean controls SHALL use identical dates
- **AND** negative skill SHALL remain visible; zero-denominator or sideless statistics SHALL be explicitly undefined

#### Scenario: Insufficient evaluation history
- **WHEN** there are too few complete training or outer outcomes
- **THEN** the command SHALL report counts and the required window/next step
- **AND** SHALL NOT replace held-out evidence with training accuracy or silently shorten the evaluation

### Requirement: Forecast uncertainty and provenance

Every forecast format SHALL include 80% and 95% future-observation prediction
bounds, the point statistic's meaning, method/assumptions and reproducibility data.

#### Scenario: Intervals are mandatory
- **WHEN** a price forecast is rendered as table, JSON or CSV
- **THEN** its point, 80% bounds and 95% bounds SHALL all be present and correctly ordered
- **AND** coefficient confidence intervals SHALL NOT be substituted for prediction intervals

#### Scenario: Joint uncertainty
- **WHEN** VAR or BVAR computes intervals
- **THEN** it SHALL use the design's joint residual bootstrap with refits or the posterior-predictive method respectively
- **AND** SHALL report the requested, usable and rejected draws and fail below the usable-draw guard

#### Scenario: Reproducible run
- **WHEN** input snapshots, catalog/model versions, configuration and seed are identical
- **THEN** predictions, intervals and evaluation choices SHALL be identical
- **AND** the run SHALL record versions, boundaries, transforms, candidate losses and the seed
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

Optional engines SHALL have actionable errors. Source inference by symbol
length or digits SHALL NOT be used.

#### Scenario: Missing extra
- **WHEN** an econ operation lacks its required optional dependency
- **THEN** it SHALL exit 3 with `This command needs the econ extra. Install it with: pip install 'sobres[econ]'`
- **AND** base package imports and command discovery SHALL still work without traceback

#### Scenario: Catalog source resolution
- **WHEN** a bare symbol is supplied
- **THEN** it SHALL be a FRED series only if it is in the FRED catalog or `--source fred` is given
- **AND** any other bare symbol SHALL be a price ticker; length and digits SHALL NOT decide

#### Scenario: Named source
- **WHEN** `fred:CPIAUCSL` or `ticker:SPY` is supplied
- **THEN** only the named provider SHALL supply that input and its transform SHALL be stated

### Requirement: Surfaces

Forecasting and evaluation SHALL be registry declarations like every other
command, so the HTTP route, the generated client and the UI form derive from them.

#### Scenario: Forecasting is exposed like every command
- **WHEN** `econ forecast` or `econ evaluate` is registered
- **THEN** the parity suite SHALL find its route, schema and view
- **AND** both SHALL run as jobs with progress over the held-out origins
