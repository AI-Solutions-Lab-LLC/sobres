# PR #15 multivariable planning amendment — 2026-09-13

The owner replaced the ARIMA-only forecasting scope with joint/multivariable
stock-price forecasting and retained GARCH volatility. Source candidate `6a1f12d`
is unchanged at runtime by this amendment. Its prior 1,025-test green suite tests
that older candidate; it does not prove implementation of the new models.

Revised artifacts: 0009 proposal, design, tasks and econometrics scenarios, plus a
primary-source research/predictor catalog. README and project/readiness context
now distinguish planned VAR/BVAR/elastic-net/boosted-tree behavior from the old
candidate. The 0013 ownership/prerequisite rules remain intact. Issue #31 remains
the implementation tracker, and the amended contract is propagated into stacked
PR #16. The docs-only planning PR against main is linked from #31 so this contract can
be accepted without merging obsolete runtime code. No duplicate implementation
issue, release, runtime edit or merge to main.

Research includes influential stock VAR/shrinkage/asset-pricing papers and recent
2025–2026 multivariate/foundation-model benchmarks. The notes separate evidence,
inference, proposed defaults and deferred models; no forecast or profitability
experiment was performed. The basic data preset remains keyless, while macro and
historical fundamentals require actual availability/vintage support.

Validation: OpenSpec CLI 1.13.0, all 14 changes passed strict validation with
telemetry disabled; whitespace checks, Ruff lint/format, mypy and actionlint passed.
No Python file was edited, so Black/isort were not needed. Full runtime tests were
not repeated locally for this documentation-only amendment; GitHub checks run on
the pushed heads. New named tests in tasks.md are future acceptance work, not
existing coverage. Implementation remains incomplete until those proofs pass.
