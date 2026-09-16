"""Scenario: Usage errors show a worked example (0014)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from sobres.registry import get_command


def test_missing_required_parameter_hint_leads_with_the_example(cli: Callable[..., Any]) -> None:
    result = cli("analyze", "stock")  # ticker and --fill are required
    assert result.exit_code == 2
    example = get_command("analyze.stock").example
    assert example
    assert f"try: sobres {example}" in result.stderr
    assert "sobres analyze stock --help" in result.stderr


def test_a_command_without_an_example_keeps_the_help_pointer(cli: Callable[..., Any]) -> None:
    # `commands` has no required parameters and declares no example; an unknown
    # flag is still a usage error with the plain --help hint.
    result = cli("commands", "--no-such-flag")
    assert result.exit_code == 2
    assert "--help" in result.stderr
    assert "try: sobres" not in result.stderr
