# 0008 — Tasks

Planning amendment: source PR #14 at `563caa73e049a18b69acca233299a73341f7c31c`.
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

- [ ] **A1. `core/goals.py`** — future value, the four inverses, `solve`, timing,
      Fisher, periodic rates, month arithmetic.
      → `tests/core/test_goals.py`
- [ ] **A2. FIRE port** — `savings_rate`, `fi_number`, `project`, `coast_fi_balance`;
      parity with the fire-calculator golden fixture.
      → `tests/core/test_goals.py::test_parity_project` and siblings
- [ ] **A3. Named goals** — house (price growth), car (resale), education (5% cost
      inflation).
      → `tests/core/test_goals.py`
- [ ] **A4. `core/simulate.py`** — Monte Carlo and moving-block bootstrap, percentiles,
      success probability, seeds.
      → `tests/core/test_simulate.py`

## Wave B — CLI

- [ ] **B1. `sobres plan retire|house|car|education|goal`** — real/nominal flags and
      labels, CPI inflation with fallback, simulation by default, seed printed,
      bootstrap with a stated window, the tax note and the disclaimer.
      → `tests/cli/test_plan.py`
- [ ] **B2. Surfaces** — registry group, API routes, UI views.
      → `tests/api/test_parity.py`, `tests/invariants/test_every_command.py`
- [ ] **B3. Docs** — README, CHANGELOG, design.
