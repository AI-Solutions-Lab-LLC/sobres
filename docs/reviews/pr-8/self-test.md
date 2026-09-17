# PR #8 — reproduce and evaluate

These instructions test head `21724ce35c6a4b3f5d89db265517bf77a38d425f` without changing your working branch or real configuration. They require git and uv. Provider fixtures at this head are synthetic.

## Isolated installation

From your existing sobres repository:

```bash
review_repo="$PWD"
review_root=$(mktemp -d /tmp/sobres-pr8-selftest.XXXXXX)
git clone --no-hardlinks "$review_repo" "$review_root/repo"
git -C "$review_root/repo" checkout --detach 21724ce35c6a4b3f5d89db265517bf77a38d425f
cd "$review_root/repo"
uv venv --python 3.12 "$review_root/venv"
uv pip install --python "$review_root/venv/bin/python" -e '.[dev]'
export PATH="$review_root/venv/bin:$PATH"
export SOBRES_CONFIG_FILE="$review_root/config.toml"
export SOBRES_DB_URL="sqlite:///$review_root/test.sqlite"
export SOBRES_FIXTURE_DIR="$review_root/repo/tests/fixtures"
unset SOBRES_FRED_API_KEY FRED_API_KEY SOBRES_LOG_FILE
unset OTEL_EXPORTER_OTLP_ENDPOINT OTEL_TRACES_EXPORTER
sobres --version
```

Expected: version 1.0.0. This is an unreleased PR build; it does not establish that 1.0.0 exists on PyPI.

## Basic journeys that should work

```bash
sobres init --non-interactive --offline
sobres doctor --offline

sobres optimize markowitz --tickers AAPL MSFT JNJ XOM \
  --start 2019-01-01 --end 2020-12-31 --fill ffill \
  --risk-free 0 --max-weight 0.35 --format table

sobres optimize frontier --tickers AAPL MSFT JNJ XOM \
  --start 2019-01-01 --end 2020-12-31 --fill ffill \
  --risk-free 0 --points 5 --format json > "$review_root/frontier.json"

sobres optimize backtest --tickers AAPL MSFT JNJ XOM \
  --start 2019-01-01 --end 2020-12-31 --fill ffill \
  --risk-free 0 --lookback 12m --rebalance quarterly --format table

sobres optimize risk --tickers AAPL MSFT --weights 0.6 0.4 \
  --start 2019-01-01 --end 2020-12-31 --fill ffill \
  --risk-free 0 --format json > "$review_root/risk.json"
```

All should exit 0. Markowitz weights should sum to 1 and respect the cap. Tables show source, currency and a research disclaimer. Backtest shows strategy/benchmark metrics, OOS dates and costs. **Known failure:** five requested frontier points currently produce six rows despite `n_points: 5`.

Use `--objective min_variance`, `max_sharpe`, `risk_parity`, or `equal_weight` for basic experimentation. Objective values use underscores. An explicitly chosen `--risk-free` avoids the future-FRED-rate dependency but does not fix the other review defects; it is an assumption, not a recommended financial rate.

## Known failures through the CLI

```bash
sobres optimize markowitz --tickers AAPL MSFT \
  --start 2019-01-01 --end 2020-12-31 --fill ffill \
  --risk-free 0 --returns-estimator capm
```

Current: exit 2 asking for a benchmark, but no benchmark option exists. Corrected behavior: an exposed estimator has a usable input path.

```bash
sobres optimize backtest --tickers AAPL MSFT \
  --start 2019-01-01 --end 2020-12-31 --fill ffill \
  --risk-free 0 --lookback 60 --objective target_return
```

Current: exit 2 asking for `--target`. Adding `--target 0.1` fails because the option does not exist. The same defect affects `target_risk`.

```bash
sobres optimize risk --tickers AAPL MSFT --weights nan nan \
  --start 2019-01-01 --end 2020-12-31 --fill ffill --risk-free 0
sobres optimize markowitz --tickers AAPL MSFT \
  --start 2019-01-01 --end 2020-12-31 --fill ffill --risk-free 0 --seed -1
```

