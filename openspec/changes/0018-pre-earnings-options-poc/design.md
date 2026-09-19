# Algorithms, evidence, and integration

All thresholds below are **proposed, versioned defaults** to freeze before
evaluation, not proven best practices or fitted results. The capability specs
are the acceptance contract; this design defines the initial algorithm precisely.

## 1. Data and time model

Use owned dataclasses/frames for `EarningsEventVersion`, `OptionContract`,
`OptionQuote`, `FeatureSnapshot`, `StrategyVersion`, `BacktestManifest`,
`RecommendationRevision`, and `PaperPosition`.

- Event identity: stable issuer/security ID, fiscal quarter, event version,
  announced release timestamp, BMO/AMC, source URL, confirmation status,
  `published_at`, `observed_at`, and `available_at`. BMO/AMC without a precise
  issuer time uses a conservative session boundary and an explicit uncertainty
  flag, never an invented confirmation timestamp. Estimated/unknown sessions
  cannot enter. Keep revisions; historical eligibility uses the version then known.
- Contract identity: vendor ID plus underlying security ID, expiry, right,
  strike, multiplier, deliverable, exercise style, settlement convention,
  currency and corporate-action version. MVP permits only standard USD
  100-share contracts and a known liquid weekly expiry after the release.
- Quote: bid/ask and sizes, underlying price and timestamps, volume/OI with
  publication times, vendor IV/Greeks with model/source, exchange session,
  ingestion time, entitlement/delay, and quality reason. Missing, stale,
  zero-bid, crossed, absent contract and closed-market are different states.
- Freeze raw-input checksums, licensed object locations, normalization version,
  calendar version, data revision cutoff and timezone. A replay resolves all
  identifiers through its immutable manifest, not today's ticker lookup.
- News/social features carry publication **and first availability** timestamps;
  late ingestion never becomes an earlier tradable observation. Store text only
  when permitted. FRED revised economic values require vintages if used as
  predictors; the baseline needs release dates, not retrospectively revised values.

All scheduling uses `America/New_York`, an exchange-session calendar with holidays
and early closes, and UTC persistence. T-1 is the last exchange session strictly
before the release's New York calendar date; T-k counts backward from there.
For both a Tuesday BMO and Tuesday AMC release, T-1 is Monday and T-2 is the
previous Friday (absent a holiday). This intentionally avoids AMC-day trading.
For a non-session release date, count earlier exchange sessions the same way.
All exits must precede the earliest plausible announced release time.

## 2. Frozen baseline `pre-earnings-straddle-v1`

1. **Universe:** a recorded, point-in-time U.S. weekly-option universe; price
   above $20 at signal cutoff. If only a fixed watchlist is licensed, label it
   watchlist-limited and make no market-wide or survivorship-corrected claim.
   Delisted/renamed securities remain in the historical ledger.
2. **Schedule:** enter T-10 at the close, using only features available before
   that session opens (normally T-11 observations); exit T-2 at the close. Planned
   entry must be inside T-14..T-7. No replacement late entry after a missed fill.
   A later-published EOD file supplies historical execution observations, not
   decision features unavailable then. If quote timestamps cannot establish a
   pre-announcement regular-session fill, that dataset cannot validate the variant.
3. **Contract selection:** choose the first standard weekly expiry strictly
   after the release timestamp (at most 14 calendar days after it), then the
   strike minimizing distance to the underlying at the signal cutoff, breaking
   ties toward the lower strike. Call and put share strike/expiry and remain
   those contracts through exit; never re-center the held pair each day.
4. **Liquidity:** use the prior 20 sessions' underlying-wide options volume,
   default minimum 1,000 contracts/day, plus per-leg OI at least 100 as last
   published before cutoff. At execution each leg requires positive ordered
   bid/ask, nonzero displayed size at least the order quantity and relative
   spread `(ask-bid)/mid <= 10%`. Baseline quote/underlying ages at the simulated
   close must be <= 60 seconds and timestamp skew <= 60 seconds; EOD labels
   without those timestamps are research-only. Threshold sensitivity is disclosed.
5. **IV:** trailing 252 valid exchange-session observations of a consistent
   30-calendar-day ATM IV measure, excluding the current observation. Interpolate
   total variance between expiries bracketing 30 days; no extrapolation.
   `IVR = 100*(IV_now-min(IV_hist))/(max(IV_hist)-min(IV_hist))` and
   `IVP = 100*count(IV_hist <= IV_now)/N`. Do not silently clamp IVR; new extrema
   can lie outside 0..100. A zero range, missing term bracket, insufficient
   history, or invalid IV means unavailable and ineligible, not IVR=0.
   Entry requires IVR < 50 and current feature IV below its prior 20-session
   mean. Report the selected event-expiry pair's IV separately.
