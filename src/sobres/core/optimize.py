"""Constrained mean-variance optimization and the efficient frontier.

Markowitz (1952) mean-variance: choose weights ``w`` with ``Σw = 1`` and box
bounds to minimize ``wᵀΣw`` (min variance), maximize ``(wᵀμ - r_f)/sqrt(wᵀΣw)``
(max Sharpe, the tangency portfolio of Tobin 1958), hit a target return or
risk, equalize risk contributions (Maillard, Roncalli & Teïletche 2010), or
hold equal weights.

Solver: SLSQP via ``scipy.optimize.minimize``. Max-Sharpe runs from several
starting points (equal weight, min variance, seeded random) and the best
feasible solution wins, so a local optimum cannot pass as the answer.
Determinism is preserved by a fixed seed. Nothing here logs; findings such as
a concentration warning are returned on the result.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

import numpy as np
import pandas as pd

from sobres.core.errors import InsufficientDataError, OptimizationError, UsageError
from sobres.core.moments import condition_covariance
from sobres.core.validation import require_finite
from sobres.solvers.base import Gradient, Solver, default_solver

Objective = Literal[
    "min_variance", "max_sharpe", "target_return", "target_risk", "risk_parity", "equal_weight"
]
OBJECTIVES: tuple[str, ...] = (
    "min_variance",
    "max_sharpe",
    "target_return",
    "target_risk",
    "risk_parity",
    "equal_weight",
)
WEIGHT_TOLERANCE = 1e-8
CONCENTRATION_THRESHOLD = 0.50
RANDOM_STARTS = 8


@dataclass(frozen=True)
class Constraints:
    """Bounds on every weight. Long-only ``[0, 1]`` unless ``allow_short``."""

    max_weight: float | None = None
    allow_short: bool = False
    min_weight: float | None = None

    def bounds(self, n: int) -> list[tuple[float, float]]:
        if n < 1 or n > 100:
            raise UsageError("optimization supports 1 to 100 assets")
        for value in (self.max_weight, self.min_weight):
            if value is not None and not np.isfinite(value):
                raise UsageError("weight bounds must be finite")
        lower = -1.0 if self.allow_short else 0.0
        if self.min_weight is not None:
            lower = max(lower, self.min_weight)
        upper = 1.0 if self.max_weight is None else min(1.0, self.max_weight)
        if upper * n < 1.0 - WEIGHT_TOLERANCE:
            raise UsageError(
                f"max_weight {upper} times {n} assets is below 1.0: the constraint is infeasible",
                hint=f"raise --max-weight to at least {1.0 / n:.4f} or add assets",
            )
        if lower * n > 1.0 + WEIGHT_TOLERANCE:
            raise UsageError("minimum weights sum to more than one: infeasible bounds")
        if lower > upper:
            raise UsageError(f"min_weight {lower} exceeds max_weight {upper}")
        return [(lower, upper)] * n


@dataclass(frozen=True)
class Estimators:
    expected_return: str
    covariance: str
    shrinkage: float | None = None
    psd_repair: dict[str, float] | None = None


@dataclass(frozen=True)
class Portfolio:
    weights: dict[str, float]
    expected_return: float
    volatility: float
    sharpe: float
    objective: str
    estimators: Estimators
    risk_free: float
    warnings: tuple[str, ...] = ()
    solver_status: str = "optimal"
    risk_contributions: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class FrontierPoint:
    expected_return: float
    volatility: float
    sharpe: float
    weights: dict[str, float]
    is_min_variance: bool = False
    is_max_sharpe: bool = False


@dataclass(frozen=True)
class Frontier:
    points: tuple[FrontierPoint, ...]
    estimators: Estimators
    risk_free: float


def _stats(
    w: np.ndarray, mu: np.ndarray, sigma: np.ndarray, rf: float
) -> tuple[float, float, float]:
    ret = float(w @ mu)
    var = float(w @ sigma @ w)
    vol = float(np.sqrt(max(var, 0.0)))
    sharpe = (ret - rf) / vol if vol > 0 else float("nan")
    return ret, vol, sharpe


def _solve(
    fun: Callable[[np.ndarray], float],
    x0: np.ndarray,
    bounds: list[tuple[float, float]],
    constraints: list[dict[str, object]],
    gradient: Gradient | None = None,
    solver: Solver | None = None,
) -> tuple[np.ndarray, bool, str]:
    result = (solver or default_solver()).solve(fun, x0, bounds, constraints, gradient)
    w = result.weights
    feasible = result.success and np.isfinite(w).all() and abs(w.sum() - 1.0) < WEIGHT_TOLERANCE
    return w, bool(feasible), result.message


def _clean(w: np.ndarray, bounds: list[tuple[float, float]]) -> np.ndarray:
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    w = np.clip(w, lo, hi)
    w[np.abs(w) < 1e-12] = 0.0
    return w / w.sum() if abs(w.sum()) > 1e-12 else w


def max_attainable_return(mu: np.ndarray, bounds: list[tuple[float, float]]) -> float:
    """Greedy: fill the highest-return assets to their upper bounds (box + sum = 1)."""
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    w = lo.copy()
    remaining = 1.0 - w.sum()
    for i in np.argsort(-mu):
        room = hi[i] - w[i]
        take = min(room, remaining)
        w[i] += take
        remaining -= take
        if remaining <= 1e-12:
            break
    return float(w @ mu)


def optimize(
    mu: pd.Series,
    sigma: pd.DataFrame,
    objective: Objective = "max_sharpe",
    constraints: Constraints | None = None,
    *,
    risk_free: float = 0.0,
    target: float | None = None,
    seed: int = 0,
    estimators: Estimators | None = None,
    explicit_max_weight: bool = False,
    solver: Solver | None = None,
    initial: np.ndarray | None = None,
) -> Portfolio:
    """Solve one objective on annualized ``mu`` and ``sigma``; return a valid portfolio.

    Weights sum to one within ``1e-8`` and satisfy every bound within ``1e-8``.
    ``OptimizationError`` is raised if the solver does not converge; no weight
    vector is returned then. A concentration warning is attached when a weight
    exceeds 50% and no explicit ``max_weight`` was given.
    """
    if objective not in OBJECTIVES:
        raise UsageError(f"objective must be one of {', '.join(OBJECTIVES)}, got {objective!r}")
    require_finite(mu, "expected returns")
    if not np.isfinite(risk_free) or (target is not None and not np.isfinite(target)):
        raise UsageError("risk-free rate and target must be finite")
    if seed < 0:
        raise UsageError("seed must be a nonnegative integer")
    if not mu.index.is_unique or not sigma.index.is_unique or not sigma.columns.is_unique:
        raise UsageError("asset identifiers must be unique")
    cons = constraints or Constraints()
    assets = list(mu.index)
    if set(sigma.index) != set(assets) or set(sigma.columns) != set(assets):
        raise UsageError("covariance labels must match expected-return assets")
    attrs = dict(sigma.attrs)
    sigma, repair = condition_covariance(sigma.loc[assets, assets])
    sigma.attrs = attrs
    if repair is not None:
        sigma.attrs["psd_repair"] = repair.__dict__
    m = mu.to_numpy(dtype="float64")
    s = sigma.to_numpy(dtype="float64")
    n = len(assets)
    bounds = cons.bounds(n)
    sum_to_one = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0), "jac": lambda w: np.ones(n)}
    ]
    equal = np.full(n, 1.0 / n)
    est = estimators or Estimators(
        expected_return=str(mu.attrs.get("estimator", "given")),
        covariance=str(sigma.attrs.get("estimator", "given")),
        shrinkage=sigma.attrs.get("shrinkage"),
        psd_repair=sigma.attrs.get("psd_repair"),
    )
    status = "optimal"
    start = equal if initial is None else initial

    def solve(
        fun: Callable[[np.ndarray], float],
        x0: np.ndarray,
        box: list[tuple[float, float]],
        conditions: list[dict[str, object]],
        gradient: Gradient | None = None,
    ) -> tuple[np.ndarray, bool, str]:
        return _solve(fun, x0, box, conditions, gradient, solver)

    def variance(w: np.ndarray) -> float:
        return float(w @ s @ w)

    def variance_gradient(w: np.ndarray) -> np.ndarray:
        return np.asarray(2.0 * s @ w, dtype="float64")

    if objective == "equal_weight":
        w = equal
    elif objective == "min_variance":
        w, ok, msg = solve(variance, start, bounds, sum_to_one, variance_gradient)
        if not ok:
            raise OptimizationError(f"min_variance did not converge: {msg}")
    elif objective == "max_sharpe":
        w = _max_sharpe(m, s, risk_free, bounds, sum_to_one, seed, solve)
    elif objective == "target_return":
        if target is None:
            raise UsageError("target_return needs --target")
        attainable = max_attainable_return(m, bounds)
        if target > attainable + 1e-9:
            raise InsufficientDataError(
                f"target return {target:.4%} exceeds the attainable maximum {attainable:.4%}",
                hint=f"choose --target at or below {attainable:.4f}",
            )
        minimum = -max_attainable_return(-m, bounds)
        if target < minimum - 1e-9:
            raise InsufficientDataError(
                f"target return {target:.4%} is below attainable minimum {minimum:.4%}"
            )
        cons_list = [
            *sum_to_one,
            {"type": "eq", "fun": lambda w: float(w @ m - target), "jac": lambda w: m},
        ]
        w, ok, msg = solve(variance, start, bounds, cons_list, variance_gradient)
        if not ok:
            raise OptimizationError(f"target_return did not converge: {msg}")
    elif objective == "target_risk":
        if target is None:
            raise UsageError("target_risk needs --target")
        w_min, ok, msg = solve(variance, start, bounds, sum_to_one, variance_gradient)
        if not ok:
            raise OptimizationError(f"target_risk did not converge: {msg}")
        min_vol = float(np.sqrt(max(variance(w_min), 0.0)))
        if target < min_vol - 1e-9:
            raise InsufficientDataError(
                f"target risk {target:.4%} is below the minimum attainable "
                f"volatility {min_vol:.4%}",
                hint=f"choose --target at or above {min_vol:.4f}",
            )
        cons_list = [
            *sum_to_one,
            {
                "type": "ineq",
                "fun": lambda w: float(target**2 - w @ s @ w),
                "jac": lambda w: -2.0 * s @ w,
            },
        ]
        w, ok, msg = solve(lambda w: -float(w @ m), w_min, bounds, cons_list, lambda w: -m)
        if not ok:
            raise OptimizationError(f"target_risk did not converge: {msg}")
    else:  # risk_parity
        w = _risk_parity(s, bounds, sum_to_one, start, solve)
    w = _clean(w, bounds)
    if abs(w.sum() - 1.0) > WEIGHT_TOLERANCE or any(
        wi < lo - WEIGHT_TOLERANCE or wi > hi + WEIGHT_TOLERANCE
        for wi, (lo, hi) in zip(w, bounds, strict=True)
    ):
        raise OptimizationError("solver returned weights outside the portfolio constraints")
    ret, vol, sharpe = _stats(w, m, s, risk_free)
    if objective == "target_return" and target is not None and abs(ret - target) > WEIGHT_TOLERANCE:
        raise OptimizationError("solver did not satisfy target return")
    if objective == "target_risk" and target is not None and vol > target + WEIGHT_TOLERANCE:
        raise OptimizationError("solver exceeded target risk")
    contributions = (w * (s @ w)) / (w @ s @ w) if vol > 0 else np.zeros(n)
    warnings: list[str] = []
    if (
        not explicit_max_weight
        and objective not in ("equal_weight",)
        and w.max() > CONCENTRATION_THRESHOLD
    ):
        top = assets[int(np.argmax(w))]
        warnings.append(
            f"{top} takes {w.max():.1%} of the portfolio: unconstrained mean-variance "
            "solutions concentrate; consider --max-weight"
        )
    return Portfolio(
        weights={a: float(x) for a, x in zip(assets, w, strict=True)},
        expected_return=ret,
        volatility=vol,
        sharpe=sharpe,
        objective=objective,
        estimators=est,
        risk_free=risk_free,
        warnings=tuple(warnings),
        solver_status=status,
        risk_contributions={a: float(c) for a, c in zip(assets, contributions, strict=True)},
    )


def _max_sharpe(
    m: np.ndarray,
    s: np.ndarray,
    rf: float,
    bounds: list[tuple[float, float]],
    sum_to_one: list[dict[str, object]],
    seed: int,
    solve: Callable[..., tuple[np.ndarray, bool, str]],
) -> np.ndarray:
    n = len(m)

    def neg_sharpe(w: np.ndarray) -> float:
        var = float(w @ s @ w)
        if var <= 0:
            return 1e6
        return -float((w @ m - rf) / np.sqrt(var))

    def gradient(w: np.ndarray) -> np.ndarray:
        variance = float(w @ s @ w)
        if variance <= 0:
            return np.zeros(n)
        vol = np.sqrt(variance)
        return np.asarray(-m / vol + (w @ m - rf) * (s @ w) / vol**3, dtype="float64")

    starts = [np.full(n, 1.0 / n)]
    w_min, ok, _ = solve(
        lambda w: float(w @ s @ w), starts[0], bounds, sum_to_one, lambda w: 2.0 * s @ w
    )
    if ok:
        starts.append(w_min)
    rng = np.random.default_rng(seed)
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    for _ in range(RANDOM_STARTS):
        raw = rng.dirichlet(np.ones(n))
        starts.append(
            np.clip(lo + raw * (hi - lo), lo, hi)
            / max(np.sum(np.clip(lo + raw * (hi - lo), lo, hi)), 1e-12)
        )
    best: np.ndarray | None = None
    best_value = np.inf
    messages: list[str] = []
    for x0 in starts:
        w, ok, msg = solve(neg_sharpe, x0, bounds, sum_to_one, gradient)
        if not ok:
            messages.append(msg)
            continue
        value = neg_sharpe(w)
        if value < best_value - 1e-12:
            best, best_value = w, value
    if best is None:
        raise OptimizationError(
            "max_sharpe did not converge from any starting point: "
            + "; ".join(sorted(set(messages)))
        )
    return best


def _inverse_volatility_start(
    s: np.ndarray, bounds: list[tuple[float, float]]
) -> np.ndarray | None:
    """Weights proportional to ``1 / sigma_i``, or ``None`` if they break a bound.

    For a diagonal covariance matrix this is the exact equal-risk-contribution
    solution, so it is both the best available starting point and, in that case,
    the answer itself. Maillard, Roncalli and Teiletche (2010), "The Properties
    of Equally Weighted Risk Contribution Portfolios", *Journal of Portfolio
    Management* 36(4), 60-70, section 3.
    """
    variances = np.diag(s)
    if not np.all(np.isfinite(variances)) or np.any(variances <= 0):
        return None
    weights = 1.0 / np.sqrt(variances)
    weights = weights / weights.sum()
    lower = np.array([low for low, _ in bounds])
    upper = np.array([high for _, high in bounds])
    if np.any(weights < lower - 1e-12) or np.any(weights > upper + 1e-12):
        return None
    return np.asarray(weights, dtype="float64")


def _risk_parity(
    s: np.ndarray,
    bounds: list[tuple[float, float]],
    sum_to_one: list[dict[str, object]],
    x0: np.ndarray,
    solve: Callable[..., tuple[np.ndarray, bool, str]],
) -> np.ndarray:
    n = s.shape[0]

    def objective(w: np.ndarray) -> float:
        total = float(w @ s @ w)
        if total <= 0:
            return 1e6
        rc = w * (s @ w) / total
        return float(np.sum((rc - 1.0 / n) ** 2)) * 1e4

    def gradient(w: np.ndarray) -> np.ndarray:
        product = s @ w
        total = float(w @ product)
        if total <= 0:
            return np.zeros(n)
        numerator = w * product
        jac = (np.diag(product) + w[:, None] * s) / total - np.outer(
            numerator, 2.0 * product
        ) / total**2
        return np.asarray(2e4 * jac.T @ (numerator / total - 1.0 / n), dtype="float64")

    w, ok, msg = solve(objective, x0, bounds, sum_to_one, gradient)
    if ok:
        return w

    # SLSQP's QP subproblem reports "Inequality constraints incompatible" from
    # some starting points when one asset's variance is far below the others --
    # a conditioning failure, not a bad gradient, which matches finite
    # differences to ~3e-9. Retrying from the inverse-volatility weights fixes
    # it: that point is the exact solution for a diagonal covariance and a much
    # better-conditioned start otherwise. Deterministic, so reproducibility holds.
    retry = _inverse_volatility_start(s, bounds)
    if retry is not None and not np.allclose(retry, x0):
        w, ok, retry_msg = solve(objective, retry, bounds, sum_to_one, gradient)
        if ok:
            return w
        msg = f"{msg}; from inverse-volatility weights: {retry_msg}"
    raise OptimizationError(f"risk_parity did not converge: {msg}")


def efficient_frontier(
    mu: pd.Series,
    sigma: pd.DataFrame,
    n_points: int = 50,
    constraints: Constraints | None = None,
    *,
    risk_free: float = 0.0,
    seed: int = 0,
    progress: Callable[[int, int], None] | None = None,
    solver: Solver | None = None,
) -> Frontier:
    """``n_points`` portfolios from the min-variance return to the max attainable.

    The minimum-variance and maximum-Sharpe portfolios are flagged. Sorted by
    expected return, volatility is non-decreasing on the efficient portion —
    the invariant that catches a broken solver.
    """
    if n_points < 2 or n_points > 500:
        raise UsageError("the frontier needs 2 to 500 points")
    cons = constraints or Constraints()
    min_var = optimize(
        mu,
        sigma,
        "min_variance",
        cons,
        risk_free=risk_free,
        explicit_max_weight=True,
        solver=solver,
    )
    max_sharpe = optimize(
        mu,
        sigma,
        "max_sharpe",
        cons,
        risk_free=risk_free,
        seed=seed,
        explicit_max_weight=True,
        solver=solver,
    )
    bounds = cons.bounds(len(mu))
    top = max_attainable_return(mu.to_numpy(dtype="float64"), bounds)
    named = [min_var.expected_return, max_sharpe.expected_return]
    if n_points >= 3 or abs(named[0] - named[1]) < 1e-10:
        named.append(top)
    targets: list[float] = []
    for value in sorted(named):
        if not targets or abs(value - targets[-1]) > 1e-10:
            targets.append(value)
    while len(targets) < n_points:
        if len(targets) == 1:
            targets.append(targets[0])
        else:
            widths = np.diff(targets)
            i = int(np.argmax(widths))
            targets.insert(i + 1, (targets[i] + targets[i + 1]) / 2.0)
    points: list[FrontierPoint] = []
    previous: np.ndarray | None = None
    flagged_min = flagged_sharpe = False
    for target in targets:
        is_min = abs(target - min_var.expected_return) < 1e-10
        is_sharpe = abs(target - max_sharpe.expected_return) < 1e-10
        if is_min:
            p = min_var
        elif is_sharpe:
            p = max_sharpe
        else:
            p = optimize(
                mu,
                sigma,
                "target_return",
                cons,
                risk_free=risk_free,
                target=float(target),
                explicit_max_weight=True,
                solver=solver,
                initial=previous,
            )
        previous = np.array([p.weights[a] for a in mu.index])
        points.append(
            FrontierPoint(
                p.expected_return,
                p.volatility,
                p.sharpe,
                p.weights,
                is_min and not flagged_min,
                is_sharpe and not flagged_sharpe,
            )
        )
        flagged_min |= is_min
        flagged_sharpe |= is_sharpe
        if progress is not None:
            progress(len(points), n_points)
    return Frontier(points=tuple(points), estimators=min_var.estimators, risk_free=risk_free)
