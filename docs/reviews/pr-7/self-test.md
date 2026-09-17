# Test PR #7 yourself

Reviewed commit: `dd5d6f077e01e972feefe85629b81b1e63df6078`. See [the report](report.md) for ten findings and their proposed fixes. Test this commit first; later commits may behave differently.

## Use the prepared checkout

The review left a detached clone and development environment ready on this Mac:

```zsh
cd /private/tmp/sobres-pr7-review
source .venv/bin/activate
git rev-parse HEAD
sobres --version
```

Expected: the SHA above and version `0.0.1`. `/private/tmp/sobres-pr7-base` contains a separate clean **base wheel** installation. Temporary directories can be removed by the OS; use the fresh-setup instructions below if they are gone.

Set up new disposable state so these commands do not modify your normal config or database:

```zsh
sobres_test_dir=$(mktemp -d /private/tmp/sobres-user-test.XXXXXX)
export SOBRES_CONFIG_FILE="$sobres_test_dir/config.toml"
export SOBRES_DB_URL="sqlite:///$sobres_test_dir/sobres.db"
unset SOBRES_FIXTURE_DIR
sobres init --non-interactive --offline --format json
sobres doctor --offline --format json
```

Expected: JSON results, actual exit 0, no failed checks; optional-key warnings and offline skips are normal. `--strict` deliberately makes warnings fail. The base wheel warns that its data extra is absent. The development installation has that extra.

## Deterministic offline commands

Only after init, select the supplied fixtures:

```zsh
export SOBRES_FIXTURE_DIR=/private/tmp/sobres-pr7-review/tests/fixtures
sobres data prices AAPL MSFT --start 2024-01-02 --end 2024-01-10 --format json
sobres data prices AAPL MSFT --start 2024-01-02 --end 2024-01-10 --format csv
sobres data prices AAPL MSFT --start 2024-01-02 --end 2024-01-10 --format table
sobres data fx EURUSD --start 2024-01-02 --end 2024-01-10 --format json
sobres cache info --format json
```

Expected: nonempty price/FX rows; price JSON names AAPL/MSFT and USD. JSON is a single document, CSV has a date header, and the table displays source/currency. Repeating a request should show cache `hit`. Fixture prices/rates are **synthetic**, not historical observations; do not use their values as market facts. Do not rerun init with `SOBRES_FIXTURE_DIR` set if you do not intend to persist fixture mode.

Run the normal checks:

```zsh
pytest -m 'not network' --cov --cov-report=term --cov-fail-under=90
ruff check .
ruff format --check .
mypy
OPENSPEC_TELEMETRY=0 openspec validate 0001-foundation-data-and-cli --strict
```

Current result: **364 tests pass**, coverage **96.38%**, Ruff and mypy pass. OpenSpec validation **fails** with 33 errors and 5 warnings. A green test suite does not mean the bugs below are fixed.

## Reproduce the important failures

**Lost market factor (F2):**

```zsh
sobres data factors --model ff3 --start 1926-07-01 --end 1926-07-31 --format json
```

Expected: the supplied known-answer fixture has `Mkt-RF: 0.0296`. Current CLI output has **`"Mkt-RF": null`**, on both the first request and repeats.

**Broken clean install (F4):** disable fixture mode and use a new database, so cached fixture prices cannot hide the missing dependency:

```zsh
SOBRES_FIXTURE_DIR='' SOBRES_DB_URL="sqlite:///$sobres_test_dir/base-only.db" \
  /private/tmp/sobres-pr7-base/bin/sobres data prices AAPL \
  --start 2024-01-02 --end 2024-01-10 --format json
print $?
```

Current result: `yfinance is not installed`, exit **4**. The source development environment can fetch prices because it installs extras. Installing `sobres[data]` is a workaround for consumers, not fulfillment of the base-install spec.

**Optional-key prompt (F5):** run this in a terminal, with no stored FRED key:

```zsh
SOBRES_CONFIG_FILE="$sobres_test_dir/wizard.toml" SOBRES_FRED_API_KEY='' FRED_API_KEY='' \
  sobres init --offline
```

Press Enter at `fred_api_key (enter to skip)`. Expected: proceed to the next setting. Current: repeats the same prompt. Press Ctrl-C to stop; the current error boundary also labels that abort an internal error. `init --non-interactive --offline` is the temporary workaround.

**Missing negative flag (F10):**

```zsh
sobres init --no-verify --offline
print $?
```

Current result: no such option, exit **2**, despite the option's mention in help text.

**Run all saved offline probes:** from the original repository, where this document lives:

```zsh
/private/tmp/sobres-pr7-review/.venv/bin/python docs/reviews/pr-7/reproduce.py \
  --checkout /private/tmp/sobres-pr7-review \
  --base-python /private/tmp/sobres-pr7-base/bin/python
```

