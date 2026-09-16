"""Pure rate conventions for research proxies, not realized Treasury cash flows."""

from __future__ import annotations

import pandas as pd

from sobres.core.errors import InsufficientDataError, UsageError
from sobres.core.validation import require_finite

BILL_DAYS = 91.0
DISCOUNT_YEAR_DAYS = 360.0
INVESTMENT_YEAR_DAYS = 365.0


def treasury_investment_yield(discount: pd.Series) -> pd.Series:
    """Annual simple investment yield from a decimal bank-discount quote.

    Price/face = 1 - discount * days/360. Holding return = face/price - 1;
    annual simple proxy = holding return * 365/days. A fixed 91-day maturity
    is an approximation, not a claim of realized bill returns (Treasury bill
    bank-discount versus investment-rate quotation conventions).
    """
    require_finite(discount, "Treasury discount yield")
    price = 1.0 - discount * BILL_DAYS / DISCOUNT_YEAR_DAYS
    if (price <= 0).any():
        raise UsageError("Treasury discount yield implies a nonpositive bill price")
    return (1.0 / price - 1.0) * INVESTMENT_YEAR_DAYS / BILL_DAYS


def prior_rates(
    rates: pd.Series, index: pd.DatetimeIndex, *, fallback: float | None = 0.0
) -> pd.Series:
    """Most recent rate strictly before each return date; never backfill from the future.

    A return date with no prior observation takes ``fallback``; with
    ``fallback=None`` it is insufficient data instead, so a proxy that starts
    too late can never silently become a zero rate (0015).
    """
    if rates.empty:
        if fallback is None:
            raise InsufficientDataError(
                "no risk-free observations for the window",
                hint="widen --start, or pass --risk-free <annual decimal>",
            )
        return pd.Series(fallback, index=index, dtype="float64")
    require_finite(rates, "risk-free rates")
    if not rates.index.is_unique or not rates.index.is_monotonic_increasing:
        raise UsageError("risk-free observations need unique, increasing dates")
    positions = rates.index.searchsorted(index, side="left") - 1
    if fallback is None and (positions < 0).any():
        uncovered = index[positions < 0]
        raise InsufficientDataError(
            f"risk-free proxy has no observation before {uncovered[0].date()}; "
            f"first available {rates.index[0].date()}",
            hint="widen --start, or pass --risk-free <annual decimal>",
        )
    values = [float(rates.iloc[pos]) if pos >= 0 else fallback for pos in positions]
    return pd.Series(values, index=index, dtype="float64")
