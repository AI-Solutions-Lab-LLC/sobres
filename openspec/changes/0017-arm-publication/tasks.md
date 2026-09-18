# 0017. tasks

## Wave A. remove the switches

- [x] **A1. Landing page deploys on main.** Drop `vars.PAGES_ENABLED == 'true'`
      from the deploy job in `.github/workflows/pages.yml` and rewrite the header
      comment. → verify: `tests/ui/test_site_source.py::test_published_automatically_with_least_privilege_and_no_broken_deploys`
      asserts the `if` is `github.event_name != 'pull_request'` alone and that
      `PAGES_ENABLED` appears nowhere in the workflow.
- [x] **A2. PyPI publishes on a version bump.** Remove the `RELEASE_ENABLED`
      variable binding from `decide` in `.github/workflows/release.yml` and the
      arming block from `.github/scripts/check_release.py`. → verify:
      `tests/test_release_script.py::test_no_arming_variable_can_suppress_a_publish`
      sets `RELEASE_ENABLED=false` and still expects `publish=true`.
- [x] **A3. The image publishes on the same gate.** Drop
      `vars.DOCKER_RELEASE_ENABLED == 'true'` from the docker job. → verify:
      `tests/architecture/test_deployment_files.py::test_release_publishes_the_image_on_the_same_gate`
      asserts `DOCKER_RELEASE_ENABLED` is absent from the whole workflow.
- [x] **A4. No dead "disabled" path.** Remove the `reason=disabled` branch from
      the report job and the `disabled` emit from the script. → verify:
      `tests/test_release_script.py::test_every_mode_emits_exactly_the_four_outputs`
      still passes for both targets, and `reason` is only `new-version` or
      `already-published`.

## Wave B. say so everywhere

- [x] **B1. Docs.** `docs/RELEASING.md` (arming section removed, replaced by the
      environment-reviewers stop), `docs/DEPLOYING.md` (Docker Hub credentials
      only), `README.md`, `CLAUDE.md`, `openspec/project.md`, `CHANGELOG.md`
      Unreleased. → verify: `rg 'PAGES_ENABLED|RELEASE_ENABLED' README.md CLAUDE.md docs/ openspec/project.md .github/`
      returns nothing.
- [x] **B2. Repository variables deleted.** `RELEASE_ENABLED` removed with
      `gh variable delete`. → verify: `gh variable list` is empty.
- [x] **B3. Pages enabled with source "GitHub Actions".** → verify:
      `gh api repos/AI-Solutions-Lab-LLC/sobres/pages --jq .build_type` returns
      `workflow`.

## Wave C. prove it end to end

- [ ] **C1. The landing page is live.** After merge, the Landing page workflow's
      deploy job runs and https://ai-solutions-lab-llc.github.io/sobres/ serves
      the built site. → verify: the deployment URL returns HTTP 200 and the page
      title is `sobres`.
- [ ] **C2. 1.1.0 is on PyPI.** The Release workflow's `decide` job reports
      `publish=true` / `reason=new-version` for 1.1.0 and the publish job
      uploads. → verify: https://pypi.org/project/sobres/1.1.0/ exists and
      `pip install sobres` in a clean virtual environment gives
      `sobres --version` = 1.1.0.
- [ ] **C3. The image is on Docker Hub.** → verify:
      `docker run --rm aisolutionslab/sobres --version` reports 1.1.0.
