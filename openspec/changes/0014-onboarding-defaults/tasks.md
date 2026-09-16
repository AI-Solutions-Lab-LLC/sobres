# Tasks

- [x] **A1. Advanced tier on settings** → `tests/test_config.py::test_only_the_fred_key_is_essential`
- [x] **A2. `init` prompts essentials only; `--advanced` walks everything** →
      `tests/cli/test_init.py::test_guided_wizard_asks_only_essential_settings`,
      `tests/cli/test_init.py::test_advanced_flag_walks_every_setting_and_masks_secrets`
- [x] **B1. Shared default window** → `tests/cli/test_window.py`
- [x] **B2. Window-taking commands default `--start`** → `tests/cli/test_window.py::test_window_params_default_start`
- [x] **C1. `register(example=...)` and the usage hint** → `tests/cli/test_usage_examples.py`
- [x] **C2. Every command with a required parameter declares an example** →
      `tests/invariants/test_every_command.py::test_every_command_with_required_params_declares_an_example`
- [x] **D1. OpenAPI document and client regenerated** → CI client-drift gate
- [x] **V1. Verification** — strict OpenSpec validation; offline suite; ruff, mypy.
