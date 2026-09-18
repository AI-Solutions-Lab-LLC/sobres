# Questions for the planning PR

These are decisions for Sharon/JJ, not prerequisites to reviewing this spec.
Defaults are proposals; record answers here before the corresponding implementation
gate. A missing commercial entitlement or budget is never inferred as approval.

| ID | Question | Proposed default | Needed before |
|---|---|---|---|
| Q1 | Is the first release an ATM-straddle research/paper tool, or must it include strangles, directional options and spreads? Any actual options execution expected? | Straddle only; no orders; other structures need separate contracts | Strategy implementation |
| Q2 | Should “7–14 days” mean trading sessions? Approve T-10 entry / T-2 exit and the stricter T-1/exit macro veto? | Trading sessions; fixed T-10/T-2; T-1 exit only in backtest sensitivity | Frozen baseline |
| Q3 | Approve reserve-first allocations? What capital, per-name/sector caps, watchlist and liquidity thresholds should be used? | 20% reserve; weights on 80%; 25% weekly per-name cap; $50k example only, never assumed user capital | Sizing and benchmark |
| Q4 | Which historical options and earnings datasets can we access, with which date range and historical bid/ask/IV permissions? Can we display derived results to Sharon? | Verify sample entitlements and rights; licensed CSV/import acceptable; no vendor purchase yet | Data acquisition / hosted display |
| Q5 | What are separate monthly caps for hosting, market data and SMS, and an acceptable one-time historical-data purchase? | Hosting target $0–5, planning ceiling $10; data and SMS budgets undecided | Purchases / deployment |
| Q6 | What constitutes success: minimum return after costs, drawdown ceiling, number of seasons/events, and paper observation period? | At least 4 held-out seasons, 100 resolved trades, 20 issuers, positive lower 95% block-bootstrap mean-net-P&L bound, and 20% sleeve drawdown ceiling; no profit guarantee | Promotion policy freeze |
| Q7 | Is this one shared research workspace for JJ/Sharon, or separate private accounts/portfolios? Is the standard `run.app` URL sufficient? | Two allowlisted identities in one shared research workspace; default URL, no public signup | Hosted identity |
| Q8 | Does “new model” mean a validated promoted version, every retraining run, or a generated portfolio? Who may promote it? | Owner promotion after backtest gates; send once per promotion/rollback, not per fit | Model lifecycle |
| Q9 | Which phone numbers/countries may opt in? Immediate texts or digest, quiet hours, and exit reminders? Existing SMS account/sender registration? | U.S. only initially; verified consent; daily entry/model digest, opted-in time-sensitive exit/invalidation notices; 200 segments/month provisional | SMS activation |
| Q10 | Is next-session EOD research acceptable? How quickly must earnings changes, exit reminders and material-news changes arrive? | Daily research; hourly session-time event rechecks; deadline reminders; publish stale status on failures; no real-time guarantee | Provider selection and schedules |
| Q11 | Are boards/news sentiment necessary for the first usable version? Any existing licenses or vendor models? | Official calendars/filings first; social and learned text sentiment optional, unavailable shown explicitly | Overlay acquisition |
| Q12 | Which GCP project/region and owner should host it, who receives billing alerts, and what recovery/data-retention targets are acceptable? | `us-central1`, daily tested logical backup, 24h recovery point, 4h manual recovery, bounded 30-day rolling backups; costs recorded | Cloud deployment |

## Blocking launch decisions

Q4–Q5 and Q7–Q12 must be resolved where they affect enabled features. The
research UI may ship with fixture/demo or unvalidated evidence clearly labelled;
recommendation promotion and SMS stay disabled until their gates pass. Research
must remain reportable if the strategy fails Q6. No threshold may be loosened
after seeing holdout results without a new version and fresh evaluation data.
