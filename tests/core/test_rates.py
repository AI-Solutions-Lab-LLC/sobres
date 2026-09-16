"""Known answers for rate conventions (0002, 0015)."""

from __future__ import annotations


def test_prior_rates_refuses_to_invent_a_rate_when_asked() -> None:
    """Scenario: Source does not cover the window (0015)."""
    import pandas as pd
    import pytest

    from sobres.core.errors import InsufficientDataError
    from sobres.core.rates import prior_rates

    quotes = pd.Series(0.02, index=pd.bdate_range("2019-06-03", "2019-12-31"))
    returns_index = pd.DatetimeIndex(pd.bdate_range("2019-01-02", "2019-12-31"))
    # The old contract: pre-coverage dates silently take the fallback.
    lenient = prior_rates(quotes, returns_index)
    assert (lenient.loc[:"2019-06-03"] == 0.0).all() and lenient.iloc[-1] == 0.02
    # The 0015 contract: no fallback means insufficient data, naming both dates.
    with pytest.raises(
        InsufficientDataError, match="before 2019-01-02; first available 2019-06-03"
    ):
        prior_rates(quotes, returns_index, fallback=None)
    with pytest.raises(InsufficientDataError, match="no risk-free observations"):
        prior_rates(pd.Series(dtype="float64"), returns_index, fallback=None)
