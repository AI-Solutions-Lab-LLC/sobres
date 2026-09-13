# PR #11 synchronization

The updated #10 base carries main `b9792d7`, #33's plans and fixes, and reviewed
#8 optimization through #35. Docker/deploy feature work is retained. Environment
file generation now uses the shared fixed secret display instead of the removed
suffix-mask helper; short/long secrets have CLI regression coverage.

Validation: 857 non-network tests passed, four live tests excluded, 95.73% branch
coverage. Black/isort, Ruff lint/format, mypy, actionlint and all 14 strict OpenSpec
checks passed. OpenAPI/client regeneration and frontend types/build/bundle gate
passed (160.3 KB gzip). Docker Desktop could not start locally; the required
GitHub Docker build/runtime/size job supplies container verification.

0005 and 0013 remain the accepted amended plans; layout migration, container
activation and outstanding R1/R2 evidence are not completed by this merge. #27
tracks remaining acceptance. No image was published or service deployed here.
