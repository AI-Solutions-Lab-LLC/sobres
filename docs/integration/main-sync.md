# Main and accepted optimization integration — 2026-09-13

The user requested updating every open PR with current main and preserving its
feature work. PR #33 was squash-merged to main as
`b9792d72dad7217f7bb642c0c90a668afc501087`. PR #8 was squash-merged as
`7f59d01273dec42461ac6817f890baf246a6f033` into
`claude/kind-sagan-4yakbc-0001-foundation`, not main. The foundation integration PR
connects that accepted optimization work back to main without merging any pending
feature PR. PRs #9–#16 retain their ordered stack bases.

Conflict decisions:
- Preserve #33's full secret masking, 0012 regressions, recorded foundation
  payloads, 0013 plan, package map, workflow rules, and amendments to 0002–0010.
- Preserve #8's reviewed mathematical contracts and tests, solver protocol,
  CLI options, release token authentication/skip reporting, and review-decisions.md.
- Keep #8's completed domain tasks distinguishable from future 0013 layout work.
  No alignment migration, R execution, provider truth, or publication is inferred
  from merging branches or from green unit tests.
- #21 still owns TestPyPI verification and production activation. No variable,
  environment, token, release, or direct main push is part of this synchronization.

Foundation integration verification: 546 non-network tests passed, four live tests
excluded, 96.08% branch coverage; Ruff lint/format, strict mypy, actionlint 1.7.7,
and all 14 OpenSpec validations passed. Black and isort ran at 100 columns on
resolved Python files. Python 3.12.13, macOS arm64; isolated config/DB fixtures.
GitHub checks on each PR provide platform and built-artifact evidence.

The dated 0013 audit describes the earlier source snapshot. Current merge status
is recorded in its tracking.md and the GitHub PR/issue bodies. Remaining issue
acceptance and feature review must not be marked complete merely by synchronization.
