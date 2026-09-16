# 0010 — Tasks

Planning amendment: source PR #16 at `dc2ba7a31a322e73c2c5401aed77e07c4d6b41f1`.
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

- [x] **A1. `core/fx.py`** — decomposition, compounding, aggregation, currency risk,
      hedged returns and hedge cost.
      → `tests/core/test_fx.py`
- [x] **A2. `core/ppp.py`** — absolute vs relative PPP, real rate, valuation gaps in
      words, goal restatement, vintage staleness, ISO3 table, framing constants.
      → `tests/core/test_ppp.py`

## Wave B — data

- [x] **B1. `PppProvider`** — World Bank (default, keyless) and OECD parsers on recorded
      shapes, vintage through the cache, missing coverage named; BIS REER provider.
      → `tests/data/test_ppp_provider.py`
- [x] **B2. Settings and checks** — `SOBRES_PPP_PROVIDER`, `SOBRES_PPP_STALE_YEARS`;
      worldbank, oecd and bis in the provider registry (doctor reachability checks).
      → `tests/cli/test_doctor.py::test_every_setting_and_provider_has_a_check`
- [x] **B3. Fixtures** — synthesized World Bank JSON, OECD and BIS SDMX-CSV, two more FRED
      series; `synthesize_fixtures.py` and `record_fixtures.py` updated.

## Wave C — CLI

- [x] **C1. `sobres fx rates|convert|attribution|hedge`** — carry-forward stated, cross term
      shown, risk decomposition with correlations and exposure, hedge caveat, missing leg loud.
      → `tests/cli/test_fx.py`
- [x] **C2. `--hedged` on the optimizer** — hedged series, labelled with the assumption;
      `--base` required for mixed currencies (0001, re-asserted).
      → `tests/cli/test_fx.py::test_base_currency_is_explicit_and_hedged_optimization_is_labelled`
- [x] **C3. `sobres ppp compare|relative|reer|adjust-goal`** — framing on every output,
      direction in words, vintage and staleness, OECD alternative, saved goals restated.
      → `tests/cli/test_ppp.py`
- [x] **C4. `sobres plan … --save-goal`** — stores the target for `ppp adjust-goal`.
      → `tests/cli/test_ppp.py::test_adjust_goal_reads_a_goal_saved_by_plan`
- [x] **C5. Docs** — README, CHANGELOG, design.

## Foundation handoff

- [x] **R3 (1h)** FX provider selection resolved: ECB reference rates stay the only
  keyless FX adapter and the default; no FRED FX adapter is selected (a future one
  needs its own coverage amendment). Recordings keep their provenance.
  Proof: `tests/architecture/test_testing_spec.py::test_every_provider_has_a_recorded_fixture_with_provenance`,
  `tests/data/test_fx.py`, `tests/cli/test_doctor.py::test_every_setting_and_provider_has_a_check`;
  keyed live checks run in `.github/workflows/live.yml` and skip without a key.
