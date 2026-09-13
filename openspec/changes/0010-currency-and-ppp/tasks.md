# 0010 — Tasks

Planning amendment: source PR #16 at `dc2ba7a31a322e73c2c5401aed77e07c4d6b41f1`.
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

- [ ] **A1. `core/fx.py`** — decomposition, compounding, aggregation, currency risk,
      hedged returns and hedge cost.
      → `tests/core/test_fx.py`
- [ ] **A2. `core/ppp.py`** — absolute vs relative PPP, real rate, valuation gaps in
      words, goal restatement, vintage staleness, ISO3 table, framing constants.
      → `tests/core/test_ppp.py`

## Wave B — data

- [ ] **B1. `PppProvider`** — World Bank (default, keyless) and OECD parsers on recorded
      shapes, vintage through the cache, missing coverage named; BIS REER provider.
      → `tests/data/test_ppp_provider.py`
- [ ] **B2. Settings and checks** — `SOBRES_PPP_PROVIDER`, `SOBRES_PPP_STALE_YEARS`;
      worldbank, oecd and bis in the provider registry (doctor reachability checks).
      → `tests/cli/test_doctor.py::test_every_setting_and_provider_has_a_check`
- [ ] **B3. Fixtures** — synthesized World Bank JSON, OECD and BIS SDMX-CSV, two more FRED
      series; `synthesize_fixtures.py` and `record_fixtures.py` updated.

## Wave C — CLI

- [ ] **C1. `sobres fx rates|convert|attribution|hedge`** — carry-forward stated, cross term
      shown, risk decomposition with correlations and exposure, hedge caveat, missing leg loud.
      → `tests/cli/test_fx.py`
- [ ] **C2. `--hedged` on the optimizer** — hedged series, labelled with the assumption;
      `--base` required for mixed currencies (0001, re-asserted).
      → `tests/cli/test_fx.py::test_base_currency_is_explicit_and_hedged_optimization_is_labelled`
- [ ] **C3. `sobres ppp compare|relative|reer|adjust-goal`** — framing on every output,
      direction in words, vintage and staleness, OECD alternative, saved goals restated.
      → `tests/cli/test_ppp.py`
- [ ] **C4. `sobres plan … --save-goal`** — stores the target for `ppp adjust-goal`.
      → `tests/cli/test_ppp.py::test_adjust_goal_reads_a_goal_saved_by_plan`
- [ ] **C5. Docs** — README, CHANGELOG, design.

## Foundation handoff

- [ ] **R3 (2h)** Reconcile real foundation FX/FRED recordings and the deferred
  FRED FX adapter selection. Keep ECB as the keyless default; if another FX
  adapter is needed, merge an explicit selection/coverage amendment first.
  Proof: recorded-provider provenance audit, cold/warm FX/vintage contract tests,
  `tests/cli/test_doctor.py`; keyed live verification is skipped if unavailable.
