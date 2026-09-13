"""SciPy SLSQP adapter implementing the repository's numerical protocol."""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from sobres.solvers.base import Gradient, ObjectiveFunction, Solution


class ScipySolver:
    def solve(
        self,
        fun: ObjectiveFunction,
        initial: np.ndarray,
        bounds: list[tuple[float, float]],
        constraints: list[dict[str, object]],
        gradient: Gradient | None = None,
    ) -> Solution:
        result = minimize(
            fun,
            initial,
            method="SLSQP",
            jac=gradient,
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 1000, "ftol": 1e-12},
        )
        return Solution(
            np.asarray(result.x, dtype="float64"),
            bool(result.success),
            str(result.message),
            int(result.nfev),
            int(result.nit),
        )
