# 0007 — Tasks

Planning amendment: source PR #13 at `4a8a60d88f60dfe1fd1409b6c7890f9416f2f668`.
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

- [ ] **A1. `core/factors.py`** — `factor_regression` (capm, ff3, ff5, ff5+mom) with
      OLS and Newey-West statistics, annualized alpha, R² and adjusted R²; the
      honesty statement; `rolling_loadings`; `capm_beta`; `to_monthly_returns`.
      → `tests/core/test_factors.py` (closed form, statsmodels as the HAC oracle)
- [ ] **A2. Minimum sample** — 36 monthly / 252 daily from `core/conventions.py`;
      the error names available and required counts.
      → `tests/core/test_factors.py::test_minimum_sample_names_available_and_required`

## Wave B — data

- [ ] **B1. Fundamentals** — `YahooSource.fundamentals`, `YFinanceProvider.get_fundamentals`,
      the fixture source, `fundamentals.json` recorded/synthesized by the scripts.
      → `tests/cli/test_analyze.py::test_missing_fundamentals_omits_the_block_and_keeps_the_rest`
- [ ] **B2. Cache casing fix** — mixed-case symbols round-trip with their values.
      → `tests/data/test_cache.py::test_mixed_case_symbols_round_trip_with_their_casing`

## Wave C — CLI

- [ ] **C1. `sobres analyze factors`** — one ticker, `--tickers`, or `--portfolio`;
      `--model`, `--frequency` (monthly default), `--rolling`, `--hac-lags`.
      → `tests/cli/test_analyze.py`
- [ ] **C2. `sobres analyze stock`** — price summary, annualized return and volatility,
      the 0002 risk panel, CAPM beta, fundamentals with the point-in-time note.
      → `tests/cli/test_analyze.py::test_stock_dashboard_has_every_section`
- [ ] **C3. Surfaces** — registry group, API route and UI view via the manifest.
      → `tests/api/test_parity.py`, `tests/invariants/test_every_command.py`
- [ ] **C4. Docs** — README, CHANGELOG, design.
