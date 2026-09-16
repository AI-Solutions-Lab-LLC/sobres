"""The broker port: what "a supported broker" means, in Sobres' own types.

Every adapter implements ``Broker`` with these owned request/result models and
raises the shared error taxonomy. A vendor's objects, enums and exceptions stop
at its adapter. Capabilities are declared, not discovered by failing: the
application checks ``BrokerCapabilities`` before any side effect.

Quantities and money are floats in the account currency, rounded to whole shares
unless the broker declares fractional support; timestamps are UTC.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol

Side = Literal["buy", "sell"]
OrderStatus = Literal[
    "new",
    "accepted",
    "partially_filled",
    "filled",
    "cancelled",
    "rejected",
    "expired",
    "unresolved",
]
ORDER_STATUSES: tuple[str, ...] = (
    "new",
    "accepted",
    "partially_filled",
    "filled",
    "cancelled",
    "rejected",
    "expired",
    "unresolved",
)
TERMINAL_ORDER_STATUSES: frozenset[str] = frozenset({"filled", "cancelled", "rejected", "expired"})
Environment = Literal["paper", "live"]
ENVIRONMENTS: tuple[str, ...] = ("paper", "live")


@dataclass(frozen=True)
class BrokerCapabilities:
    name: str
    environments: tuple[str, ...]
    fractional_shares: bool
    order_types: tuple[str, ...] = ("market",)
    time_in_force: tuple[str, ...] = ("day",)
    close_position: bool = True
    activities: bool = True


@dataclass(frozen=True)
class BrokerAccount:
    id: str
    environment: str
    currency: str
    cash: float
    buying_power: float
    equity: float
    as_of: datetime


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: float
    as_of: datetime
    source: str = "broker"


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    quantity: float
    average_cost: float
    current_price: float
    market_value: float
    unrealized_pl: float
    currency: str = "USD"


@dataclass(frozen=True)
class OrderRequest:
    client_order_id: str
    symbol: str
    side: Side
    quantity: float
    order_type: str = "market"
    time_in_force: str = "day"


@dataclass(frozen=True)
class BrokerOrder:
    id: str
    client_order_id: str
    symbol: str
    side: str
    quantity: float
    filled_quantity: float
    filled_avg_price: float | None
    status: str
    submitted_at: datetime | None
    updated_at: datetime | None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def terminal(self) -> bool:
        return self.status in TERMINAL_ORDER_STATUSES


@dataclass(frozen=True)
class Fill:
    order_id: str
    """The broker's order id."""
    symbol: str
    side: str
    quantity: float
    price: float
    at: datetime
    source: str = "broker"
    """``broker`` for a fill the broker reported; ``external`` when no Sobres order matches."""


@dataclass(frozen=True)
class CashFlow:
    at: datetime
    amount: float
    """Positive for a deposit, negative for a withdrawal, in the account currency."""
    kind: str


class SubmissionUnresolvedError(Exception):
    """The request may have reached the broker but no answer came back (timeout, reset).

    The order is neither failed nor filled; only a later lookup by client order id
    can say. Adapters raise this — never a plain provider error — for that case.
    """

    def __init__(self, client_order_id: str, reason: str) -> None:
        super().__init__(f"submission of {client_order_id} is unresolved: {reason}")
        self.client_order_id = client_order_id
        self.reason = reason


class Broker(Protocol):
    name: str
    environment: str

    @property
    def capabilities(self) -> BrokerCapabilities: ...

    def account(self) -> BrokerAccount: ...

    def positions(self) -> list[BrokerPosition]: ...

    def quotes(self, symbols: Sequence[str]) -> dict[str, Quote]: ...

    def submit_order(self, request: OrderRequest) -> BrokerOrder:
        """Raise ``SubmissionUnresolvedError`` when the outcome is unknown."""
        ...

    def get_order(self, broker_order_id: str) -> BrokerOrder | None: ...

    def find_order(self, client_order_id: str) -> BrokerOrder | None: ...

    def cancel_order(self, broker_order_id: str) -> BrokerOrder: ...

    def fills(self, since: datetime | None = None) -> list[Fill]: ...

    def cash_flows(self, since: datetime | None = None) -> list[CashFlow]: ...
