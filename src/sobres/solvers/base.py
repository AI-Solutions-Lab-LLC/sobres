"""Pure numerical optimization protocol; no third-party solver result types escape."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np

ObjectiveFunction = Callable[[np.ndarray], float]
Gradient = Callable[[np.ndarray], np.ndarray]


@dataclass(frozen=True)
class Solution:
    weights: np.ndarray
    success: bool
    message: str
    evaluations: int
    iterations: int


class Solver(Protocol):
    def solve(
        self,
        fun: ObjectiveFunction,
        initial: np.ndarray,
        bounds: list[tuple[float, float]],
        constraints: list[dict[str, object]],
        gradient: Gradient | None = None,
    ) -> Solution: ...


def default_solver() -> Solver:
    from sobres.solvers.scipy import ScipySolver

    return ScipySolver()
