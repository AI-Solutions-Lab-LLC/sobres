# Review remediation tasks

- [ ] **F1. Secret-valued config logging** → `tests/test_redaction.py::test_secret_config_value_is_redacted`
- [ ] **F2. Opaque factor identifiers** → `tests/data/test_ken_french.py::test_cached_factor_values_match_direct`
- [ ] **F3. Consistent migration backup** → `tests/data/test_storage_port.py::test_backup_contains_committed_wal`
- [ ] **F4. Base price dependency** → `tests/test_packaging.py::test_price_client_is_a_base_dependency`
- [ ] **F5. Empty optional input** → `tests/cli/test_init.py::test_real_prompt_accepts_empty_input`
- [ ] **F6. Missing revisions** → `tests/data/test_cache.py::test_refresh_preserves_missing_observations`
- [ ] **F7. Empty calendar tails** → `tests/data/test_yfinance.py::test_cached_weekend_extension`
- [ ] **F8. Complete currency metadata** → `tests/data/test_currency.py::test_conversion_rejects_incomplete_currency`
- [ ] **F9. Init health status** → `tests/cli/test_init.py::test_init_propagates_failed_doctor`
- [ ] **F10. Boolean options** → `tests/cli/test_init.py::test_no_verify_option`
- [ ] **V1. Verification** — strict OpenSpec validation; offline suite/coverage;
      Black/isort, Ruff, mypy; clean wheel onboarding; live keyless smoke.

Recorded fixture replacement and the D4 reuse audit remain open in 0001.
