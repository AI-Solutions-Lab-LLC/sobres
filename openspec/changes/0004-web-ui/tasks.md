# 0004 — Tasks

Planning amendment: source PR #10 at `dbdfe69ecc4783aecd848637b07cf8b16a73fa69`.
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

## Wave A — HTTP API

- [ ] **A1. Routes from the registry** — `POST /api/v1/<group>/<name>` for every
      explicitly HTTP-exposed command, body = the parameter model, `/api/docs` from the same declarations.
      → `tests/api/test_parity.py::test_every_exposed_command_has_a_route`
- [ ] **A2. Errors keep their class and exit code** — usage 400, config 400,
      provider 502, insufficient data 422, internal 500 with the run id and no
      traceback.
      → `tests/api/test_api.py::test_errors_carry_the_shared_taxonomy`,
      `test_internal_errors_hide_the_traceback`
- [ ] **A3. Jobs** — long-running commands return 202 and a job id; progress and
      state over SSE from the job stream; cancel stops the computation; the
      worker reconciles interrupted persisted jobs after restart.
      → `tests/api/test_api.py::test_long_running_commands_are_jobs_with_streamed_progress`,
      `test_cancellation_stops_at_the_next_checkpoint`, `test_job_survives_a_new_client`
- [ ] **A4. Settings and doctor over HTTP** — the browser-safe settings allowlist
      uses shared config services; unsafe fields and local repairs are refused.
      → `tests/api/test_api.py::test_settings_endpoints_share_the_config_set_path`,
      `test_doctor_and_history_and_portfolios_over_the_api`
- [ ] **A5. Observability** — every response carries `X-Run-Id` (and the trace id
      when tracing is on); `traceparent` is honoured and carried into jobs.
      → `tests/api/test_api.py::test_every_response_is_traced_and_carries_the_run_id`

## Wave B — Serving and security

- [ ] **B1. `sobres serve`** — loopback by default; non-loopback generates a token
      once, stores it hashed, prints it once.
      → `tests/cli/test_serve.py`
- [ ] **B2. Token handling** — bearer or `HttpOnly` `SameSite=Strict` cookie; never
      a query string; login rate-limited; rotation invalidates sessions.
      → `tests/api/test_api.py::test_non_loopback_requires_a_stored_hashed_token`,
      `test_login_attempts_are_rate_limited`, `test_token_strength_rules`
- [ ] **B3. `sobres open [view ...]`** — starts the server if nothing answers,
      refuses a foreign process on the port, honours `BROWSER`.
      → `tests/cli/test_serve.py::test_open_reuses_a_running_server_and_rejects_a_foreign_one`
- [ ] **B4. Terminal-only commands have no route, schema entry or actionable UI form.**
      → `tests/api/test_api.py::test_terminal_only_commands_have_no_route_or_schema`

## Wave C — Frontend

- [ ] **C1. Generated client** — `scripts/export_openapi.py --check` and
      `npm run check:client` fail CI on drift.
      → `.github/workflows/ci.yml` (`frontend` job)
- [ ] **C2. Forms from the registry** — every field type has a renderer, defaults
      pre-filled, the equivalent command line shown live and copyable.
      → `tests/ui/test_frontend_source.py::test_defaults_are_visible_and_the_equivalent_command_is_shown`
- [ ] **C3. Results** — provenance header, in-sample label, disclaimer, CSV
      download; frontier and backtest charts, code-split.
      → `tests/ui/test_frontend_source.py`
- [ ] **C4. Theme** — dark by default, both themes complete, WCAG AA contrast
      computed over the palette, preference persists with a system option.
      → `tests/ui/test_frontend_source.py::test_text_contrast_meets_wcag_aa`
- [ ] **C5. Views for every capability** — the manifest names every UI-exposed registry
      command plus settings, doctor, runs, portfolios, jobs.
      → `tests/api/test_parity.py::test_every_exposed_command_has_a_view`
- [ ] **C6. Bundle budget** — 300 KB gzip on the initial bundle, enforced by
      `npm run build`; the wheel carries the built SPA.
      → `frontend/scripts/check-bundle.mjs`, `ci.yml` build job

## Additional acceptance proofs after the amendment

- [ ] **R3 (2h)** App factory/lifecycle and nonblocking worker execution.
  Proof: `tests/api/test_composition.py`; fresh factory cleanup, concurrent health
  during blocked synchronous work, restart recovery and no permanent running rows.
- [ ] **R4 (2h)** Browser scenarios with a real browser, not source-string assertions.
  Proof: `frontend/tests/e2e/` verifies forms, unsafe-operation absence, keyboard,
  charts, 400px layout, reduced motion, job cancellation and state after reload.
