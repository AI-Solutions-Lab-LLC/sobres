# 0009 — Tasks

Planning amendment: source PR #15 at `88df04e01a5993c24a0857ef387e0b03c24fbacc`.
All tasks are unchecked because acceptance must be reverified on the new base.
Each unestimated task has a maximum 2h budget; split larger work before coding.
Each original task uses the named suite in its wave plus the R2 behavior checks.
No task authorizes publication; release activation remains a maintainer action.

Each task names the test that proves it.

## Alignment prerequisite — before the original waves

- [ ] **R0 (1h)** Verify the issue and merged planning ancestry, then reconcile the
  candidate branch with merged 0013 and its predecessor. Preserve the foundation's
  real recordings and fixes. Proof: source diff, merge-base and task/scenario ledger.
- [ ] **R1 (2h)** Apply this proposal's package/ownership amendment using 0013's
  shared services and ports; keep public commands and financial math compatible.
  Proof: `tests/architecture/test_layering.py` plus the existing capability's
  CLI/contract tests on the new base; no new use cases in legacy facades.
- [ ] **R2 (2h)** Re-run affected behavior through the installed package and any
  exposed API/UI, all formats, dummy-secret checks and relevant real integration.
  Proof: named tests below, full `make check`, `make build`, `make audit` and a
  scenario-to-assertion report. Source-only UI checks or synthetic vendor fixtures
  cannot establish browser behavior or live vendor truth.

## Wave A — core

- [ ] **A1. `core/timeseries.py`** — ADF/KPSS with disagreement stated, ACF/PACF with
      bounds, differencing to stationarity (refuse past d=2), ARIMA grid selection
      with candidates, forecasts with 80%/95% intervals, Ljung-Box.
      → `tests/core/test_timeseries.py`
- [ ] **A2. Volatility** — GARCH(1,1), EGARCH, EWMA via `arch` with simulated bands,
      annualized by the conventions table, seed reported.
      → `tests/core/test_timeseries.py::test_garch_fit_recovers_persistence_and_offers_egarch_and_ewma`
- [ ] **A3. GARCH covariance in the estimator registry** — `covariance(..., method="garch")`.
      → `tests/core/test_timeseries.py::test_feeds_the_optimizer_through_the_estimator_registry`
- [ ] **A4. `core/regression.py`** — OLS with hac/hc0–hc3/none, VIF (>10 flagged), R²,
      adjusted R², F, Durbin-Watson, Breusch-Pagan.
      → `tests/core/test_regression.py`
- [ ] **A5. Dependency gating** — exit 3 with the install hint, no traceback.
      → `tests/core/test_timeseries.py::test_missing_extra_is_an_exit_3_with_the_install_hint`,
      `tests/cli/test_econ.py::test_missing_extra_exits_3_with_the_install_hint`

## Wave B — CLI

- [ ] **B1. `sobres econ diagnose|forecast|volatility|regress`** — symbol resolution,
      transforms stated, every header line the spec asks for.
      → `tests/cli/test_econ.py`
- [ ] **B2. Surfaces** — registry group, API routes, UI views; `arch` in the econ extra and
      in doctor's extras table.
      → `tests/api/test_parity.py`, `tests/invariants/test_every_command.py`
- [ ] **B3. Docs** — README, CHANGELOG, design.

## Additional source-selection acceptance

- [ ] **R3 (2h)** Remove source guessing from the candidate branch and require
  explicit prefixes/flags or unambiguous catalog metadata.
  Proof: `tests/application/test_econ_sources.py`; ambiguous input exits 2 before
  network access, explicit FRED/ticker inputs call exactly the named provider.
