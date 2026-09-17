# PR #8 review — request changes

Reviewed September 13, 2026. [0002: Portfolio optimization](https://github.com/AI-Solutions-Lab-LLC/sobres/pull/8).

**Request changes before releasing v1.0.0.** The four basic commands work, including live-data runs, and the Python 3.12 suite is green. Independent execution nevertheless found incorrect drawdowns, lookahead in the actual backtest adapter, and biased returns after dropping missing prices. The current release cannot yet be installed from PyPI or Homebrew.

This is a review, not implementation approval. No PR comments were posted, no implementation files changed, and no release was published.

## Revision, stack, and contract

| Item | Reviewed state |
|---|---|
| Repository | AI-Solutions-Lab-LLC/sobres |
| PR | #8, open |
| Head | `21724ce35c6a4b3f5d89db265517bf77a38d425f` |
| Actual base / merge base | `dd5d6f077e01e972feefe85629b81b1e63df6078` |
| Base branch | `claude/kind-sagan-4yakbc-0001-foundation` |
| Remote main | `2b844ebcf2df350a5cdc07133ab1e7056777e709` |
| User's local main | `e0432c5`, four commits ahead of remote main |
| Changed files | 32, confirmed with local three-dot diff and paginated GitHub API |
| Review checkout | `/private/tmp/sobres-pr8-review.7emJ3R/head`, detached |
| OpenSpec | `0002-portfolio-optimization`; foundation contracts in 0001 |
| Remote review discussions | No reviews, issue comments, or inline comments at inspection |
| Final head check | Same head at the final check |

PR #8 stacks on merged PR #7's old head. Local main contains foundation corrections and PR #17's recorded fixtures, but this PR does not. Remote main also lags local main. Integrating that work and reviewing the resulting delta is necessary; simply changing the PR base does not add the missing corrections.

I read the proposal, design, tasks, spec delta, project/config conventions, CLAUDE.md, PR template, CI, pyproject, related foundation requirements, tests, and complete changed-file list. The 0002 design/spec are identical at base and head; the proposal changes status to implemented and tasks change to checked. There is no populated accepted-spec collection under `openspec/specs` at this revision. The change documents carry the contract.

The scope is CLI/library optimization. Saved portfolios/jobs belong to 0003, web UI to 0004, containers to 0005; their absence is not a defect in this PR. Homebrew was added as a distribution expectation during this review and needs an explicit follow-up contract.

## Prioritized findings

The standalone [reproduction script](reproduce.py) uses synthetic inputs, the installed PR package, and isolated temporary state. Full CLI outputs are in [evidence](evidence/). Synthetic data establishes code behavior, not provider truth.

### F1 — P1: Use only risk-free observations available before each rebalance

Location: [src/sobres/cli/commands/optimize.py:472–479](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/cli/commands/optimize.py#L472-L479).

The strategy closes over `u.risk_free`, computed once from the entire fetched window, including future out-of-sample dates. Changing only DTB3 at/after the first trade changes the allocation on that trade, despite identical prior prices and rates. The independent synthetic reproduction moves A from 58.1251% to 50.9666% on 2020-05-20. This invalidates the no-lookahead guarantee; the existing test perturbs only the return frame supplied to a different strategy. Resolve a lagged/as-of risk-free input separately for each rebalance, retain explicit constant overrides, and test future-rate perturbations through this handler. Separate the rate used for decisions from any ex-post reporting average.

### F2 — P1: Include starting capital in the drawdown high-water mark

Location: [src/sobres/core/risk.py:107–109](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/core/risk.py#L107-L109).

For returns `[-0.5, 0.1, 0.1]`, `max_drawdown` reports 0.0 and a recovery on the second date. Starting from 1.0, wealth is 0.50, 0.55, 0.605: the correct maximum drawdown is -50%, with no recovery. The running peak begins after the first loss and therefore excludes initial capital. This understates losses in both the risk command and the backtest, and corrupts Calmar. Include initial wealth, define how its timestamp is represented, and add first-period-loss, unrecovered-loss, and first-period-cost regression cases. Relevant scenario: Max drawdown.

### F3 — P1: Preserve return intervals when dropping missing prices

Location: [src/sobres/cli/commands/optimize.py:129–140](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/cli/commands/optimize.py#L129-L140).

`--fill drop` removes price rows before calculating returns. On a daily series growing 10% per trading day, an interior missing price creates a 21% two-session return that is then treated as one daily observation. The probe returns `[0.1, 0.21, 0.1, 0.1, 0.1, 0.1]` with frequency `daily`. This biases means, volatility, and annualization used by every optimization command. Compute period returns on the original trading index before dropping invalid intervals, or explicitly represent and annualize irregular intervals. Add a hand-calculated interior-gap test through `load_universe`, and report the dates/observations lost. Relevant scenarios: Return computation and conventions; Missing observations; Filling is explicit.

### F4 — P2: Provide the benchmark required by the exposed CAPM estimator

Location: [src/sobres/cli/commands/optimize.py:171–173](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/cli/commands/optimize.py#L171-L173).

`--returns-estimator capm` is offered by the shared model, but `estimate` supplies neither a benchmark nor the resolved risk-free rate to `expected_returns`. A fixture-backed Markowitz command exits 2 with 'the capm estimator needs a benchmark return series'; there is no benchmark option that repairs the invocation. Frontier and backtest have the same missing input. Add a declared benchmark parameter and align/convert its returns, forwarding the appropriate risk-free input, or explicitly narrow the CLI's advertised choices pending a scoped follow-up. Test every estimator through the generated CLI. Relevant scenarios: Available estimators; Markowitz; parameter validation before the handler.

### F5 — P2: Make target objectives usable in the backtest interface

Location: [src/sobres/cli/commands/optimize.py:406–409](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/cli/commands/optimize.py#L406-L409).

BacktestParams accepts `target_return` and `target_risk`, but declares no target parameter and the strategy does not pass one to the solver. Selecting `target_return` exits 2 asking for `--target`; adding `--target 0.1` exits 2 because that option does not exist. Supply the target field with cross-field validation and pass it at each solve, or restrict the objective choices to the supported backtest subset and document that scope. Test both target objectives through actual CLI parsing and an out-of-sample run. Relevant scenarios: Supported objectives; Backtest; Cross-field rules live in the model.

### F6 — P2: Condition or reject covariance at the public optimizer boundary

Location: [src/sobres/core/optimize.py:181–184](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/core/optimize.py#L181-L184).

The public `optimize` function directly uses the supplied covariance; only the separate estimator path conditions it. For `sigma=[[1,2],[2,1]]` (eigenvalues -1 and 3), min-variance returns 50/50 with variance 1.5, no repair, and status 'optimal', although an endpoint has variance 1.0. The proposal explicitly promises never to solve silently on a broken covariance, and core is part of the v1 compatibility surface. Condition/reject non-finite, asymmetric, or non-PSD input at this boundary and return repair provenance. Test direct-library calls as well as estimator-produced matrices.

### F7 — P2: Reject non-finite weights and invalid seeds before fetching data

Location: [src/sobres/cli/commands/optimize.py:536–542](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/cli/commands/optimize.py#L536-L542).

The sum validator accepts `[NaN, NaN]` and `[Infinity, -Infinity]` because comparisons with NaN are false. `optimize risk --weights nan nan` consequently fetches data and exits 1 as an internal 'no weight' error. Similarly, the newly exposed `--seed -1` reaches NumPy and exits 1 after fetching; a NaN risk-free override becomes a solver failure. Use finite numeric types and nonnegative seed constraints in the parameter models, with usage exit 2 before provider calls. Test NaN, infinity, negative seeds, and target/lookback cross-field constraints. Duplicate tickers also trigger an inherited provider failure and should be rejected or deliberately aggregated.

### F8 — P2: Return the requested number of frontier portfolios

Location: [src/sobres/core/optimize.py:390–397](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/21724ce35c6a4b3f5d89db265517bf77a38d425f/src/sobres/core/optimize.py#L390-L397).

The implementation produces `n_points` grid portfolios and then appends the max-Sharpe portfolio. `--points 5` returns six rows while the JSON declares `n_points: 5`; `--points 50` returns 51, contrary to Frontier generation. The CLI test explicitly asserts this contradictory extra row. Include the named points within the requested count, deduplicate coincident extrema, and test actual row count and metadata. If an additional named point is the intended product choice, agree and update the contract, option description, and metadata together.

## Spec decisions and completion claims

These are contract issues, not reasons to change correct math merely to satisfy a flawed sentence.

1. **Validation:** OpenSpec 1.13.0, with `OPENSPEC_TELEMETRY=0`, reports three strict-validation errors: missing requirement text for One currency per computation, Efficient frontier, and the optimize command group. Those exact spec bytes already exist at the base; the validation defects are inherited. Add normative requirement text.
2. **Sharpe comparability:** Markowitz uses arithmetic expected returns, while the risk panel subtracts annual risk-free from geometric CAGR. The spec's geometric default plus generic “annualized_return” wording makes this internally plausible, but these are different statistics. Comparing their gap as estimation error alone is misleading. Define/report a conventional arithmetic excess-return Sharpe consistently and show CAGR separately, or explicitly label the geometric variant. Sharpe's original definition uses the mean and standard deviation of differential returns. [Sharpe (1994)](https://www-leland.stanford.edu/~wfsharpe/art/sr/sr.htm).
3. **Sortino:** The scenario calls the denominator the standard deviation of below-target returns. The implementation uses root-mean-square shortfall over all observations, which is a different quantity. Specify the lower partial moment, target units, denominator population, and numerator convention before adjusting the implementation.
4. **Risk-free rate:** Specify which observations are available at a decision date, how historical revisions/vintages are handled, and the currency of the risk-free proxy. A USD Treasury proxy is currently used even for GBP/EUR portfolios. DTB3 is explicitly a discount-basis yield, not a realized daily investable return; define any yield/holding-period conversion rather than treating division by 100 as all the semantics. [FRED DTB3](https://fred.stlouisfed.org/series/DTB3), [ALFRED vintages](https://alfred.stlouisfed.org/series/downloaddata?seid=DTB3).
5. **Transaction cost wording:** The engine follows the stated formula, `cost_rate * 0.5 * sum(abs(delta_weights))`. The docs also call this “10 bps per side.” A complete A-to-B switch gives turnover 1, so code charges 10 bps total rather than 10 bps on both sale and purchase. Entry from all-zero risky weights is charged half the rate. Agree whether the fee is per traded notional, per complete rotation, or a round-trip quote; model initial cash explicitly. The tests intentionally assert initial turnover 0.5, so this is a spec decision. `total_cost` sums fractions charged on different wealth bases, not currency costs or necessarily the terminal performance drag; give it a precise label.
6. **Missing data:** Define handling at every public core boundary. Apart from F3, `portfolio_returns` fills NaN with zero and `walk_forward` uses `nan_to_num` without an explicit caller policy. The standalone probe returns 10% for a row with one unavailable half-weight asset. Estimators/risk metrics also drop missing values internally. Clarify which inputs must already be clean and reject unresolved gaps instead of silently assuming them away. Listing/delisting alignment must record exclusions.
7. **Interface examples:** Proposal examples use `max-sharpe`; actual choices use `max_sharpe`. Several examples omit mandatory `--fill`. Update copy-paste examples, including risk's required start. Define target-risk as a ceiling (current implementation), whereas the design describes an equality.
8. **Frontier contract:** Resolve F8's requested count, actual count, extrema deduplication and machine-output fields before v1's JSON compatibility commitment.
9. **Completion honesty:** C1 says “groups” but the constraint model has none. Either implement them or explicitly defer them. F1's fixture comes from independent Python vertex enumeration, not an R run; this is useful evidence, but does not establish R execution parity. F2's three-asset example checks frontier bounds, not a separately published set of exact weights. F4 is marked complete while release is pending. The definition of done was weakened from live data to “recorded fixtures,” although this revision's provider fixtures are synthetic. Local main's PR #17 recordings are not in this head. Mark partial/deferred scope accurately.
10. **Reproducibility:** Warm-cache table and CSV stdout matched byte-for-byte across WARNING/INFO/DEBUG in these runs. JSON differed in `provenance.fetched_at` despite cache hits. I did not strip it to claim invariance. Freeze the clock/cache for byte comparisons or agree documented metadata exceptions; do not equate changing timestamps with a log-level-induced math change.

## Security and inherited foundation issues

The optimization diff adds no broker connection, order execution, server listener, or shell command execution. Ticker character validation limits the new inputs. The dependency audit found no known vulnerabilities in the resolved review environment. This is a bounded source/runtime review, not proof that every dependency or use case is secure.

**Confirmed inherited credential leak:** An actual `config set fred_api_key` using only a dummy sentinel exits 0 but writes the sentinel to both DEBUG stderr and the configured log file. stdout is masked. This PR inherits the old generic key/value redactor; local main contains the fix. Do not test this with a real key on this head.

**Confirmed inherited install failure:** A wheel installed with base dependencies runs version/init/doctor, but actual prices and Markowitz exit 4: yfinance is missing. The dev extra and fixture smoke tests conceal this. Local main moves yfinance into base dependencies.

**Confirmed inherited wizard failure:** In a real PTY, pressing Enter at “fred_api_key (enter to skip)” repeats that prompt. The blank optional input cannot advance. The command was interrupted, and the user's real configuration was never used.

Other foundation corrections absent from this head include the WAL-safe migration backup, null-revision cache behavior, factor identifier preservation, and boolean option generation. Those were reported in PR #7; they were not all independently rerun in this review. Incorporate the existing fixes rather than duplicating them.

Input validation and resource limits deserve attention before a future HTTP surface: non-finite values currently reach the solver, asset counts are unbounded, and a large lookback can overflow date arithmetic. In this CLI-only milestone these are error handling/resource-control concerns, not a claim of a remotely exploitable endpoint.

## Latency, scale, and architecture

Measured on macOS 26.5.1 arm64, Python 3.14.5, NumPy/SciPy from the isolated review environment. Inputs are synthetic 600-observation matrices, fixed seed 71. Each entry is one measured run, not a p95 or a general latency guarantee; concurrent review activity may affect timings.

| Assets | Min variance | Max Sharpe | 50-point frontier |
|---:|---:|---:|---:|
| 6 | 0.003 s | 0.021 s | 0.162 s |
| 20 | 0.005 s | 0.108 s | 0.438 s |
| 50 | 0.017 s | 0.627 s | 1.570 s |
| 100 | 0.049 s | 3.511 s | 7.508 s |

Max Sharpe invokes 11 solves (one min-variance start plus ten Sharpe starts). The frontier invokes 61 solves and, at 100 assets, about 283,000 objective evaluations. No analytic Jacobian is passed. These observations support adding analytic derivatives and reusing neighboring frontier solutions as initial guesses, while preserving numerical acceptance checks. SciPy exposes `jac` and SLSQP tolerances directly. [SciPy SLSQP documentation](https://scipy.github.io/devdocs/reference/optimize.minimize-slsqp.html).

The fixture-backed two-asset CLI median was roughly 1.1–1.2 seconds per invocation, including Python startup, imports, data parsing/cache work, computation and rendering. Live runs in the shared live cache took about 0.9–1.9 seconds for this small historical window. These are not large-universe or cold-provider benchmarks.

Priorities:

- Add elapsed-time/call-count instrumentation around estimation and solving, with progress on stderr. Backtest already supplies a callback, but progress is INFO-only and does not cover initial fetching. Frontier has no progress callback.
- Validate impossible bounds/targets and malformed lookbacks before network I/O. Set documented asset/point/work limits and offer cancellation for expensive runs; benchmark realistic 50/100-asset monthly backtests before making performance promises.
- Price acquisition currently fetches symbols serially. Consider bounded parallel requests only inside provider adapters, respecting rate limits and avoiding shared SQLite write contention. Keep the synchronous local path simple.
- Preserve the repository's solver port rule: SciPy is currently imported directly by core and no repository-owned solver protocol exists. Add the protocol and behavior-based conformance checks before exposing alternative solvers. Keep provider I/O outside core.
- Do not require a job queue, horizontal scaling, or web load tests for this CLI PR. Those become acceptance criteria when the API/job milestones land.

## Output and user friendliness

The basics are useful: Markowitz prints estimators, shrinkage, weights, expected return/volatility/Sharpe, an in-sample warning, currency, source, and seed. Backtest prints strategy versus equal-weight benchmark, its OOS window, costs and a research disclaimer. JSON remains parseable at all four tested log levels, and CSV is available.

Before calling this a polished v1, I recommend these explicit acceptance cases:

| Surface | Improvement | Acceptance evidence |
|---|---|---|
| Risk/backtest table | Label returns/volatility as percent or decimal, ratios as unitless, VaR/CVaR horizon and sign, observations as count | Known panel renders 0.10 as “10.00%” where appropriate while Sharpe 1.2 stays “1.20”; loss convention is visible |
| Backtest provenance | Include objective, both estimators, seed, bounds, risk-free decision policy and actual training windows | JSON and table identify how the weights were produced; rerun manifest is sufficient without reconstructing CLI history |
| Warnings | Surface concentration and PSD-repair notes from each backtest solve; currently the strategy drops the Portfolio warnings and repair metadata | Deliberately concentrated/repaired case emits a bounded warning summary and records it in JSON |
| Frontier | Print estimator provenance and seed in the table; identify named points within the agreed count | Table/header/JSON agree with requested settings |
| Errors | Cross-field validation before downloads, finite numbers, unique tickers and actionable lookback bounds | Invalid input returns usage exit 2 with the exact next action; no “internal error” for routine typos |
| Documentation | Explain shorting limits, target units, risk-parity interpretation, risk-free assumptions and rebalancing policy | Every documented example executes and its output matches the explanation |
| Comparisons | Distinguish in-sample estimated statistics from realized metrics and the cost/estimation conventions | Do not state that the OOS Sharpe must be smaller or that the gap has only one cause |
| Help link | Replace the relative `docs/why-your-backtest-looks-too-good.md` path with an accessible versioned URL | A wheel-only user outside the repo can open it |

Charts, interactive allocation controls, saved runs and web accessibility are useful for the later UI milestone. They are not required to merge the CLI math foundation.

## PyPI and Homebrew release readiness

At inspection:

- PyPI `https://pypi.org/pypi/sobres/json`: **404**.
- TestPyPI `https://test.pypi.org/pypi/sobres/json`: **404**.
- Homebrew's official formula API for sobres: **404**.
- GitHub releases: none returned.
- `RELEASE_ENABLED=false`.
- Latest Release run [34709406193](https://github.com/AI-Solutions-Lab-LLC/sobres/actions/runs/34709406193): decision/report succeeded; verify, build, publish, and GitHub release jobs were skipped.
- No Homebrew formula/tap files in this repo and no homebrew-named repository among the visible organization repositories.
- Organization secret names `PYPI_PROD` and `PYPI_TEST` exist with visibility ALL; no repository-level copies were listed. Only metadata was inspected, not values or token validity.

At the user's request, [issue #21](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/21) was created for release enablement, authentication alignment, and accurate skip reporting. Its exact body is saved in [pypi-issue.md](pypi-issue.md). No release setting was changed.

The existing 0000 spec requires organization API tokens, and task B5 to wire them remains unchecked. The workflow and release guide still use OIDC and attestations. This mismatch must be resolved before arming; the current agreed path is `PYPI_PROD`/`PYPI_TEST` through the publish action's password input, with OIDC permission and attestation claims removed. OIDC is an alternative only if the contract is deliberately updated.

The inherited Release report claims “Version 0.0.1 is already on the index” for any non-publish decision, including disabled publishing. That message is misleading and explains why a green workflow can look like a completed release. Report the actual skip reason.

**PyPI and Homebrew are separate distribution paths.** After a successful PyPI release, users can install with pip/pipx. Homebrew requires a formula and tap (or acceptance into Homebrew core). The documented tap workflow supports a fully qualified install such as `brew install AI-Solutions-Lab-LLC/tap/sobres` once an organization tap and formula have actually been created. This command is proposed, not currently working. [Homebrew tap documentation](https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap).

Suggested release acceptance order:

1. Fix the review blockers, incorporate the completed foundation into the eventual release branch, resolve spec/status discrepancies, and rerun CI on the resulting exact commit.
2. Finish 0000/B5: wire the existing organization credentials to the correct indexes, disable token-auth attestations, reconcile the release guide, and confirm the intended version/commit and changelog. Token validity and successful authentication remain unverified until a controlled upload succeeds.
3. Exercise the gated TestPyPI path and install the resulting artifact in a fresh environment, then publish the intended production version through the approved workflow. Changing a variable alone does not run the workflow.
4. Verify the public version page, wheel/sdist hashes, GitHub tag/release, and a fresh `pipx install sobres==1.0.0` (or pip in a venv), followed by actual no-key optimization. Do not promise PEP 740 attestations under the agreed token-auth flow.
5. Add a scoped Homebrew distribution change: organization tap, versioned release URL and SHA256, correct Python/runtime dependencies, formula installation/test, update automation and user instructions. Test `brew install` and `brew upgrade`, including an actual data/optimization command.
6. Document platform support actually tested. This review ran on arm64 macOS; it does not establish Intel Homebrew support.

Publishing and creating a tap were not executed as part of this review.

## Capability evidence matrix

| Capability/scenarios | Existing evidence | Independent evidence / gap | Result |
|---|---|---|---|
| Simple/log returns; annualization; geometric vs arithmetic | Formula tests and conventions tests | Gap removal turns a two-session return into one daily return | Partial, F3 |
| Missing observations | Explicit helper-policy tests | Public portfolio aggregation silently zero-fills NaN | Contract/implementation gap |
| Risk panel; max drawdown; Calmar | Hand-computed ten-row case begins with a gain | First loss of 50% reports zero drawdown | Contradicted, F2 |
| Sharpe/Sortino; VaR/CVaR; beta overlap | Existing hand calculations, overlap checks | Definitions and units need reconciliation as above | Partial |
| Mean/EWMA/CAPM expected returns | Core estimator tests | CAPM CLI cannot supply its benchmark | Partial, F4 |
| Covariance methods; shrinkage; PSD repair | Core tests, shrinkage attrs, generated matrices | Public optimizer accepts indefinite covariance without repair | Partial, F6 |
| Min variance/max Sharpe | Analytic two-asset tests at 1e-6; live Markowitz | Supported ordinary positive-definite cases work | Verified for exercised inputs |
| Bounds, target objectives, risk parity, equal weight | Existing core tests | Target backtests lack target input; finite validation absent | Partial, F5/F7 |
| Determinism | Repeated-weight assertions | Warm tables/CSV identical; JSON cache timestamp changes | Partial metadata contract |
| Frontier count; named points; monotonicity | Tests intentionally accept N+1; positive-excess examples | Five requested gives six, also live | Contradicted count, F8 |
| No lookahead | Core-only future-return perturbation test | Actual adapter responds to future Treasury rates | Contradicted, F1 |
| Rebalance schedule; weight drift; benchmark window | Existing core tests include hand-computed drift | Real backtest and live same-window report work | Verified for tested cases |
| Costs | Tests assert specified turnover formula and initial 0.5 turnover | Per-side fee wording and cumulative cost units conflict | Spec correction required |
| Currency conversion/base naming | Existing mixed-GBP/USD fixture CLI test | Full suite passes; live multi-currency optimization not rerun | Existing-test evidence |
| Four CLI commands; formats; logs | Existing CLI/invariant tests | 48 table/JSON/CSV × ERROR/WARNING/INFO/DEBUG runs all exit 0 | Verified happy paths |
| Optional setup/no-key installation | Existing mocked wizard and fixture-wheel checks | Base wheel prices/optimization fail; blank PTY input repeats | Inherited blockers |
| Secret redaction | Existing sentinel checks use nonsecret config value | Actual dummy secret appears in stderr and file | Inherited blocker |
| Textbook/legacy validation | Analytic two-asset cases; Python-enumerated LP fixture | No actual R output, not all claimed textbook coverage | Partial |
| Release/distribution | Green Release status, version 1.0.0 in PR | Publishing skipped; package endpoints absent; no formula | Unshipped |

## Executed verification and limits

| Check | Result |
|---|---|
| Fresh editable dev install, Python 3.12.13 | Passed |
| `pytest -m 'not network' --cov --cov-report=term-missing --cov-fail-under=90` | **453 passed**, 4 deselected, 1 warning; **96.72%** |
| Earlier resumed run, Python 3.14.5 | 452 passed, 1 failed, 4 deselected; **96.62%**; inherited registry introspection emits `Union` instead of `date \| None` |
| Ruff 0.16.7 lint and format | Passed; 114 Python files |
| mypy 2.3.1 | Passed; 51 source files |
| Build wheel + sdist and Twine strict validation | Passed |
| Fresh base-wheel environment | Version/init/doctor pass; live price dependency missing |
| Real interactive init | Optional blank key repeats prompt; interrupted |
| Independent math/integration probes | F1–F3/F6/F8 reproduced; explicit output saved |
| Generated CLI edge cases | CAPM/target paths fail; NaN/negative seed errors reproduced |
| Formats/log levels | 48/48 happy-path calls exit 0; JSON parses |
| Dependency audit | No known vulnerabilities; cache deserialization warnings were emitted |
| Live Yahoo/ECB/Ken French tests | 3 passed |
| Live FRED test | Skipped; no real key accessed or supplied |
| Live end-to-end optimize commands | Markowitz/frontier/risk/backtest all exit 0 for AAPL/MSFT, 2024-01-02 through 2024-03-28, explicit rf=0 |
| OpenSpec 1.13.0 strict validation | 3 inherited errors |
| GitHub CI | All listed checks successful for reviewed head, including Linux/macOS/Windows jobs |
| Workflow lint | Not rerun: this PR does not change workflows; GitHub lint job green |
| Local review script formatting | Black line length 100 and isort Black profile/line length 100 executed; Ruff lint/format pass |

Local dependency resolution is not pinned: versions can differ from the historical GitHub run. The 3.14 issue matters because metadata permits Python >=3.11, although the reviewed CI only lists 3.11–3.13. Tests declared “not network” are a selection, not a network sandbox. Existing test fixtures manipulate HOME internally; the review's independent runtime probes used explicit temporary config/database paths and preserved the actual HOME.

No exhaustive stress/load test, live credential failure test with real secrets, R execution, full multi-currency live journey, frontend evaluation, Homebrew installation, or real publishing was performed. The performance measurements are samples, not service-level promises. The changing JSON timestamps were disclosed rather than removed from comparisons.

See [self-test.md](self-test.md) for commands and expected failures, [github-review.md](github-review.md) for the exact draft, and [github-review.json](github-review.json) for its structured payload. No review has been submitted.
