# PR #10 synchronization

The updated #9 base includes main `b9792d7` (PR #33), accepted PR #8 through
#35, and the reconciled saved-portfolio validation. This merge retains the web
candidate and current 0004/0013 plans; explicit exposure and the new layout remain
pending acceptance under #26, not completed by this synchronization.

Job progress/cancellation is preserved for backtests and frontier work; the API
uses the shared fixed secret marker, covered with short and long sentinel tests.
OpenAPI and its generated TypeScript client are refreshed for the reviewed
optimizer parameters. No accepted optimization math or main provider fixture is
replaced by an older branch copy.

Validation: 804 non-network tests passed, four live tests excluded, 95.32% branch
coverage. Black/isort, Ruff lint/format, mypy, actionlint and all 14 strict OpenSpec
checks passed. OpenAPI/client drift checks and frontend types/build/bundle gate
passed (160.3 KB gzip against 300 KB). Browser journeys and live providers were
not manually exercised; these remain review/implementation acceptance work.
