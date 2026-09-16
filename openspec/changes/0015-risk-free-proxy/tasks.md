# Tasks

- [x] **A1. Keyless USD uses Ken French RF; FRED failure falls through** → `tests/cli/test_optimize.py::test_risk_free_is_sourced_without_a_key_and_from_fred_with_one`
- [x] **A2. Non-USD without an override is a usage error** → `tests/cli/test_optimize.py::test_non_usd_without_override_names_the_flag`
- [x] **A3. Coverage guard replaces the pre-first-quote zero** → `tests/core/test_rates.py::test_prior_rates_refuses_to_invent_a_rate_when_asked`
- [x] **A4. Selection is announced on stderr and in provenance** → covered by A1
- [x] **V1. Verification** — strict OpenSpec validation; offline suite; ruff, mypy.
