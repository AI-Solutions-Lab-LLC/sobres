"""Scenario: One essential setting (0014)."""

from __future__ import annotations

from sobres.settings import all_settings


def test_only_the_fred_key_is_essential() -> None:
    essential = [s.key for s in all_settings() if not s.advanced]
    assert essential == ["fred_api_key"]
    assert all(s.advanced for s in all_settings() if s.key != "fred_api_key")
