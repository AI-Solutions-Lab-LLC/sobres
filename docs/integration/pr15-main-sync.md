# PR #15 synchronization

The updated #14 base includes main `b9792d7`, PR #33 plans/fixes, and reviewed #8
optimization through #35. Econometrics and the GARCH covariance candidate remain
included. The econ extra keeps arch/statsmodels and their doctor coverage; Yahoo
remains a base dependency, while the data extra retains pandas-datareader.

Validation: 1,025 non-network tests passed, four live tests excluded, 95.77% branch
coverage. Black/isort, Ruff lint/format, mypy, actionlint and all 14 strict OpenSpec
checks passed. OpenAPI/client regenerated for current parameters; frontend types,
build and bundle gate passed. Main's recorded provider files remain unchanged.

0009/0013 layout and R1/R2 acceptance remain pending under #31. Green regression
checks do not prove forecast accuracy or complete every amended scenario. No
release, deployment, or pending feature merge was performed here.
