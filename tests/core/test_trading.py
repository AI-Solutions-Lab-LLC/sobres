"""Execution accounting against hand-computed answers.

Scenarios: Known allocation; Holdings and pending orders reduce the delta;
Insufficient funds or unusable quote; Unsupported capability fails before side
effects; Known P&L; Plan must match.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sobres.core import trading as tr
from sobres.core.errors import UsageError

NOW = datetime(2026, 9, 16, 20, 0, tzinfo=UTC)


def _quotes(**prices: float) -> dict[str, tr.QuoteSnapshot]:
    return {s: tr.QuoteSnapshot(s, p, NOW - timedelta(seconds=2)) for s, p in prices.items()}


def test_known_allocation_sixty_forty() -> None:
    """Scenario: Known allocation."""
    plan = tr.size_orders(
        {"AAPL": 0.6, "MSFT": 0.4}, 1000.0, _quotes(AAPL=100.0, MSFT=50.0), now=NOW
    )
    assert [(o.symbol, o.side, o.quantity) for o in plan.orders] == [
        ("AAPL", "buy", 6.0),
        ("MSFT", "buy", 8.0),
    ]
    assert plan.residual_cash == pytest.approx(0.0)
    assert plan.buy_notional == pytest.approx(1000.0) and plan.sell_notional == 0.0
    assert plan.orders[0].target_value == 600.0 and plan.orders[0].drift == pytest.approx(0.0)
    assert plan.quotes_as_of == NOW - timedelta(seconds=2)
    assert plan.skipped == []
    # Whole shares: 0.6 x 1000 / 101 = 5.94 -> 5 shares, and the 95 stays as residual, visibly.
    rounded = tr.size_orders(
        {"AAPL": 0.6, "MSFT": 0.4}, 1000.0, _quotes(AAPL=101.0, MSFT=50.0), now=NOW
    )
    assert rounded.orders[0].quantity == 5.0
    assert rounded.residual_cash == pytest.approx(1000.0 - 505.0 - 400.0)
    assert rounded.orders[0].drift == pytest.approx(505.0 / 1000.0 - 0.6)
    fractional = tr.size_orders(
        {"AAPL": 0.6, "MSFT": 0.4}, 1000.0, _quotes(AAPL=101.0, MSFT=50.0), fractional=True, now=NOW
    )
    assert fractional.orders[0].quantity == pytest.approx(600.0 / 101.0, abs=1e-6)  # 1e-6 precision


def test_holdings_and_pending_orders_reduce_the_delta() -> None:
    """Scenario: Holdings and pending orders reduce the delta."""
    quotes = _quotes(AAPL=100.0, MSFT=50.0)
    plan = tr.size_orders(
        {"AAPL": 0.6, "MSFT": 0.4},
        1000.0,
        quotes,
        holdings=[tr.Holding("AAPL", 2.0, 90.0)],
        pending=[tr.PendingOrder("MSFT", "buy", 3.0)],
        now=NOW,
    )
    by = {o.symbol: o for o in plan.orders}
    assert by["AAPL"].quantity == 4.0 and by["AAPL"].current_value == 200.0  # 600 - 200 held
    assert by["MSFT"].quantity == 5.0  # 400 - 150 pending
    assert by["AAPL"].resulting_weight == pytest.approx(0.6)
    # Over-target holdings are sold down, never ignored.
    sell = tr.size_orders(
        {"AAPL": 0.6, "MSFT": 0.4},
        1000.0,
        quotes,
        holdings=[tr.Holding("AAPL", 10.0, 90.0)],
        now=NOW,
    )
    aapl = next(o for o in sell.orders if o.symbol == "AAPL")
    assert aapl.side == "sell" and aapl.quantity == 4.0
    exact = tr.size_orders(
        {"AAPL": 1.0}, 600.0, _quotes(AAPL=100.0), holdings=[tr.Holding("AAPL", 6.0, 90.0)], now=NOW
    )
    assert exact.orders == [] and exact.skipped == []  # already on target: nothing to do


def test_insufficient_funds_and_unusable_quotes_fail_before_anything() -> None:
    """Scenario: Insufficient funds or unusable quote."""
    quotes = _quotes(AAPL=100.0, MSFT=50.0)
    with pytest.raises(UsageError, match="cash"):
        tr.size_orders({"AAPL": 0.6, "MSFT": 0.4}, 1000.0, quotes, cash_available=500.0, now=NOW)
    with pytest.raises(UsageError, match="no quote for MSFT"):
        tr.size_orders({"AAPL": 0.6, "MSFT": 0.4}, 1000.0, _quotes(AAPL=100.0), now=NOW)
    with pytest.raises(UsageError, match=r"quote is 0\.0"):
        tr.size_orders({"AAPL": 1.0}, 1000.0, _quotes(AAPL=0.0), now=NOW)
    stale = {"AAPL": tr.QuoteSnapshot("AAPL", 100.0, NOW - timedelta(minutes=6))}
    with pytest.raises(UsageError, match="stale"):
        tr.size_orders({"AAPL": 1.0}, 1000.0, stale, now=NOW)
    with pytest.raises(UsageError, match="positive"):
        tr.size_orders({"AAPL": 1.0}, 0.0, quotes, now=NOW)
    with pytest.raises(UsageError, match="sum to"):
        tr.size_orders({"AAPL": 0.5, "MSFT": 0.4}, 1000.0, quotes, now=NOW)
    with pytest.raises(UsageError, match="no weights"):
        tr.size_orders({}, 1000.0, quotes, now=NOW)


def test_fingerprint_changes_with_quotes_and_holdings() -> None:
    """Scenario: Plan must match."""
    a = tr.size_orders({"AAPL": 1.0}, 1000.0, _quotes(AAPL=100.0), now=NOW)
    b = tr.size_orders({"AAPL": 1.0}, 1000.0, _quotes(AAPL=100.0), now=NOW)
    key = {"account_id": "A1", "environment": "paper", "broker": "fake"}
    assert a.fingerprint(**key) == b.fingerprint(**key)
    moved = tr.size_orders({"AAPL": 1.0}, 1000.0, _quotes(AAPL=101.0), now=NOW)
    assert moved.fingerprint(**key) != a.fingerprint(**key)
    held = tr.size_orders(
        {"AAPL": 1.0},
        1000.0,
        _quotes(AAPL=100.0),
        holdings=[tr.Holding("AAPL", 1.0, 99.0)],
        now=NOW,
    )
    assert held.fingerprint(**key) != a.fingerprint(**key)
    assert a.fingerprint(account_id="A2", environment="paper", broker="fake") != a.fingerprint(
        **key
    )
    assert a.fingerprint(account_id="A1", environment="live", broker="fake") != a.fingerprint(**key)


def test_known_pnl_under_average_cost_and_deposits_are_not_profit() -> None:
    """Scenario: Known P&L."""
    t0 = NOW
    fills = [
        tr.FillLike("AAPL", "buy", 10.0, 100.0, t0),
        tr.FillLike("AAPL", "sell", 4.0, 110.0, t0 + timedelta(days=1)),
    ]
    ledger = tr.average_cost_ledger(fills)
    assert ledger.realized == {"AAPL": pytest.approx(40.0)} and ledger.realized_total == 40.0
    assert (
        ledger.positions["AAPL"].quantity == 6.0 and ledger.positions["AAPL"].average_cost == 100.0
    )
    assert tr.unrealized_pnl(ledger.positions, {"AAPL": 105.0}) == {"AAPL": pytest.approx(30.0)}
    # Average cost after a second buy: (6 x 100 + 4 x 120) / 10 = 108
    more = tr.average_cost_ledger(
        [*fills, tr.FillLike("AAPL", "buy", 4.0, 120.0, t0 + timedelta(days=2))]
    )
    assert more.positions["AAPL"].average_cost == pytest.approx(108.0)
    with pytest.raises(UsageError, match="exceeds"):
        tr.average_cost_ledger([tr.FillLike("AAPL", "sell", 1.0, 100.0, t0)])
    with pytest.raises(UsageError, match="no mark"):
        tr.unrealized_pnl(ledger.positions, {})
    # A 1,000 deposit between two observations of a flat account is not a return.
    equity = [
        tr.EquityPoint(t0, 10_000.0),
        tr.EquityPoint(t0 + timedelta(days=1), 11_000.0),
        tr.EquityPoint(t0 + timedelta(days=2), 11_550.0),
    ]
    flows = [tr.ExternalFlow(t0 + timedelta(days=1), 1_000.0)]
    total, subs = tr.time_weighted_return(equity, flows)
    assert subs[0] == pytest.approx(0.0) and subs[1] == pytest.approx(0.05)
    assert total == pytest.approx(0.05)
    naive_total, _ = tr.time_weighted_return(equity, [])
    assert naive_total == pytest.approx(0.155)  # what counting the deposit as profit would claim
    with pytest.raises(UsageError):
        tr.time_weighted_return(equity[:1], [])
    assert tr.max_drawdown_of_equity(
        [
            tr.EquityPoint(t0, 100.0),
            tr.EquityPoint(t0 + timedelta(days=1), 80.0),
            tr.EquityPoint(t0 + timedelta(days=2), 90.0),
        ]
    ) == pytest.approx(-0.2)
    assert tr.max_drawdown_of_equity(equity) == 0.0
