# PR #12 synchronization

The updated #11 base includes main `b9792d7`, PR #33's plans and fixes, and reviewed
optimization from #8/#35. Current 0006/0013 plans and deferred hosting/layout work
remain intact. The candidate's site, shared tokens and build tooling are retained.

Figures and terminal output were regenerated offline from main's recorded provider
payloads using the corrected optimizer. Metadata now distinguishes these recordings
from the former synthetic dataset. The fee label states cash-inclusive one-way
turnover, matching #8. No live provider call or Pages deployment was performed.

Validation: 872 non-network tests passed, four live tests excluded, 95.73% branch
coverage; Black/isort, Ruff lint/format, mypy, actionlint and all 14 strict OpenSpec
checks passed. Frontend and site types/build/bundle checks passed; site initial JS
is 26.8 KB gzip against 150 KB. Two Lighthouse mobile runs scored 99/100 performance,
100 accessibility and 100 best practices; configured >=95 assertions passed.
Audit reports were kept local (no public-storage upload). Docker remains verified
by GitHub because local Docker Desktop cannot start. #28 retains unfinished
alignment and product-home-page acceptance.
