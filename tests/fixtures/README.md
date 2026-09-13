# Recorded provider payloads

All four provider directories contain live recordings from 2026-09-13, made
with `scripts/record_fixtures.py`. These replace the original synthetic corpus.
Small constructed inputs in parser/error tests remain explicitly synthetic.

| Directory | Payload / revision | Client | Requested window |
|---|---|---|---|
| `yfinance/` | Yahoo daily history with `auto_adjust=False`, `actions=False`; CSV rounded to six decimals | yfinance 1.7.0 | 2015-01-02 through 2024-12-31, inclusive |
| `fred/` | FRED observations JSON, including vintage fields and `.` missing markers | httpx 0.28.1 | 2015-01-02 through 2024-12-31 |
| `ecb/` | ECB SDMX `csvdata` response, daily quotes per EUR | httpx 0.28.1 | 2015-01-02 through 2024-12-31 |
| `ken_french/` | Complete six published CSVs, **202607 CRSP database** revision | httpx 0.28.1 | Full published history |

Each `meta.json` records the actual UTC capture time, source, client/version,
request window where applicable, and SHA-256 of every payload. FRED and ECB do
not expose a release version for these responses; their provider version is
explicitly `unversioned`. Their payloads and digests identify the captured data.
`.gitattributes` preserves fixture bytes across Git checkouts on all platforms.

Regenerate deliberately, then review and commit the fixture diff separately:

```bash
# Configure the optional FRED credential through the hidden init prompt first.
sobres init
python scripts/record_fixtures.py
python -m pytest -m 'not network'
```

Use `--only yfinance fred ecb ken_french` to select providers and `--start` /
`--end` to change the bounded history window. FRED resolves its credential from
the normal settings registry (environment or local config); the compatibility
`--fred-api-key` option also works, but the key need not appear in shell history.
Sobres does not load `.env` automatically. No credential belongs in a recording,
manifest, or Git commit. A missing FRED key prints a skip; it does not replace
FRED's existing payloads or establish that FRED was recorded.

The recorder allows 60 seconds per ECB request because a decade of reference
rates is larger than a normal interactive request. If recording fails, inspect
the diff and rerun the affected provider; checksum checks prevent accepting
partial payload updates under an old manifest.

## Changes from the synthetic data

Yahoo timestamps retain numeric offsets across daylight saving time. Replay
now preserves the exchange-local date before slicing, including both endpoints.
UTC conversion would shift London summer-midnight dates to the preceding day.
The regression covers both US and UK DST transitions.

Yahoo `Close` is already split-adjusted; `Adj Close` also adjusts dividends.
The old synthetic Apple fixture falsely required a 75% split-day loss in
`Close`. The test now checks the recorded closes on 2020-08-28 and 2020-08-31
(124.807503 and 129.039993 USD), and the difference between price and adjusted
returns at the August 7 dividend. See the
[yfinance maintainer's explanation](https://github.com/ranaroussi/yfinance/issues/687).

FRED's January 2020 DGS10 payload contains missing observations on January 1
**and January 20**. The regression checks those dates and the recorded January
2 value of 1.88 percent. Mixed daily/monthly requests retain native CPI dates,
including weekend observations, through caching.

The recorded Fama–French 3-factor CSV's first row is:

```text
192607,   2.89,  -2.42,  -2.75,   0.22
```

In column order this is `Mkt-RF`, `SMB`, `HML`, `RF`, in percent. Known-answer
tests use these literal values divided by 100, independently of the parser.
They are tied to the **202607 CRSP revision**. The old synthetic corpus used
2.96, -2.56, -2.43, 0.22 from an earlier series. The
[Ken French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
documents historical revisions and the change from CRSP FIZ to CIZ data in 2025.
Investigate failures against the new raw response and its provenance before
updating a known-answer assertion.