6. **Ramp:** at least four earlier confirmed quarterly events, each fully
   completed and known by cutoff. For each prior event, select the pair by the
   same entry rule and compare its mean call/put IV at T-10 and T-2 without
   changing contracts. Require a positive median change and at least three of
   the latest four positive ramps.
   This gate is a hypothesis, not proof of profitability; preserve failure counts.
7. **Macro:** skip if T-1 or the planned exit is an officially scheduled FOMC
   decision, CPI, PCE or payroll release day. This stricter rule resolves the
   guide's alternatives. A calendar change after entry moves the exit earlier
   if feasible; otherwise flag urgent invalidation/exit-required, never extend it.
8. **Exit:** scheduled T-2 dominates any enthusiasm signal. The T-3 scratch
   check compares the held contracts' IV with entry; with only daily data its
   actionable exit is the next eligible session, normally T-2 already. Record
   `no_ramp` as an exit reason, without inventing a distinct intraday fill.
   Material unscheduled events trigger review/invalidation and earliest feasible
   exit. EOD research cannot promise instantaneous flattening.
9. **Rank and abstention:** filter first; rank eligible names by median prior
   ramp, then lower execution spread, then stable issuer ID. This is a research
   ordering, not a calibrated profit probability. Empty results carry reason
   counts. New recommendations require a promoted passing strategy version.

IV from prices must use a documented American-option-aware solver with dividends,
rates and exercise conventions, or a vendor method whose limitations are disclosed.
No European Black–Scholes inversion silently relabelled as exact American IV;
no arbitrage-bound violation, nonconvergence or missing rate defaulted to zero.
P&L comes from observed quotes, never from the IV model's theoretical values.

## 3. Sizing and paper state

Require explicit positive USD sleeve capital S. Hold 0.20S in reserve; distribute
0.80S over configured earnings-week cohorts with weights 20/25/25/20/10.
Each position's committed debit including entry fees is at most 25% of its cohort
cap. All open positions plus pending allocations count against their own cohort
and the global 0.80S ceiling; proposed sector ceiling is 40% of deployable S.
Whole contracts only; use the smallest remaining cap and available paper cash.
Allocations are serialized transactionally so simultaneous candidates cannot
each spend the same remaining balance. Losses reduce available cash; exits do
not magically restore the original sleeve. Display the allocation ledger.

For S=$50,000, Week 2 cap is $10,000 and per-name cap $2,500. A $12 pair with
100 multiplier costs $1,200 before fees: two pairs fit, three do not. These
are example inputs, not account assumptions. Standard long pairs' maximum
contractual loss is debit plus fees, subject to closing before exercise exposure.

Recommendation state is separate from actual or paper position state. Users
explicitly mark paper entry/exit quantity and timestamp; recommending an exit
does not mean a position has closed. A deadline passing while still open becomes
`overdue`/`exit_unconfirmed`. No broker fill or flatness is claimed without evidence.

## 4. Backtesting and promotion

For each event, hold the selected identities fixed. With multiplier M and quantity q:

`net_pnl = q*M*((call_exit_bid + put_exit_bid) - (call_entry_ask + put_entry_ask)) - fees`

Fees include four leg-side commissions per pair on a complete round trip.
Midpoint results are a separate optimistic diagnostic. Stress adds half the
contemporaneous spread adversely at each leg's entry and exit, separately from
fees; do not deduct the spread twice from ask-to-bid baseline results.
Mark portfolio equity using cash plus liquidation bids, preserving USD metadata.

Known answer: entry asks 6+6, exit bids 7+6, M=100, q=2,
$0.65 per contract-side yields $200 gross, $5.20 fees, **$194.80 net**.
If each of four leg-side spreads is $0.20, half-spread stress subtracts $80
for two pairs, leaving **$114.80**. Entry capital includes $2.60 entry fees.

Backtests retain every attempted event and gate/failure. Missing entry means
no fill; missing exit for an entered pair is unresolved, never a dropped trade
or fictitious last-price fill. Report a zero-liquidation-value downside bound
(full debit loss), observed-resolution results separately, and block promotion
while unresolved exits remain. Halts, unexpected early announcements, and late
calendar changes can make an exit impossible: record a strategy breach and
its adverse bound; never use hindsight to remove the position or claim a safe exit.

Two result layers are required: equal-unit event diagnostics and a chronological
portfolio simulation applying cohort caps, cash, overlap, fees and deterministic
allocation order. Report attempted/eligible/filled/resolved events; net expectancy,
median return on debit, hit rate, worst ten events, cost drag, turnover, exposure,
drawdown and season/issuer/sector segments. Sharpe and annualized statistics,
if shown, use daily portfolio equity and `core/conventions.py`, never event-count
annualization. Include idle cash and disclosure of the cash-yield assumption.

