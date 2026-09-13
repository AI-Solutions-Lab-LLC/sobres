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
Code-gate results from an isolated checkout will be recorded before handoff.
No application Python files were edited during planning, so Black/isort were not
required for this turn's file changes. No cloud or release operation was performed.
