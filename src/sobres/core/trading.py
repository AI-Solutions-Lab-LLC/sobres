"""Execution accounting: order sizing, drift, average-cost P&L, cash-flow-aware returns.

Pure functions over the owned models; no broker, no storage. The conventions:

    Sizing        target value = w · budget; delta = target - (held + pending) value;
                  whole shares floor(|delta| / price) toward the sign of delta
                  (a broker declaring fractional support rounds to 1e-6 instead).
                  Residual cash and drift are reported, never hidden.
    Realized P&L  average-cost basis: a buy updates avg = (q·avg + q'·p) / (q + q');
                  a sell realizes (p - avg) · q_sold and leaves avg unchanged
                  (a common brokerage default; tax lots are out of scope).
    Unrealized    (mark - avg) · held.
    Return        time-weighted between external cash flows (GIPS 2020 §2.A.2):
                  chain-link sub-period returns so a deposit is never profit.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sobres.core.errors import UsageError

MAX_QUOTE_AGE = timedelta(minutes=5)
FRACTIONAL_PRECISION = 6


@dataclass(frozen=True)
class Holding:
    symbol: str
    quantity: float
    average_cost: float


@dataclass(frozen=True)
class PendingOrder:
    symbol: str
    side: str
    remaining_quantity: float


@dataclass(frozen=True)
class QuoteSnapshot:
    symbol: str
    price: float
    as_of: datetime


@dataclass(frozen=True)
class PlannedOrder:
    symbol: str
    side: str
    quantity: float
    price: float
    notional: float
    target_weight: float
    target_value: float
    current_value: float
    resulting_weight: float
    drift: float
    """Resulting weight minus target weight, after this order fills at the quote."""


@dataclass(frozen=True)
class OrderPlan:
    budget: float
    orders: list[PlannedOrder]
    residual_cash: float
    quotes_as_of: datetime
    """The oldest quote used; the plan is only as fresh as that."""
    fractional: bool
    skipped: list[dict[str, object]] = field(default_factory=list)
    """Symbols whose delta rounded to zero shares, with the unfilled delta."""

    @property
    def buy_notional(self) -> float:
        return sum(o.notional for o in self.orders if o.side == "buy")

    @property
    def sell_notional(self) -> float:
        return sum(o.notional for o in self.orders if o.side == "sell")

    def fingerprint(self, *, account_id: str, environment: str, broker: str) -> str:
        """A stable hash of what would be submitted; a changed quote changes it."""
        doc = {
            "account": account_id,
            "environment": environment,
            "broker": broker,
            "budget": round(self.budget, 2),
            "orders": [
                [o.symbol, o.side, round(o.quantity, FRACTIONAL_PRECISION), round(o.price, 6)]
                for o in self.orders
            ],
            "quotes_as_of": self.quotes_as_of.isoformat(),
        }
        text = json.dumps(doc, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def size_orders(
    weights: Mapping[str, float],
    budget: float,
    quotes: Mapping[str, QuoteSnapshot],
    *,
    holdings: Sequence[Holding] = (),
    pending: Sequence[PendingOrder] = (),
    cash_available: float | None = None,
    fractional: bool = False,
    now: datetime | None = None,
    max_quote_age: timedelta = MAX_QUOTE_AGE,
) -> OrderPlan:
    """Orders that move the account toward ``weights`` with ``budget`` of new money.

    ``budget`` is the total value the portfolio should reach for these symbols
    (existing holdings count toward it); a symbol above its target is sold down.
    Nothing here has side effects.
    """
    if budget <= 0:
        raise UsageError("--budget must be positive")
    if not weights:
        raise UsageError("the portfolio has no weights", hint="save it with --weights")
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise UsageError(f"weights sum to {total:.6f}, not 1.0")
    when = now
    held = {h.symbol: h for h in holdings}
    pend: dict[str, float] = {}
    for p in pending:
        sign = 1.0 if p.side == "buy" else -1.0
        pend[p.symbol] = pend.get(p.symbol, 0.0) + sign * p.remaining_quantity
    oldest: datetime | None = None
    orders: list[PlannedOrder] = []
    skipped: list[dict[str, object]] = []
    for symbol, weight in weights.items():
        quote = quotes.get(symbol)
        if quote is None:
            raise UsageError(f"no quote for {symbol}", hint="the broker returned no price")
        if not math.isfinite(quote.price) or quote.price <= 0:
            raise UsageError(f"{symbol} quote is {quote.price}; cannot size an order")
        if when is not None and when - quote.as_of > max_quote_age:
            raise UsageError(
                f"{symbol} quote is stale ({quote.as_of.isoformat()}); "
                f"older than {int(max_quote_age.total_seconds() // 60)} minutes",
                hint="run the preview again when the market is open",
            )
        oldest = quote.as_of if oldest is None or quote.as_of < oldest else oldest
        current_qty = (held[symbol].quantity if symbol in held else 0.0) + pend.get(symbol, 0.0)
        current_value = current_qty * quote.price
        target_value = weight * budget
        delta = target_value - current_value
        raw_qty = abs(delta) / quote.price
        if fractional:
            qty = round(raw_qty, FRACTIONAL_PRECISION)
        else:
            qty = float(math.floor(raw_qty + 1e-9))
        if qty <= 0:
            if abs(delta) > 0.005:  # below one share; an exact match is not "skipped"
                skipped.append({"symbol": symbol, "unfilled_delta": round(delta, 2)})
            continue
        side = "buy" if delta > 0 else "sell"
        notional = qty * quote.price
        resulting_value = current_value + (notional if side == "buy" else -notional)
        orders.append(
            PlannedOrder(
                symbol=symbol,
                side=side,
                quantity=qty,
                price=quote.price,
                notional=notional,
                target_weight=weight,
                target_value=target_value,
                current_value=current_value,
                resulting_weight=resulting_value / budget,
                drift=resulting_value / budget - weight,
            )
        )
    buys = sum(o.notional for o in orders if o.side == "buy")
    sells = sum(o.notional for o in orders if o.side == "sell")
    held_value = sum(
        held[s].quantity * quotes[s].price for s in weights if s in held and s in quotes
    )
    new_money = budget - held_value
    if cash_available is not None and buys - sells > cash_available + 1e-9:
        raise UsageError(
            f"the plan needs {buys - sells:,.2f} of cash but {cash_available:,.2f} is available",
            hint="lower --budget or deposit first",
        )
    residual = new_money - buys + sells
    return OrderPlan(
        budget=budget,
        orders=orders,
        residual_cash=residual,
        quotes_as_of=oldest or (when or datetime.min),
        fractional=fractional,
        skipped=skipped,
    )


# --------------------------------------------------------------------------- #
# Performance
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class FillLike:
    symbol: str
    side: str
    quantity: float
    price: float
    at: datetime


@dataclass(frozen=True)
class Ledger:
    realized: dict[str, float]
    positions: dict[str, Holding]
    """Open quantity and average cost per symbol after every fill."""

    @property
    def realized_total(self) -> float:
        return sum(self.realized.values())


def average_cost_ledger(fills: Sequence[FillLike]) -> Ledger:
    """Replay fills in time order under average-cost accounting."""
    realized: dict[str, float] = {}
    qty: dict[str, float] = {}
    avg: dict[str, float] = {}
    for f in sorted(fills, key=lambda x: x.at):
        q = qty.get(f.symbol, 0.0)
        a = avg.get(f.symbol, 0.0)
        if f.side == "buy":
            new_q = q + f.quantity
            avg[f.symbol] = (q * a + f.quantity * f.price) / new_q if new_q else 0.0
            qty[f.symbol] = new_q
        elif f.side == "sell":
            if f.quantity > q + 1e-9:
                raise UsageError(
                    f"a sell of {f.quantity} {f.symbol} exceeds the {q} held; "
                    "history is incomplete",
                    hint="run: sobres trade status  to pull the missing fills",
                )
            realized[f.symbol] = realized.get(f.symbol, 0.0) + (f.price - a) * f.quantity
            qty[f.symbol] = q - f.quantity
        else:
            raise UsageError(f"unknown side {f.side!r}")
    positions = {s: Holding(s, q, avg.get(s, 0.0)) for s, q in qty.items() if abs(q) > 1e-12}
    return Ledger(realized=realized, positions=positions)


def unrealized_pnl(
    positions: Mapping[str, Holding], marks: Mapping[str, float]
) -> dict[str, float]:
    out: dict[str, float] = {}
    for symbol, h in positions.items():
        mark = marks.get(symbol)
        if mark is None:
            raise UsageError(f"no mark for {symbol}", hint="quote it before valuing")
        out[symbol] = (mark - h.average_cost) * h.quantity
    return out


@dataclass(frozen=True)
class EquityPoint:
    at: datetime
    equity: float


@dataclass(frozen=True)
class ExternalFlow:
    at: datetime
    amount: float


def time_weighted_return(
    equity: Sequence[EquityPoint], flows: Sequence[ExternalFlow]
) -> tuple[float, list[float]]:
    """Chain-linked sub-period returns, each ending at an external cash flow.

    A flow at time ``t`` is treated as arriving just before the equity observation
    at ``t``: ``r_i = E_t / (E_prev + flow_t) - 1``. Returns the cumulative return
    and the sub-period returns. A deposit therefore raises equity without raising
    the return.
    """
    points = sorted(equity, key=lambda p: p.at)
    if len(points) < 2:
        raise UsageError("at least two equity observations are needed for a return")
    by_time: dict[datetime, float] = {}
    for f in flows:
        by_time[f.at] = by_time.get(f.at, 0.0) + f.amount
    subs: list[float] = []
    prev = points[0]
    for point in points[1:]:
        flow = sum(a for t, a in by_time.items() if prev.at < t <= point.at)
        base = prev.equity + flow
        if base <= 0:
            raise UsageError("equity plus flows is not positive; the return is undefined")
        subs.append(point.equity / base - 1.0)
        prev = point
    total = 1.0
    for r in subs:
        total *= 1.0 + r
    return total - 1.0, subs


def max_drawdown_of_equity(equity: Sequence[EquityPoint]) -> float:
    """Most negative peak-to-trough decline of the equity path (0 for a rising path)."""
    peak = -math.inf
    worst = 0.0
    for point in sorted(equity, key=lambda p: p.at):
        peak = max(peak, point.equity)
        if peak > 0:
            worst = min(worst, point.equity / peak - 1.0)
    return worst
