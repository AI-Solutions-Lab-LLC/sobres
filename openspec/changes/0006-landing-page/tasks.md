# 0006 — Tasks

Planning amendment: source PR #12 at `a2f297c44ed61cc341c6da9778abf14acf6c4540`.
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

## Wave A — figures from the product

- [x] **A1. `site/scripts/record_figures.py`** — runs `sobres optimize frontier`,
      `backtest`, `markowitz` (JSON and the table transcript) and writes
      `site/src/data/`; `figures-meta.json` records commands, window, estimators
      and whether the data was the synthetic fixtures.
      → `tests/ui/test_site_source.py::test_animation_shows_the_product_from_recorded_data`
- [x] **A2. Shared tokens** — `frontend/src/theme/tokens.css`, imported by both
      the app and the page.
      → `tests/ui/test_site_source.py::test_shares_the_apps_design_tokens_and_is_dark_by_design`

## Wave B — the page

- [x] **B1. `site/index.html`** — headline, description, install commands, repo
      link, disclaimer and roadmap present in the served HTML; dark ground painted
      inline; OG/Twitter metadata; one h1, correct heading order, skip link.
      → `tests/ui/test_site_source.py`
- [x] **B2. `main.ts`** — generated version and commands, copy buttons that announce,
      text alternatives set before any library loads, deferred imports.
      → `tests/ui/test_site_source.py::test_readable_before_javascript_and_libraries_deferred`
- [x] **B3. `figures.ts`** — ECharts frontier (max-Sharpe lands last, labelled) and
      equity curve, drawn on entering the viewport; final state under reduced motion.
- [x] **B4. `motion.ts`** — GSAP + ScrollTrigger + Lenis: terminal typing, the Sharpe
      number falling, cards fading in; never loaded under reduced motion; no pinning.
      → `tests/ui/test_site_source.py::test_reduced_motion_renders_final_states_and_native_scrolling`
- [x] **B5. `og-image.png`** — rendered from the built page by `scripts/og_image.py`.
      → `tests/ui/test_site_source.py::test_link_previews_depict_the_product`

## Wave C — gates and publishing

- [x] **C1. Build gates** — `generate.mjs` (version or fail), `tsc --strict`,
      `check-bundle.mjs` (150 KB), `check-content.mjs` (no old command name, no third-party
      request, readable content, disclaimer).
      → `tests/ui/test_site_source.py::test_performance_gates_are_build_failures`
- [x] **C2. Lighthouse** — `lighthouserc.json`, mobile, three categories ≥ 0.95, run
      by `pages.yml` before any deploy.
- [x] **C3. `pages.yml`** — build and audit on PRs and `main`; deploy job alone holds
      `pages: write` and `id-token: write`, only on `main` and only when the repository
      variable `PAGES_ENABLED` is `true` (the build and audit still run otherwise).
      → `tests/ui/test_site_source.py::test_published_automatically_with_least_privilege_and_no_broken_deploys`
- [x] **C4. Docs** — README, CHANGELOG; 0011 C2.

## Additional site acceptance

- [x] **R3 (1h)** Hosting inquiry and explicit publication. The page links a public
  GitHub issue form (`.github/ISSUE_TEMPLATE/hosting-inquiry.yml`) that states its
  visibility and asks for no credentials or financial records; the deploy job is gated
  on `PAGES_ENABLED`.
  Proof: `tests/ui/test_site_source.py::test_hosting_inquiry_is_public_and_asks_for_nothing_confidential`,
  `::test_published_automatically_with_least_privilege_and_no_broken_deploys`.
- [ ] **R4 (2h)** Browser scenarios with a real browser, not source-string assertions.
  Proof: `site/tests/e2e/` verifies the inquiry link, keyboard, reduced motion and
  narrow screens in a real browser.
