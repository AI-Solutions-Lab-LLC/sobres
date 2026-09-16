# 0002 — Tasks

The checked domain tasks record PR #8's reviewed implementation, merged to `main`
through #35 and re-verified there. Future work uses at most two-hour units.

Depends on 0001.

## Alignment prerequisite — removed 2026-09-16

The R0/R1/R2 tasks that required implementing 0013 before this capability could be
accepted were removed when 0013 was superseded (see its proposal). The shipped code
lives in `core/`, `data/`, `cli/` and `api/`, the layout enforced by
`tests/architecture/test_layering.py`; the domain tasks below are checked against the
tests that actually prove them on `main`.

## Wave A — return and risk primitives (parallel-safe)

- [x] **A1. Conventions** (0.5h)
      `core/conventions.py`: `PERIODS_PER_YEAR`, frequency inference from an index.
      → `tests/core/test_conventions.py::test_frequency_inference`
- [x] **A2. Returns** (2h)
      `core/returns.py`: simple, log, cumulative wealth, annualized (geometric +
      arithmetic), explicit NaN policy.
      → `tests/core/test_returns.py::test_geometric_matches_hand_computed`,
        `::test_annualization_uses_convention_table`,
        `::test_nan_policy_has_no_default`
- [x] **A3. Risk panel** (3h)
      `core/risk.py`: vol, Sharpe, Sortino, Calmar, max drawdown (+peak/trough/
      recovery dates), VaR/CVaR, skew, kurtosis, beta, correlation matrix.
      → `tests/core/test_risk.py` — every metric against a hand-computed 10-row
        fixture; `::test_max_drawdown_identifies_recovery_date`;
        `::test_beta_requires_30_overlapping_observations`

## Wave B — estimation (A2 first)

- [x] **B1. Expected returns** (2h)
      `core/moments.py`: `mean_historical`, `ewma`, `capm`.
      → `tests/core/test_moments.py::test_capm_uses_benchmark_and_risk_free`
- [x] **B2. Covariance** (3h)
      `sample`, `ledoit_wolf`, `ewma`, `semicovariance`; shrinkage intensity in
      `attrs`; `n_obs <= n_assets` → `InsufficientDataError`.
      → `::test_ledoit_wolf_is_default`,
        `::test_singular_case_raises_with_both_counts`
- [x] **B3. PSD conditioning** (2h)
      Symmetrize, eigenvalue clip, trace-preserving rescale, stderr warning.
      → `tests/core/test_psd.py::test_repairs_non_psd_and_warns`,
        `::test_repaired_matrix_is_psd`,
        `::test_already_psd_matrix_is_unchanged`

## Wave C — optimizer (B first) — critical path

- [x] **C1. Constraint model** (1.5h)
      `Constraints` dataclass: bounds, `max_weight`, `allow_short`; group constraints explicitly deferred.
      Infeasibility detected before the solver runs (`max_weight * n < 1`).
      → `tests/core/test_constraints.py::test_infeasible_max_weight_raises_usage`
- [x] **C2. `min_variance` + `equal_weight`** (2h)
      SLSQP scaffold, weight-sum equality, box bounds.
      → `::test_min_variance_matches_analytic_two_asset`
- [x] **C3. `max_sharpe`** (3h)
      Multi-start (equal-weight, min-variance, seeded random); best feasible wins.
      → `::test_max_sharpe_matches_closed_form_tangency`,
        `::test_deterministic_across_runs`
- [x] **C4. `target_return` / `target_risk`** (2h)
      → `::test_target_return_above_attainable_raises_with_max`
- [x] **C5. `risk_parity`** (2h)
      → `::test_risk_contributions_equal_within_tolerance`
- [x] **C6. Solver failure + concentration warning** (1h)
      → `::test_nonconvergence_raises_optimization_error`,
        `::test_concentration_warning_above_50pct`
- [x] **C7. Efficient frontier** (2.5h)
      N points from min-variance return to max attainable; flag min-var and
      max-Sharpe points.
      → `::test_volatility_non_decreasing_in_return`,
        `::test_named_points_flagged`

## Wave D — backtest (C first)

- [x] **D1. Walk-forward engine** (4h)
      Rebalance schedule; the slicing discipline from `design.md`; weight drift
      between rebalances.
      → `tests/core/test_backtest.py::test_no_lookahead_under_future_perturbation`
        ← *the most important test in this change*
      → `::test_weights_drift_between_rebalances`
