# 0006 — Tasks

Planning amendment: source PR #12 at `a2f297c44ed61cc341c6da9778abf14acf6c4540`.
All tasks are unchecked because acceptance must be reverified on the new base.
Each unestimated task has a maximum 2h budget; split larger work before coding.
Each original task uses the named suite in its wave plus the R2 behavior checks.
No task authorizes publication; release activation remains a maintainer action.

Each task names the test that proves it.

## Alignment prerequisite — before the original waves

- [ ] **R0 (1h)** Verify the issue and merged planning ancestry, then reconcile the
  candidate branch with merged 0013 and its predecessor. Preserve the foundation's
  real recordings and fixes. Proof: source diff, merge-base and task/scenario ledger.
- [ ] **R1 (2h)** Reconcile the one `site/` home page with the template's contact
  route and explicit publication controls. Proof: site build/content checks,
  real browser navigation, and disabled-publication workflow fixtures.
- [ ] **R2 (2h)** Re-run affected behavior through the installed package and any
  exposed API/UI, all formats, dummy-secret checks and relevant real integration.
  Proof: named tests below, full `make check`, `make build`, `make audit` and a
  scenario-to-assertion report. Source-only UI checks or synthetic vendor fixtures
  cannot establish browser behavior or live vendor truth.

## Wave A — figures from the product

- [ ] **A1. `site/scripts/record_figures.py`** — runs `sobres optimize frontier`,
      `backtest`, `markowitz` (JSON and the table transcript) and writes
      `site/src/data/`; `figures-meta.json` records commands, window, estimators
      and whether the data was the synthetic fixtures.
      → `tests/ui/test_site_source.py::test_animation_shows_the_product_from_recorded_data`
- [ ] **A2. Shared tokens** — `frontend/src/theme/tokens.css`, imported by both
      the app and the page.
      → `tests/ui/test_site_source.py::test_shares_the_apps_design_tokens_and_is_dark_by_design`

## Wave B — the page

- [ ] **B1. `site/index.html`** — headline, description, install commands, repo
      link, disclaimer and roadmap present in the served HTML; dark ground painted
      inline; OG/Twitter metadata; one h1, correct heading order, skip link.
      → `tests/ui/test_site_source.py`
- [ ] **B2. `main.ts`** — generated version and commands, copy buttons that announce,
      text alternatives set before any library loads, deferred imports.
      → `tests/ui/test_site_source.py::test_readable_before_javascript_and_libraries_deferred`
- [ ] **B3. `figures.ts`** — ECharts frontier (max-Sharpe lands last, labelled) and
      equity curve, drawn on entering the viewport; final state under reduced motion.
- [ ] **B4. `motion.ts`** — GSAP + ScrollTrigger + Lenis: terminal typing, the Sharpe
      number falling, cards fading in; never loaded under reduced motion; no pinning.
      → `tests/ui/test_site_source.py::test_reduced_motion_renders_final_states_and_native_scrolling`
- [ ] **B5. `og-image.png`** — rendered from the built page by `scripts/og_image.py`.
      → `tests/ui/test_site_source.py::test_link_previews_depict_the_product`

## Wave C — gates and publishing

- [ ] **C1. Build gates** — `generate.mjs` (version or fail), `tsc --strict`,
      `check-bundle.mjs` (150 KB), `check-content.mjs` (no old command name, no third-party
      request, readable content, disclaimer).
      → `tests/ui/test_site_source.py::test_performance_gates_are_build_failures`
- [ ] **C2. Lighthouse** — `lighthouserc.json`, mobile, three categories ≥ 0.95, run
      by `pages.yml` before any deploy.
- [ ] **C3. `pages.yml`** — build and audit on PRs and `main`; deploy job alone holds
      `pages: write` and `id-token: write`, only on `main` with `PAGES_ENABLED=true` and reviewed publication access.
      → `tests/ui/test_site_source.py::test_published_automatically_with_least_privilege_and_no_broken_deploys`
- [ ] **C4. Docs** — README, CHANGELOG; 0011 C2.

## Additional site acceptance

- [ ] **R3 (2h)** Hosting inquiry, explicit publication and browser behavior.
  Proof: `site/tests/e2e/` verifies visible/non-confidential inquiry, real product
  examples, keyboard/reduced motion/narrow screens; workflow fixtures assert PRs
  and `PAGES_ENABLED=false` never deploy or upload the repository/context lake.