Freeze outer chronological season splits and configuration hashes. All rolling
features, scaling, hyperparameters, overlay choices and ramp history use only
earlier observations. Purge any event whose holding/label interval overlaps the
validation/test interval; embargo at least the maximum configured holding period.
Keep the last evaluation block untouched. Log every attempted parameter family.
Use training/inner validation for selection; final test results cannot pick winners.

Required comparisons: cash/no trade, the frozen baseline, baseline with each
overlay separately and the selected combination, midpoint versus conservative
versus stress execution, T-2 versus T-1 exit, and concentration/missingness slices.
All variants, including failures, stay in the report. Session/season block
bootstrap (seeded, 2,000 resamples, block length fixed before test) estimates
uncertainty while preserving same-day portfolio dependence; report confidence
bounds and event counts rather than treating same-week names as independent.

Proposed initial promotion gates: >=4 held-out earnings seasons, >=100 resolved
filled events, >=20 issuers; no unresolved exits/time leakage; positive lower
95% bootstrap bound for conservative net event P&L; positive stress mean;
portfolio maximum drawdown <=20% of initial sleeve; positive net result in at
least three of four latest held-out seasons. These are product risk gates, not
claims of statistical sufficiency. Evidence failing a gate is still published
as rejected/inconclusive. Owner promotion pins the exact data/model/config hash.

## 5. Overlay and model experiments

First record, then test: VIX trailing-year percentile; 20/60-session correlation
and OLS beta of changes in feature IV versus changes in VIX; IV-minus-HV;
20/50/200-session moving averages, 5-session MA slopes, 14-session Wilder ATR;
10/60-session annualized log-return HV; trailing 52-week high/low distances.
ATH requires full available listing history and is explicitly unknown otherwise.
Candidate diagnostics also include straddle mid, pair debit/spot as a heuristic
implied-move percentage (not a probability interval), event-expiry DTE, 30-day
feature-IV minus VIX in consistent volatility points, and the latest eight
available completed earnings moves. Define an earnings move as the return from
the last regular-session close before release to the first regular-session
close after release; AMC and BMO therefore join different closes. Record fewer
than eight as partial history; the baseline's four-prior-event gate is distinct.
Post-event prices may describe earlier completed events only, never the current
event's entry features. Display event/entry/exit dates together on the calendar.
Never label a basket median as VIXEQ; optional VIX9D/VIX3M, skew, put/call and
VIXEQ need licensed history and their own timestamps.

Pre-register candidate cuts: VIX top quartile => half size; IV/VIX correlation
>0.7 => skip; within 2% of trailing high with IVR>60 => skip; bottom range decile
with IVR>70 => skip; >2 ATR extension => half size. Some IVR cuts are redundant
with baseline IVR<50: report that fact, do not claim incremental benefit from
a rule that never changes a trade. Threshold changes create a new version.

Optional board features: 5-day counts, unique authors, sentiment mean/dispersion,
20-session mention z-score against the ticker's history (zero variance => missing),
and market-attention control. News: 24h/5d headline counts, classified official
filing/event flags. No sentiment score without a versioned trained/vendor model.
Risk-on/off composition needs a separately frozen threshold table before use.
Disable unsupported/unlicensed inputs; a model requiring them becomes ineligible.
Retain an overlay only if it improves conservative held-out results versus the
same-event baseline and remains stable across at least two seasons.

A bounded learned challenger is ridge regression predicting held-pair net
return on debit using only pre-entry features, with a small predeclared penalty
grid selected inside purged training folds. Compare against training-mean and
rule-only controls; compute held-out calibration/error and empirical residual
intervals. It can rank already eligible pairs but cannot override hard gates.
No LLM stock picks or untested model automatically deployed after retraining.
An unsuccessful challenger leaves the rule baseline intact or no model promoted.

## 6. Repository placement and interfaces

| Area | Responsibility |
|---|---|
| `core/options/` | Pure feature math, eligibility, sizing, simulated fills/accounting, evaluation; injected frames/clock values/seed, no I/O or logging |
| `data/options/`, `data/earnings/` | Owned `OptionsDataSource`/`EarningsCalendarSource` ports, one adapter module per vendor, calendars, entitlement and quality normalization; vendor field names, units, pagination and auth never leave the adapter |
| `deploy/terraform/` and `cli/commands/deploy.py` | Versioned Terraform root and bootstrap modules for the hosted profile; the CLI wraps the `terraform` and `gcloud` binaries as subprocesses and never reimplements them |
| `data/storage/base.py`, `data/storage/adapters/` | Domain repositories, transactions, SQLite and limited Firestore implementations; database SDK imports only here |
| `data/artifacts/` | Artifact protocol, GCS adapter and a deterministic fake |
| Shared command handlers following existing CLI context pattern | Fetch → core → persist/publish orchestration, reused by API and Jobs; no numerical policy in adapters |
| `registry.py`, `settings.py`, `doctor.py` | One command/setting/check declaration; model validators for cross-field rules, credentials redacted, cloud/provider prerequisites diagnosed |
| Existing `api/` and `frontend/` | Auth, bounded job dispatch, rendering and forms, evidence links, recommendation/model history |

