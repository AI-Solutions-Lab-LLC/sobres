# Foundation completion: recordings and reuse audit

Completes the two remaining 0001 tasks after PR #7 merged at
`13b0a13ba8317d477cc71ad010a8a76c0d5420c9`: real provider recordings and D4's
`NewsWaveMetrics` audit. The follow-up is based on `claude/kind-sagan-4yakbc`,
where GitHub merged PR #7; `main` still pointed to the scaffold at verification.

All Yahoo, FRED, ECB, and Ken French payloads are now recorded from their live
sources with timestamps, source/version information, and exact-byte digests.
See [fixture provenance](../tests/fixtures/README.md) and the
[reuse audit](foundation-reuse-audit.md). Payload replacement is committed
separately from implementation/test changes so the corpus is reviewable.

Recording uncovered and corrected:

- Yahoo CSV replay lost the end date and mishandled mixed DST offsets. It now
  normalizes exchange-local dates before slicing, with US/UK regressions.
- Synthetic Apple data expected an artificial split-day crash in Yahoo Close.
  Tests now verify actual split-adjusted prices and dividend adjustment.
- Fama–French July 1926 expectations needed an explicit vendor revision;
  assertions now use the recorded 202607 CRSP release's literal values.
- FRED holiday missing values and mixed-frequency observation dates are now
  checked against real payloads, including cold/warm cache preservation.
- Clean-wheel doctor incorrectly warned that prices needed an optional extra.
  It now checks the required yfinance client separately from optional modules.

The recorder resolves the declared FRED setting and reports request failures
without exposing credential-bearing URLs. No credentials are committed.

## Verification on 2026-09-13

macOS arm64, Python 3.12.13, OpenSpec 1.13.0:

| Check | Result |
|---|---|
| Offline suite, 90% coverage gate | 408 passed, four live tests deselected; 96.50% line/branch coverage |
| Same suite with macOS sandbox denying network access | 408 passed; 96.50% coverage |
| Live provider tests | All four passed, including authenticated FRED |
| Base wheel, no development/optional extras | Version, noninteractive offline init, offline doctor passed |
| Base-wheel fixture CLI | Prices/macro/FX returned seven rows; monthly factors three rows; JSON/CSV/table at WARNING and DEBUG passed |
| Base-wheel live CLI | Prices, FRED macro, FX, and populated market-factor results passed through provider/cache/rendering |
| Actual terminal wizard | Blank optional answers completed setup with exit 0 and a 0600 config |
| Corrected base-wheel doctor | `installed extras: none` is OK; only missing optional FRED credential warns in the keyless state |
| Formatting/type checks | Black and isort on every edited Python file; Ruff lint/format and strict mypy passed |
| Commit gate | All pre-commit hooks passed, including actionlint and hygiene checks |
| Packaging | Wheel/sdist build and strict Twine checks passed |
| OpenSpec | Strict 0001 validation and implemented-scenario reference gate passed |
| Secret check | Actual FRED credential absent from every candidate repository file and smoke-test stdout/stderr |

The suite still emits its advisory warning for scenarios in later proposed
milestones. The live Yahoo check emits an upstream `raise_errors` deprecation
warning; no provider failure occurred. Vendor values may change when re-recorded.
The wider 0002–0010 milestones and the deferred FRED FX adapter are not completed
by this follow-up. No release version changes or release action is included.

## Reproduce locally

From this branch, with Python 3.11 or later:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest -m 'not network' --cov --cov-report=term-missing --cov-fail-under=90
OPENSPEC_TELEMETRY=0 openspec validate 0001-foundation-data-and-cli --strict

SOBRES_TEST_DIR=$(mktemp -d)
export SOBRES_CONFIG_FILE="$SOBRES_TEST_DIR/config.toml"
export SOBRES_DB_URL="sqlite:///$SOBRES_TEST_DIR/data.db"
export SOBRES_FIXTURE_DIR="$PWD/tests/fixtures"
sobres init --non-interactive --offline
sobres doctor --offline
sobres data prices AAPL MSFT --start 2024-01-02 --end 2024-01-10 --format json
sobres data macro DGS10 --start 2024-01-02 --end 2024-01-10 --format json
sobres data factors --model ff3 --start 1926-07-01 --end 1926-07-31 --format json
```

Expect seven price/macro observations, and July 1926 `Mkt-RF` of 0.0289.
For live tests use a separate database, unset `SOBRES_FIXTURE_DIR`, and configure
the FRED key through `sobres init` or the declared environment variable. Then
run `python -m pytest tests/network -m network -vv`; FRED skips if no key is set.
