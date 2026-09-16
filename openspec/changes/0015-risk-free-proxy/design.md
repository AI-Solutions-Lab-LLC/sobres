# Design

## Source order

1. `--risk-free` — an explicit annual simple proxy, used as a constant.
2. FRED DTB3 when `fred_api_key` is set: the bank-discount quote is converted
   with the 91-day investment-yield approximation from 0002 and aligned
   strictly prior to each return date (`core.rates.prior_rates`).
3. Ken French daily `RF` for USD: a decimal daily simple return, already the
   period-matched risk-free the Sharpe convention subtracts. The annual simple
   proxy series is `RF × PERIODS_PER_YEAR["daily"]`, so dividing back per
   period recovers the published daily rate exactly.

FRED failing or returning nothing falls through to Ken French rather than to
zero. Both sources are daily business-day series; the fetch window starts 45
calendar days before `start` so a prior observation exists for the first
return date. If the series still begins after `start`, that is insufficient
data, not a zero.

Rejected: keeping a zero fallback behind a flag. A default that flatters
results is exactly what the non-negotiable forbids. Rejected: inventing a
non-USD proxy from FX-implied rates — a forecast dressed as a fact.

## Announcing the choice

`ctx.note` prints one human line; `ctx.log.warning("risk_free.selected", ...)`
carries the same facts for logs, at WARNING because an automatically chosen
input changes the number. stdout is untouched, so `--format json|csv` remain
byte-identical across log levels.
