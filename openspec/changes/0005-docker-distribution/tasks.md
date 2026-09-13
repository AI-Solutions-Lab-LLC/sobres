# 0005 — Tasks

Planning amendment: source PR #11 at `eef53608b231e826f44edee9476aa4196bc20d77`.
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

## Wave A — the image

- [ ] **A1. Multi-stage `Dockerfile`** — Node builds the SPA, Python builds the
      wheel (or the release passes its published wheel), a slim runtime carries
      neither toolchain; `ENTRYPOINT ["sobres"]`, non-root uid/gid 1000, `/data`
      volume, `EXPOSE 8787`, `HEALTHCHECK` on `sobres deploy health`.
      → `tests/architecture/test_deployment_files.py`,
      `tests/cli/test_deploy.py::test_dockerfile_makes_the_cli_the_entrypoint_with_no_container_code_path`
- [ ] **A2. `.dockerignore`, `compose.yaml`** — nothing from a developer's
      machine reaches the build; the reference compose serves from a volume.
      → `tests/architecture/test_deployment_files.py::test_compose_reference_serves_on_8787_from_a_volume`

## Wave B — the container's behaviour through the CLI

- [ ] **B1. Data on a volume** — `sqlite:////data/sobres.db` by default; a
      non-writable mount fails at startup with exit 3 naming the mount; doctor's
      `data-volume` and `container-user` checks.
      → `tests/cli/test_deploy.py::test_the_database_lives_on_the_volume_and_a_missing_mount_fails_loudly`
- [ ] **B2. `sobres open` / `sobres init` in the container** — print the host URL,
      never launch; non-interactive by default, exit 3 naming a missing value.
      → `tests/cli/test_deploy.py`
- [ ] **B3. Health is doctor** — `/api/v1/health` runs the fast offline checks and
      reports `ready`; `sobres deploy health` exits 1 when it is not.
      → `tests/api/test_api.py::test_health_and_docs`, `tests/cli/test_deploy.py::test_health_command_reports_readiness`
- [ ] **B4. Signals** — a running job is cancelled at its checkpoint on shutdown and
      anything left is recorded as failed; orphans are recovered on start.
      → `tests/cli/test_deploy.py::test_signals_leave_no_job_running_forever`

## Wave C — `sobres deploy`

- [ ] **C1. `compose`** — pinned image, `/data` mounted, port published, resolved
      non-default settings inline, secrets referenced by name.
      → `tests/cli/test_deploy.py::test_compose_is_generated_from_resolved_configuration_without_secrets`
- [ ] **C2. `env`** — every variable, default and description; no secret values.
      → `tests/cli/test_deploy.py::test_env_template_lists_every_variable_and_no_secret_value`
- [ ] **C3. `check`** — doctor's checks plus image, database, bind, token
      (exposure is an error) and credentials by key.
      → `tests/cli/test_deploy.py::test_preflight_reports_the_deployment_and_calls_out_exposure`

## Wave D — pipeline and docs

- [ ] **D1. CI docker job** — builds the image, runs the documented quickstart
      (serve, health, UI, one-off command on the same volume, replacement),
      the missing-volume failure, the non-root check, the size budget.
      → `tests/architecture/test_deployment_files.py::test_ci_builds_the_image_and_runs_the_documented_quickstart`
- [ ] **D2. Release docker job** — same gate as PyPI, exact wheel, version parity,
      never overwrite a tag, amd64+arm64, provenance and SBOM, trivy scan, Docker
      Hub login with repository secrets, disarmed until `DOCKER_RELEASE_ENABLED`.
      → `tests/architecture/test_deployment_files.py::test_release_publishes_the_image_on_the_same_gate`
- [ ] **D3. `docs/DEPLOYING.md`**, README, CHANGELOG; 0011 C1 (the legacy name never
      appears in `sobres deploy` output).
      → `tests/cli/test_deploy.py`

## Additional container acceptance

- [ ] **R3 (2h)** Build and run the real image with lake/state sentinels present in
  the checkout. Proof: `tests/integration/test_container.py`; absent secret/lake
  files in layers, non-root writable volume, health, actual command, replacement
  and SIGTERM. Do not replace runtime checks with Dockerfile text assertions.