Current: both exit 1 as internal errors after loading data. Corrected behavior: usage exit 2 before any provider call.

## Independent math and adapter probes

```bash
python "$review_repo/docs/reviews/pr-8/reproduce.py" \
  --output "$review_root/evidence"
```

This takes about a minute and writes all table/JSON/CSV outputs at all four log levels. It changes no PR source files and uses only temporary state and dummy credentials.

Current results to inspect in `independent.json`:

- Future Treasury-rate changes alter the first allocation from approximately 58.13% A to 50.97% A; only future rates changed. Correct result: identical first weights.
- Returns `[-50%, +10%, +10%]` report zero maximum drawdown. Correct result: -50%, no recovery.
- Missing daily price with `--fill drop` creates a 21% two-session return labeled daily. Correct handling must preserve the interval or exclude that invalid return.
- Indefinite covariance is accepted without repair. Correct behavior: explicit repair with provenance or a domain error.
- Requested frontier count 5 returns 6. Correct behavior: agreed count and truthful metadata.
- `portfolio_returns` silently treats a missing asset return as zero. Correct behavior needs an explicit policy/precondition.

To rerun just these math/adapter checks, add `--skip-cli`.

## Required local checks

```bash
python -m pytest -m 'not network' --cov --cov-report=term-missing --cov-fail-under=90
ruff check .
ruff format --check .
mypy
uv pip install --python "$review_root/venv/bin/python" build twine
python -m build
twine check --strict dist/*
OPENSPEC_TELEMETRY=0 openspec validate 0002-portfolio-optimization --strict
```

Observed on Python 3.12.13: 453 tests pass, 96.72% coverage; Ruff/mypy/build/Twine pass. OpenSpec 1.13.0 fails with three inherited missing-requirement-text errors. Python 3.14 additionally fails the inherited registry type-name assertion.

## Actual base-wheel installation

```bash
uv venv --python 3.12 "$review_root/base-venv"
uv pip install --python "$review_root/base-venv/bin/python" dist/*.whl
unset SOBRES_FIXTURE_DIR
export SOBRES_DB_URL="sqlite:///$review_root/base.sqlite"
"$review_root/base-venv/bin/sobres" --version
"$review_root/base-venv/bin/sobres" init --non-interactive --offline
"$review_root/base-venv/bin/sobres" doctor --offline
"$review_root/base-venv/bin/sobres" data prices AAPL \
  --start 2024-01-02 --end 2024-01-10
```

Current: version/init/doctor exit 0; prices exit 4 because yfinance is missing. This is inherited and already fixed on local main. Installing the data extra is a temporary workaround for this head, not evidence that the advertised base installation works.

For the real wizard, set `SOBRES_CONFIG_FILE` to a new path under `$review_root`, run `sobres init --offline` in your terminal, and press Enter at the optional FRED prompt. Current: it repeats. Interrupt with Ctrl-C; do not enter a real key on this old head because its config command can log secrets.

## Optional bounded live smoke

Keep the development environment on PATH. Use a separate live cache:

```bash
unset SOBRES_FIXTURE_DIR SOBRES_FRED_API_KEY FRED_API_KEY
export SOBRES_CONFIG_FILE="$review_root/live.toml"
export SOBRES_DB_URL="sqlite:///$review_root/live.sqlite"
python -m pytest tests/network -m network
sobres optimize markowitz --tickers AAPL MSFT \
  --start 2024-01-02 --end 2024-03-28 --fill raise --risk-free 0 --format json
```

Observed: three live provider tests passed, FRED skipped, and live optimization succeeded. Vendor availability and historical revisions can change later results. The full review also ran live frontier, risk and backtest.

## Distribution expectation

As reviewed, PyPI/TestPyPI endpoints are 404 and `RELEASE_ENABLED=false`; there is no Homebrew formula. A successful green workflow with skipped publishing does not mean a package was released.

After a real release, test PyPI installation in a fresh environment. Homebrew needs a separately implemented/tested tap and formula; `brew install sobres` is not enabled automatically by PyPI publishing. See the release acceptance sequence in [report.md](report.md).
