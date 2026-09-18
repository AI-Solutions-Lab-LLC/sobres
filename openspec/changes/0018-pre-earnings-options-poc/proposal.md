---
change: 0018-pre-earnings-options-poc
milestone: next options research POC
depends_on: [0001-foundation-data-and-cli, 0003-local-persistence, 0004-web-ui, 0005-docker-distribution]
status: proposed
---

# 0018 — Pre-earnings options research, hosted recommendations, and SMS

## Outcome

Sharon can open a deployed Sobres website, see explainable pre-earnings options
research candidates and their historical evidence, and receive text updates when
a validated model is promoted or a recommendation changes. Every recommended
strategy must first pass a reproducible, cost-aware, point-in-time backtest. An
honest result may be **no validated strategy and no trade**.

This PR is the planning contract, not an implementation or a completed backtest.
No cloud resources, paid subscriptions, trades, or SMS are created by this PR.
Implementation acceptance remains unchecked in [tasks.md](tasks.md).

## Why

The supplied `Pre_Earnings_Options_Trading_Guide.docx` describes buying defined-risk
long options before earnings and selling before the announcement. Despite its
title, this is a **pre-earnings IV-expansion** strategy, not selling volatility or
holding through the earnings crush. Existing Sobres equity backtests cannot prove
options returns: they lack historical contract quotes, event-time provenance,
exercise/deliverable metadata, and bid/ask execution.

The owner additionally requested an actual hosted website, recommendations,
model/recommendation text updates, and very cheap Google Cloud hosting without
Cloud SQL. These additions are explicit scope even though absent from the guide.

## What changes

- Versioned earnings and options data contracts with verified vendor entitlements.
- A mechanical ATM-straddle baseline, explicit timing/liquidity/risk rules,
  optional overlay experiments, and a bounded statistical challenger.
- Event and portfolio backtests with spreads, costs, overlapping positions,
  chronological validation, failure accounting, and publishable evidence.
- Registry-generated `options` commands/API forms plus research, recommendations,
  model history, paper-position tracking, and notification views in the existing SPA.
- Consent-based SMS with durable deduplication, delivery state, and budget controls.
- A restricted hosted-options profile: Cloud Run service and Jobs, Firestore for
  small durable operational records, Cloud Storage for immutable research artifacts.
  Local Sobres continues to use SQLite. No SQLite file is opened on a bucket mount.
- Deployment, backup/restore, job-recovery, identity, and cost acceptance tests.

## Existing foundations and contract changes

Inspected merged base: `60f123a6f79ab2a2b803525c91ed93eaa3c47a3c` on `main`.
The React SPA, FastAPI registry routes, Dockerfile and Compose deployment exist.
SQLite is the operational backend; `api/jobs.py` uses an in-process worker;
`api/auth.py` uses a shared deployment token. They are not yet the hosted design
specified here. The GitHub Pages site is a landing page, not the research app.

Reuse 0002's conventions and reporting ideas, not its equity execution simulator.
0009's VAR/BVAR price forecasts are not evidence for an options strategy. 0016's
broker execution is whole-share equity scope: this change adds no options orders.
There are no archived accepted capability specs beyond the placeholder; the
implemented change specs and actual base code establish the current contract.

This deliberately extends 0004/0005 with a restricted cloud profile and identity
boundary. It also extends the single-file **local** persistence convention with
explicit artifact and operational ports for that profile; it does not advertise
Firestore as a drop-in replacement for all Sobres repositories. See
[design.md](design.md). Release-engineering changes and open PR #53 are independent.
No private template/context material is needed. Issue: none created; this planning
PR is the tracking item. Planning PR URL is recorded in its GitHub description.

## Scope and non-goals

Required POC: standard USD U.S. equity ATM long straddles, confirmed earnings,
daily research, realistic historical evaluation, paper recommendations, authenticated
website, and SMS. A frozen baseline is followed by overlay/challenger evaluation;
only a promoted, passing version can produce actionable paper candidates.

Strangles, directional calls/puts, and debit spreads are captured from the guide
but deferred until their own selection, exercise/assignment, and backtest scenarios
exist. Social sentiment is an optional licensed experiment, never a launch
dependency. No short premium, autonomous execution, through-earnings positions,
broker integration for options, public signup, multi-tenant SaaS, streaming tick
platform, Cloud SQL, always-on VM, or claims of guaranteed profitability.

## Delivery and decision gates

1. Resolve the policy decisions in [questions.md](questions.md); validate actual
   data access, historical earnings confirmations, and display rights first.
2. Implement offline domain contracts and known-answer math; ingest a bounded,
   licensed historical universe; run the locked baseline and challengers.
3. Publish all results, including failures. Insufficient evidence leaves the app
   in research/demo mode and suppresses actionable recommendations.
4. Add local UI, persistent recommendation/model state, paper tracking and SMS.
5. Add the restricted cloud profile and deploy the tested image using the owner's
   selected project, budget, identity configuration, and licensed data. Verify
   restart/restore, a paper journey, and a consenting recipient's test SMS.

## Risks and proposed defaults

Historical quote and redistribution rights may cost more than hosting. The guide's
cheap-plan claims do not establish historical bid/ask access. Free data can prove
plumbing, not multi-season profitability. Same-close feature selection and filling
would introduce look-ahead. Calendar revisions, missing exits, corporate actions,
and correlated losses need explicit treatment. SMS has fees and delivery uncertainty.

Proposed infrastructure target: **$0–5/month** at tiny usage, with a **$10/month
planning ceiling** before data/SMS; this is an estimate, not a price guarantee or
an enforced billing cap. [hosting.md](hosting.md) separates all cost buckets.
Decisions and thresholds below are proposed engineering defaults for Sharon to
review; none is represented as an empirically established trading edge.

## Reading order

1. [Requirements extracted from the guide](source-analysis.md)
2. [Questions for Sharon and JJ](questions.md)
3. [Algorithms and architecture](design.md), [hosting and costs](hosting.md)
4. [Research and vendor evidence](research.md)
5. [Acceptance specs](specs/earnings-options/spec.md) and [implementation tasks](tasks.md)
