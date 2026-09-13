---
change: 0008-goal-planning
milestone: v1.4
depends_on: [0001-foundation-data-and-cli, 0002-portfolio-optimization, 0013-template-development-alignment, 0004-web-ui]
status: proposed
planning_depth: proposal + design + tasks + spec deltas; amended by 0013
---

# 0008 — Goal planning

## Outcome

```bash
sobres plan retire --income 200000 --expenses 90000 --portfolio 400000 --return 0.07
sobres plan house --price 950000 --down-pct 0.20 --by 2029-06-01 --monthly 3000
sobres plan car --price 45000 --by 2027-01-01 --current 5000
sobres plan goal --target 250000 --by 2032-01-01 --monthly 1500 --simulate 10000
```

Deterministic answers to "when / how much," and a Monte Carlo distribution behind
each so the answer comes with a probability rather than a false promise.

## Why

This is the slice closest to how JJ actually uses these numbers — the
`Areas/personal-finance-fire/` analyses are exactly these calculations, currently
done by hand per scenario. It also has the most existing code to reuse:
`espin086/fire-calculator`'s `core.py` (`savings_rate`, `fi_number`, `project`) is a
direct seed, and `espin086/CompountInterestAPI` already owns the compounding math.

It closes the loop with 0002: the optimizer says what to hold, the planner says
whether holding it gets you there.

## What changes

- **New capability `goal-planning`**: `core/goals.py` (generic funding solver plus
  retirement, house, car, education specializations) and `core/simulate.py`
  (Monte Carlo and historical-bootstrap engines).
- **New CLI group `sobres plan`**: `retire`, `house`, `car`, `education`, `goal`.
- Port `fire-calculator`'s core functions, with its tests carried over as regression
  fixtures so the ported math is provably identical.

## Non-goals

- **No tax modeling.** Marginal rates, Roth conversion ladders, RMDs, and state tax
  are each their own project. Inputs are after-tax; the spec says so at the edge.
- No Social Security benefit estimation. Users supply an expected benefit.
- No mortgage amortization, PMI, or closing-cost modeling in this milestone — `house` solves
  the down-payment savings path only.
- No account-type modeling (401k vs. Roth vs. taxable).
- No real-estate cash-flow analysis. That is `espin086/Real_Estate`'s job.

## Risks

| Risk | Mitigation |
|---|---|
| A single-point projection reads as a promise | Every `plan` command reports a success probability from simulation, not just the deterministic path; the deterministic answer is labeled as the 50th-percentile case |
| Sequence-of-returns risk is invisible in a CAGR model | Historical bootstrap mode resamples actual return sequences, so bad-early-years paths appear in the distribution |
| Real vs. nominal confusion — the most common error in retirement math | An explicit `--real` / `--nominal` choice, with real as the labelled default; every output labels which it is; inflation sourced from FRED `CPIAUCSL` |
| The 4% rule applied as universal truth | The withdrawal rate is a parameter, defaulting to 4%, with the output stating the assumption and its origin (Trinity study, 30-year US history) |

## Development alignment and review readiness (0013)

Keep goal/simulation mathematics in `core/`, orchestration in `application/commands/plan.py`, inflation/history through provider ports and saved goals through storage ports. Inject clock and seed; browser and CLI use the same service. No tax, enterprise or speculative storage profile is introduced.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #14 at `563caa73e049a18b69acca233299a73341f7c31c` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge is PR #33 (`b9792d7`).
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#30](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/30).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. The plan merged in PR #33 at `b9792d72dad7217f7bb642c0c90a668afc501087`;
the 0013 package migration remains unimplemented.
