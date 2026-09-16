# sobres — project context

## Where it lives

| What | Value |
|---|---|
| Repository | `AI-Solutions-Lab-LLC/sobres` — https://github.com/AI-Solutions-Lab-LLC/sobres |
| PyPI distribution | `sobres` (first publish, 1.1.0, waits on `RELEASE_ENABLED`; see #21) |
| Import package | `sobres` (`src/sobres/`) |
| Console script | `sobres` |
| Container image | `aisolutionslab/sobres` on Docker Hub |
| Landing page | https://ai-solutions-lab-llc.github.io/sobres/ |
| Env var prefix | `SOBRES_` |

The project was previously `espin086/Stocks`, packaged and installed under a
different name. Change 0011 carries that rename through the code; every document
here already uses the new names.

## What this is

A one-stop **CLI for equity analysis**: pull market and macro data, optimize a
portfolio, analyze an individual stock with factor models, run econometric
forecasts, and plan real-world money goals (retirement, house, car, college).

The CLI is the first surface. The library underneath it is designed so a web API
or notebook can sit on top later without moving any logic.

## Architecture

One rule, enforced by `tests/architecture/test_layering.py` rather than by review:

```text
src/sobres/
  __about__.py / py.typed        package identity; the one version source
  registry.py / results.py      one declaration per command; CLI, API and UI derive from it
  settings.py                   one settings registry: env var, secret flag, how to obtain,
                                live validator, browser editability
  doctor.py                     one check registry; init/doctor/deploy check/health use it
  core/                         pure, I/O-free math over frames and dataclasses:
                                no network, no disk, no logging, no tracing
  data/                         providers and the storage port -> pandas objects; no math
    base.py                     provider Protocols (prices, macro, factors, FX) and frame rules
    *_provider.py               vendor adapters (yfinance, FRED, ECB, Ken French, World Bank/OECD/BIS)
    cache.py / align.py / gaps.py  observation cache, alignment, gap classification
    storage/base.py             repository Protocols in domain terms; open_storage()
    storage/adapters/           the only place a database driver is imported (SQLite today)
  cli/                          Typer adapters generated from the registry; rendering, prompts
  api/                          FastAPI adapters generated from the registry; jobs, SSE, auth
  observability/                structlog + optional OpenTelemetry; adapters instrument calls
frontend/                       React SPA; forms and views generated from the registry
site/                           the GitHub Pages home page
compose.yaml / Dockerfile       the container profile
```

Dependencies flow `cli`/`api` → `core` + `data`. Anything swappable — a data
provider, the storage backend, the solver — sits behind a `Protocol` in our own
namespace, and its library types never appear in a signature outside its adapter.
Where more than one implementation is plausible, a shared conformance suite
(`tests/data/storage_conformance.py`, the provider contract tests) defines the contract.
If code computes something in `cli/` or `api/`, it belongs in `core/`; if `core/`
would call a provider or open a connection, pass the frame in instead.

Tests are organized by what they prove: `tests/core/` (known answers), `tests/data/`
(recorded fixtures and conformance), `tests/cli/`, `tests/api/`, `tests/ui/`
(source-level checks of the SPA and the site), `tests/architecture/` (import and
literal rules, scenario coverage), `tests/invariants/` (every registered command),
`tests/network/` (marked, excluded from CI; run by `.github/workflows/live.yml`).

Change 0013 proposed renaming these boundaries into `ports/`, `application/` and
`adapters/` packages plus template tooling. It was superseded on 2026-09-16
(see its proposal): the boundaries already exist and are tested, and the rename had
no user-visible outcome.

## Development contract

`CLAUDE.md` is the entry point for contributors and agents. Behavior changes start
with an OpenSpec change (`proposal`, `design`, `tasks`, spec deltas); every
`#### Scenario:` gets a test, and `tests/architecture/test_scenarios.py` fails the
build when an `implemented` change has a scenario without one.

ruff (lint and format), `mypy --strict`, actionlint and the hygiene hooks run before a
commit exists (`pre-commit install`; the Claude Code commit gate runs the same set).
CI adds the offline test suite with a 90% branch-coverage floor on Linux, macOS and
Windows, the base-wheel smoke test (no extras), the sdist/wheel build, the container
quickstart, the frontend client-drift and bundle checks, CodeQL and `pip-audit`.
Strict OpenSpec validation: `npx @fission-ai/openspec validate --all --strict`.

Registry generation is mandatory for CLI commands; the API route and the UI form come
from the same declaration and a parity test fails the build if one is missing.
Commands that only make sense in a terminal (`serve`, `open`, `serve token rotate`)
refuse over HTTP before any side effect. Browser-editable settings are an explicit
subset of the declarations (`browser_editable`); the database URL, the trace exporter
destination and the config-file path are CLI-only.

## Command surface

| Command | Does |
|---|---|
| `sobres init` | Guided setup of every declared setting; ends by running doctor |
| `sobres doctor` | Every check actionable; `--fix` for safe repairs; `--format json` |
| `sobres upgrade` | Detects the installer and runs the matching upgrade |
| `sobres data prices AAPL MSFT --start 2015-01-01` | Fetch + cache price history |
| `sobres data macro DGS10 CPIAUCSL` | Fetch FRED series |
| `sobres analyze stock NVDA` | Fundamentals, risk, CAPM beta |
| `sobres analyze factors NVDA --model ff5` | Fama-French regression, alpha + t-stats |
| `sobres optimize markowitz --tickers ... --objective max-sharpe` | Optimal weights |
| `sobres optimize frontier --tickers ... --points 50` | Efficient frontier |
| `sobres optimize backtest --weights ... --rebalance quarterly` | Walk-forward test |
| `sobres plan retire --income ... --expenses ...` | FIRE number + date |
| `sobres plan house --price ... --down-pct ...` | Savings path to a down payment |
| `sobres plan goal --target ... --by 2032-01-01` | Generic funding solver |
| `sobres econ forecast ticker:AAPL --model var --horizon 20` | Joint VAR/BVAR price distribution with held-out controls and 80%/95% bounds |
| `sobres econ evaluate ticker:AAPL --models var bvar` | Score both models against no-change and training-mean on identical held-out dates |
| `sobres fx rates EURUSD` / `sobres fx convert 1000 --from USD --to EUR` | Exchange rates and conversion |
| `sobres fx attribution --tickers ... --base USD` | Split return into asset vs currency |
| `sobres fx hedge --tickers ... --compare unhedged` | What hedging would have cost |
| `sobres ppp compare --base USD --vs EUR MXN` | Market rate vs purchasing-power rate |
| `sobres ppp adjust-goal --goal fire --to PRT` | Restate a goal at another price level |
| `sobres portfolio save core --tickers ...` | Save a named portfolio |
| `sobres run list` / `sobres run show <id>` | Browse saved analysis runs |
| `sobres db info` / `sobres db export --to ...` | Inspect and back up the database |
| `sobres serve --host 0.0.0.0` | Run the web UI and API |
| `sobres open [doctor\|settings\|run 42\|...]` | Start the server if needed and open the browser to a view |
| `sobres deploy compose` / `sobres deploy check` | Generate and verify a deployment |

## Data sources

| Source | Key needed | Used for | From |
|---|---|---|---|
| **yfinance** | no | Prices, dividends, splits, fundamentals | 0001 |
| **ECB reference rates** | no | Daily exchange rates | 0001 |
| **FRED** | free API key (`FRED_API_KEY`) | Risk-free rate, CPI, macro series | 0001 |
| **Ken French Data Library** | no | Fama-French 3/5-factor + momentum returns | 0001 |
| **World Bank ICP / OECD** | no | PPP conversion factors, comparative price levels | 0010 |
| **BIS** | no | Published real effective exchange rates | 0010 |

`pip install sobres` must produce a working tool with **no keys
configured**. Anything requiring a key degrades with a clear, actionable error —
never a stack trace.

## Onboarding

Three commands, kept to three by construction:

```
pip install sobres  →  sobres init  →  sobres doctor
```

**Settings are declared once**, like commands. Each carries its env var, whether
it is a secret, how to obtain it, and an optional live validator; `sobres init`,
`sobres doctor`, `sobres config`, and the browser-safe 0004 settings projection derive from the
declaration. A test asserts every env var the code reads is a declared setting.

**Doctor's checks are declared once**, too — a `Check` registry with `run` and
an optional idempotent `fix`. A milestone that adds a provider, a setting, or a
runtime dependency registers a check in the same change; a test asserts every
setting and provider has one. Every failing line carries its next step. `sobres
deploy check` and the container health check call doctor rather than
re-implementing health.

## Storage: owned ports, with SQLite behind them

Persistence is reachable only through repository protocols in
`data/storage/base.py`, phrased in domain terms — observations, date ranges,
portfolios — never as SQL execution. A port phrased as SQL is a SQL port, and
swapping it would still be a rewrite.

`SOBRES_DB_URL` selects the adapter, defaulting to
`sqlite:///<user-data-dir>/sobres.db`. **Database drivers stay inside
`data/storage/adapters/`**, enforced by architecture tests.

SQLAlchemy Core (the expression language, not the ORM) sits *below* the
protocols as the dialect layer, with adapter-owned migrations. Call sites never see
a `Session`, a `Table`, or a `Row`, so even that choice stays reversible.

SQLite is the only implemented operational backend. Use portable owned data
contracts, stable IDs and UTC timestamps; SQL and released migration details stay
behind adapters. Shared behavioral conformance covers transactions, failures,
concurrency and restoration. PostgreSQL requires its own implementation, actual
engine tests and explicit export/import/cutover/rollback before portability is
claimed. DuckDB, cache and vectors are separate capabilities, not interchangeable
operational repositories. Changing a URL does not migrate user data.

With SQLite, one file is the entire local state — cache, portfolios, goals, runs,
jobs. That is a property of the default backend, not of the system: it is what
lets Docker mount one volume. Take consistent backups through the SQLite backup
API, including committed WAL data; copying a live main database file is insufficient.

API keys are the exception: they stay in the config file at mode `0600` and never
enter the database.

## Currency

Handled like timezone: every monetary series declares its currency, conversion is
one explicit operation, and mixing is refused rather than guessed.

Direction is carried by `CurrencyPair(base, quote)` — units of *quote* per one
unit of *base* — and **no call site ever multiplies or divides by a rate**; they
call `convert()`. That removes the inversion bug by removing the opportunity.

Return conversion uses the exact identity `(1+r_local)(1+r_fx)-1`, never the
additive approximation. Sub-unit quotations (GBp, ZAc, ILA) are normalized in the
data layer, with a test against a real pence-quoted listing.

The model lands in 0001 because returns computed without a currency concept must
be recomputed when one arrives — which by 0002 means every risk and optimization
function. The analytics are 0010. A single-currency run fetches no rates and is
identical to a build without any of this.

## Observability

Structured logging always (default WARNING); OpenTelemetry tracing behind the
`otel` extra, no-op unless `OTEL_*` is configured.

Three rules that everything else follows from:

1. **Logs go to stderr, always.** `--format json` must stay a single parseable
   document on stdout at any log level.
2. **`core/` imports no logging or tracing.** Instrumentation lives in the
   adapters, which observe the calls they make. Long computations take an
   optional progress callback; the caller decides whether that becomes a log
   line, a span event, or a job progress update.
3. **Redaction happens at the formatter**, not at call sites — a test runs every
   command with a sentinel credential at DEBUG and asserts it appears nowhere.

Observability may never change a result: stdout is byte-identical across log
levels and with tracing on or off, and that is a test. An unreachable exporter
warns once and never fails a command.

## Prior art in JJ's repos (reuse, don't rebuild)

| Source repo | What to lift |
|---|---|
| `espin086/fire-calculator` | The core/adapter architecture itself, plus `savings_rate`, `fi_number`, `project` → seeds `core/goals.py` |
| `espin086/CompountInterestAPI` | Compounding math, already packaged and tested |
| `legacy_code/` (git history) | The R allocation LP this project ported; its formulation and known answer are in `docs/allocation-lp-reference.md` |
| `espin086/NewsWaveMetrics` | `fetch_yfinance.py` and `extract_economic_data.py` — working yfinance + FRED extraction patterns |
| `espin086/jjutils` | `base_regression.py` — regression scaffolding for `core/factors.py` |
| `espin086/Econometrics` | statsmodels usage patterns for `core/timeseries.py` |

## Milestones

Each is one OpenSpec change under `openspec/changes/`.

| # | Change | Ships |
|---|---|---|
| 0000 | `release-engineering` | CI gate, version-gated PyPI publishing |
| 0001 | `foundation-data-and-cli` | Onboarding (`init`/`doctor`/`upgrade`), command registry, storage port + SQLite adapter, providers, data quality, currency model, logging + tracing, test scaffolding, `sobres data *` |
| 0002 | `portfolio-optimization` | **v1.0.0** — returns/risk, MVO, frontier, backtest |
| 0003 | `local-persistence` | Schema + migrations, saved portfolios/goals/runs, `sobres db` |
| 0004 | `web-ui` | API and UI derived from the registry, React SPA, jobs + SSE, `sobres serve`, `sobres open` |
| 0005 | `docker-distribution` | One image on Docker Hub, CLI entrypoint, `sobres deploy` |
| 0006 | `landing-page` | Animated dark GitHub Pages site |
| 0007 | `equity-factor-analysis` | Single-stock analysis, CAPM, Fama-French 3/5 + momentum |
| 0008 | `goal-planning` | Retirement/FIRE, house, car, education, Monte Carlo |
| 0009 | `econometrics-forecasting` | Joint ridge VAR / Minnesota BVAR price forecasts with held-out controls, stationarity diagnostics, GARCH volatility, robust regression (direct ML models and the macro preset deferred) |
| 0010 | `currency-and-ppp` | FX attribution and hedging, PPP comparison, PPP-adjusted goals |
| 0011 | `rebrand-sobres` | Rename through the code: import package, console script, env vars, image, pages URL |
| 0012 | `foundation-review-fixes` | Foundation correctness and regression contracts, implemented in the local foundation |
| 0013 | `template-development-alignment` | **Superseded 2026-09-16** — the boundaries it proposed already exist and are tested |
| 0014 | `onboarding-defaults` | `init` asks one question, `--start` defaults to five years, usage errors show an example |
| 0015 | `risk-free-proxy` | Risk-free rate sourced from FRED or Ken French; never an assumed zero |

0001 → 0002 is the v1.0.0 release. 0003 → 0006 turn it into a deployable product
with a UI. 0007–0009 then add analytics to a UI that already exists, rather than
retrofitting one at the end. 0010 makes the whole tool international, last because
it is the change that touches every earlier one. 0002–0008 and 0010 shipped in the
first published version, 1.1.0. See each proposal for exact dependencies rather than
inferring them from numbers.

0011 is out of band: it renames the project and can land at any point, though the
longer it waits the more published artifacts carry the old name.

## Versioning and releasing

SemVer, and the version has exactly one home: `src/sobres/__about__.py`. Nothing
else declares it. `pyproject.toml` reads it dynamically, the wheel metadata, the
container tag, and `sobres --version` all derive from it, and a packaging test
fails the build if any of them disagree.

**The version bump is the release trigger.** Merging a bump to `main` publishes;
any other merge publishes nothing and says so. There is no separate release
command to remember and no window where `main` is "about to be" released.

| Rule | Enforced by |
|---|---|
| One version source | `tests/test_packaging.py` asserts installed metadata parity |
| A published version is never re-published | `check_release.py` queries the index and fails closed on any non-404 error |
| Every version has a CHANGELOG section | the release gate refuses a bump without one |
| Every published version is tagged and has a GitHub release | the publish job creates both, from the CHANGELOG section |
| Nothing publishes from a red build | `release.yml` calls `ci.yml` via `workflow_call`; one definition of green |
| Nothing publishes from an unreviewed commit | `main` is protected: pull request required, `All checks passed` required, admin-only merge, linear history |
| Publishing is off until deliberately armed | the repository variable `RELEASE_ENABLED` must be `true` |

Pre-1.0 the minor version carries breaking changes. From v1.0.0 — shipped by 0002 —
the CLI's command surface, its `--format json` shapes, and the `sobres.core` public
functions are the compatibility surface, and breaking any of them is a major bump.
Anything under a module named `_internal` is not part of it.

Credentials, by index and registry:

| Target | Credential | Scope |
|---|---|---|
| PyPI | `PYPI_PROD` | organization secret, shared across `AI-Solutions-Lab-LLC` |
| TestPyPI | `PYPI_TEST` | organization secret |
| Docker Hub | `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | repository secrets — only this repository publishes an image |

## Non-negotiables

1. **Not investment advice.** Every report-style output carries a disclaimer footer.
2. **No key, no problem.** The tool works out of the box on free sources.
3. **Reproducible.** Same inputs + same cached data + same seed → identical output.
4. **Cite the math.** Each core function's docstring names the formula and a source.
5. **Exposed UI operations never diverge from the CLI.** Both use shared services
   and explicit registry exposure; parity also rejects routes for excluded commands.
6. **Swappable things sit behind ports.** Data providers, the storage backend,
   and the solver are protocols in this codebase's namespace; their library types
   never appear in signatures outside their adapter.
7. **Observability never changes behavior.** No secret in a log or a span, no
   log on stdout, no instrumentation inside `core/`.
8. **Onboarding stays three commands.** A milestone that adds a key, provider,
   or dependency declares a setting and a doctor check in the same change, and
   the build fails if it does not.
9. **No forecasting of exchange rates, ever.** PPP is reported as a valuation
   gap, never as a signal, a target, or a convergence path.
10. **Every release is versioned, gated, and recorded.** Nothing reaches an index
    or a registry except through the pipeline in 0000, from a green `main`, with a
    CHANGELOG section and a git tag. No manual upload, ever.

## Template and context decisions

Change 0013 recorded the AISL project-template revision (52e8426) and a private
context-lake pin as a baseline; it was superseded (see its proposal) and no private
context is needed to build, test or release this repository. 0000's organization-token
publishing contract (`PYPI_PROD` / `PYPI_TEST`, no OIDC, `RELEASE_ENABLED`) stands, tracked
by #21. The landing page deploys only when `PAGES_ENABLED` is `true`; the container image
publishes only when `DOCKER_RELEASE_ENABLED` is `true`.
