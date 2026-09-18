# Planning validation — 18 September 2026

Base: `60f123a6f79ab2a2b803525c91ed93eaa3c47a3c` (`origin/main`).
Work isolated in `/tmp/sobres-options-spec`, branch
`spec/0018-pre-earnings-options-poc`. The original checkout and its four unrelated
release edits were preserved. This change modifies Markdown only.

## Executed checks

| Check | Result |
|---|---|
| Word source extraction / SHA-256 | Read paragraphs and table cells; source fingerprint recorded in `source-analysis.md` |
| `OPENSPEC_TELEMETRY=0 openspec validate 0018-pre-earnings-options-poc --strict --no-interactive` | Pass, OpenSpec 1.13.0 |
| `OPENSPEC_TELEMETRY=0 openspec validate --all --strict --no-interactive` | 18 passed, 0 failed; inherited archive advisories in 0014/0015 because accepted spec targets do not yet exist |
| Relative Markdown links / scenario/task inventory | No broken local links; 42 new scenarios, 37 unchecked implementation tasks |
| `python -m pytest tests/architecture/test_scenarios.py -q` | 2 passed; expected warning for 105 proposed scenarios across the repository lacking implementation tests |
| `ruff check .` / `ruff format --check .` | Pass; 196 Python files already formatted, none changed |
| `python -m mypy` in fresh Python 3.12 dev environment | Pass, 89 source files |
| `actionlint` | Pass; locally cached source-build version `v0.0.0-20250119115933-03d0035246f3+dirty`, not a claimed CI-version match |
| `git diff --check` | Pass |

Environment: macOS arm64; final check venv `/tmp/sobres-options-spec-ci`, CPython
3.12.13, `uv pip install -e '.[dev]'`, mypy 2.3.1, Ruff 0.16.8, pytest 9.1.1,
pandas 3.0.6, pandas-stubs 3.0.5.260914. This uses the repository's declared
dependency ranges and matches CI's Python 3.12 type-check job.

An initial check in the machine's older Python 3.11/mypy 1.20 environment reported
seven pandas slice-index type errors in unchanged files. Matching pandas 2.3
stubs in a temporary environment and changing the target alone did not resolve
them. The clean Python 3.12/current-dev environment passed without source edits
or ignored errors. The user's installed environment was not modified.

## Verification limits

The full application coverage suite, builds, live market-data probes, empirical
backtests, browser deployment, and real SMS were not run for this documentation-only
PR. They are implementation gates in `tasks.md`, not completed evidence. No
performance, cloud deployment or provider entitlement is claimed. All 42 scenarios
are specified contracts with planned proof locations, not implemented scenarios.

Source facts/pricing were checked against linked primary sources. The original
Word file was not committed; its estimates and unsupported percentage claims
were not treated as verified financial results. No subscription, cloud resource,
trade, model promotion, or outbound SMS was created.

## Repeat the planning checks

```bash
OPENSPEC_TELEMETRY=0 openspec validate 0018-pre-earnings-options-poc --strict --no-interactive
OPENSPEC_TELEMETRY=0 openspec validate --all --strict --no-interactive
python -m pytest tests/architecture/test_scenarios.py -q
ruff check .
ruff format --check .
python -m mypy
git diff --check
```

Use a fresh Python 3.12 environment installed with `.[dev]` for the Python checks.
