# PR #7 remediation and self-test

The ten reproduced findings from the review of `dd5d6f0` are addressed by change
0012. The OpenSpec contract was committed and pushed first as `2aa4f30`; the
implementation and this report follow it on `claude/kind-sagan-4yakbc-0001-foundation`.

## Resolution evidence

| Finding | Result and regression evidence |
| --- | --- |
| F1: config values leaked in logs | Registry-declared secret values are redacted in generic command parameters. Actual CLI tests cover INFO/DEBUG, stderr and log files, including secret database URLs. |
| F2: market factor values disappeared | Generic cache identifiers retain their case. Six model/frequency combinations compare direct, cold, warm and subrange values; the CLI also checks a known July 1926 row. |
| F3: backup omitted WAL commits | Migration uses SQLite's online backup API. A backup restores a user table committed in an open WAL connection and passes integrity checking. |
| F4: base install could not fetch prices | `yfinance` is a base dependency. A fresh wheel-only environment fetched seven AAPL/MSFT trading-day rows without extras. CI checks the base client import. |
| F5: Enter could not skip setup | Empty prompt defaults remain empty. Actual Typer input tests and a real terminal session completed setup with blank optional answers. |
| F6: missing revisions retained stale values | NaN observations are persisted; previously cached dates omitted by a refresh become missing. Tests retain unaffected dates and verify subsequent cache hits. |
| F7: weekend extension rejected valid ticker | Empty history with verified currency metadata is accepted. Cached AAPL Jan 2–5 extended through Jan 7 successfully in a live CLI check. Other provider failures remain errors. |
| F8: unknown currency silently relabeled | Conversion requires a valid source currency for every column, including same-currency fast paths. Missing, partial and malformed mappings are rejected. |
| F9: init success hid failed doctor | CLI status follows the health report, and unchanged config files have secure permissions restored. Tests exercise both behaviors. |
| F10: negative boolean option unavailable | Registry-generated booleans expose positive and negative forms. CLI tests verify `--verify`, `--no-verify`, and default values reach validation correctly. |

## Validation

Executed on macOS arm64 with Python 3.12.13:

- Offline pytest: **401 passed**, four live tests deselected, **96.45% branch-aware
  coverage** (90% gate). All ten 0012 scenarios have regression assertions. One
  advisory warning covers scenarios in other proposed changes without tests yet.
- Black and isort on every edited Python file; Ruff lint/format and strict mypy.
- OpenSpec 1.13.0 strict validation of changes 0001, 0011 and 0012.
- Wheel/sdist build and strict Twine validation; fresh base wheel installation,
  version, offline init/doctor, and a real price fetch.
- Actionlint and ShellCheck for CI/hook syntax; installed dependency audit.
- Live Yahoo, ECB and Ken French tests passed. Live CLI factor results contain
  populated `Mkt-RF`; both initial and weekend-extended price commands succeeded.
- Fixed-clock, warmed-cache stdout is compared byte-for-byte for data commands
  across warning/debug logging and console tracing.

FRED's live test was skipped because no key was supplied to the review environment.
Most repository fixtures are synthetic; their replacement with recorded vendor
payloads and the D4 cross-repository reuse audit remain open in 0001. Foundation
therefore remains `in_progress`, while the bounded review correction is implemented.
The live results are observations at review time, not promises of provider uptime.

## Test it yourself

Use a fresh checkout and temporary app state (Python 3.11 or newer):

```bash
git clone --branch claude/kind-sagan-4yakbc-0001-foundation \
  https://github.com/AI-Solutions-Lab-LLC/sobres.git sobres-pr7-test
cd sobres-pr7-test
python3 -m venv .venv
source .venv/bin/activate
python -m pip install .
sobres --version

SOBRES_TEST_DIR=$(mktemp -d)
export SOBRES_CONFIG_FILE="$SOBRES_TEST_DIR/config.toml"
export SOBRES_DB_URL="sqlite:///$SOBRES_TEST_DIR/sobres.db"
sobres init --offline --no-verify
sobres doctor --offline
```

Press Enter at every optional prompt. Setup should finish, show a first command,
and exit successfully. A missing FRED key produces a warning; keyless data works.

```bash
sobres data prices AAPL --start 2024-01-02 --end 2024-01-05 --format json
sobres data prices AAPL --start 2024-01-02 --end 2024-01-07 --format json
sobres data prices AAPL --start 2024-01-02 --end 2024-01-07 --format json
sobres data factors --model ff5 --frequency monthly \
  --start 2024-01-01 --end 2024-03-31 --format json
```

Expect four trading-day rows in each price response, with the same values. The
third response should report a cache hit. The three monthly factor rows must
contain numeric `Mkt-RF` values. Adjusted price values can change with vendor revisions.

Run the regression suite after adding development dependencies:

```bash
python -m pip install -e '.[dev]'
pytest -m 'not network' --cov --cov-report=term-missing --cov-fail-under=90
pytest tests/network -m network -vv
```

For FRED, set `SOBRES_FRED_API_KEY` privately in the shell before live tests, or
save `fred_api_key` in your local config using interactive `sobres init`.
For normal macOS use without the temporary override above, the config lives at
`~/Library/Application Support/sobres/config.toml` and should have mode `0600`.
An organization Actions secret can be named `SOBRES_FRED_API_KEY` and restricted
to this repository; workflows must explicitly map it into the test step's environment.
No credential is included in these commits.
