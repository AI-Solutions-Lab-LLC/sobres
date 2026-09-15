"""Independent regression evidence for the PR 8 corrections.

Scenarios: Initial capital is part of drawdown; Public analytics reject unresolved gaps;
Public optimizer validates covariance; Exact frontier size; Cash-inclusive entry costs;
Risk-free observations precede decisions; Consistent risk ratios; Solver port conformance.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from sobres.core.backtest import walk_forward
from sobres.core.errors import UsageError
from sobres.core.moments import covariance, expected_returns
from sobres.core.optimize import efficient_frontier, optimize
from sobres.core.rates import prior_rates, treasury_investment_yield
from sobres.core.returns import annualized_return, portfolio_returns
from sobres.core.risk import max_drawdown, risk_metrics
from sobres.solvers.scipy import ScipySolver


def test_initial_loss_and_initial_fee_are_drawdowns() -> None:
    index = pd.bdate_range("2020-01-01", periods=3)
    result = max_drawdown(pd.Series([-0.5, 0.1, 0.1], index=index))
    assert result.max_drawdown == -0.5
    assert result.peak is None and result.trough == index[0].date()
    assert result.recovery is None
    recovered = max_drawdown(pd.Series([-0.5, 1.0, 0.0], index=index))
    assert recovered.recovery == index[1].date()
    fee = max_drawdown(pd.Series([-0.001, 0.0, 0.0], index=index))
    assert fee.max_drawdown == pytest.approx(-0.001)


def test_consistent_arithmetic_sharpe_and_rms_sortino() -> None:
    returns = pd.Series([0.2, -0.1, 0.0], index=pd.date_range("2020-01-31", periods=3, freq="ME"))
    panel = risk_metrics(returns, 0.12, "monthly")
    # Monthly excess = .19, -.11, -.01; mean = .023333..., sample std = sqrt(.023333...).
    mean = (0.19 - 0.11 - 0.01) / 3
    std = math.sqrt(sum((r - mean) ** 2 for r in [0.19, -0.11, -0.01]) / 2)
    assert panel.sharpe == pytest.approx(mean / std * math.sqrt(12))
    assert panel.sortino == pytest.approx(0.28 / math.sqrt(0.01 / 3 * 12))
    assert panel.annualized_return == pytest.approx((1.2 * 0.9) ** 4 - 1)
    assert panel.arithmetic_return == pytest.approx(0.4)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -np.inf])
def test_public_analytics_reject_unresolved_gaps(bad: float) -> None:
    returns = pd.DataFrame(
        {"A": [0.01, bad, 0.03, 0.01]}, index=pd.bdate_range("2020-01-01", periods=4)
    )
    for call in [
        lambda: portfolio_returns(returns, {"A": 1.0}),
        lambda: expected_returns(returns, "daily"),
        lambda: covariance(returns, "daily"),
        lambda: annualized_return(returns.A, "daily"),
        lambda: risk_metrics(returns.A, 0.0, "daily"),
        lambda: walk_forward(
            returns, lambda w: pd.Series({"A": 1.0}), frequency="daily", lookback=2
        ),
    ]:
        with pytest.raises(UsageError, match="missing or non-finite"):
            call()


def test_public_optimizer_conditions_indefinite_covariance() -> None:
    mu = pd.Series({"A": 0.08, "B": 0.13})
    sigma = pd.DataFrame([[1.0, 2.0], [2.0, 1.0]], index=mu.index, columns=mu.index)
    result = optimize(mu, sigma, "min_variance")
    assert result.estimators.psd_repair is not None
    assert result.estimators.psd_repair["min_eigenvalue"] == -1
    assert sum(result.weights.values()) == pytest.approx(1)
    with pytest.raises(UsageError, match="non-finite"):
        optimize(mu, sigma * np.nan)
    with pytest.raises(UsageError, match="labels"):
        optimize(mu, sigma.rename(columns={"A": "C"}))


@pytest.mark.parametrize("count", [2, 3, 5, 50])
@pytest.mark.parametrize("equal_means", [False, True])
def test_exact_frontier_size_and_named_points(count: int, equal_means: bool) -> None:
    mu = pd.Series({"A": 0.08, "B": 0.08 if equal_means else 0.13})
    sigma = pd.DataFrame([[0.0144, 0.0072], [0.0072, 0.04]], index=mu.index, columns=mu.index)
    progress = []
    result = efficient_frontier(
        mu, sigma, count, progress=lambda done, total: progress.append((done, total))
    )
    assert len(result.points) == count
    assert sum(p.is_min_variance for p in result.points) == 1
    assert sum(p.is_max_sharpe for p in result.points) == 1
    assert progress[-1] == (count, count)
    for point in result.points:
        assert sum(point.weights.values()) == pytest.approx(1, abs=1e-8)


def test_cash_entry_and_paid_cost_use_actual_wealth() -> None:
    index = pd.bdate_range("2020-01-28", periods=6)
    returns = pd.DataFrame(0.0, index=index, columns=["A", "B"])

    def rotating(window: pd.DataFrame) -> pd.Series:
        return pd.Series(
            {"A": 1.0, "B": 0.0}
            if window.index[-1].month == 1 and window.index[-1].day < 31
            else {"A": 0.0, "B": 1.0}
        )

    result = walk_forward(returns, rotating, frequency="daily", rebalance="monthly", lookback=2)
    assert result.total_turnover == 2
    assert result.total_cost_rate == pytest.approx(0.002)
    assert result.total_cost == pytest.approx(0.001 + 0.999 * 0.001)
    assert result.equity_curve.iloc[-1] == pytest.approx(0.999**2)
    assert result.strategy.max_drawdown == pytest.approx(-(0.001 + 0.999 * 0.001))


def test_rates_are_strictly_prior_and_discount_quote_is_converted() -> None:
    dates = pd.bdate_range("2020-01-01", periods=3)
    rates = pd.Series([0.01, 0.99, 0.5], index=dates)
    assert prior_rates(rates, dates).tolist() == [0.0, 0.01, 0.99]
    # Face 100, 91-day discount at 5% => price 98.736111..., 365-day simple yield.
    converted = treasury_investment_yield(pd.Series([0.05]))
    assert converted.iloc[0] == pytest.approx(0.05 * 365 / (360 - 0.05 * 91))


def test_solver_port_conformance() -> None:
    solver = ScipySolver()
    # Minimum of (x-.2)^2 + (y-.8)^2 with x+y=1, bounded at x>=.3.
    solution = solver.solve(
        lambda w: float((w[0] - 0.2) ** 2 + (w[1] - 0.8) ** 2),
        np.array([0.5, 0.5]),
        [(0.3, 1.0), (0.0, 1.0)],
        [{"type": "eq", "fun": lambda w: float(w.sum() - 1)}],
        lambda w: 2 * (w - np.array([0.2, 0.8])),
    )
    assert solution.success
    np.testing.assert_allclose(solution.weights, [0.3, 0.7], atol=1e-8)
    assert solution.evaluations > 0
    impossible = solver.solve(
        lambda w: float(w @ w),
        np.array([0.5, 0.5]),
        [(0.0, 0.1), (0.0, 0.1)],
        [{"type": "eq", "fun": lambda w: float(w.sum() - 1)}],
    )
    assert not impossible.success and impossible.message
