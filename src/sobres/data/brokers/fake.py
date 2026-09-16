"""``FakeBroker``: a deterministic in-memory broker for tests, conformance and demos.

It fills market orders immediately at the quotes it was given (a configurable
partial fill and a submission-timeout switch let tests exercise the honest
lifecycle), keeps positions with average cost, and reports fills and cash flows.
It is an adapter like any other: the application cannot tell it from a vendor.
"""

from __future__ import annotations

import itertools
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from sobres.core.errors import ProviderError, UsageError
from sobres.data.brokers.base import (
    BrokerAccount,
    BrokerCapabilities,
    BrokerOrder,
    BrokerPosition,
    CashFlow,
    Fill,
    OrderRequest,
    Quote,
    SubmissionUnresolvedError,
)


class FakeBroker:
    name = "fake"

    def __init__(
        self,
        quotes: dict[str, float],
        *,
        cash: float = 100_000.0,
        environment: str = "paper",
        account_id: str = "FAKE-PAPER-1",
        currency: str = "USD",
        fractional: bool = False,
        clock: datetime | None = None,
        partial_fill_symbols: dict[str, float] | None = None,
    ) -> None:
        self.environment = environment
        self._quotes = dict(quotes)
        self._cash = cash
        self._account_id = account_id
        self._currency = currency
        self._fractional = fractional
        self._now = clock or datetime(2026, 9, 16, 20, 0, tzinfo=UTC)
        self._partial = dict(partial_fill_symbols or {})
        self._positions: dict[str, tuple[float, float]] = {}  # symbol -> (qty, avg cost)
        self._orders: dict[str, BrokerOrder] = {}
        self._fills: list[Fill] = []
        self._flows: list[CashFlow] = []
        self._ids = itertools.count(1)
        self.timeout_next_submission = False
        """When True the next ``submit_order`` records the order and then raises
        ``SubmissionUnresolvedError`` — the request left, no answer came back."""
        self.submitted: list[OrderRequest] = []

    # ---------------------------------------------------------------- helpers
    def tick(self, seconds: float = 1.0) -> None:
        self._now = self._now + timedelta(seconds=seconds)

    def set_quote(self, symbol: str, price: float) -> None:
        self._quotes[symbol.upper()] = price

    def deposit(self, amount: float, kind: str = "deposit") -> None:
        self._cash += amount
        self._flows.append(CashFlow(self._now, amount, kind))

    def seed_position(self, symbol: str, quantity: float, average_cost: float) -> None:
        """A holding that exists outside any Sobres order (an external trade)."""
        self._positions[symbol.upper()] = (quantity, average_cost)

    @property
    def capabilities(self) -> BrokerCapabilities:
        return BrokerCapabilities(
            name=self.name, environments=("paper", "live"), fractional_shares=self._fractional
        )

    # ------------------------------------------------------------------ reads
    def account(self) -> BrokerAccount:
        equity = self._cash + sum(
            qty * self._quotes.get(sym, avg) for sym, (qty, avg) in self._positions.items()
        )
        return BrokerAccount(
            id=self._account_id,
            environment=self.environment,
            currency=self._currency,
            cash=self._cash,
            buying_power=self._cash,
            equity=equity,
            as_of=self._now,
        )

    def positions(self) -> list[BrokerPosition]:
        out = []
        for symbol, (qty, avg) in sorted(self._positions.items()):
            if qty == 0:
                continue
            price = self._quotes.get(symbol, avg)
            out.append(
                BrokerPosition(
                    symbol=symbol,
                    quantity=qty,
                    average_cost=avg,
                    current_price=price,
                    market_value=qty * price,
                    unrealized_pl=(price - avg) * qty,
                    currency=self._currency,
                )
            )
        return out

    def quotes(self, symbols: Sequence[str]) -> dict[str, Quote]:
        out: dict[str, Quote] = {}
        for symbol in symbols:
            price = self._quotes.get(symbol.upper())
            if price is None:
                raise ProviderError(
                    f"no quote for {symbol}", provider=self.name, hint="check the symbol"
                )
            out[symbol.upper()] = Quote(symbol.upper(), price, self._now, source=self.name)
        return out

    # ----------------------------------------------------------------- orders
    def submit_order(self, request: OrderRequest) -> BrokerOrder:
        symbol = request.symbol.upper()
        if any(o.client_order_id == request.client_order_id for o in self._orders.values()):
            raise UsageError(f"client order id {request.client_order_id} was already submitted")
        if not self._fractional and float(request.quantity) != int(request.quantity):
            raise UsageError(f"{self.name} does not support fractional shares ({request.quantity})")
        price = self._quotes.get(symbol)
        if price is None:
            raise UsageError(f"{symbol} is not tradable here")
        self.submitted.append(request)
        self.tick()  # every order lands at a later instant, as at a real venue
        order_id = f"fake-{next(self._ids):04d}"
        fill_qty = float(request.quantity)
        if symbol in self._partial:
            fill_qty = min(fill_qty, self._partial[symbol])
        status = "filled" if fill_qty == request.quantity else "partially_filled"
        held, avg = self._positions.get(symbol, (0.0, 0.0))
        if request.side == "buy":
            cost = fill_qty * price
            if cost > self._cash + 1e-9:
                order = self._store(request, order_id, 0.0, None, "rejected")
                return order
            self._cash -= cost
            new_qty = held + fill_qty
            new_avg = (held * avg + fill_qty * price) / new_qty if new_qty else 0.0
            self._positions[symbol] = (new_qty, new_avg)
        else:
            if fill_qty > held + 1e-9:
                return self._store(request, order_id, 0.0, None, "rejected")
            self._cash += fill_qty * price
            self._positions[symbol] = (held - fill_qty, avg)
        self._fills.append(
            Fill(order_id, symbol, request.side, fill_qty, price, self._now, source="broker")
        )
        order = self._store(request, order_id, fill_qty, price, status)
        if self.timeout_next_submission:
            self.timeout_next_submission = False
            raise SubmissionUnresolvedError(request.client_order_id, "timed out after sending")
        return order

    def _store(
        self,
        request: OrderRequest,
        order_id: str,
        filled: float,
        price: float | None,
        status: str,
    ) -> BrokerOrder:
        order = BrokerOrder(
            id=order_id,
            client_order_id=request.client_order_id,
            symbol=request.symbol.upper(),
            side=request.side,
            quantity=float(request.quantity),
            filled_quantity=filled,
            filled_avg_price=price,
            status=status,
            submitted_at=self._now,
            updated_at=self._now,
            raw={"fake": True},
        )
        self._orders[order_id] = order
        return order

    def get_order(self, broker_order_id: str) -> BrokerOrder | None:
        return self._orders.get(broker_order_id)

    def find_order(self, client_order_id: str) -> BrokerOrder | None:
        for order in self._orders.values():
            if order.client_order_id == client_order_id:
                return order
        return None

    def cancel_order(self, broker_order_id: str) -> BrokerOrder:
        order = self._orders.get(broker_order_id)
        if order is None:
            raise UsageError(f"no order {broker_order_id}")
        if order.terminal:
            return order
        cancelled = BrokerOrder(
            **{**order.__dict__, "status": "cancelled", "updated_at": self._now}
        )
        self._orders[broker_order_id] = cancelled
        return cancelled

    def fills(self, since: datetime | None = None) -> list[Fill]:
        return [f for f in self._fills if since is None or f.at >= since]

    def cash_flows(self, since: datetime | None = None) -> list[CashFlow]:
        return [f for f in self._flows if since is None or f.at >= since]
