# 0008 — Tasks

Planning amendment: source PR #14 at `563caa73e049a18b69acca233299a73341f7c31c`.
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

- [x] **A1. `core/goals.py`** — future value, the four inverses, `solve`, timing,
      Fisher, periodic rates, month arithmetic.
      → `tests/core/test_goals.py`
- [x] **A2. FIRE port** — `savings_rate`, `fi_number`, `project`, `coast_fi_balance`;
      parity with the fire-calculator golden fixture.
      → `tests/core/test_goals.py::test_parity_project` and siblings
- [x] **A3. Named goals** — house (price growth), car (resale), education (5% cost
      inflation).
      → `tests/core/test_goals.py`
- [x] **A4. `core/simulate.py`** — Monte Carlo and moving-block bootstrap, percentiles,
      success probability, seeds.
      → `tests/core/test_simulate.py`

## Wave B — CLI

- [x] **B1. `sobres plan retire|house|car|education|goal`** — real/nominal flags and
      labels, CPI inflation with fallback, simulation by default, seed printed,
      bootstrap with a stated window, the tax note and the disclaimer.
      → `tests/cli/test_plan.py`
- [x] **B2. Surfaces** — registry group, API routes, UI views.
      → `tests/api/test_parity.py`, `tests/invariants/test_every_command.py`
- [x] **B3. Docs** — README, CHANGELOG, design.
