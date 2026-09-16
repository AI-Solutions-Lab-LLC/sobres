# 0009 — Implementation tasks

Shipped scope (2026-09-16): joint ridge VAR and Minnesota-prior BVAR over the
keyless `equity-basic` state, optional sector series, chronological selection and
held-out evaluation with controls, mandatory intervals, `econ evaluate`, ARIMA
removal. The R/D/M/E/U/S/V plan of the 2026-09-13 amendment is reduced to what is
checked below; every unchecked item is deferred and tracked as a follow-up issue.

Each task names the test that proves it.

## R — Accepted scope and aligned base

- [x] **R0** Recorded: issue #31; ARIMA never shipped to an index (1.1.0 unpublished), so its
      removal needs no deprecation cycle. → `tests/cli/test_econ.py::test_removed_arima_model_exits_2_with_the_new_example`
- [x] **R1** Forecast math in `core/forecast.py`, orchestration in `cli/commands/econ.py`,
      data through the price provider. → `tests/architecture/test_layering.py`

## D — Predictor and target data contracts

- [x] **D1** Split-only close as the price basis, distinct from adjusted close; nonpositive
      prices refused. → `tests/core/test_forecast.py::test_invalid_systems_are_refused_not_repaired`,
      `tests/cli/test_econ.py::test_default_stock_forecast_is_a_joint_model_with_held_out_evidence`
- [x] **D2** Raw close and raw volume from the provider (`field="close"`, `field="volume"`).
      → `tests/cli/test_econ.py::test_default_stock_forecast_is_a_joint_model_with_held_out_evidence`
- [x] **D3** The four basic features with versioned formulas and windows; zero volume rejected.
      → `tests/core/test_forecast.py::test_basic_state_formulas_by_hand`
- [x] **D4** Explicit `--sector ticker:<symbol>`; duplicates refused. → `tests/cli/test_econ.py::test_sector_joins_the_state_and_invalid_systems_are_refused`
- [ ] **D5 (deferred)** Availability/vintage joins for macro series.
- [ ] **D6 (deferred)** The `equity-macro` preset (DGS3MO, T10Y3M, VIXCLS) with vintage cache identity.
- [ ] **D7 (deferred)** Extended catalog entries (fundamentals, factor states, credit spread).

## M — Bounded multivariable models

- [x] **M1** Ridge VAR closed form; λ = 0 equals least squares; cross-lag recovery on a known
      process. → `tests/core/test_forecast.py::test_cross_variable_dynamics_are_recovered_and_matter`,
      `::test_ridge_zero_is_least_squares_and_shrinkage_is_visible`
- [x] **M2** Lag/sample guards, full residual covariance, companion stability, recursive means.
      → `tests/core/test_forecast.py::test_companion_radius_matches_closed_form_roots`,
      `::test_forecast_from_reports_the_selection_and_refuses_an_unstable_system`
- [x] **M3/M4** BVAR conjugate posterior checked against the written-out NIW update and its
      prior limits. → `tests/core/test_forecast.py::test_bvar_posterior_matches_the_conjugate_formulas_and_prior_limits`
- [ ] **M5 (deferred)** Direct cumulative-horizon labels and an elastic-net engine.
- [ ] **M6 (deferred)** Bounded boosted-tree engine (needs scikit-learn in the econ extra).
- [x] **M7** ADF/KPSS per series, conditioning, spectral radius and residual Ljung-Box in the
      result. → `tests/cli/test_econ.py::test_default_stock_forecast_is_a_joint_model_with_held_out_evidence`

## E — Leakage-resistant evaluation

- [x] **E1** Three chronological inner blocks with horizon purging; outer origins spaced by
      the horizon; at least 12 outcomes. → `tests/core/test_forecast.py::test_evaluation_is_fold_local_and_reports_counts`
- [x] **E2** Fold-local scaling/priors/selection; later data leaves earlier folds unchanged.
      → `tests/core/test_forecast.py::test_evaluation_is_fold_local_and_reports_counts`
- [ ] **E3 (deferred)** Direct-model tuning on the same folds.
- [x] **E4** No-change and training-mean controls; hand-computed metrics with undefined cases.
      → `tests/core/test_forecast.py::test_metrics_by_hand_including_undefined_cases`
- [x] **E5** Interval coverage and width per model. → `tests/cli/test_econ.py::test_evaluate_scores_models_and_controls_on_identical_dates`
- [ ] **E5b (deferred)** Optional costed strategy diagnostic through 0002.

## U — Honest uncertainty

- [x] **U1** Joint residual moving-block bootstrap with batched parameter refits; seeded;
      usable-draw guard. → `tests/core/test_forecast.py::test_draws_are_seeded_and_reproducible_and_the_guard_counts_rejections`
- [x] **U2** BVAR posterior-predictive paths with joint innovations and stability rejection.
      → same test
- [ ] **U3 (deferred)** Direct-model validation-residual intervals.

## S — Application and public surfaces

- [x] **S1** Catalog-based source resolution; no length/digit heuristic. → `tests/cli/test_econ.py::test_catalog_source_resolution_never_guesses_from_shape`
- [x] **S2** `econ forecast` / `econ evaluate` parameter and result models with provenance
      (price basis, catalog/model versions, boundaries, candidates, seed). → `tests/cli/test_econ.py`
- [x] **S3** ARIMA removed from the model enum, core and docs with a migration error.
      → `tests/cli/test_econ.py::test_removed_arima_model_exits_2_with_the_new_example`
- [x] **S4** Econ extra gating unchanged (exit 3). → `tests/cli/test_econ.py::test_missing_extra_exits_3_with_the_install_hint`
- [x] **S5** Routes, OpenAPI and generated client regenerated; both commands are jobs with
      progress. → `tests/api/test_parity.py`, `frontend/openapi.json`
- [x] **S6** The UI form and result table derive from the registry (no ARIMA choices remain).
      → `frontend/src/api/schema.d.ts`
- [x] **S7** GARCH/EGARCH/EWMA, CCC covariance and robust regression preserved.
      → `tests/core/test_timeseries.py`, `tests/cli/test_econ.py`

## V — Evidence

- [x] **V1** Fixture-based CLI journeys for both models in every format; invariants over every
      command. → `tests/invariants/test_every_command.py`
- [ ] **V2 (deferred)** Bounded live-provider checks for a real SPY history (the offline
      benchmark is a labelled synthetic market proxy; `scripts/synthesize_market_proxy.py`).
- [ ] **V3 (deferred)** Preregistered held-out research evaluation and ablations.
- [x] **V4** Scenario-to-test coverage enforced by `tests/architecture/test_scenarios.py`
      (status implemented); strict OpenSpec validation.
