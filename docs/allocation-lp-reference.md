# The budget-allocation LP: reference formulation

`src/sobres/core/allocate.py` is a port of the R script
`Financial Portfolio Optimization.R` from this repository's pre-sobres history
(`legacy_code/`, removed in the commit that added this file; see `git log` for
the last revision that carried it). This page records the formulation that
script solved with `linprog::solveLP`, so the known-answer fixture in
`tests/fixtures/r_reference/allocation.json` keeps a derivation a reader can
check without the original source.

## Problem

Split a budget across six vehicles. Decision variable `w ∈ R^6`, the fraction of
the budget in each vehicle. Inputs per vehicle: an expected return in percent
(`returns_pct`) and a risk score (`risk`). Uninvested money sits in a savings
account earning 3% with the lowest risk score.

The fixture's table (the one `scripts/r_reference.py` solves):

| # | Vehicle | Return % | Risk |
|---|---|---|---|
| 1 | first_mortgages | 9.0 | 6.0 |
| 2 | second_mortgages | 12.0 | 8.0 |
| 3 | personal_loans | 15.0 | 10.0 |
| 4 | commercial_loans | 8.0 | 4.0 |
| 5 | savings | 3.0 | 1.0 |
| 6 | treasuries | 5.0 | 2.0 |

## Objective

Maximize average return per dollar:

```
max  Σ_i (returns_pct_i / 100) · w_i
```

## Constraints, exactly as the R script coded them

| Name | Row | Direction | RHS | Meaning |
|---|---|---|---|---|
| budget | `(1, 1, 1, 1, 1, 1)` | `==` | 1 | fractions sum to one |
| average_risk | `risk − 5` | `<=` | 0 | weighted-average risk ≤ 5, over all six vehicles |
| commercial_minimum | `0.20·1 − e_4` | `<=` | 0 | commercial loans ≥ 20% of the budget |
| mortgage_ratio | `(−1, 2, 3, 0, 0, 0)` | `<=` | 0 | see the note below |

with `0 ≤ w_i ≤ 1`.

**A note on `mortgage_ratio`.** The R script's comment describes the constraint
as "second mortgages and personal loans combined should be no higher than first
mortgages", i.e. `w_2 + w_3 ≤ w_1`, which would be the row `(−1, 1, 1, 0, 0, 0)`.
The code, however, used `c(-1, 2, 3, 0, 0, 0)`, i.e. `2·w_2 + 3·w_3 ≤ w_1`. The
port and the fixture follow **the code**, because that is what produced the
reference numbers; the discrepancy is recorded here rather than silently fixed.
Anyone wanting the constraint the comment describes should change the row and
regenerate the fixture with `scripts/r_reference.py`.

**A note on `average_risk`.** The comment says the average is "over the 5
investments not the savings account", but the code applied `risk − 5` to every
vehicle including savings. The fixture again follows the code.

## Reference solution

`scripts/r_reference.py` solves the same LP by exhaustive vertex enumeration —
independent of the `scipy.optimize.linprog` path the port uses — and records:

```
first_mortgages   0.25
second_mortgages  0.00
personal_loans    0.0833…
commercial_loans  0.6667…
savings           0.00
treasuries        0.00
objective         0.08833…   (8.83% average return per dollar)
```

R's own `solveLP` output was never captured (neither R nor the Google Sheet the
script read were reachable from the implementing environment); the vertex
enumeration is the independent oracle the tests assert against.
