# PR #16 synchronization

Merges updated #15, including main `b9792d7` (PR #33) and accepted #8 corrections
through #35. FX/PPP candidate functionality remains on the existing stacked base.
Current 0010/0013 plans distinguish domain code from pending layout/R1/R2 acceptance.

Compatibility corrections:

- Hedge comparison supplies the reporting currency to the reviewed risk-free
  resolver and passes prior-date rates to both historical risk panels.
- Hedge short rates convert FRED DTB3 percent bank-discount quotes through the
  shared 91-day investment-yield helper; other annual percent rates scale to decimal.
- Dropped price observations do not bridge gaps. Hedged CAPM includes its benchmark
  in the same return construction without adding it to investable weights.
- Synthetic GBP rate/CPI additions live under `tests/fixtures/synthetic/fred/`;
  fixture mode prefers recorded payloads. Live providers never use the fallback.
  Main's four recorded provider directories and manifests remain byte-identical.
- Fixture recording retains main's key/provenance checks and the corrected
  fundamentals manifest while preserving the FX/PPP document recorder.

Validation: 1,112 non-network tests passed, four live tests excluded, 95.64% branch
coverage. Includes hedged CAPM and independently calculated Treasury quote
regressions. Black/isort 100, Ruff lint/format, mypy, actionlint and all 14 strict
OpenSpec validations passed. OpenAPI/client regenerated; frontend types/build and
160.3 KB initial gzip bundle passed its 300 KB gate.

World Bank/OECD/BIS and the added GBP corpus remain labelled synthetic; this run
proves fixture behavior, not live provider truth. GitHub supplies the distribution,
container, audit and OS/Python matrix gates. Docker Desktop was unavailable locally.
Pending migration and acceptance are tracked by #32/#23. The new automatic-rate
policy in #36 still requires its own spec update; it is not implemented here.
No pending feature PR was merged and no release or deployment was activated.
