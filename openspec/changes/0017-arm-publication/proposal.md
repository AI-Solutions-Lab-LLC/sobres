# 0017 — Arm publication

## Outcome

A version bump merged to `main` reaches PyPI, Docker Hub and the public landing
page without anyone setting a repository variable first.

## Why

0000 shipped three arming switches — `RELEASE_ENABLED`, `PAGES_ENABLED` and
`DOCKER_RELEASE_ENABLED` — so that merging the pipeline itself could not fire a
publish before upload credentials existed. That reason has expired. The
credentials exist as organization secrets visible to this repository
(`PYPI_PROD`, `PYPI_TEST`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`), GitHub Pages
is enabled with source "GitHub Actions", and 1.1.0 is described in
`CHANGELOG.md` and absent from PyPI.

What the switches buy now is a silent no-op. A release that does nothing and
reports success is worse than no release: the run is green, the summary says
"disabled", and the version sits unpublished until someone notices. The version
gate already answers the only question that matters — is this version on the
index? — and it answers it correctly whether or not a variable is set.

## What changes

- `.github/workflows/pages.yml` — the deploy job drops `vars.PAGES_ENABLED == 'true'`.
- `.github/workflows/release.yml` — the docker job drops
  `vars.DOCKER_RELEASE_ENABLED == 'true'`; `decide` no longer reads
  `RELEASE_ENABLED`; the report job loses its "publishing is disabled" branch.
- `.github/scripts/check_release.py` — the arming block is removed. `reason` is
  now `new-version` or `already-published`; `disabled` no longer exists.
- Tests pin the absence of all three variables rather than their presence.
- `docs/RELEASING.md`, `docs/DEPLOYING.md`, `README.md`, `CLAUDE.md`,
  `openspec/project.md`, `CHANGELOG.md` — updated to describe the version gate as
  the only gate, and required reviewers on the `pypi` environment as the way to
  hold a release.

## Non-goals

- Changing any quality gate. CI, the Lighthouse audit, the CHANGELOG requirement,
  the version-parity check and the Trivy scan are untouched and each still
  publishes nothing on failure.
- Changing the credential model. Organization API tokens, no OIDC, no PEP 740
  attestations on a token upload — 0000's contract stands.
- Publishing on a push that does not change the version. That was never the
  behavior and still is not.

## Risks

| Risk | Mitigation |
|---|---|
| A version bump merged by accident publishes immediately, and PyPI versions are immutable | `main` is protected: the bump arrives through a reviewed pull request. For a hard stop, add required reviewers to the `pypi` environment — an approval gate, not a variable someone forgets to re-arm |
| A bad landing page goes live | The Lighthouse audit (95+ performance, accessibility, best practices) and the content checks run before the upload; a failure leaves the previous version live |
| A vulnerable image reaches Docker Hub | The Trivy scan on the candidate image fails the job before any push, and the image must report the wheel's exact version |
| The kill switch is gone when something is actively wrong | Documented replacement in `docs/RELEASING.md`: environment reviewers, or revoke the organization token |
