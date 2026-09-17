## Problem

`sobres` cannot currently be installed from PyPI because production publishing is disabled and the release workflow still uses a different authentication mechanism from the agreed OpenSpec. A successful Release run also misleadingly says the version is already on the index when publishing was merely disabled.

Observed on 2026-09-13 while reviewing #8:

- Repository variable `RELEASE_ENABLED=false`.
- PyPI and TestPyPI package JSON endpoints both return HTTP 404 for `sobres`.
- Release run [34709406193](https://github.com/AI-Solutions-Lab-LLC/sobres/actions/runs/34709406193) is green, but Verify, Build, Publish and GitHub release jobs were skipped.
- Its Report job says “Version 0.0.1 is already on the index.”
- `pypi` and `testpypi` GitHub environments exist.
- Organization Actions secrets **`PYPI_PROD`** and **`PYPI_TEST`** exist with visibility **ALL**, so this repository is eligible to use them. No repository-level secret copies were listed. Only secret names/metadata were inspected; token values and validity were not retrieved or tested.

## Existing contract and root cause

`openspec/changes/0000-release-engineering/specs/release-pipeline/spec.md` requires organization-token authentication:

- Production uploads use `secrets.PYPI_PROD`.
- TestPyPI uploads use `secrets.PYPI_TEST`.
- Tokens go only to the publish action's password input; no logs, files, or repository-level duplicates.
- Token-auth releases do not claim OIDC/PEP 740 attestations.

Task **B5 (Token-auth upload)** remains unchecked. The owner arming task explicitly depends on the rename and B5.

However, `.github/workflows/release.yml` currently requests `id-token: write`, passes no upload password, and enables `attestations: true`; `docs/RELEASING.md` still describes Trusted Publishing setup. The rename is in place, but the token-auth migration and arming are not.

Do not resolve this solely by toggling the repository variable: finish the workflow/configuration mismatch and validate the intended artifact first.

## Proposed work

- [ ] Scope the fix against OpenSpec 0000/B5 and update proposal/tasks/docs consistently before implementation.
- [ ] Wire the existing organization secrets into the correct index-specific upload action: `PYPI_PROD` for production and `PYPI_TEST` for TestPyPI. Keep secret values out of outputs and files; do not copy them to repository secrets.
- [ ] Remove the unused OIDC permission and explicitly disable attestations for token authentication, as the existing spec requires. If the owner instead elects OIDC, update the agreed contract explicitly rather than silently mixing mechanisms.
- [ ] Give the decision script a machine-readable reason such as `disabled`, `already-published`, or `new-version`, and render that exact reason in the workflow report.
- [ ] Add regression coverage for disabled publishing, already-published version, new version, index failures, index-specific credential selection, and absence of token-auth attestation claims.
- [ ] Update release instructions to describe the actual authentication/setup and activation sequence.
- [ ] Run the full quality gate and a successful TestPyPI rehearsal using `PYPI_TEST`; install the specific produced artifact in a fresh environment and exercise the CLI.
- [ ] Confirm the intended release commit/version and its changelog, then enable `RELEASE_ENABLED=true` and run the gated production workflow for that intended release. Do not publish an incidental scaffold or the uncorrected optimization PR just to reserve a name.
- [ ] Verify the public PyPI version, wheel/sdist, GitHub tag/release, and a fresh installation running actual no-key data/optimization commands. Record the resulting URLs and version on this issue.

## Acceptance criteria

1. A green “no publish” run accurately explains why it skipped; it never asserts an index release without checking it.
2. TestPyPI and PyPI uploads authenticate with the existing organization secrets for their respective indexes, with no token exposure or duplicated repository secrets.
3. The agreed production version is visible at `https://pypi.org/project/sobres/<version>/`, and `pip install sobres==<version>` / `pipx install sobres==<version>` work in clean environments.
4. Version/init/doctor and an actual keyless data/optimization journey succeed from the published base artifact. The old foundation's missing-yfinance issue must not be hidden by dev extras or fixture injection.
5. The GitHub tag/release matches the intended version and commit.

## Scope and dependencies

Release enablement is separate from #8's optimization correctness findings. The current PR head has review blockers; packaging work can proceed, but production release must use the accepted, corrected source. Local main also contains foundation completion commits not yet present on remote main, so confirm the release branch contents.

Homebrew distribution is separate: publishing to PyPI does **not** create a Homebrew formula. A tap/formula and its installation/update tests need their own packaging scope.

Reference: [PyPA publish action authentication and attestations](https://github.com/pypa/gh-action-pypi-publish).

