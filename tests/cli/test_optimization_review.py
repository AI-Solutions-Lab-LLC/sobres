"""Adapter regressions independent of the original happy-path assertions.

Scenarios: Future rates cannot change past allocations; Dropped prices do not bridge periods;
CAPM benchmark input; Target backtests; Validate before downloading; Typed risk presentation;
Backtest decision provenance; Bounded optimization work.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import numpy as np
import pandas as pd
import pytest

from sobres.cli.commands.optimize import BacktestParams, UniverseParams, backtest, load_universe
from sobres.cli.context import Context


def context(prices: pd.DataFrame, rates: pd.DataFrame | None = None) -> Any:
    return SimpleNamespace(
        price_provider=lambda: SimpleNamespace(get_prices=lambda *a: prices.copy()),
        macro_provider=lambda: SimpleNamespace(get_series=lambda *a: rates),
        config={"fred_api_key": "REVIEW-DUMMY-KEY"},
        log=Mock(),
        note=Mock(),
    )


def test_future_rates_cannot_change_past_allocations() -> None:
    index = pd.bdate_range("2020-01-01", periods=180)
    rng = np.random.default_rng(123)
    returns = rng.normal([0.0004, 0.0007], [0.01, 0.02], (180, 2))
    prices = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=index, columns=["A", "B"])
    prices.attrs = {"currency": {"A": "USD", "B": "USD"}, "provider": "synthetic"}
    start = index[100].date()
    params = BacktestParams(
        tickers=["A", "B"],
        start=start,
        end=index[-1].date(),
        fill="raise",
        lookback="60",
        rebalance="monthly",
    )
    results = []
    for future in [0.0, 20.0]:
        rates = pd.DataFrame({"DTB3": np.where(index.date >= start, future, 0.0)}, index=index)
        results.append(backtest(params, context(prices, rates)))
    first = min(results[0].weights_history)
    assert results[0].weights_history[first] == results[1].weights_history[first]
    assert results[0].decisions[0]["risk_free"] == results[1].decisions[0]["risk_free"] == 0.0
    assert all(d["training_end"] < d["trade_date"] for d in results[0].decisions)
    assert results[0].settings["seed"] == 0


def test_dropped_prices_do_not_bridge_daily_intervals() -> None:
    index = pd.bdate_range("2020-01-01", periods=8)
    prices = pd.DataFrame(
        {"A": [100, 110, np.nan, 133.1, 146.41, 161.051, 177.1561, 194.87171]}, index=index
    )
    prices.attrs = {"currency": "USD", "provider": "synthetic"}
    params = UniverseParams(
        tickers=["A"], start=index[0].date(), end=index[-1].date(), fill="drop", risk_free=0
    )
    result = load_universe(params, context(prices))
    np.testing.assert_allclose(result.returns.A, 0.1, atol=1e-12)
    assert len(result.returns) == 5 and result.frequency == "daily"
    assert index[2] not in result.returns.index and index[3] not in result.returns.index
    assert "2020-01-03" in " ".join(result.provenance.notes)


@pytest.mark.parametrize("objective,target", [("target_return", 0.35), ("target_risk", 0.5)])
def test_target_backtests_run_end_to_end(objective: str, target: float) -> None:
    index = pd.bdate_range("2020-01-01", periods=120)
    wiggle = np.tile([-0.0001, 0.0001], 60)
    returns = np.column_stack([0.001 + wiggle, 0.002 - wiggle])
    prices = pd.DataFrame(100 * np.cumprod(1 + returns, axis=0), index=index, columns=["A", "B"])
    prices.attrs = {"currency": "USD", "provider": "synthetic"}
    params = BacktestParams(
        tickers=["A", "B"],
        start=index[60].date(),
        end=index[-1].date(),
        fill="raise",
        lookback="20",
        objective=objective,
        target=target,
        risk_free=0,
    )
    result = backtest(params, context(prices))
    assert result.n_rebalances >= 1
    assert result.settings["target"] == target
    assert result.oos_start == str(index[60].date())


@pytest.mark.parametrize(
    "command,extra",
    [("markowitz", []), ("frontier", ["--points", "3"]), ("backtest", ["--lookback", "60"])],
)
def test_capm_benchmark_through_generated_cli(
    cli: Callable[..., Any], command: str, extra: list[str]
) -> None:
    result = cli(
        "optimize",
        command,
        "--tickers",
        "AAPL",
        "MSFT",
        "--start",
        "2019-01-01",
        "--end",
        "2020-12-31",
        "--fill",
        "ffill",
        "--risk-free",
        "0.02",
        "--returns-estimator",
        "capm",
        "--benchmark",
        "JNJ",
        "--format",
        "json",
        *extra,
    )
    assert result.exit_code == 0, result.stderr
    doc = json.loads(result.stdout)
    assert (
        doc["estimators"]["expected_return"] == "capm"
        if command != "backtest"
        else doc["settings"]["benchmark"] == "JNJ"
    )


@pytest.mark.parametrize(
    "command,extra",
    [
        ("markowitz", ["--seed", "-1"]),
        ("markowitz", ["--risk-free", "nan"]),
        ("markowitz", ["--returns-estimator", "capm"]),
        ("markowitz", ["--max-weight", "0.1"]),
        ("backtest", ["--objective", "target_return"]),
        ("backtest", ["--lookback", "-1"]),
        ("backtest", ["--lookback", "99999y"]),
        ("risk", ["--weights", "nan", "nan"]),
    ],
)
def test_validate_before_downloading(
    cli: Callable[..., Any], monkeypatch: pytest.MonkeyPatch, command: str, extra: list[str]
) -> None:
    def fail(*args: Any) -> Any:
        raise AssertionError("invalid input must never reach a provider")

    monkeypatch.setattr(Context, "price_provider", fail)
    result = cli(
        "optimize",
        command,
        "--tickers",
        "AAPL",
        "MSFT",
        "--start",
        "2020-01-01",
        "--end",
        "2020-12-31",
        "--fill",
        "raise",
        *extra,
    )
    assert result.exit_code == 2, result.stderr


def test_risk_table_labels_units_and_keeps_json_numeric(cli: Callable[..., Any]) -> None:
    args = [
        "optimize",
        "risk",
        "--tickers",
        "AAPL",
        "MSFT",
        "--weights",
        "0.6",
        "0.4",
        "--start",
        "2019-01-01",
        "--end",
        "2020-12-31",
        "--fill",
        "ffill",
        "--risk-free",
        "0",
    ]
    table = cli(*args, "--format", "table")
    assert table.exit_code == 0 and "%" in table.stdout and "unitless" in table.stdout
    doc = json.loads(cli(*args, "--format", "json").stdout)
    metrics = {r["metric"]: r["value"] for r in doc["rows"]}
    assert isinstance(metrics["sharpe"], float) and isinstance(metrics["n_obs"], int)
