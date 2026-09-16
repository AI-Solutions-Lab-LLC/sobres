# 0005 — Tasks

Planning amendment: source PR #11 at `eef53608b231e826f44edee9476aa4196bc20d77`.
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

## Wave A — the image

- [x] **A1. Multi-stage `Dockerfile`** — Node builds the SPA, Python builds the
      wheel (or the release passes its published wheel), a slim runtime carries
      neither toolchain; `ENTRYPOINT ["sobres"]`, non-root uid/gid 1000, `/data`
      volume, `EXPOSE 8787`, `HEALTHCHECK` on `sobres deploy health`.
      → `tests/architecture/test_deployment_files.py`,
      `tests/cli/test_deploy.py::test_dockerfile_makes_the_cli_the_entrypoint_with_no_container_code_path`
- [x] **A2. `.dockerignore`, `compose.yaml`** — nothing from a developer's
      machine reaches the build; the reference compose serves from a volume.
      → `tests/architecture/test_deployment_files.py::test_compose_reference_serves_on_8787_from_a_volume`

## Wave B — the container's behaviour through the CLI

- [x] **B1. Data on a volume** — `sqlite:////data/sobres.db` by default; a
      non-writable mount fails at startup with exit 3 naming the mount; doctor's
      `data-volume` and `container-user` checks.
      → `tests/cli/test_deploy.py::test_the_database_lives_on_the_volume_and_a_missing_mount_fails_loudly`
- [x] **B2. `sobres open` / `sobres init` in the container** — print the host URL,
      never launch; non-interactive by default, exit 3 naming a missing value.
      → `tests/cli/test_deploy.py`
- [x] **B3. Health is doctor** — `/api/v1/health` runs the fast offline checks and
      reports `ready`; `sobres deploy health` exits 1 when it is not.
      → `tests/api/test_api.py::test_health_and_docs`, `tests/cli/test_deploy.py::test_health_command_reports_readiness`
- [x] **B4. Signals** — a running job is cancelled at its checkpoint on shutdown and
      anything left is recorded as failed; orphans are recovered on start.
      → `tests/cli/test_deploy.py::test_signals_leave_no_job_running_forever`

## Wave C — `sobres deploy`

- [x] **C1. `compose`** — pinned image, `/data` mounted, port published, resolved
      non-default settings inline, secrets referenced by name.
      → `tests/cli/test_deploy.py::test_compose_is_generated_from_resolved_configuration_without_secrets`
- [x] **C2. `env`** — every variable, default and description; no secret values.
      → `tests/cli/test_deploy.py::test_env_template_lists_every_variable_and_no_secret_value`
- [x] **C3. `check`** — doctor's checks plus image, database, bind, token
      (exposure is an error) and credentials by key.
      → `tests/cli/test_deploy.py::test_preflight_reports_the_deployment_and_calls_out_exposure`

## Wave D — pipeline and docs

- [x] **D1. CI docker job** — builds the image, runs the documented quickstart
      (serve, health, UI, one-off command on the same volume, replacement),
      the missing-volume failure, the non-root check, the size budget.
      → `tests/architecture/test_deployment_files.py::test_ci_builds_the_image_and_runs_the_documented_quickstart`
- [x] **D2. Release docker job** — same gate as PyPI, exact wheel, version parity,
      never overwrite a tag, amd64+arm64, provenance and SBOM, trivy scan, Docker
      Hub login with repository secrets, disarmed until `DOCKER_RELEASE_ENABLED`.
      → `tests/architecture/test_deployment_files.py::test_release_publishes_the_image_on_the_same_gate`
- [x] **D3. `docs/DEPLOYING.md`**, README, CHANGELOG; 0011 C1 (the legacy name never
      appears in `sobres deploy` output).
      → `tests/cli/test_deploy.py`

## Additional container acceptance

- [x] **R3 (2h)** Build and run the real image in CI: the documented quickstart
  (serve, health, UI, a one-off command on the same volume, replacement), the
  missing-volume failure, the non-root check and the size budget run against the
  built container, not against Dockerfile text.
  Proof: the `Container image` job in `.github/workflows/ci.yml`, pinned by
  `tests/architecture/test_deployment_files.py::test_ci_builds_the_image_and_runs_the_documented_quickstart`;
  `test_no_secret_reaches_the_image` covers the build context. (The private context-lake
  sentinels the 0013 plan mentioned do not exist in this repository.)
