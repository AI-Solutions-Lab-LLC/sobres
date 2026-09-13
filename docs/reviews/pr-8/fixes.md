# PR #8 — implemented review corrections

The eight findings against `21724ce35c6a4b3f5d89db265517bf77a38d425f` are addressed.
The PR retains its existing optimization branch. Foundation corrections and the
recorded vendor fixtures are integrated from local main `e0432c5`; the original
stack base was `dd5d6f077e01e972feefe85629b81b1e63df6078` (PR #7).

## Findings and regression evidence

| Finding | Result | Evidence |
|---|---|---|
| F1: future risk-free observations change past allocations | Lag annual proxies strictly before each trade; record training dates, decision rate and vintage limitation | `tests/cli/test_optimization_review.py::test_future_rates_cannot_change_past_allocations` |
| F2: initial loss omitted from drawdown | Include initial capital in the high-water mark; null peak date identifies that baseline | `tests/core/test_review_corrections.py`, initial loss, recovery and entry-cost cases |
| F3: dropped prices bridge return intervals | Compute ratios on the original index and record excluded return dates | `tests/cli/test_optimization_review.py::test_dropped_prices_do_not_bridge_daily_intervals` |
| F4: CAPM missing benchmark input | Add validated benchmark ticker, currency conversion and per-window slicing | Generated CLI CAPM tests for Markowitz, frontier and backtest |
| F5: target backtest objectives missing target | Add finite cross-validated target; target risk is a ceiling | Synthetic target-return and target-risk backtests; CLI option validation |
| F6: public optimization accepts invalid covariance | Validate labels/finite entries, condition covariance and verify final constraints | Public optimizer covariance regressions and existing PSD tests |
| F7: invalid inputs reach downloads/solver | Reject nonfinite numbers, negative seeds, duplicate tickers, impossible bounds and oversized work before fetching | Parameterized CLI regression proves provider is never called |
| F8: frontier returns N+1 rows | Exactly N including named optima, with documented coincidence/degenerate policy | Counts 2/3/5/50, coincident means, named flags and progress assertions |

The accepted contract is in
[`review-decisions.md`](../../../openspec/changes/0002-portfolio-optimization/review-decisions.md)
and the revised 0002 spec/design/tasks. Sharpe uses arithmetic excess returns;
CAGR is separate. Sortino uses RMS shortfall over the full population. DTB3 has
an explicit discount-yield conversion; other currencies default to a disclosed
zero proxy. Initial cash participates in turnover; paid fees and summed fee
fractions have distinct fields. Public analytics reject unresolved missing data.

Risk tables distinguish percentages, unitless ratios, counts and per-observation
losses. Backtests retain settings, decision windows and bounded warning summaries;
frontiers show estimator/seed provenance. Analytic derivatives and warm starts
reduce solver evaluations. SciPy sits behind a repository-owned solver protocol
with feasibility/failure conformance tests. CLI adapters report elapsed time and
progress; the performance probe measures solver call/evaluation counts.

## Release corrections

The workflow selects the organization secret name for the chosen index before
reading its value, so missing `PYPI_TEST` cannot fall back to `PYPI_PROD`. A boolean
availability check fails early; only the upload action receives the credential.
OIDC write permission is removed and attestations disabled. Disabled publishing
and existing versions emit different reasons and accurate summaries. Unit tests
cover decisions and credential selection; actionlint with shellcheck passes.
0000's normative requirement text and release documentation are reconciled.

Organization metadata confirms both secret names have ALL visibility. Values and
token validity were not inspected. `RELEASE_ENABLED` remains false. No package,
tag, release, or Homebrew tap was published. [Issue #21](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/21)
remains open for upload rehearsal, token validation and production activation.
A PyPI release enables pip/pipx installation; Homebrew still requires a formula/tap.

## Verification

Executed on arm64 macOS with Python 3.12.13 in isolated source and wheel environments:

- 531 offline tests passed, 4 live tests deselected; coverage 96.08% (required 90%).
  The advisory about proposed future-milestone scenarios remains; implemented
  0002 scenarios pass the repository's reference check. Assertions and independent
  hand calculations, rather than that naming check alone, establish the fixes.
- Black (100 columns), isort (Black profile/100 columns), Ruff lint/format and
  mypy passed. Both changed OpenSpecs (0000 and 0002) validate strictly.
- Wheel/sdist build and strict Twine check passed; the sdist builds another wheel.
- Fresh base-only wheel: version, noninteractive offline init, offline doctor,
  live AAPL/MSFT prices and all four live optimization commands passed. A real TTY
  init accepted Enter for every optional setting and ended with zero failures.
- All four commands passed table/JSON/CSV at ERROR/WARNING/INFO/DEBUG (48 cases).
  CSV/table stdout and JSON numeric rows agreed. Source timestamps are documented
  metadata exceptions; full changing JSON is not claimed byte-identical.
- Live Yahoo, ECB and Ken French checks passed. Live FRED was skipped because the
  isolated config has no key. Fixture tests exercise dated FRED behavior separately.
- Dependency audit found no known vulnerabilities in the fully resolved, pinned
  development/runtime dependency list. The default audit resolver hit a local
  `ensurepip` SIGABRT; auditing that complete list with `--disable-pip --no-deps`
  succeeded. No dependency was excluded to silence an advisory.
- Workflow lint passed with actionlint 1.7.7 and shellcheck.

Raw concise evidence is in [verification/](verification/). Live vendor tests emit
a yfinance deprecation warning; no data failure was hidden. Local platform checks
do not establish the Linux/Windows matrix; GitHub CI supplies that evidence.

One-run synthetic benchmarks (600 observations, seed 71; not a latency guarantee):

| Assets | Min variance | Max Sharpe | 50-point frontier | Monthly backtest, 17 rebalances |
|---:|---:|---:|---:|---:|
| 6 | 0.003 s | 0.005 s | 0.024 s | — |
| 20 | 0.001 s | 0.017 s | 0.045 s | — |
| 50 | 0.003 s | 0.153 s | 0.194 s | 2.84 s |
| 100 | 0.002 s | 1.668 s | 1.931 s | 30.98 s |

The 100-asset frontier used 3,631 objective evaluations in 60 solver calls. This
is a local synthetic observation, not a provider-inclusive production benchmark.

## Remaining scope

Actual execution of the legacy R script remains deferred; the independent Python
LP enumeration is labeled accurately. The three-asset case asserts synthetic
frontier bounds, not published exact weights. Group constraints, additional solver
backends, concurrent provider fetches, Homebrew and publication remain explicit
follow-ups. These are no longer marked complete in the optimization tasks.

## Reproduce the important checks

From the PR checkout:

```bash
python -m pip install -e '.[dev]'
pytest -m 'not network' --cov --cov-report=term-missing --cov-fail-under=90
ruff check .
ruff format --check .
mypy
OPENSPEC_TELEMETRY=0 openspec validate 0002-portfolio-optimization --strict
OPENSPEC_TELEMETRY=0 openspec validate 0000-release-engineering --strict
python -m build
twine check --strict dist/*

# Isolated fixture journey: no real settings or database are used.
review_state=$(mktemp -d)
export SOBRES_CONFIG_FILE="$review_state/config.toml"
export SOBRES_DB_URL="sqlite:///$review_state/data.db"
export SOBRES_FIXTURE_DIR="$PWD/tests/fixtures"
sobres init --non-interactive --offline
sobres doctor --offline
sobres optimize markowitz --tickers AAPL MSFT --start 2020-01-01 --end 2020-03-31 --fill drop --returns-estimator capm --benchmark JNJ
sobres optimize frontier --tickers AAPL MSFT --start 2020-01-01 --end 2020-03-31 --fill drop --points 5 --format json
sobres optimize backtest --tickers AAPL MSFT --start 2020-01-01 --end 2020-03-31 --fill drop --lookback 20 --format json
sobres optimize risk --tickers AAPL MSFT --weights .6 .4 --start 2020-01-01 --end 2020-03-31 --fill drop --format table
```

Expect successful commands, five frontier rows, recorded backtest decision windows
and typed risk values. A missing key gives the documented zero-rate warning.
`--seed -1`, duplicate tickers and `--risk-free nan` must return usage exit 2.