Proposed commands (not available yet): `sobres options calendar`, `options scan`,
`options backtest`, `options recommendations`, `options models`, `options promote`,
`options position record`, `deploy cloud-run check`, `deploy cloud-run plan`,
`deploy cloud-run apply` and `deploy cloud-run destroy`. Define typed Pydantic
parameters/results once; emit table/json/csv with consistent units/reason codes.
Publication/promotion actions require explicit permissions; every `deploy`
command is terminal-only. No shell/cloud command execution through HTTP.

Hosted exposure is a declared profile allowlist shared by schema, routes, forms
and parity tests. Full desktop portfolio/equity/broker/settings/database-export
commands are absent from the hosted API; route-by-guess attempts are rejected
before opening local storage. Local CLI/full self-hosted mode keeps its surface.
Split API construction so hosted startup never opens an ephemeral default SQLite
database or starts the existing thread worker for durable cloud jobs.

The new operational ports cover hosted users/roles, shared watchlist/config,
paper allocations/positions, runs/job checkpoints and publication pointers. SQLite implements the same new ports for local use. Firestore
implements only these capabilities and must pass shared behavioral tests; it is
not selected as a general `SOBRES_DB_URL` backend with missing repositories.
GCS is immutable dataset/report storage behind its own artifact port, not a cache
sidecar bypassing SQLite. Local artifacts can be BLOB-backed in the existing
SQLite store; cloud references carry checksum, generation, schema and retention.

### 6.1 Provider abstraction needs more than one vendor

The options and earnings ports are only credible once at least two vendors sit
behind them. Design the ports from vendor documentation or live keys for the
two chosen vendors, Massive and ThetaData (Q12, human task H1); a port designed against one vendor's
payload is that vendor's schema under another name. Each adapter publishes a
capability declaration naming which required inputs it supplies: historical
bid/ask with sizes and timestamps, contract identity (OCC symbol or vendor ID
plus strike/expiry/right/multiplier/deliverable), corporate-action versions,
underlying quote, vendor IV/Greeks with method, OI/volume publication times,
earnings confirmation timestamps and revisions, rate limits, pagination and
history depth. One recorded-fixture conformance suite runs over every adapter;
a missing capability is declared and shown as unavailable (OD1, OD6, OD9),
never emulated. A vendor whose sample cannot supply pre-announcement
regular-session bid/ask with timestamps cannot validate the baseline.

### 6.2 Terraform-driven deployment from the CLI

The hosted profile is provisioned only through Terraform, invoked by the CLI:
`sobres deploy cloud-run check|plan|apply|destroy`. The CLI shells out to the
`terraform` and `gcloud` binaries on `PATH`, at pinned minimum versions, and
streams their output. It never recreates resources with SDK calls and never
runs through HTTP or the SPA. `sobres doctor` diagnoses the cloud profile's
prerequisites: `gcloud` installed and authenticated (active account and
application-default credentials), project and region set, `terraform` inside
the pinned range, the state bucket reachable, the named Secret Manager secrets
present (existence only; values are never read) and the runtime service
accounts' IAM bindings. Every failing line carries its fix, including the exact
`gcloud` command for a missing secret.

`plan` writes a saved plan file and prints the resource summary. `apply` applies
exactly that saved plan and rejects a stale one. `destroy` runs a destroy plan,
prints every resource it will remove, requires the project ID typed back, and
leaves the artifact bucket, the backup bucket, the Firestore database and the
state bucket in place unless `--include-data` is passed and confirmed a second
time after a verified export. Secret values are never inputs to the CLI or to
Terraform: the human adds them with `gcloud secrets` (H2) and Terraform manages
only the secret containers and access bindings. [hosting.md](hosting.md) lists
the module layout and the practices it must follow.

## 7. Model/recommendation publication

Publish artifacts first under immutable IDs, verify checksums, then atomically
commit a revision/current pointer. Uncommitted
objects are harmless orphans removed only after a grace period. A revision carries
event/model IDs, contracts, as-of times, expiration/deadline, gate reasons, size,
max debit/loss, evidence summary, missing inputs and research disclaimer.

Lifecycle: candidate → published → revised/invalidated/expired; paper positions
separately open/closed/overdue. New event times invalidate unsafe old revisions;
links always show current status and retain history. Model states are
draft/evaluated/rejected/promoted/retired with evidence and owner audit trail.
