# 0009 — Revised implementation tasks

2026-09-13 owner amendment: multivariable price forecasting replaces ARIMA;
GARCH and robust diagnostics remain. Source candidate: PR #15 at `6a1f12d`.
**All boxes are unchecked.** Existing tests establish older candidate behavior,
not the scenarios newly specified here. This commit is planning only.

Each item is one coherent commit of at most about two hours. Split an item further
before coding if necessary; group 1–3 related items per implementation PR. Named
proofs below are required future tests, not claims that those files already exist.

## R — Accepted scope and aligned base

- [ ] **R0 (1h)** Record issue #31, this amendment's merged planning SHA, implemented
  0013/predecessors, current candidate and scenario ledger. Proof: ancestry/diff report.
- [ ] **R1 (2h)** Map forecasting types/services/engines to the 0013 package map;
  specify owned ForecastEngine inputs/results. Proof: `tests/architecture/test_layering.py`
  and `tests/contracts/test_forecast_engines.py` scaffolding contract review.
- [ ] **R2 (1h)** Record whether ARIMA ever shipped and choose its removal/version
  route. Proof: release/tag audit and `tests/cli/test_econ_migration.py` cases agreed.

## D — Predictor and target data contracts

- [ ] **D1 (2h)** Implement split-only target/price-draw transformations and explicit
  dividend/total-return separation. Proof: `tests/core/test_forecast_target.py`
  independently computed splits/dividends, Jensen effect and sub-unit examples.
- [ ] **D2 (2h)** Extend market-provider ingestion/metadata where needed for raw
  close/volume/actions; preserve existing recordings. Proof:
  `tests/contracts/test_forecast_market_data.py` matching units and unavailable fields.
- [ ] **D3 (2h)** Implement the four basic features with versioned formulas/windows.
  Proof: `tests/core/test_forecast_features.py` hand-computed activity/volatility;
  no bridged gaps, zero volume or duplicate/constant columns.
- [ ] **D4 (2h)** Add momentum, sector and optional beta/illiquidity transforms.
  Proof: `tests/core/test_forecast_features.py` exact lag/window boundaries and
  `tests/application/test_econ_sources.py` explicit sector selection.
- [ ] **D5 (2h)** Specify and implement availability/vintage joins through owned
  provider ports. Proof: `tests/contracts/test_forecast_vintages.py` delayed release,
  revision and distinct vintage cache identity; no current-fundamental backfill.
- [ ] **D6 (2h)** Implement the macro preset, transforms and staleness/credential
  errors using the vintage contract. Proof: `tests/application/test_forecast_presets.py`
  DGS3MO/T10Y3M units, VIX, no-key failure and no preset substitution.
- [ ] **D7 (2h)** Register extended entries only where provider history/rights and
  availability are supported; expose capability errors otherwise. Proof:
  `tests/contracts/test_forecast_catalog.py` metadata, rights decision, source fixtures
  and unavailable fundamentals/factors; no synthetic payload passed off as recorded.

## M — Bounded multivariable models

- [ ] **M1 (2h)** Write normalized VAR/ridge formulas and implement a joint fit with
  cross-lag coefficients. Proof: `tests/core/test_var.py` known two-variable process,
  lambda-zero equivalence and independent ridge matrix answer.
- [ ] **M2 (2h)** Add lag/conditioning/sample guards, full residual covariance,
  companion stability and recursive means. Proof: `tests/core/test_var.py`
  unstable, collinear, too-short and cross-covariance cases.
- [ ] **M3 (2h)** Verify the design's BVAR prior/posterior formula note: all hyperparameters,
  scale/lag normalization, degrees of freedom and intercept treatment. Proof:
  independent small normal–inverse-Wishart oracle reviewed before posterior coding.
- [ ] **M4 (2h)** Implement BVAR fit and posterior draws against M3. Proof:
  `tests/core/test_bvar.py` posterior oracle, zero-centered return prior and seeds.
- [ ] **M5 (2h)** Implement direct cumulative-horizon labels and elastic-net adapter.
  Proof: `tests/contracts/test_forecast_engines.py` horizon/lag semantics and
  `tests/core/test_direct_forecasts.py` known multivariable linear case.
- [ ] **M6 (2h)** Implement bounded boosted-tree adapter without random validation
  or implicit random early stopping. Proof: `tests/contracts/test_forecast_engines.py`
  fixed seed, multifeature dependence and frozen-origin future perturbations.
- [ ] **M7 (2h)** Add shared system/ADF/KPSS/residual diagnostics and candidate
  rejection records. Proof: `tests/core/test_forecast_diagnostics.py`, retaining
  `tests/core/test_timeseries.py` diagnostic and GARCH regression cases.

## E — Leakage-resistant evaluation

