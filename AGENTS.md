# Repository instructions

## Pull request reviews

Use [`skills/openspec-pr-review/SKILL.md`](skills/openspec-pr-review/SKILL.md) for requested PR reviews. The skill is versioned here so every reviewer can load the same workflow; it can also be installed as `$openspec-pr-review`.

Review intended functionality, not only the diff or test results. Most behavior changes need an OpenSpec. Assess the spec early, reproduce the user journey yourself, and provide a full report and instructions the user can follow. Keep implementation fixes separate unless requested.

### Read and establish scope

1. Read `openspec/project.md`, `openspec/config.yaml`, the applicable change's proposal/design/tasks/spec deltas, related accepted specs, `CLAUDE.md`, the PR template, and CI at the reviewed revision.
2. Inspect both base and head specs. Record repository, PR number, head/base SHAs, merge base, and stacked dependencies. Use `git diff <base>...<head>` and the local complete file list. Distinguish inherited issues from changes introduced by the PR.
3. Review in a temporary clone or detached worktree. Preserve the user's branch, uncommitted work, and personal data. Use explicit `SOBRES_CONFIG_FILE` and `SOBRES_DB_URL` in a temporary directory; do not repurpose `HOME`.
4. Recheck PR head before the final report. A later push requires reviewing the new delta or explicitly limiting the report to the tested SHA.

This repository is transitioning from an earlier package identity; use the package paths and commands declared in `pyproject.toml` at the reviewed commit. Current specs describe `sobres`. Old identifiers in historical base revisions are not automatically new regressions.

### Assess the OpenSpec

- Contract order: explicit task intent, agreed scope, relevant accepted specs, and change deltas. When these disagree, explain the conflict instead of silently choosing the implementation.
- Check whether requirements are useful, mutually consistent, testable, and sufficient for the claimed user outcome. Recommend spec corrections before using a flawed requirement to justify a code change.
- Run `openspec validate <change-id> --strict` with telemetry disabled where supported; record tool version. Report inherited validation problems separately.
- Trace scenarios to code, actual assertions, and observed behavior. Do not equate scenario names in docstrings, checked task boxes, or coverage with correctness.
- Separate implemented, partial, deferred, and untested scope. Later milestones' UI, math, containers, and deployments are not acceptance criteria for an earlier foundation PR unless explicitly included.
- Document a missing spec. Small documentation/maintenance/mechanical PRs can have a reasoned exception; behavior changes need a contract before they are considered complete.

### Architecture and data rules

- `registry.py` declares commands once; CLI and later API/UI derive from it. Validate model defaults, booleans, list options, aliases, and cross-field rules through the generated interface.
- `core/` owns pure math and business rules, with no disk, network, logging, or tracing. `cli/` and later `api/` adapt inputs and render results. `data/` owns providers and storage. Database drivers belong only under `data/storage/adapters/`.
- External providers, storage, and solvers sit behind repository-owned protocols. Shared conformance tests must assert behavior, including transaction failures and migrations, rather than merely matching adapter internals.
- Settings belong in `settings.py`; inspect configuration precedence and doctor coverage for new providers/settings/dependencies. Never print real secrets. Probe secret-valued command parameters, malformed input, exceptions, stderr, log files, and tracing with dummy sentinels.
- Preserve currency metadata and quote direction. Normalize sub-unit quotations, refuse missing or mixed currency when an operation requires a known unit, and use `(1 + local_return) * (1 + fx_return) - 1`. Currency conversion happens through `data/currency.py`.
- Missing observations must remain distinguishable from unrequested dates, closures, pre-listing, and delisting. Exercise cold/warm cache equivalence, weekend-only extensions, revisions to missing values, refresh and TTL expiry. Never accept silent data loss as alignment.
- Check migration backups with committed data still in WAL and with open connections. Backups must restore user-authored state. Cache clearing must preserve that state.
- Math tests use hand-computed, textbook, or independently verified answers with justified tolerances. Annualization uses `core/conventions.py`; no unexplained periods-per-year literals. Respect per-milestone research disclaimers and provenance requirements.

### Required verification

Read the reviewed revision's `pyproject.toml` and `.github/workflows/ci.yml`; adapt these commands to its installed tools:

```bash
python -m pip install -e '.[dev]'
pytest -m 'not network' --cov --cov-report=term-missing --cov-fail-under=90
ruff check .
ruff format --check .
mypy
python -m build
twine check --strict dist/*
```

Use the exact coverage threshold from the reviewed CI if it changes. Run workflow lint and the dependency audit when affected; disclose local tool/environment failures alongside GitHub's results. A test selection excludes declared live tests but does not itself prove networking is disabled.

For installation promises, install the built wheel with base dependencies in a second fresh venv. Run `sobres --version`, `init --non-interactive --offline`, `doctor --offline`, and actual data commands. Then test interactive `init` in a TTY, including skipping optional keys. Development extras and fixture injection must not conceal broken base installations.

Run bounded live provider checks when authorized and available (`pytest tests/network -m network`), then an end-to-end CLI call; a raw payload shape check alone is insufficient. Use separate live and fixture databases. `SOBRES_FIXTURE_DIR` selects fixtures where the reviewed revision supports it. Synthetic fixtures prove parser behavior only; they do not establish vendor truth. FRED checks requiring a key must be reported as skipped if none is available.

Exercise affected commands with all supported formats and log levels. Verify parsed values, units, missing data, exit codes, and state changes. For proposed byte-identical invariants, identify and freeze time/cache state or explicitly document permissible metadata differences; do not silently strip arbitrary output to make a test pass.

### Review deliverables

Save reports under `docs/reviews/pr-<number>/` with:

- Recommendation and tested head/base SHAs.
- Prioritized, reproducible findings with narrow PR-head locations, impact, relevant scenario, and proposed regression coverage.
- Spec changes needed, inherited issues, task-status discrepancies, and a scenario/capability evidence matrix.
- Executed checks, versions/platform, results, skips, and verification limitations.
- Copy-paste self-testing instructions with expected successes and current failures.
- An exact draft GitHub review. Post only when authorized in the session; avoid duplicate comments and stale line locations. Never merge or publish a release as part of a review.

## Python formatting — every edit

After modifying any Python file, always run both commands before completion or commit:

```bash
black --line-length=100 <file>
isort --profile=black --line-length=100 <file>
```

Python line length is 100. Let isort arrange standard library, third-party, and local imports; do not reorder imports manually. These user requirements apply in addition to this repository's Ruff checks. Do not reformat unrelated source files during review.