The script makes its own temporary state, uses only dummy keys, and removes that state on completion. It **reports observations rather than failing the process on known bugs**. Compare its JSON with [captured evidence](evidence/probes.json). It covers secret logging, missing market factors, stale refresh values, dropped missing dates, weekend extensions, unknown currency, WAL backup restoration, and init's process exit code. F5/F10 are the terminal commands above. After fixes, verify each expected behavior in the report rather than expecting the old evidence to remain unchanged.

## Test real providers

Keep live data in its own database; do not mix it with synthetic fixture cache entries:

```zsh
unset SOBRES_FIXTURE_DIR
export SOBRES_DB_URL="sqlite:///$sobres_test_dir/live.db"
pytest tests/network -m network -vv
sobres data prices AAPL MSFT --start 2024-01-02 --end 2024-01-10 --format json
sobres data fx EURUSD --start 2024-01-02 --end 2024-01-10 --format json
sobres data factors --model ff5 --start 2024-01-01 --end 2024-03-31 --format json
```

At review time Yahoo, ECB, and Ken French shape tests passed; FRED skipped without a key. Prices and FX returned 7 rows each. Factors returned 3 rows but all three market-factor values were null. Vendor data can be revised and providers can be unavailable; distinguish a network outage from the reproducible cache bug.

## Your FRED key: GitHub and local storage

For shared GitHub Actions use, add an **organization Actions secret**:

1. Open **AI-Solutions-Lab-LLC → Settings → Secrets and variables → Actions**.
2. Choose **New organization secret**, named **`SOBRES_FRED_API_KEY`**.
3. Set repository access to selected repositories and select **`sobres`**.

A repository secret with the same name also works if only this repo needs it. Organization-level secrets support selected-repository access; workflows must explicitly pass them to an environment variable. See [GitHub's secret documentation](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets).

Adding the secret alone will not make current CI run FRED tests. A separate manually dispatched live-provider workflow should map the secret only into its live-test step:

```yaml
- name: Live FRED contract
  env:
    SOBRES_FRED_API_KEY: ${{ secrets.SOBRES_FRED_API_KEY }}
  run: pytest tests/network/test_live_providers.py -m network -k fred -vv
```

Keep ordinary PR CI offline. My recommendation is a manual run against a reviewed branch; do not expose the secret to unreviewed PR code. GitHub supports this with `workflow_dispatch`; such a workflow must exist on the default branch before it can be manually dispatched. See [manual workflow runs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow). No workflow or secret was created as part of this review.

For a local test **now**, enter the key through a hidden zsh prompt:

```zsh
read -rs 'SOBRES_FRED_API_KEY?FRED API key: '
print
export SOBRES_FRED_API_KEY
pytest tests/network/test_live_providers.py -m network -k fred -vv
sobres data macro DGS10 --start 2024-01-02 --end 2024-01-10 --format json
unset SOBRES_FRED_API_KEY
```

Use the isolated live config/database from above. Expected: the FRED test runs instead of skipping; the macro command returns observations. `DGS10` is a percentage-valued FRED series; the separate risk-free helper converts to decimal. I have not executed these with your key.

For **persistent local storage**, the app's macOS default is:

```text
/Users/jjespinoza/Library/Application Support/sobres/config.toml
```

Its TOML setting is `fred_api_key = "YOUR_KEY"`, and its file mode must be **0600**. `SOBRES_CONFIG_FILE` overrides this path. This is outside your repository and its Google Drive checkout. Preserve existing settings when editing the file; do not commit the key, put it in a review report, or paste it into chat. The app does not automatically load a repository `.env` file.

Until F1 is fixed, avoid entering the key through `sobres config set` with INFO/DEBUG logging. Using your editor directly avoids that code path; create/protect the file before entering the key:

```zsh
mkdir -p "$HOME/Library/Application Support/sobres"
touch "$HOME/Library/Application Support/sobres/config.toml"
chmod 600 "$HOME/Library/Application Support/sobres/config.toml"
nano "$HOME/Library/Application Support/sobres/config.toml"
```

Add or update the `fred_api_key` setting inside the editor, keeping the key out of shell history. To return to your normal app configuration after testing, unset the review overrides:

```zsh
unset SOBRES_CONFIG_FILE SOBRES_DB_URL SOBRES_FIXTURE_DIR SOBRES_FRED_API_KEY
```

## Fresh setup if the temporary clone is gone

Use a new path instead of overwriting any existing checkout. Python 3.11+ is required; the review used 3.12.

```zsh
git clone https://github.com/AI-Solutions-Lab-LLC/sobres.git sobres-pr7-check
cd sobres-pr7-check
git fetch origin pull/7/head
git checkout --detach dd5d6f077e01e972feefe85629b81b1e63df6078
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]' build twine
python -m build
twine check --strict dist/*
python3.12 -m venv .base-venv
.base-venv/bin/python -m pip install dist/sobres-0.0.1-py3-none-any.whl
```

Then adapt the absolute checkout/base paths above to this clone. If testing a later fix instead, record its SHA and rerun both existing checks and independent reproductions.
