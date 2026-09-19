# Research and data feasibility

Primary sources consulted 18 September 2026. Vendor pages are mutable; implementers
must recheck entitlements with actual credentials before acquisition. Research
motivates controls; it does not establish that this guide is profitable.

## Trading and evaluation

| Primary source | What it supports | Implication / limit |
|---|---|---|
| [Leung and Santoli, Accounting for Earnings Announcements in the Pricing of Equity Options](https://arxiv.org/abs/1412.8414) | Explicit announcement jumps affect the pre-event volatility surface and American-option valuation | Calendar-aware term structure and American exercise conventions matter; this is not a backtest of T-10/T-2 straddles |
| [Driessen, Lin and Van Hemert, How the 52-week high and low affect option-implied volatilities and stock returns](https://hub.hku.hk/bitstream/10722/227463/1/Content.pdf?accept=1) | Studies option IV around price reference points | Test high/low features as hypotheses; does not establish the guide's earnings-crush percentages or filter thresholds |
| [Bailey et al., The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) | Searching strategy variants creates selection/overfitting risk | Log all trials, separate selection from final evaluation, report unsuccessful models; a single attractive backtest is insufficient |

The proposed baseline, purged event splits, net-fill ledger, uncertainty gates and
overlay ablations are design choices informed by these problems, not prescriptions
copied from those papers. An IV increase is not a net-return target. Options
prices also reflect time decay, spot path, dividend/rate assumptions and liquidity.

## Provider feasibility table

| Source checked | Verified public statement | Decision |
|---|---|---|
| [Massive options pricing](https://massive.com/pricing?product=options) | Basic $0 / 2 years; Starter $29 / 2 years; Developer $79 / 4 years; Advanced $199 / 5+ years. Quotes are listed on Advanced; current snapshot IV is distinct from historical quotes | Do not select Starter merely because it lists Greeks/IV. Individual-use plans do not establish hosted sharing rights; confirm business/display terms |
| [Massive quote flat files](https://massive.com/docs/flat-files/options/quotes) | Quote-file access is not included in Basic/Starter/Developer; history begins March 7, 2022; archives are large | Full OPRA archive download conflicts with a tiny storage budget; require bounded extraction and verified rights |
| [ThetaData subscription docs](https://docs.thetadata.us/Articles/Getting-Started/Subscriptions.html) | Advertises one year free EOD and requires Theta Terminal. Endpoint access differs by tier; rate-limit text/tables differ | Good bounded ingestion candidate, not verified multi-season historical bid/ask/IV entitlement. Probe endpoint, timestamps, rate limit, terminal operation and deployment compatibility |
| [ThetaData pricing](https://www.thetadata.net/pricing) | Live pricing interface did not expose a reliable paid options tier quote in the retrieved text | The guide's ~$40 VALUE price is **unverified**; do not repeat it as a current quotation |
| [ThetaData EOD behavior](https://docs.thetadata.us/Articles/Data-And-Requests/OHLC-EOD.html) | Normalized EOD reports are generated at 17:15 ET; zero-trade bars need careful interpretation | Publication time and quote time are not interchangeable. Confirm regular-session bid/ask cutoff before using for fills |

Implement a repository-owned licensed CSV/Parquet import adapter first if it avoids
committing to a vendor runtime. Contract-level samples must cover an ordinary
event, a BMO event, an AMC event, holiday/early close, a split/adjusted contract,
zero/stale quotes, and a delisted issuer. Document both permitted and unavailable
fields; fixture success is not entitlement or market truth.

Procurement must verify: standard option identities and deliverables; timestamps,
bid/ask/sizes; enough history for warmup and four held-out seasons; underlying
and rates/dividend inputs; point-in-time event confirmation/revisions; corporate
actions/delistings; historical OI/volume publication; commercial derived-display
and retention rights; export limits; and all-in cost. Unknown historical earnings
confirmation time is a material coverage limitation: retrospective IR discovery
must not masquerade as then-known information.

If no affordable dataset meets this, ingest a small licensed historical file set
or begin forward paper collection; ship research/demo mode. Do not invent
historical spreads from OHLC, backfill current IV as history, or call synthetic
fixtures a historical strategy validation. Buying data remains a Q4/Q5 decision.

## Infrastructure

Official calendar/filing starting points: [FOMC meeting calendars](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm),
[BLS release schedule](https://www.bls.gov/schedule/) for CPI/employment,
[BEA release schedule](https://www.bea.gov/news/schedule) for PCE,
[NYSE hours and holidays](https://www.nyse.com/trade/hours-calendars), and
[SEC EDGAR APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces)
for filings. Persist observed calendar revisions. Current calendar pages do not
alone establish historical availability; issuer IR confirmation remains a
separate requirement for each candidate.

- [Cloud Storage mount limitations](https://docs.cloud.google.com/run/docs/configuring/services/cloud-storage-volume-mounts)
  establish missing locking; [Cloud Run runtime contract](https://docs.cloud.google.com/run/docs/container-contract)
  establishes ephemeral storage/lifecycle constraints. These motivate the storage
  split and Jobs design; merely wrapping the present SQLite container is insufficient.
- [Firestore transaction contention](https://firebase.google.com/docs/firestore/transaction-data-contention)
  documents retryable transactions. Publish/allocate in transactions and keep
  provider and artifact I/O outside them, with durable idempotency.
- Live pricing sources and the workload calculation are in [hosting.md](hosting.md).

Social/network collection is optional. The POC does not assume public web content
is licensed for commercial ingestion; source rights and availability must be
verified before enabling any board/news adapter. No text was scraped to create
training data in this planning PR.
