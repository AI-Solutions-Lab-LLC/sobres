# 0007 — Tasks

Planning amendment: source PR #13 at `4a8a60d88f60dfe1fd1409b6c7890f9416f2f668`.
Checked tasks are proven by the named tests on `main` (2026-09-16 reconciliation).
Each unestimated task has a maximum 2h budget; split larger work before coding.
No task authorizes publication; release activation remains a maintainer action.

Each task names the test that proves it.

## Alignment prerequisite — removed 2026-09-16

The R0/R1/R2 tasks that required implementing 0013 before this capability could be
accepted were removed when 0013 was superseded (see its proposal). The shipped code
lives in `core/`, `data/`, `cli/` and `api/`, the layout enforced by
`tests/architecture/test_layering.py`; the domain tasks below are checked against the
tests that actually prove them on `main`.

## Wave A — core

- [x] **A1. `core/factors.py`** — `factor_regression` (capm, ff3, ff5, ff5+mom) with
      OLS and Newey-West statistics, annualized alpha, R² and adjusted R²; the
      honesty statement; `rolling_loadings`; `capm_beta`; `to_monthly_returns`.
      → `tests/core/test_factors.py` (closed form, statsmodels as the HAC oracle)
- [x] **A2. Minimum sample** — 36 monthly / 252 daily from `core/conventions.py`;
      the error names available and required counts.
      → `tests/core/test_factors.py::test_minimum_sample_names_available_and_required`

## Wave B — data

- [x] **B1. Fundamentals** — `YahooSource.fundamentals`, `YFinanceProvider.get_fundamentals`,
      the fixture source, `fundamentals.json` recorded/synthesized by the scripts.
      → `tests/cli/test_analyze.py::test_missing_fundamentals_omits_the_block_and_keeps_the_rest`
- [x] **B2. Cache casing fix** — mixed-case symbols round-trip with their values.
      → `tests/data/test_cache.py::test_mixed_case_symbols_round_trip_with_their_casing`

## Wave C — CLI

- [x] **C1. `sobres analyze factors`** — one ticker, `--tickers`, or `--portfolio`;
      `--model`, `--frequency` (monthly default), `--rolling`, `--hac-lags`.
      → `tests/cli/test_analyze.py`
- [x] **C2. `sobres analyze stock`** — price summary, annualized return and volatility,
      the 0002 risk panel, CAPM beta, fundamentals with the point-in-time note.
      → `tests/cli/test_analyze.py::test_stock_dashboard_has_every_section`
- [x] **C3. Surfaces** — registry group, API route and UI view via the manifest.
      → `tests/api/test_parity.py`, `tests/invariants/test_every_command.py`
- [x] **C4. Docs** — README, CHANGELOG, design.
