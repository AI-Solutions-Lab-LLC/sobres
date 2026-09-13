# Review remediation tasks

- [x] **F1. Secret-valued config logging** → `tests/test_redaction.py::test_secret_config_value_is_redacted`
- [x] **F2. Opaque factor identifiers** → `tests/data/test_ken_french.py::test_cached_factor_values_match_direct`
- [x] **F3. Consistent migration backup** → `tests/data/test_storage_port.py::test_backup_contains_committed_wal`
- [x] **F4. Base price dependency** → `tests/test_packaging.py::test_price_client_is_a_base_dependency`
- [x] **F5. Empty optional input** → `tests/cli/test_init.py::test_real_prompt_accepts_empty_input`
- [x] **F6. Missing revisions** → `tests/data/test_cache.py::test_refresh_preserves_missing_observations`
- [x] **F7. Empty calendar tails** → `tests/data/test_yfinance.py::test_cached_weekend_extension`
- [x] **F8. Complete currency metadata** → `tests/data/test_currency.py::test_conversion_rejects_incomplete_currency`
- [x] **F9. Init health status** → `tests/cli/test_init.py::test_init_propagates_failed_doctor`
- [x] **F10. Boolean options** → `tests/cli/test_init.py::test_no_verify_option`
- [x] **F11. Fixed secret displays** → `tests/test_config.py::test_secrets_masked`,
      `tests/cli/test_config_commands.py::test_show_masks_api_keys`, and
      `tests/cli/test_init.py::test_guided_wizard_walks_every_setting_and_masks_secrets`
- [x] **F12. Explicit conformance mutations and rollback assertions** →
      `tests/data/storage_conformance.py::StorageConformance`
- [x] **V1. Verification** — strict OpenSpec validation; offline suite/coverage;
      Black/isort, Ruff, mypy; clean wheel onboarding; live keyless smoke.

Recorded fixture replacement and the D4 reuse audit remain open in 0001.