- [x] **D2. Transaction costs** (1.5h)
      `turnover = 0.5 * Σ|w_new - w_drifted|` including residual cash; 10 bps per unit turnover.
      → `::test_turnover_formula`, `::test_default_cost_is_10bps`
- [x] **D3. Benchmark + result assembly** (2h)
      Equal-weight benchmark over the identical window; `BacktestResult`.
      → `::test_benchmark_uses_same_window`
- [x] **D4. Short-lookback handling** (1h)
      → `::test_start_shifts_to_first_viable_date_and_reports`

## Wave E — CLI (C, D first)

- [x] **E1. `sobres optimize markowitz`** (2h) — estimator provenance in the header.
      → `tests/cli/test_optimize.py::test_header_names_estimators`
- [x] **E2. `sobres optimize frontier`** (1.5h)
      → `::test_csv_columns_are_ret_vol_sharpe_then_tickers`
- [x] **E3. `sobres optimize backtest`** (2h) — side-by-side panels, OOS window, costs.
      → `::test_output_states_oos_window_and_costs`
- [x] **E4. `sobres optimize risk`** (1h) — fixed weights, full panel.
      → `::test_weights_must_match_ticker_count_and_sum_to_one`

## Wave F — validation and release

- [ ] **F1. R reference execution (deferred)** (2h)
      Run `legacy_code/Financial Portfolio Optimization.R` on a fixed universe; check
      outputs into `tests/fixtures/r_reference/`.
      *R and the script's Google Sheet were not reachable from the implementing
      environment; `scripts/r_reference.py` solves the same LP by exhaustive vertex
      enumeration (independent of the `linprog` path the port uses) on a fixed
      six-vehicle table. Re-run the R script on that table to replace the fixture.*
      → `tests/test_r_parity.py::test_weights_match_within_1e-4`
- [x] **F2. Textbook validation** (2h)
      Published two-asset min-variance/tangency answers, plus a synthetic three-asset frontier boundary check (not claimed as an independently published solution).
      → `tests/core/test_textbook_cases.py`
- [x] **F3. Docs: "Why your backtest looks too good"** (2h)
      Plain-language page on estimation error, in-sample vs. walk-forward, and how
      to read the gap. Linked from `sobres optimize backtest` output.
- [x] **F4. README** (1h) — worked example with real output (README quickstart).
- [ ] **F5. Publication** — the first published version is 1.1.0, not 1.0.0: it ships
      0002 together with 0003–0010. Tag and PyPI upload happen when `RELEASE_ENABLED`
      is armed (#21).

**Total: ~48h.** Critical path: B2 → B3 → C2 → C3 → C7 → D1 → E3.

## Definition of done

- [x] All four `sobres optimize` subcommands have CLI integration coverage; live checks are recorded in the PR verification notes
- [x] The no-lookahead test passes (D1)
- [x] Weights match independently enumerated LP vertices within `1e-4`; actual R execution remains deferred (F1)
- [x] Max-Sharpe matches the closed-form tangency portfolio within `1e-6` (C3)
- [x] `mypy --strict` clean; `pytest -m "not network"` green offline
- [x] Every scenario in the spec delta has a test referencing it
- [ ] Tagged and published — as 1.1.0, when `RELEASE_ENABLED` is armed (0000, #21)

## Review corrections (authorized follow-up)

- [x] G1. Integrate foundation correctness fixes and recorded fixtures.
- [x] G2. Fix future-rate leakage and retain per-decision provenance.
- [x] G3. Correct initial drawdown, arithmetic ratios and cash-inclusive cost accounting.
- [x] G4. Preserve return intervals and reject unresolved public-core gaps.
- [x] G5. Wire CAPM benchmark and target backtests; validate before fetching.
- [x] G6. Condition public covariance, expose the solver protocol and analytic gradients.
- [x] G7. Return exact frontier counts, add progress and typed metric tables.
- [x] G8. Reconcile spec/contracts/examples and retain honest deferred/release status.
- [x] G9. Validate tests, lint, typing, packaging, strict OpenSpec and bounded live runs.

## Verification on the future aligned layout — removed 2026-09-16

The A3v–D1v re-verification units existed to re-prove the known answers on the 0013
package layout. 0013 was superseded; the known-answer suites they named
(`tests/core/test_risk.py`, `test_optimize.py`, `test_backtest.py`) are the proofs and
run on `main`.
