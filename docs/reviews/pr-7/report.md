# PR #7 review — request changes

Reviewed 2026-09-13: [0001: Foundation](https://github.com/AI-Solutions-Lab-LLC/sobres/pull/7).

**Recommendation: request changes.** The test suite and CI are green, but independent execution found broken onboarding, a missing runtime dependency, secret logging, silent factor-data loss, and an incomplete migration backup. These are observable failures of the intended foundation, not style preferences.

## Revision and scope

| Item | Reviewed value |
|---|---|
| Head | `dd5d6f077e01e972feefe85629b81b1e63df6078` |
| Base branch | `claude/kind-sagan-4yakbc` |
| Base SHA | `8e989f36d93e565df9281ff68bde70402c0ab7c2` |
| Head/main merge base | `81affc822b7db01f4a6e9ce318143ec7023c450f` |
| Current remote main | `2b844ebcf2df350a5cdc07133ab1e7056777e709` |
| OpenSpec | `0001-foundation-data-and-cli`; also `0011` tasks B1–B4 |
| Changes | 127 files, including large synthetic fixture files |
| Review checkout | `/private/tmp/sobres-pr7-review`, detached at the head above |
| Test platform | macOS arm64, Python 3.12.13 |

PR #7 is still targeted at the rebrand branch, despite PR #6 having merged. Its base tree and remote main tree are identical at review time, so this does not change the code findings; retargeting to main would make the stack easier to follow. The remote head was rechecked and unchanged. No GitHub review or comment was posted. The user's original working branch was preserved, and the reviewed clone's source tree remains unchanged.

## Findings

P1 means fix before merge because a central workflow, data correctness, or credential/state protection fails. P2 means a concrete correctness issue requiring a fix, with a narrower trigger.

### F1 — P1: Secret-valued config commands leak their value into logs

Location: [`src/sobres/cli/main.py:153–156`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/cli/main.py#L153-L156).

`sobres --log-level DEBUG config set fred_api_key REVIEW-DUMMY-NOT-A-REAL-KEY-987654321` succeeds but writes that exact dummy key to stderr. `command.start` logs `params.model_dump()`, which has separate `key` and `value` fields. The redactor masks `key` while leaving the secret under the innocently named `value`. The record is emitted at INFO, so DEBUG is not the only affected level. The same logging pipeline can write it to the optional file sink.

Expected: observability “Redaction” / “Enforced by test” and CLI “Secrets are never echoed.” Actual: the dummy secret appears in stderr; stdout is masked. Existing all-command redaction tests use `config set log_level WARNING`, so they never exercise this path.

Fix: derive redaction from the setting/parameter's secret semantics before rendering logs, including values passed through generic key/value parameters. Add actual `config set fred_api_key` tests at INFO/DEBUG and against the file sink. Use only dummy keys in these tests.

### F2 — P1: The cache discards every `Mkt-RF` observation

Location: [`src/sobres/data/cache.py:123`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/data/cache.py#L123).

The generic cache uppercases all symbols, changing `Mkt-RF` to `MKT-RF`. The factor frame keeps its required mixed-case name, so `_to_observations()` skips the missing uppercase column. Reindexing the result later creates an all-missing `Mkt-RF` column. This affects both cold and warm cache paths and therefore the actual CLI.

Reproduction: direct fixture-backed FF3 July 1926 returns `Mkt-RF = 0.0296`; the same request through cache returns `NaN` and CLI JSON returns `null`. A live FF5 CLI request for January–March 2024 also returned `null` for all three market-factor rows, despite the live provider shape test passing.

Expected: market-data “Supported models,” “Decimal convention,” and “Cache hit.” This silently breaks the market input needed by later factor analysis. The existing cached-factor test checks call counts, row counts, and column names, but never values.

Fix: preserve opaque series identifiers in shared storage/cache; normalize ticker symbols at the ticker boundary. Assert equality of uncached, cold-cache, warm-cache, subrange, and CLI values for all factor columns.

### F3 — P1: Migration backup omits committed WAL data

Location: [`src/sobres/data/storage/adapters/sqlite.py:242–247`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/data/storage/adapters/sqlite.py#L242-L247).

`_backup_before_migration()` copies only the main database file using `shutil.copy2`. With WAL enabled, committed data can still reside in the WAL sidecar. The resulting backup is not a consistent snapshot.

Reproduction: create an existing schema-version-0 WAL database, disable automatic checkpointing, commit a `user_authored` table and row, keep its connection open, and open it through the adapter to apply migration 1. The backup opens, but querying it fails with `no such table: user_authored`. The live database still contains the row; the defect is in recovery protection.

Expected: the automatic pre-migration backup promised by onboarding “Post-upgrade migration” and the PR's storage implementation. Fix: use SQLite's online backup operation, as the adapter already does in `export_to`, and test restoration with committed WAL data and another connection open. A file-exists assertion is insufficient.

### F4 — P1: A base install cannot execute the advertised price command

Location: [`src/sobres/data/yfinance_provider.py:62–69`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/data/yfinance_provider.py#L62-L69); dependency declaration: `pyproject.toml`.

I built the wheel and installed it with only its normal dependencies in `/private/tmp/sobres-pr7-base`. Onboarding works in noninteractive mode, but `sobres data prices AAPL --start 2024-01-02 --end 2024-01-10` exits **4**, reporting `yfinance is not installed` and requiring `sobres[data]`.

Expected: the proposal's explicit fresh-`pip install sobres`, no-key outcome and onboarding “Time to first result.” The optional dependency placement is inherited from the scaffold, but this PR introduces the live price implementation and claims that installation outcome. The development extra and CI's fixture source hide the failure.

Fix: make the required price client part of the base install, or explicitly resolve a product/spec change to the installation promise. Prefer preserving the promised base experience. Test dependency availability from the clean wheel without fixture injection. Keep live network failures separate from dependency failures.

### F5 — P1: Optional settings cannot be skipped in the real init wizard

Location: [`src/sobres/cli/context.py:150–152`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/cli/context.py#L150-L152).

In an actual PTY, `sobres init --offline` displays `fred_api_key (enter to skip):`. Pressing Enter displays the same prompt again. `default=default or None` turns an intended empty-string default into `None`, causing Typer/Click to require a nonempty answer. This prevents the keyless guided path.

Expected: onboarding “Optional settings can be skipped.” Existing wizard tests inject a fake `Context.prompt` and bypass the real prompt implementation, so they pass.

Fix: preserve the empty-string default where skipping is allowed. Test through the real TTY/input boundary, entering blanks for every optional setting and confirming that setup finishes without a FRED key.

### F6 — P2: Refresh preserves withdrawn values and caching removes missing dates

Location: [`src/sobres/data/cache.py:204–207`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/data/cache.py#L204-L207).

The cache skips NaN observations before upsert. If a provider revises a previously valid value to missing, refresh never overwrites that row. The old number survives and the refreshed range is marked fresh. On an initial fetch, dates that are missing in every requested series disappear entirely, undermining explicit gap handling.

Reproduction: cache `[10.0, 11.0]`, refresh with `[10.0, NaN]`; the second value remains **11.0**. A separate two-date request `[1.0, NaN]` is returned as just **one date**.

Expected: “Forced refresh,” “Observation identity,” and “Missing data has a policy, never a default.” Fix: preserve explicit null observations through the port and define replacement semantics for withdrawals, including dates omitted altogether from a later payload. Test value-to-null revision and all-series-missing dates as distinct cases.

### F7 — P2: Extending cached prices through a weekend rejects a valid ticker

Location: [`src/sobres/data/yfinance_provider.py:161–163`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/data/yfinance_provider.py#L161-L163).

Cache AAPL for January 2–5, 2024, then extend the end date to Sunday January 7. The cache correctly requests only January 6–7, but that empty history is interpreted as `UnknownTickerError`, so the whole request fails rather than returning cached weekday observations. This was reproduced offline with the supplied Yahoo fixtures.

Expected: “Partial-range reuse.” The spec itself also needs correction: “A requested ticker does not exist” currently equates any empty response with an unknown ticker. A valid ticker can have an empty weekend/holiday window.

Fix: distinguish symbol validation from “no observations in this interval”; record the valid empty interval in the fetch log and return existing observations. Test weekend-only and holiday-only tails, and retain a separate true-unknown-symbol failure case.

### F8 — P2: Conversion assigns a currency when metadata is missing

Location: [`src/sobres/data/currency.py:218–222`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/data/currency.py#L218-L222).

`convert_frame(frame, "USD", rates=None)` accepts a frame with no currency metadata and returns its unconverted values labeled USD. `all(...)` is true for an empty currency mapping, so the later missing-column validation is bypassed. A partial mapping whose listed columns all match the target has the same problem.

Expected: currency “Unknown currency,” “Currency is discovered, not assumed,” and “Single-currency work is unaffected” only when every input is actually known to share that currency. This is a public data-layer failure; current Yahoo provider validation reduces its exposure through the price CLI.

Fix: validate complete currency coverage before taking the no-conversion shortcut. Test absent metadata, partial mappings, and a correctly labeled single-currency frame.

### F9 — P2: Init exits successfully after its closing doctor fails

Location: [`src/sobres/cli/commands/init.py:178–187`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/cli/commands/init.py#L178-L187).

Initialize, set the config's mode to `0644`, and repeat unchanged `init --non-interactive --offline --format json`. JSON reports a failed `config-file` check and `exit_code: 1`, while the actual process exits **0**. Unlike the doctor handler, init never sets `ctx.pending_exit_code`.

Expected: onboarding “Ends with proof” and a dependable automation result; the spec should explicitly state how init propagates closing doctor failures. Fix: propagate that status and test the subprocess return code against the report. Also decide whether unchanged init repairs permissions to satisfy “Storage is set up,” which promises a `0600` config.

### F10 — P2: The documented `--no-verify` option does not exist

Location: [`src/sobres/registry.py:383–384`](https://github.com/AI-Solutions-Lab-LLC/sobres/blob/dd5d6f077e01e972feefe85629b81b1e63df6078/src/sobres/registry.py#L383-L384).

`sobres init --no-verify --offline` exits **2** with `No such option: --no-verify (Possible options: --verify)`, although `InitParams.verify` documents that spelling and defaults to true. The generator declares only a positive boolean flag, so users cannot select false through the promised option.

Expected: registry “Defaults have one source” / generated parameter behavior, and onboarding's consent controls. Fix: generate both boolean forms where needed and test false-default and true-default parameters through actual CLI parsing. `--offline` currently governs the closing doctor checks; it is not a replacement for configuring the wizard's verification option.

## OpenSpec assessment and changes needed

**Do not weaken the no-key, no-data-loss, or secret-redaction requirements to make this implementation pass.** Correct the code against those requirements. Several spec issues also need a deliberate update:

1. **Strict validation fails before considering implementation.** OpenSpec 1.13.0 reports 33 errors and 5 warnings for change 0001: requirement headings often have scenarios but no requirement text, and some omit normative SHALL/MUST language. The spec delta files are unchanged from this PR's base, so these are inherited authoring defects. Add requirement-level text and validate again.
2. **Empty data is not proof that a ticker is invalid.** Revise the unknown-ticker scenario to distinguish a nonexistent symbol, a closed-market interval, and a date range outside available history. Add cache-extension acceptance cases (F7).
3. **Define canonical identifiers per dataset.** The price model describes uppercase ticker symbols, while factor requirements explicitly require `Mkt-RF`. State that generic storage preserves identifiers; price normalization does not apply to factor names (F2).
4. **Resolve naming exceptions in writing.** 0011 says every declared environment variable starts with `SOBRES_`; 0001 still names `FRED_API_KEY`, while tracing uses standard `OTEL_*`. The implementation uses primary `SOBRES_FRED_API_KEY`, a lower-priority `FRED_API_KEY` alias, and standard OTel exceptions. This is a reasonable compatibility choice that needs matching scenarios in both specs.
5. **Specify what “identical output” includes.** Observability requires byte-identical stdout across log/tracing settings. Tests instead remove timestamps, cache metadata, settings rows, disk/cache checks, and other fields. Freeze controlled state for strict byte comparisons, or explicitly approve a narrower data-value invariant and enumerate allowed diagnostic differences. Do not call the current test a byte comparison.
6. **Restore honest completion status.** `status: implemented` and checked completion boxes overstate readiness. Fixtures remain synthetic rather than recorded as required; D4's reuse audit is deferred; the FRED FX alternative is advertised by the currency spec/settings but `FxParams.source` permits only `ecb`. Add the adapter or explicitly defer it. Map follow-on UI/analytics promises to their own milestones rather than claiming them complete in 0001.
7. **Clarify storage wording.** “Everything stored locally is one SQLite file” conflicts with secret TOML configuration, optional log files, backups, and WAL sidecars. Define the database as the authoritative application/cache store with documented operational exceptions. Keep the backend-neutral storage contract separate from SQLite's default deployment layout.
8. **Make operational failure semantics explicit.** Add init's exit propagation, real optional-input behavior, consistent backup restoration, and cache null-revision cases. For future observability work, retain the existing explicit carry-forward/alignment logging promises; helper unit tests alone do not demonstrate those events at integration boundaries.

The lack of a recorded fixture is disclosed by the author rather than concealed. Live shape tests now provide additional evidence, but I did not replace the fixture corpus or verify FRED without the user's key. A scenario-name search cannot substantiate the claim that all 179 scenarios are behaviorally proven.

## Evidence matrix

This matrix groups related acceptance scenarios. “Partial” means the named tests passed but independent checks contradicted part of the requirement, or some necessary verification was not performed.

| Spec / scenarios | Implementation / existing assertions | Independent evidence | Assessment |
|---|---|---|---|
| CLI: Version, Bare invocation | `cli/main.py`; `tests/cli/test_main.py` checks exits/help | Installed wheel entrypoint ran | Verified for tested environment |
| CLI: Prices, Factors, JSON complete | data handlers/renderers; CLI tests parse JSON and columns | Live prices/FX populated; cached factor value becomes null | Partial; F2, F4 |
| Onboarding: three-command path | init/doctor; clean-wheel CI with fixtures | Base wheel init/doctor run; live price dependency absent | Partial; F4 |
| Onboarding: optional skip, guided TTY | `Context.ask`; wizard unit tests replace prompts | Real PTY repeats blank FRED prompt | Contradicted; F5 |
| Onboarding: idempotent, storage set up | init; byte-identical config test | Unchanged insecure config remains insecure | Partial; F9 |
| Onboarding: Ends with proof / doctor exit | separate init/doctor handlers | JSON failure exit 1, init process exit 0 | Contradicted; F9 |
| Registry: CLI generated, validation | `registry.py`; generated command count and model-rule tests | Documented negative boolean option rejected | Partial; F10 |
| Market data: model columns/decimal values | factor parser; known 1926 row tested without cache | 0.0296 direct; missing through cold/warm cache and live CLI | Contradicted; F2 |
| Cache: hits, subranges, revisions | cache tests check hits/TTL/numeric updates | Weekend tail fails; null revision retains stale number | Partial; F6, F7 |
| Missing data: explicit policies | `gaps.py`; synthetic classification/fill tests | Cache removes all-missing dates before policy can inspect them | Partial; F6 |
| Storage: round-trip, rollback, portability | storage conformance suite and schema tests | Full suite passes | Verified by existing suite on SQLite; other backends not shipped |
| Storage: migration recovery | sqlite adapter; pre-migration backup | Restored backup has no committed user table from WAL | Contradicted; F3 |
| Currency: quote normalization, triangulation | currency/FX tests use known rates and subunits | Existing suite passes; live EURUSD fetched | Verified for covered cases |
| Currency: unknown metadata | `convert_frame`; provider-level missing-currency tests | Unlabeled frame silently becomes USD | Contradicted; F8 |
| Currency: keyless default/FRED alternative | ECB adapter and `FxParams.source` | ECB live command works; no selectable FRED alternative | Partial; spec scope decision |
| Observability: redaction | formatter; sentinel test samples nonsecret config value | Actual secret-valued command leaks dummy key | Contradicted; F1 |
| Observability: output invariance | invariant suite strips selected fields | Semantic comparisons pass; strict bytes not established | Partial; spec clarification |
| Testing: recorded payloads/drift | fixture metadata and live source tests | Synthetic corpus; 3 live shape checks pass, FRED skipped | Partial |
| Testing: every scenario has a test | `test_scenarios.py` scans text references | Name coverage passes but misses all failures above | Reference coverage only |
| 0011: stale env / legacy directories | dedicated main/doctor tests | Offline suite passes; actual legacy migration not executed | Existing-test evidence only |

## Checks executed

| Check | Result |
|---|---|
| `pytest -m 'not network' --cov --cov-report=term --cov-fail-under=90` | **364 passed**, 4 deselected, 1 warning; **96.38%** coverage; 12.78s |
| Ruff 0.16.7 lint + format | Pass; 96 Python files already formatted |
| mypy 2.3.1 | Pass; 44 source files |
| Wheel + sdist build, wheel built from sdist | Pass |
| Twine strict artifact validation | Both pass |
| Clean base wheel install | Pass; price command fails as F4 |
| Live Yahoo / ECB / Ken French shape tests | **3 passed** in 3.07s |
| Live FRED shape test | **Skipped**: key not available to reviewer |
| Live end-to-end prices | 7 rows, AAPL/MSFT, Jan 2–10 2024 |
| Live end-to-end FX | 7 EURUSD rows; Jan 2 2024 = 1.0956 |
| Live end-to-end factors | 3 FF5 rows Jan–Mar 2024; market factor null in each |
| Independent offline probes | Reproduced F1–F4 and F6–F9; see `evidence/probes.json` |
| Actual PTY init | Reproduced F5; cancelled without entering a key |
| `init --no-verify --offline` | Reproduced F10: exit 2 |
| OpenSpec 1.13.0 strict validation | **33 errors, 5 warnings**, inherited spec files |
| Dependency audit of resolved environment | No known vulnerabilities; pinned-version audit completed after pip-audit's temporary ensurepip subprocess crashed |
| Workflow lint | Not rerun locally: actionlint absent. Reviewed changed workflow/hooks; GitHub lint job passed |
| GitHub aggregate / platform checks | All success, including Python 3.11–3.13 Linux and 3.12 macOS/Windows |

The offline suite ran in the restricted execution environment with live tests deselected; no socket-level audit was performed. Only Python 3.12/macOS was executed locally. Numerical analytics in later PRs, future backends, the deferred cross-repository reuse audit, and production deployment were outside scope. Dependency versions were freshly resolved because the PR has no lockfile; this was not a minimum-version compatibility matrix.

## Deliverables and next step

- [Self-test guide, including FRED setup](self-test.md).
- [Independent probes](reproduce.py) and [captured observations](evidence/probes.json).
- [Exact draft GitHub review](github-review.md), with inline locations above.
- Repo guidance: [`AGENTS.md`](../../../AGENTS.md).
- Reusable skill: [`openspec-pr-review`](../../../skills/openspec-pr-review/SKILL.md).

I would submit a **request-changes review**, grouping the cache's null/withdrawal symptoms into one comment and separating inherited spec authoring issues from new defects. Fix and rerun the reproductions before approving. This review does not authorize merging or publishing anything.
