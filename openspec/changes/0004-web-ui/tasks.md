# 0004 — Tasks

Planning amendment: source PR #10 at `dbdfe69ecc4783aecd848637b07cf8b16a73fa69`.
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

## Wave A — HTTP API

- [x] **A1. Routes from the registry** — `POST /api/v1/<group>/<name>` for every
      command, body = the parameter model, `/api/docs` from the same declarations.
      → `tests/api/test_parity.py::test_every_command_has_a_route`
- [x] **A2. Errors keep their class and exit code** — usage 400, config 400,
      provider 502, insufficient data 422, internal 500 with the run id and no
      traceback.
      → `tests/api/test_api.py::test_errors_carry_the_shared_taxonomy`,
      `test_internal_errors_hide_the_traceback`
- [x] **A3. Jobs** — long-running commands return 202 and a job id; progress and
      state over SSE from the job stream; cancel stops the computation; the
      worker reconciles interrupted persisted jobs after restart.
      → `tests/api/test_api.py::test_long_running_commands_are_jobs_with_streamed_progress`,
      `test_cancellation_stops_at_the_next_checkpoint`, `test_job_survives_a_new_client`
- [x] **A4. Settings and doctor over HTTP** — settings share the `config set` code path;
      settings declared `browser_editable=False` (the database URL, the trace exporter
      destination, the config-file path) are refused over HTTP before anything is written;
      doctor's `--fix` repairs are the approved browser allowlist.
      → `tests/api/test_api.py::test_settings_endpoints_share_the_config_set_path`,
      `test_unsafe_settings_are_refused_over_http_but_not_from_the_cli`,
      `test_doctor_and_history_and_portfolios_over_the_api`
- [x] **A5. Observability** — every response carries `X-Run-Id` (and the trace id
      when tracing is on); `traceparent` is honoured and carried into jobs.
      → `tests/api/test_api.py::test_every_response_is_traced_and_carries_the_run_id`

## Wave B — Serving and security

- [x] **B1. `sobres serve`** — loopback by default; non-loopback generates a token
      once, stores it hashed, prints it once.
      → `tests/cli/test_serve.py`
- [x] **B2. Token handling** — bearer or `HttpOnly` `SameSite=Strict` cookie; never
      a query string; login rate-limited; rotation invalidates sessions.
      → `tests/api/test_api.py::test_non_loopback_requires_a_stored_hashed_token`,
      `test_login_attempts_are_rate_limited`, `test_token_strength_rules`
- [x] **B3. `sobres open [view ...]`** — starts the server if nothing answers,
      refuses a foreign process on the port, honours `BROWSER`.
      → `tests/cli/test_serve.py::test_open_reuses_a_running_server_and_rejects_a_foreign_one`
- [x] **B4. Terminal-only commands refuse over HTTP** — `serve`, `open` and
      `serve token rotate` keep their generated route (parity is one declaration, three
      surfaces) but answer 400 before any side effect; only the CLI performs them.
      → `tests/api/test_api.py::test_terminal_only_commands_refuse_over_http`

## Wave C — Frontend

- [x] **C1. Generated client** — `scripts/export_openapi.py --check` and
      `npm run check:client` fail CI on drift.
      → `.github/workflows/ci.yml` (`frontend` job)
- [x] **C2. Forms from the registry** — every field type has a renderer, defaults
      pre-filled, the equivalent command line shown live and copyable.
      → `tests/ui/test_frontend_source.py::test_defaults_are_visible_and_the_equivalent_command_is_shown`
- [x] **C3. Results** — provenance header, in-sample label, disclaimer, CSV
      download; frontier and backtest charts, code-split.
      → `tests/ui/test_frontend_source.py`
- [x] **C4. Theme** — dark by default, both themes complete, WCAG AA contrast
      computed over the palette, preference persists with a system option.
      → `tests/ui/test_frontend_source.py::test_text_contrast_meets_wcag_aa`
- [x] **C5. Views for every capability** — the manifest names every UI-exposed registry
      command plus settings, doctor, runs, portfolios, jobs.
      → `tests/api/test_parity.py::test_every_command_has_a_view`
- [x] **C6. Bundle budget** — 300 KB gzip on the initial bundle, enforced by
      `npm run build`; the wheel carries the built SPA.
      → `frontend/scripts/check-bundle.mjs`, `ci.yml` build job

## Additional acceptance proofs after the amendment

- [x] **R3 (2h)** Nonblocking worker execution and restart recovery.
  Proof: `tests/api/test_api.py::test_health_answers_while_a_job_runs` (health is served
  while a job computes on the worker thread) and
  `::test_orphaned_running_jobs_are_failed_on_restart` (no permanent `running` rows;
  the orphan is failed with the documented reason, never reported complete).
- [ ] **R4 (2h)** Browser scenarios with a real browser, not source-string assertions.
  Proof: `frontend/tests/e2e/` verifies forms, unsafe-operation absence, keyboard,
  charts, 400px layout, reduced motion, job cancellation and state after reload.
