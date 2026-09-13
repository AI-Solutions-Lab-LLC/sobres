"""Input preconditions shared by pure analytics."""

from __future__ import annotations

import numpy as np
import pandas as pd

from sobres.core.errors import UsageError


def require_finite(values: pd.DataFrame | pd.Series, name: str = "returns") -> None:
    """Reject unresolved gaps/infinities; resolve missing observations explicitly first."""
    if not np.isfinite(values.to_numpy(dtype="float64")).all():
        raise UsageError(
            f"{name} contains missing or non-finite values",
            hint="resolve missing observations with an explicit policy before computing",
        )


def require_time_index(values: pd.DataFrame | pd.Series) -> None:
    """Positional walk-forward slices require a unique, increasing datetime index."""
    if (
        not isinstance(values.index, pd.DatetimeIndex)
        or not values.index.is_monotonic_increasing
        or not values.index.is_unique
    ):
        raise UsageError("returns need a unique, increasing DatetimeIndex")
