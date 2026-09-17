# Draft GitHub review — not submitted

Event: **REQUEST_CHANGES**

Commit: `dd5d6f077e01e972feefe85629b81b1e63df6078`

## Review body

I reproduced this branch in a detached clone, built wheel/sdist artifacts, installed the base wheel separately from `[dev]`, ran the offline suite and live provider checks, and exercised the real CLI and terminal wizard.

364 offline tests pass at 96.38% coverage; Ruff, mypy, artifact validation, and the resolved dependency audit pass. Yahoo, ECB, and Ken French live shape tests pass. FRED was skipped because no key was available to the reviewer. Live prices/FX worked, but the actual factor CLI returned null market-factor values.

Requesting changes for the reproducible defects below. The highest priority are secret-valued config logging, lost market-factor observations, incomplete WAL migration backups, the broken base-install price path, and optional inputs that cannot be skipped in the real wizard. Green CI misses these because its samples/mock boundaries do not exercise the failure conditions.

The OpenSpec also needs a readiness pass: strict validation on 1.13.0 reports 33 errors and 5 warnings in inherited spec files; the empty-response/unknown-symbol rule conflicts with weekend cache reuse; environment naming exceptions and the actual output-invariance policy need explicit scenarios. Synthetic fixtures, deferred D4, and the absent FRED FX alternative do not justify marking the entire change complete. These spec gaps should be resolved explicitly rather than weakening data integrity or the no-key install promise.

## Inline comments

### `src/sobres/cli/main.py`, RIGHT line 155

**[P1] Redact secret-valued generic parameters before logging.** Running `sobres --log-level DEBUG config set fred_api_key REVIEW-DUMMY-NOT-A-REAL-KEY-987654321` prints that exact dummy key in stderr. The serialized params have separate `key` and `value` fields: the formatter masks `key` and leaves the secret under `value`. This record is emitted at INFO and reaches the configured logging sinks. Resolve sensitivity from the setting, and add a real secret-valued config command to the redaction tests; the current sample sets only `log_level`.

### `src/sobres/data/cache.py`, RIGHT line 123

**[P1] Preserve factor identifiers in the shared cache.** Uppercasing changes `Mkt-RF` to `MKT-RF`, but the fetched factor frame still has `Mkt-RF`, so `_to_observations` discards the column and the CLI renders null. July 1926 FF3 returns 0.0296 without cache and NaN with either cold or warm cache; live FF5 shows the same defect. Keep ticker normalization at the ticker boundary and compare actual factor values across direct/cache/CLI paths, not just column lists.

### `src/sobres/data/storage/adapters/sqlite.py`, RIGHT line 247

**[P1] Make the pre-migration backup a consistent SQLite snapshot.** Copying only the main file loses committed rows still in WAL. I kept a connection open to a pre-migration WAL database with a committed user table, then opened it through the adapter: querying the resulting backup failed with `no such table: user_authored`. Use the online backup API, already used by `export_to`, and verify restoration with an open writer and uncheckpointed committed data.

### `src/sobres/data/yfinance_provider.py`, RIGHT line 64

**[P1] Include the price client in the promised base installation.** A clean install of the built base wheel followed by `sobres data prices AAPL --start 2024-01-02 --end 2024-01-10` exits 4 because yfinance is absent. The dependency was optional in the scaffold, but this PR now implements and promises prices after plain `pip install sobres`. `[dev]` and the fixture-backed build smoke hide that gap. Add the necessary base dependency and verify it from the clean artifact.

### `src/sobres/cli/context.py`, RIGHT line 151

**[P1] Allow an empty answer for optional wizard settings.** `default=default or None` turns an empty default into a required prompt. In a real terminal, Enter at `fred_api_key (enter to skip)` just repeats the prompt, blocking the keyless setup path. Preserve the empty default and add a real prompt-boundary test; the current wizard tests supply their own prompt callback.

### `src/sobres/data/cache.py`, RIGHT line 205

**[P2] Persist explicit missing observations on refresh.** Skipping NaN leaves a stale cached number unchanged when the provider withdraws it. Cache `[10,11]`, refresh with `[10,NaN]`, and the result still contains 11 despite a fresh fetch record. It also removes dates missing from every series on an initial fetch. Preserve null observations and test both value-to-null revisions and all-missing dates; define how omitted dates are replaced as well.

### `src/sobres/data/yfinance_provider.py`, RIGHT line 163

**[P2] Distinguish empty date windows from unknown symbols.** After caching AAPL for Jan 2–5, 2024, extending through Jan 7 fetches only Saturday/Sunday and raises `UnknownTickerError` for AAPL. A valid empty tail should be recorded as fetched and return cached weekdays. Add a weekend/holiday extension regression and clarify the spec's overly broad empty-response rule.

### `src/sobres/data/currency.py`, RIGHT line 218

**[P2] Validate currency coverage before the no-conversion shortcut.** For a frame without currency metadata, `currencies` is empty and `all(...)` is true. `convert_frame(frame, 'USD', rates=None)` then labels unchanged, unknown-unit values as USD. A partial all-USD mapping similarly bypasses validation. Require known currency for every column before returning the single-currency fast path.

### `src/sobres/cli/commands/init.py`, RIGHT line 178

**[P2] Propagate the closing doctor status to init's process exit.** Initialize, chmod the config to 0644, then rerun unchanged `init --non-interactive --offline --format json`: JSON reports `config-file` failed and `exit_code: 1`, but the process returns 0. Set the pending exit status as the doctor handler does and assert both JSON and subprocess exit behavior. Clarify whether init should repair the permissions as part of its storage/setup guarantee.

### `src/sobres/registry.py`, RIGHT line 384

**[P2] Generate a false form for default-true boolean parameters.** `InitParams.verify` documents `--no-verify`, but `sobres init --no-verify --offline` fails with no such option and exit 2. Only `--verify` is generated, preventing the advertised false selection. Cover both true-default and false-default boolean options through real CLI parsing.
