"""Scenarios: Default window; Explicit dates are untouched (0014)."""

from __future__ import annotations

from datetime import date

import pytest

from sobres.cli.commands.analyze import FactorParams
from sobres.cli.commands.data import PricesParams
from sobres.cli.commands.fx import RatesParams
from sobres.cli.commands.optimize import UniverseParams
from sobres.cli.window import DEFAULT_WINDOW_YEARS, default_start, years_before


def test_years_before_is_calendar_years_and_clamps_leap_day() -> None:
    # Hand-derived: five calendar years back, day preserved; 29 Feb 2024 -> 28 Feb 2019.
    assert years_before(date(2024, 6, 15), 5) == date(2019, 6, 15)
    assert years_before(date(2024, 2, 29), 5) == date(2019, 2, 28)
    assert years_before(date(2024, 2, 29), 4) == date(2020, 2, 29)  # leap-to-leap keeps the 29th


def test_default_start_is_five_years_before_end_or_today() -> None:
    assert DEFAULT_WINDOW_YEARS == 5
    assert default_start(date(2024, 1, 31)) == date(2019, 1, 31)
    today = date.today()
    assert default_start(None) == years_before(today, 5)


def test_window_params_default_start() -> None:
    """Scenario: Default window — every window-taking model fills start from end."""
    for model, extra in (
        (PricesParams, {"tickers": ["AAPL"], "field": "adj_close"}),
        (UniverseParams, {"tickers": ["AAPL"], "fill": "drop"}),
        (FactorParams, {"tickers": ["AAPL"], "fill": "drop"}),
        (RatesParams, {"pairs": ["EURUSD"]}),
    ):
        p = model.model_validate({**extra, "end": "2024-01-31"})
        assert p.start == date(2019, 1, 31), model.__name__
        assert p.end == date(2024, 1, 31)
        fresh = model.model_validate(extra)
        assert fresh.start == default_start(None), model.__name__
        assert not model.model_fields["start"].is_required(), model.__name__


def test_explicit_start_is_untouched_and_order_is_still_checked() -> None:
    """Scenario: Explicit dates are untouched."""
    p = PricesParams.model_validate(
        {"tickers": ["AAPL"], "field": "adj_close", "start": "2021-03-01", "end": "2024-01-31"}
    )
    assert p.start == date(2021, 3, 1)
    with pytest.raises(ValueError, match="precedes"):
        PricesParams.model_validate(
            {"tickers": ["AAPL"], "field": "adj_close", "start": "2024-03-01", "end": "2024-01-31"}
        )
