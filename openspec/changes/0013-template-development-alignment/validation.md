# Planning validation

## Executed locally

- OpenSpec CLI 1.13.0, telemetry disabled.
- Baseline: 13 changes, 3 passed, 10 failed strict validation.
- Revised set: 14 changes pass strict validation; missing substantive requirement
  bodies were repaired without dropping existing scenarios.
- All ten implementation-tracked changes report complete planning artifacts.
- Dependency references resolve and form an acyclic graph.
- `git diff --check` passes.
- `python -m pytest tests/architecture/test_scenarios.py tests/architecture/test_testing_spec.py -q`:
  7 passed. Warning: 371 proposed scenarios lack implementation tests, expected
  because these plans are not implemented. A reference to a future test is not proof.

## Reproduce planning checks

```bash
OPENSPEC_TELEMETRY=0 openspec validate --all --strict
OPENSPEC_TELEMETRY=0 openspec status --change 0013-template-development-alignment
python -m pytest tests/architecture/test_scenarios.py tests/architecture/test_testing_spec.py -q
git diff --check
```

Use each change's tasks.md for future behavior checks. The 0013 task proofs name
proposed tests, not files claimed to exist already. Do not run the future Make
commands as evidence of today's environment: they have not been implemented.

## Included foundation verification

The PR includes the pre-existing local-main foundation at the user's request.
Verified code tree: planning commit `d90da8d` on foundation base `e0432c5`, in
`/tmp/sobres-alignment-verification` with a fresh uv environment, macOS arm64,
Python 3.12.13, uv 0.11.7, Ruff 0.16.7, pytest 9.1.1. Later publication-link and
validation edits affect Markdown only, leaving that tested application tree intact.

| Check | Result |
|---|---|
| Full non-network pytest with branch coverage and 90% gate | 408 passed, 4 live tests deselected; 96.50% coverage |
| Ruff lint and current Ruff format check | Passed, 97 files already formatted |
| mypy strict | Passed, 44 source files |
| Strict OpenSpec validation | 14 passed, zero errors/warnings |
| Build wheel and sdist; twine strict | Passed |
| Second fresh environment, base wheel only | Version, offline noninteractive init and doctor passed |
| Interactive init in a real TTY | Passed with every optional prompt skipped; exit 0, 22 checks OK, 1 optional-key warning, 6 offline skips |
| Installed base-wheel data journey | Recorded AAPL/MSFT prices passed JSON/CSV/table with symbols/rows checked |
| Dependency audit of fully resolved dev environment | Passed: no known vulnerabilities, using workaround below |

The ordinary `pip-audit --strict -r ...` invocation failed because this uv-managed
Python's `ensurepip` subprocess aborted while the auditor created a temporary
resolver environment. The installed environment was already fully resolved and
frozen. Auditing that exact list with `--disable-pip --no-deps` succeeded without
omitting transitive packages or advisory checks. Cache-deserialization warnings
were emitted and the affected entries were ignored/refetched by the tool.
This workaround does not claim the default audit invocation succeeded.

```bash
uv pip freeze --python .venv/bin/python --exclude-editable > /tmp/sobres-audit.txt
.venv/bin/pip-audit --strict --disable-pip --no-deps --progress-spinner=off -r /tmp/sobres-audit.txt
```

Local workflow lint was not separately executed (actionlint absent); CI's workflow
lint and Linux/macOS/Windows/Python-version matrix must be checked on the PR.
Live providers were not called during this task. Selecting non-network tests
alone does not prove socket-level network isolation; 0013 proposes that stronger gate.
The fixture-backed smoke proves installation/parser wiring, not live vendor availability.
No application Python files were edited during planning, so Black/isort were not
required for this turn's file changes. No cloud or release operation was performed.

GitHub review: [PR #33](https://github.com/AI-Solutions-Lab-LLC/sobres/pull/33).
Its CI runs are additional platform evidence and were pending at publication.

## GitHub findings on the included foundation

At `d90da8d`, CI lint (including workflow lint), typing, distribution verification,
standard dependency audit and Linux/macOS test jobs passed; Windows was still
running at the inspection. CodeQL analysis executed successfully, but the separate
CodeQL findings check failed: one high potential secret-logging path at
`src/sobres/cli/context.py:155`, two assert-side-effect errors and an unreachable
warning in `tests/data/storage_conformance.py`, plus 36 informational notes.

Tracked separately in [issue #34](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/34).
The high finding is not claimed to be a reproduced exposure or a false positive.
Resolve it before considering the foundation integration ready to merge. These
findings belong to the included foundation code, not the Markdown alignment work;
no suppression or code fix was added during this planning task.
