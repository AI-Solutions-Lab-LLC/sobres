# Source requirements and corrections

Source: `Pre_Earnings_Options_Trading_Guide.docx`, supplied in Downloads, 31,182
bytes, document update label 17 September 2026; examined 18 September 2026.
SHA-256: `715e5bd693af85c59dff61cb366b8b4ea14cf26079ab092c744208daaa13ade6`.
Paragraphs and table cells were extracted from the Word document. This summary
preserves requirements without committing the private original document.

| Guide section | Requirement / intent | Proposed disposition and acceptance home |
|---|---|---|
| 1, 14 | Buy pre-earnings expansion; exit before the print; defined debit risk | ATM baseline required; timing, contract identity and exit scenarios in `earnings-options` |
| 1.2 | Straddle, strangle, long call/put, debit spread choices | Straddle first; other structures explicitly deferred, never silently substituted |
| 1.3 | Moderate IV rank, four prior quarterly ramps, scratch if no expansion | Exact trailing metric, training-only ramp gate, pre-scheduled T-2 exit; `earnings-options` |
| 2 | Confirmed event calendar, weekly sleeves, reserve, overlap limits | Session calendar and reserve-first budget; no hardcoded Q3 dates; `earnings-options` |
| 3 | Affordable historical contracts, IV, underlying, bid/ask, corporate actions | Entitlement and point-in-time data gate; `options-data` |
| 4 | Mention/author/sentiment features through licensed access | Optional, separately backtested overlay; unavailable is not zero; `options-data`, `options-backtesting` |
| 5 | News counts, 8-K and unscheduled-event flags | Timestamped official/approved sources; material-event review can invalidate recommendation; `options-data`, `options-publication` |
| 6 | FOMC/CPI/PCE/NFP collisions and regime context | Official versioned calendar; default skip if T-1 or planned exit is a red day; `earnings-options` |
| 7 | Joined candidate sheet | As-of features, source availability, gate reasons, event and quote times on each candidate; `options-publication` |
| 8 | VIX level/percentile, spread, 20/60-day change correlation/beta, term structure | Report features where licensed; test overlays against baseline; no raw level correlation substituted |
| 9–10 | Trend/range, HV, volume, 20/50/200-day averages, ATR | Deterministic definitions and overlay ablations; no discretionary prose used as code |
| 11 | Market sentiment, skew, put/call context | Optional risk-on/neutral/risk-off experiment with explicit versioned thresholds; no five-product averaging |
| 12 | High/low/ATH distance, IVR saturation cuts | Split-aware trailing features, ATH only with full history, holdout segmentation; `options-backtesting` |
| 13 | Conservative and midpoint backtests, macro skips, costs, worst events | Event ledger + overlapping portfolio returns + stressed fills; `options-backtesting` |
| Owner's call | Deployed website, recommendations, visible new-model/recommendation changes | Required authenticated hosted POC and durable publication lifecycle; `options-publication`, `options-hosting` |

## Conflicts that need an explicit resolution

1. **Name and claimed edge:** the title calls this a crush trade, but the position
   is long options before earnings. IV rising alone does not prove net profit or
   “pure vega”; a straddle also has theta, gamma and changing delta. No source
   consulted validates this guide's exact entry/exit rules or claimed crush ranges.
2. **Calendar arithmetic:** 14 November 2026 is Saturday, not Friday. Several
   weekly labels end on Saturdays; the season's session count is approximate.
   Use an exchange calendar, not those labels as trading dates. The bank dates
   are planning estimates, not verified trade eligibility.
3. **Days and exits:** the text mixes calendar days, sessions, T-1 morning, EOD
   T-2/T-1, and AMC-day exits. Proposed contract: T offsets are exchange sessions
   before the release's New York date; T-2 close is primary, T-1 close a separately
   labelled sensitivity, both strictly before the event. Never use AMC-day close
   as this POC's default. Early closes and revised releases override schedules.
4. **Reserve arithmetic:** weekly percentages sum to 100%, then the guide asks
   for 20% reserve. Apply 20/25/25/20/10 to the remaining 80%, yielding
   16/20/20/16/8% of total capital. Its $12,500 Week-2 example becomes $10,000
   for a $50,000 sleeve. Per-name ceiling is 25% of that weekly cap, or $2,500.
5. **What a week owns:** define cohorts by earnings week. Reserve each event's
   debit against its cohort even when entered in the prior week; also enforce a
   whole-book open-debit ceiling. Reuse only settled/released paper cash after an
   exit, never reset capacity at midnight while old trades remain open.
6. **IV rank versus percentile:** these are not interchangeable. Store both;
   historical extreme rank is sensitive to old shocks. Constant-maturity feature
   IV and event-expiry IV have different purposes and cannot be spliced silently.
7. **Costs:** ask entry/bid exit already pays the spread. Do not deduct a second
   “full spread.” Add commissions once and a separately labelled half-spread
   adverse-execution stress on each side.
8. **Timestamp leakage:** a board snapshot collected at 16:15, a later EOD report,
   or today's revised earnings calendar was unavailable at an earlier close.
   Daily baseline decisions use data available before the entry session; any
   same-session variant needs genuine earlier timestamped observations.
9. **Free data:** aggregate OHLC, current snapshot Greeks and historical NBBO
   quotes are distinct products. Free one-year history also cannot supply a full
   warmup year plus several honest held-out seasons.
10. **Scope versus evidence:** the guide's “skip or shrink,” directional choices,
    sentiment words, and macro rules require fixed definitions. Defaults below
    are proposals, and every promoted variation needs its own measured evidence.

The guide's 30–60%, 44%, and 12–25% crush figures lack a reproducible cited
dataset in the document. They are not acceptance targets, forecast labels or
marketing claims. No historical performance has been computed in this PR.
