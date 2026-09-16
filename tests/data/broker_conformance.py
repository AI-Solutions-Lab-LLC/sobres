"""The shared broker conformance suite: what "a supported broker" means.

Parametrized over adapters in ``test_brokers.py`` (the fake broker and the
Alpaca adapter on the synthetic fixture source). It walks the workflow the
application relies on — account, quotes, positions, submit, look up by both
ids, fills, cash flows, cancel — in the owned vocabulary, so a future adapter
is one more entry there.

Scenarios: Adapter replacement.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sobres.data.brokers.base import (
    ORDER_STATUSES,
    Broker,
    BrokerAccount,
    BrokerCapabilities,
    BrokerOrder,
    OrderRequest,
)


class BrokerConformance:
    """Every method returns owned types with the same semantics on every adapter."""

    def test_account_and_capabilities(self, broker: Broker) -> None:
        caps = broker.capabilities
        assert isinstance(caps, BrokerCapabilities) and caps.name == broker.name
        assert broker.environment in caps.environments
        account = broker.account()
        assert isinstance(account, BrokerAccount)
        assert account.environment == broker.environment and account.currency == "USD"
        assert account.cash > 0 and account.as_of.tzinfo is not None

    def test_quotes_are_timestamped_and_unknown_symbols_fail(self, broker: Broker) -> None:
        quotes = broker.quotes(["AAPL", "msft"])
        assert set(quotes) == {"AAPL", "MSFT"}
        for q in quotes.values():
            assert q.price > 0 and q.as_of.tzinfo is not None and q.source == broker.name
        with pytest.raises(Exception, match=r"(?i)quote|trade|symbol"):
            broker.quotes(["NOPE"])

    def test_submit_fill_position_close_and_history(self, broker: Broker) -> None:
        """Scenario: Adapter replacement."""
        assert broker.positions() == []
        price = broker.quotes(["AAPL"])["AAPL"].price
        buy = broker.submit_order(OrderRequest("conf-buy-1", "AAPL", "buy", 6.0))
        assert isinstance(buy, BrokerOrder) and buy.status in ORDER_STATUSES
        assert buy.client_order_id == "conf-buy-1" and buy.symbol == "AAPL"
        assert buy.quantity == 6.0 and buy.submitted_at is not None
        by_id = broker.get_order(buy.id)
        by_client = broker.find_order("conf-buy-1")
        assert by_id is not None and by_client is not None and by_id.id == by_client.id == buy.id
        assert broker.get_order("no-such-order") is None
        assert broker.find_order("no-such-client-id") is None
        # The fixture and fake brokers fill market orders at once.
        assert by_id.status == "filled" and by_id.filled_quantity == 6.0
        assert by_id.filled_avg_price == pytest.approx(price)
        positions = broker.positions()
        assert [p.symbol for p in positions] == ["AAPL"]
        assert positions[0].quantity == 6.0 and positions[0].average_cost == pytest.approx(price)
        assert positions[0].market_value == pytest.approx(6.0 * positions[0].current_price)
        sell = broker.submit_order(OrderRequest("conf-sell-1", "AAPL", "sell", 4.0))
        assert sell.status == "filled" and sell.filled_quantity == 4.0
        assert broker.positions()[0].quantity == 2.0
        fills = broker.fills()
        assert [(f.symbol, f.side, f.quantity) for f in fills] == [
            ("AAPL", "buy", 6.0),
            ("AAPL", "sell", 4.0),
        ]
        assert all(f.at.tzinfo is not None and f.order_id for f in fills)
        assert broker.fills(since=datetime(2100, 1, 1, tzinfo=UTC)) == []
        assert isinstance(broker.cash_flows(), list)
        with pytest.raises(Exception, match=r"(?i)unique|already"):
            broker.submit_order(OrderRequest("conf-buy-1", "AAPL", "buy", 1.0))

    def test_unsupported_capability_fails_before_side_effects(self, broker: Broker) -> None:
        """Scenario: Unsupported capability fails before side effects."""
        if broker.capabilities.fractional_shares:
            pytest.skip("this adapter supports fractional shares")
        before = len(broker.fills())
        with pytest.raises(Exception, match=r"(?i)fraction|whole"):
            broker.submit_order(OrderRequest("conf-frac", "AAPL", "buy", 1.5))
        assert len(broker.fills()) == before and broker.find_order("conf-frac") is None

    def test_rejections_are_reported_not_raised(self, broker: Broker) -> None:
        too_many = broker.submit_order(OrderRequest("conf-reject", "AAPL", "sell", 1_000_000.0))
        assert too_many.status == "rejected" and too_many.filled_quantity == 0.0

    def test_cancel_of_a_terminal_order_is_reported_as_is(self, broker: Broker) -> None:
        order = broker.submit_order(OrderRequest("conf-cancel", "MSFT", "buy", 1.0))
        cancelled = broker.cancel_order(order.id)
        assert cancelled.id == order.id and cancelled.status == "filled"  # already done
