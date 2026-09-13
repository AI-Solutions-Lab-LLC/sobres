"""``sobres config`` group.

Scenarios: Setting a key; Secrets are never echoed; Config file location.
"""

from __future__ import annotations

import json
import stat
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_set_persists_at_0600(cli: Callable[..., Any], env: dict[str, str]) -> None:
    result = cli("config", "set", "fred_api_key", "ABC123XYZ")
    assert result.exit_code == 0 and "****" in result.stdout and "ABC123XYZ" not in result.stdout
    path = Path(env["SOBRES_CONFIG_FILE"])
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert 'fred_api_key = "ABC123XYZ"' in path.read_text(encoding="utf-8")
    assert cli("config", "path").stdout.strip().endswith("config.toml")


@pytest.mark.parametrize("secret_value", ["Z9!", "Q7$!", "ABC123XYZ"])
@pytest.mark.parametrize("fmt", ["json", "csv", "table"])
def test_show_masks_api_keys(cli: Callable[..., Any], secret_value: str, fmt: str) -> None:
    """Scenario: Secret displays reveal no credential characters."""
    saved = cli("config", "set", "fred_api_key", secret_value)
    assert saved.exit_code == 0
    assert secret_value not in saved.stdout + saved.stderr
    assert "****" in saved.stdout
    result = cli("config", "show", "--format", fmt)
    assert result.exit_code == 0
    assert secret_value not in result.stdout + result.stderr
    assert "****" in result.stdout
    if fmt == "json":
        rows = {r["key"]: r for r in json.loads(result.stdout)["rows"]}
        assert rows["fred_api_key"]["value"] == "****"
        assert rows["fred_api_key"]["source"] == "file"
        assert rows["db_url"]["value"] == "****"  # a DB URL may carry credentials
        assert rows["log_level"]["value"] == "WARNING"
        assert rows["log_level"]["source"] == "default"


def test_set_validates_key_and_value(cli: Callable[..., Any]) -> None:
    assert cli("config", "set", "nope", "1").exit_code == 3
    bad = cli("config", "set", "log_level", "LOUD")
    assert bad.exit_code == 3 and "DEBUG, INFO" in bad.stderr


def test_unset_removes_key(cli: Callable[..., Any], env: dict[str, str]) -> None:
    cli("config", "set", "log_level", "INFO")
    assert "removed" in cli("config", "unset", "log_level").stdout
    assert "log_level" not in Path(env["SOBRES_CONFIG_FILE"]).read_text(encoding="utf-8")
    assert "was not set" in cli("config", "unset", "log_level").stdout
