---
change: 0015-risk-free-proxy
depends_on: [0002-portfolio-optimization, 0007-equity-factor-analysis]
status: implemented
---

# A sourced risk-free proxy, never an assumed zero

## Outcome

Optimization, risk and hedging output uses a historical risk-free series
whether or not a FRED key is configured. With a key, the proxy is FRED DTB3 as
before. Without one, it is the 1-month Treasury bill return that Ken French
publishes alongside the factor files — keyless, dated, and already a recorded
provider. Either way the command says so on stderr and in provenance. A
currency with no automatic proxy is an actionable usage error naming
`--risk-free`, not a silent zero.

```
$ sobres optimize markowitz --tickers AAPL MSFT JNJ --start 2018-01-01 --fill drop
risk-free: selected automatically — Ken French RF (1-month T-bill, USD), daily
  2018-01-02..2020-03-31, mean 1.86% annualized; pass --risk-free to override
```

Issue: [#36](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/36).
Predecessors: 0002 defined the Sharpe convention and permitted a disclosed zero
fallback; 0007 added the Ken French provider whose `RF` column this reuses.
Implemented directly against `main` after the feature stack merged.

## Why

A zero risk-free rate inflates every Sharpe ratio, and the fresh-install path
had no FRED key, so the default experience flattered results — against the
"honest by default" non-negotiable. The disclosed fallback note was easy to
miss inside a provenance block.

## What changes

- `resolve_risk_free` selects, in order: an explicit `--risk-free`; FRED DTB3
  when a key is configured and the series is usable; Ken French daily `RF` for
  USD. It never returns an assumed constant.
- A currency other than USD with no override raises `UsageError` naming the
  flag and the currency.
- The dated series is fetched from before `start` so every return date has a
  prior observation; if the source still does not cover `start`, the command
  raises `InsufficientDataError` with the first available date.
- Automatic selection is announced with one stderr line and a `WARNING`
  log event (`risk_free.selected`), and the provenance note names the source,
  currency, coverage and the summary rate. Dates before the first observation
  no longer receive zero.

## Non-goals

No new provider, setting or dependency. No change to `analyze factors`, which
already takes `RF` from the same factor file, nor to `plan`'s inflation
assumption. No non-USD proxy: the honest answer there is the explicit flag.