- [ ] **E1 (2h)** Implement chronological inner/outer splits, horizon purging and
  sample/history guards. Proof: `tests/core/test_forecast_splits.py` exact boundaries,
  incomplete labels and at least 12 nonoverlapping default outer outcomes.
- [ ] **E2 (2h)** Implement fold-local preprocessing and bounded tuning for VAR/BVAR.
  Proof: `tests/application/test_forecast_selection.py` future perturbation leaves
  earlier scaling/prior/candidates/selection unchanged.
- [ ] **E3 (2h)** Wire direct-model tuning to identical folds with fold-local feature
  construction. Proof: same selection suite; no global scaling/ranking/PCA or
  future label enters training.
- [ ] **E4 (2h)** Implement no-change and training-mean baselines plus common-date
  price/return/direction/R² metrics. Proof: `tests/core/test_forecast_evaluation.py`
  hand calculations, negative skill and undefined-denominator cases.
- [ ] **E5 (2h)** Implement interval coverage/width and optional costed diagnostics
  through 0002. Proof: same evaluation suite plus
  `tests/application/test_forecast_strategy.py` next-session execution, fixed signal
  rule, turnover/costs and no mutation of optimizer/goal/trading state.

## U — Honest uncertainty

- [ ] **U1 (2h)** Implement joint block residual bootstrap and VAR parameter refits.
  Proof: `tests/core/test_forecast_intervals.py` correlated innovations, parameter
  uncertainty, deterministic seeds and failed-draw guard.
- [ ] **U2 (2h)** Implement BVAR posterior-predictive paths and price conversion.
  Proof: interval suite and BVAR oracle; include observation noise, not only
  coefficient uncertainty, and report stability rejection counts.
- [ ] **U3 (2h)** Implement direct horizon-specific validation-residual intervals
  and calibration sample guard. Proof: interval suite with known quantiles,
  overlapping labels and no outer-test calibration.

## S — Application and public surfaces

- [ ] **S1 (2h)** Implement explicit source/catalog resolution and preset orchestration
  in application. Proof: `tests/application/test_econ_sources.py` ambiguity-before-I/O,
  required variable errors and `tests/application/test_forecast_presets.py` defaults.
- [ ] **S2 (2h)** Register forecast/evaluate parameter/result models and provenance
  including price basis, sources, versions and boundaries. Proof:
  `tests/cli/test_econ_multivariable.py` proposed default/examples and every format.
- [ ] **S3 (2h)** Remove candidate ARIMA model/flags/auto-differencing routes and
  migrate help/current docs; retain historical saved-run readability and diagnostic
  APIs. Proof: `tests/cli/test_econ_migration.py` plus `tests/cli/test_persistence.py`.
- [ ] **S4 (2h)** Register optional engines/dependencies and doctor checks. Proof:
  `tests/cli/test_econ_dependencies.py` base-wheel import/help and missing-extra
  exit 3; dependency audit with no GPU/cloud package in the basic install.
- [ ] **S5 (2h)** Update explicit API exposure/OpenAPI/client with shared service and
  cancellation. Proof: `tests/api/test_econ_forecasts.py` parity, progress and cancel;
  actual generated-client drift/type/build checks.
- [ ] **S6 (2h)** Update forecast/evaluate UI inputs, intervals, warnings and run
  history. Proof: browser journey for selected model/preset, negative skill,
  cancellation and old ARIMA history (not merely source assertions).
- [ ] **S7 (2h)** Preserve GARCH/EGARCH/EWMA, CCC covariance and robust regression.
  Proof: existing timeseries/regression/CLI suites with independent volatility
  answers, PSD checks and no new univariate mean forecaster.

## V — Review evidence and release separation

- [ ] **V1 (2h)** Execute fixture-based CLI/API/installed-wheel journeys for all four
  forecasters, with dummy secrets and every format/log level. Proof: saved outputs,
  `tests/invariants/test_every_command.py`, redaction and architecture checks.
- [ ] **V2 (2h)** Execute bounded authorized real-provider checks when available;
  record vintage/price-action/volume limitations and fixture provenance. Proof:
  provider contract + separate live evidence; do not infer vendor truth from simulation.
- [ ] **V3 (2h)** Run held-out research evaluation and ablations (basic vs sector /
  macro / momentum) on a preregistered ticker/date set. Proof: reproducible data/model
  manifests, baseline/calibration tables, negative results and compute cost. This is
  a bounded evaluation unit; split any larger research experiment into new tasks.
- [ ] **V4 (2h)** Produce scenario-to-assertion evidence, reconcile PR #16/spec 0010,
  update issue #31 and run full aligned make check/build/audit plus strict OpenSpec
  validation. Proof: reviewed artifact report; no release/deployment activation.

FAVAR/PCR, VECM and foundation models are deferred extension decisions in
research.md, not unchecked promises silently required by this milestone. Core
multivariable model tasks above are required. A green old ARIMA suite completes none
of M/E/U/S acceptance by itself.
