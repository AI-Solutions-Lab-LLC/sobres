"""``sobres trade`` — invest a saved portfolio through a broker adapter (0016).

Adapters only: the broker comes from ``Context.broker()``, the math from
``core.trading``, the records from the storage port. ``preview`` has no side
effects. ``execute`` persists the intent before the first order leaves and
records what the broker actually answered, order by order. ``status``
reconciles open and unresolved orders. ``execute`` and ``close`` are terminal
commands: over HTTP they refuse before anything happens. Paper is the default;
live needs the environment setting, the enablement setting, ``--live`` and a
typed confirmation of the account id.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from typing import Any, ClassVar

from pydantic import Field

from sobres.cli.context import Context
from sobres.core import trading as tr
from sobres.core.errors import ConfigurationError, StorageConflictError, UsageError
from sobres.data.brokers.base import (
    TERMINAL_ORDER_STATUSES,
    Broker,
    BrokerAccount,
    BrokerOrder,
    BrokerPosition,
    Fill,
    OrderRequest,
    SubmissionUnresolvedError,
)
from sobres.data.storage.base import TradeFill, TradeIntent, TradeOrder, TradeRepository
from sobres.registry import Params, Ticker, positional, register
from sobres.results import RecordsResult, Result
from sobres.settings import ALPACA_ENVIRONMENT, TRADING_LIVE_ENABLED

NOT_ATOMIC = "a multi-order plan is not atomic: every order carries its own broker state"


class TradeReport(Result):
    report: ClassVar[bool] = True


# --------------------------------------------------------------------------- #
# Gates
# --------------------------------------------------------------------------- #


def _terminal_only(ctx: Context, command: str) -> None:
    if ctx.surface != "cli":
        raise UsageError(
            f"`sobres {command}` places orders and runs only from the terminal",
            hint=f"run: sobres {command} ... in a shell",
        )


def _broker(ctx: Context, live: bool) -> Broker:
    """The configured broker, after the live gate: paper unless everything says live."""
    environment = str(ctx.config.get(ALPACA_ENVIRONMENT.key) or "paper")
    enabled = bool(ctx.config.get(TRADING_LIVE_ENABLED.key))
    if live:
        missing = []
        if environment != "live":
            missing.append(f"{ALPACA_ENVIRONMENT.env}=live")
        if not enabled:
            missing.append(f"{TRADING_LIVE_ENABLED.env}=true")
        if missing:
            raise ConfigurationError(
                "--live was passed but live trading is not enabled: " + ", ".join(missing),
                hint="set both deliberately (sobres config set alpaca_environment live; "
                "sobres config set trading_live_enabled true) and use separate live credentials",
            )
    elif environment == "live":
        raise ConfigurationError(
            f"{ALPACA_ENVIRONMENT.env} is live but --live was not passed",
            hint="pass --live to address the live account, or set the environment back to paper",
        )
    broker: Broker = ctx.broker()
    if broker.environment != environment:
        raise ConfigurationError(
            f"the broker adapter addresses {broker.environment} but the setting says {environment}",
            hint="run: sobres config show",
        )
    return broker


def _confirm_live(ctx: Context, account: BrokerAccount, yes: bool) -> None:
    if account.environment != "live":
        return
    typed = ctx.ask(f"Type the LIVE account id to confirm ({account.id}):")
    if typed.strip() != account.id:
        raise UsageError("live execution cancelled: the account id did not match")
    if not yes and not ctx.ask_confirm("Submit real orders to this live account?"):
        raise UsageError("live execution cancelled")


# --------------------------------------------------------------------------- #
# Plan construction
# --------------------------------------------------------------------------- #


def _weights(portfolio: str, run_id: str | None, ctx: Context) -> dict[str, float]:
    from sobres.cli.commands.portfolio import resolve_portfolio

    record = resolve_portfolio(portfolio, ctx)
    if run_id is not None:
        from sobres.cli.commands.run import resolve_run

        run = resolve_run(run_id, ctx)
        weights = run.result.get("weights") if isinstance(run.result, dict) else None
        if not isinstance(weights, dict) or not weights:
            raise UsageError(
                f"run {run_id} carries no weights", hint="choose an optimize.markowitz run"
            )
        return {str(k).upper(): float(v) for k, v in weights.items() if float(v) > 0}
    if record.weights is None:
        raise UsageError(
            f"portfolio {portfolio!r} has no weights",
            hint="save it with --weights, or pass --run <id> of an optimization",
        )
    return {t: float(w) for t, w in zip(record.tickers, record.weights, strict=True)}


def _pending(ctx: Context, broker: Broker) -> list[tr.PendingOrder]:
    out = []
    for order in ctx.storage.trades.list_orders(open_only=True):
        remaining = max(order.quantity - order.filled_quantity, 0.0)
        if remaining > 0 and order.status not in ("failed",):
            out.append(tr.PendingOrder(order.symbol, order.side, remaining))
    return out


def _snapshot(
    broker: Broker, weights: dict[str, float], ctx: Context
) -> tuple[BrokerAccount, list[BrokerPosition], dict[str, tr.QuoteSnapshot]]:
    account = broker.account()
    positions = broker.positions()
    quotes = broker.quotes(list(weights))
    snaps = {s: tr.QuoteSnapshot(s, q.price, q.as_of) for s, q in quotes.items()}
    return account, positions, snaps


def _build_plan(
    p: PreviewParams, ctx: Context, broker: Broker
) -> tuple[tr.OrderPlan, BrokerAccount, str, dict[str, float]]:
    weights = _weights(p.portfolio, p.run, ctx)
    account, positions, quotes = _snapshot(broker, weights, ctx)
    holdings = [tr.Holding(x.symbol, x.quantity, x.average_cost) for x in positions]
    plan = tr.size_orders(
        weights,
        p.budget,
        quotes,
        holdings=holdings,
        pending=_pending(ctx, broker),
        cash_available=account.cash,
        fractional=broker.capabilities.fractional_shares,
        now=account.as_of,
    )
    fingerprint = plan.fingerprint(
        account_id=account.id, environment=account.environment, broker=broker.name
    )
    return plan, account, fingerprint, weights


def _plan_rows(plan: tr.OrderPlan, held: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {
            "symbol": o.symbol,
            "side": o.side,
            "quantity": o.quantity,
            "price": o.price,
            "notional": o.notional,
            "target_weight": o.target_weight,
            "held": held.get(o.symbol, 0.0),
            "resulting_weight": o.resulting_weight,
            "drift": o.drift,
        }
        for o in plan.orders
    ]


PLAN_COLUMNS = [
    "symbol",
    "side",
    "quantity",
    "price",
    "notional",
    "target_weight",
    "held",
    "resulting_weight",
    "drift",
]


# --------------------------------------------------------------------------- #
# trade preview
# --------------------------------------------------------------------------- #


class PreviewParams(Params):
    portfolio: str = positional(description="Saved portfolio name (needs weights).")
    budget: float = Field(
        gt=0, description="Total value the portfolio should reach, in the account currency."
    )
    run: str | None = Field(
        default=None, description="Use the weights of this saved optimization run instead."
    )
    live: bool = Field(default=False, description="Address the live account (gated).")


class PlanResult(TradeReport, RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {
        "symbol": "text",
        "side": "text",
        "quantity": "value",
        "price": "price",
        "notional": "price",
        "target_weight": "weight",
        "held": "value",
        "resulting_weight": "weight",
        "drift": "weight",
    }
    plan_hash: str
    broker: str
    environment: str
    account_id: str
    currency: str
    cash: float
    buying_power: float
    budget: float
    buy_notional: float
    sell_notional: float
    residual_cash: float
    quotes_as_of: str
    fractional: bool
    skipped: list[dict[str, Any]]
    portfolio: str
    run_id: str | None
    next_step: str

    def header_lines(self) -> list[str]:
        lines = [
            f"account {self.account_id} ({self.broker}, {self.environment}): cash "
            f"{self.cash:,.2f} {self.currency}, buying power {self.buying_power:,.2f} "
            f"{self.currency}",
            f"plan {self.plan_hash}: {len(self.rows)} orders, {self.budget:,.2f} {self.currency} "
            f"budget, buys {self.buy_notional:,.2f}, sells {self.sell_notional:,.2f}, residual "
            f"{self.residual_cash:,.2f}; quotes as of {self.quotes_as_of}",
        ]
        if self.skipped:
            lines.append(
                "below one share: "
                + ", ".join(f"{s['symbol']} ({s['unfilled_delta']:+.2f})" for s in self.skipped)
            )
        lines.append(f"no side effects; to submit: {self.next_step}")
        return [*lines, *super().header_lines()]


@register(
    "trade.preview",
    "Size whole-share orders that move the account toward a saved portfolio. No side effects.",
    result=PlanResult,
    example="trade preview core --budget 1000",
)
def preview(p: PreviewParams, ctx: Context) -> PlanResult:
    broker = _broker(ctx, p.live)
    plan, account, fingerprint, _weights_used = _build_plan(p, ctx, broker)
    held = {x.symbol: x.quantity for x in broker.positions()}
    live_flag = " --live" if p.live else ""
    run_flag = f" --run {p.run}" if p.run else ""
    return PlanResult(
        rows=_plan_rows(plan, held),
        columns=PLAN_COLUMNS,
        plan_hash=fingerprint,
        broker=broker.name,
        environment=account.environment,
        account_id=account.id,
        currency=account.currency,
        cash=account.cash,
        buying_power=account.buying_power,
        budget=plan.budget,
        buy_notional=plan.buy_notional,
        sell_notional=plan.sell_notional,
        residual_cash=plan.residual_cash,
        quotes_as_of=plan.quotes_as_of.isoformat(),
        fractional=plan.fractional,
        skipped=plan.skipped,
        portfolio=p.portfolio,
        run_id=p.run,
        next_step=(
            f"sobres trade execute {p.portfolio} --budget {p.budget:g} --plan {fingerprint}"
            f"{run_flag}{live_flag}"
        ),
    )


# --------------------------------------------------------------------------- #
# trade execute
# --------------------------------------------------------------------------- #


class ExecuteParams(PreviewParams):
    plan: str = Field(description="The plan hash printed by `trade preview`.")
    yes: bool = Field(default=False, description="Skip the confirmation prompt (paper only).")


class ExecutionResult(TradeReport, RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {
        "symbol": "text",
        "side": "text",
        "status": "text",
        "order_id": "text",
        "broker_order_id": "text",
        "quantity": "value",
        "filled_quantity": "value",
        "filled_avg_price": "price",
    }
    intent_id: str
    plan_hash: str
    environment: str
    account_id: str
    submitted: int
    unresolved: int
    rejected: int

    def header_lines(self) -> list[str]:
        return [
            f"intent {self.intent_id} (plan {self.plan_hash}, {self.environment} account "
            f"{self.account_id}): {self.submitted} submitted, {self.unresolved} unresolved, "
            f"{self.rejected} rejected",
            NOT_ATOMIC,
            "next: sobres trade status  (reconciles open and unresolved orders with the broker)",
            *super().header_lines(),
        ]


EXECUTION_COLUMNS = [
    "symbol",
    "side",
    "quantity",
    "status",
    "filled_quantity",
    "filled_avg_price",
    "order_id",
    "broker_order_id",
]


def _order_row(order: TradeOrder) -> dict[str, Any]:
    return {
        "symbol": order.symbol,
        "side": order.side,
        "quantity": order.quantity,
        "status": order.status,
        "filled_quantity": order.filled_quantity,
        "filled_avg_price": order.filled_avg_price,
        "order_id": order.id,
        "broker_order_id": order.broker_order_id,
    }


def _submit_all(
    ctx: Context, broker: Broker, intent: TradeIntent, orders: list[TradeOrder]
) -> list[TradeOrder]:
    trades = ctx.storage.trades
    out: list[TradeOrder] = []
    for order in orders:
        request = OrderRequest(order.id, order.symbol, order.side, order.quantity)  # type: ignore[arg-type]
        try:
            answer = broker.submit_order(request)
        except SubmissionUnresolvedError as exc:
            ctx.log.warning("trade.unresolved", order=order.id, reason=exc.reason)
            out.append(
                trades.update_order(
                    order.id,
                    status="unresolved",
                    submitted_at=datetime.now(UTC),
                    raw={"reason": exc.reason},
                )
            )
            continue
        except UsageError as exc:
            out.append(
                trades.update_order(order.id, status="rejected", raw={"reason": exc.message})
            )
            continue
        out.append(_apply_broker_order(trades, order.id, answer))
    trades.update_intent(intent.id, state="submitted")
    return out


def _apply_broker_order(trades: TradeRepository, order_id: str, answer: BrokerOrder) -> TradeOrder:
    return trades.update_order(
        order_id,
        status=answer.status,
        broker_order_id=answer.id,
        filled_quantity=answer.filled_quantity,
        filled_avg_price=answer.filled_avg_price,
        submitted_at=answer.submitted_at,
        raw=answer.raw,
    )


@register(
    "trade.execute",
    "Submit the previewed plan: the intent is recorded first, then each order independently.",
    result=ExecutionResult,
    example="trade execute core --budget 1000 --plan <hash-from-preview>",
)
def execute(p: ExecuteParams, ctx: Context) -> ExecutionResult:
    _terminal_only(ctx, "trade execute")
    broker = _broker(ctx, p.live)
    plan, account, fingerprint, _ = _build_plan(p, ctx, broker)
    if fingerprint != p.plan:
        raise UsageError(
            f"the plan changed since the preview (now {fingerprint}, you passed {p.plan}): "
            "quotes moved or holdings changed",
            hint="run: sobres trade preview again and pass its new --plan",
        )
    if not plan.orders:
        raise UsageError("the plan has no orders", hint="nothing to submit")
    trades = ctx.storage.trades
    if trades.find_intent(fingerprint, broker.name, account.id, account.environment):
        raise UsageError(
            f"plan {fingerprint} was already confirmed for this account",
            hint="run: sobres trade status  to see its orders; a new preview makes a new plan",
        )
    _confirm_live(ctx, account, p.yes)
    if account.environment != "live" and not p.yes:
        summary = ", ".join(f"{o.side} {o.quantity:g} {o.symbol}" for o in plan.orders)
        if not ctx.ask_confirm(
            f"Submit to the {account.environment} account {account.id}: {summary}?"
        ):
            raise UsageError("execution cancelled", hint="pass --yes to skip the prompt")
    intent = TradeIntent(
        id=uuid.uuid4().hex[:12],
        kind="rebalance",
        broker=broker.name,
        account_id=account.id,
        environment=account.environment,
        plan_hash=fingerprint,
        plan={
            "budget": plan.budget,
            "orders": _plan_rows(plan, {}),
            "residual_cash": plan.residual_cash,
            "quotes_as_of": plan.quotes_as_of.isoformat(),
        },
        portfolio=p.portfolio,
        run_id=p.run,
    )
    try:
        intent = trades.save_intent(intent)  # durable before any network call
    except StorageConflictError:
        raise UsageError(f"plan {fingerprint} was already confirmed for this account") from None
    orders = [
        trades.save_order(
            TradeOrder(
                id=f"sobres-{intent.id}-{i:02d}",
                intent_id=intent.id,
                symbol=o.symbol,
                side=o.side,
                quantity=o.quantity,
            )
        )
        for i, o in enumerate(plan.orders, start=1)
    ]
    done = _submit_all(ctx, broker, intent, orders)
    _pull_fills(ctx, broker)
    return ExecutionResult(
        rows=[_order_row(o) for o in done],
        columns=EXECUTION_COLUMNS,
        intent_id=intent.id,
        plan_hash=fingerprint,
        environment=account.environment,
        account_id=account.id,
        submitted=sum(1 for o in done if o.status not in ("unresolved", "rejected")),
        unresolved=sum(1 for o in done if o.status == "unresolved"),
        rejected=sum(1 for o in done if o.status == "rejected"),
    )


# --------------------------------------------------------------------------- #
# trade positions / orders / status / history
# --------------------------------------------------------------------------- #


class PositionsParams(Params):
    live: bool = Field(default=False, description="Address the live account (gated).")


class PositionsResult(TradeReport, RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {
        "symbol": "text",
        "origin": "text",
        "quantity": "value",
        "average_cost": "price",
        "current_price": "price",
        "market_value": "price",
        "unrealized_pl": "price",
    }
    environment: str
    account_id: str
    currency: str
    equity: float
    cash: float

    def header_lines(self) -> list[str]:
        return [
            f"{self.environment} account {self.account_id}: equity {self.equity:,.2f} "
            f"{self.currency}, cash {self.cash:,.2f} {self.currency}; positions as the broker "
            "reports them (no order was placed)",
            *super().header_lines(),
        ]


POSITION_COLUMNS = [
    "symbol",
    "quantity",
    "average_cost",
    "current_price",
    "market_value",
    "unrealized_pl",
    "origin",
]


@register(
    "trade.positions",
    "Open positions as the broker reports them; reads never place orders.",
    result=PositionsResult,
    example="trade positions",
)
def positions(p: PositionsParams, ctx: Context) -> PositionsResult:
    broker = _broker(ctx, p.live)
    account = broker.account()
    ours = {o.symbol for o in ctx.storage.trades.list_orders(limit=10000)}
    rows = [
        {
            "symbol": x.symbol,
            "quantity": x.quantity,
            "average_cost": x.average_cost,
            "current_price": x.current_price,
            "market_value": x.market_value,
            "unrealized_pl": x.unrealized_pl,
            "origin": "sobres" if x.symbol in ours else "external",
        }
        for x in broker.positions()
    ]
    return PositionsResult(
        rows=rows,
        columns=POSITION_COLUMNS,
        environment=account.environment,
        account_id=account.id,
        currency=account.currency,
        equity=account.equity,
        cash=account.cash,
    )


class OrdersParams(Params):
    intent: str | None = Field(default=None, description="Only this intent's orders.")
    open: bool = Field(default=False, description="Only orders that are not terminal.")


class OrdersResult(RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {
        "symbol": "text",
        "side": "text",
        "status": "text",
        "order_id": "text",
        "broker_order_id": "text",
        "intent_id": "text",
    }


@register(
    "trade.orders",
    "Recorded orders with the broker state last observed.",
    result=OrdersResult,
    example="trade orders --open",
)
def orders(p: OrdersParams, ctx: Context) -> OrdersResult:
    rows = [
        {
            **_order_row(o),
            "intent_id": o.intent_id,
            "updated_at": o.updated_at.isoformat() if o.updated_at else "",
        }
        for o in ctx.storage.trades.list_orders(p.intent, open_only=p.open)
    ]
    return OrdersResult(rows=rows, columns=[*EXECUTION_COLUMNS, "intent_id", "updated_at"])


class StatusParams(Params):
    live: bool = Field(default=False, description="Address the live account (gated).")


class StatusResult(TradeReport, RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {
        "symbol": "text",
        "side": "text",
        "status": "text",
        "order_id": "text",
        "broker_order_id": "text",
        "was": "text",
    }
    checked: int
    changed: int
    new_fills: int
    still_unresolved: int

    def header_lines(self) -> list[str]:
        return [
            f"reconciled {self.checked} open/unresolved orders with the broker: {self.changed} "
            f"changed, {self.new_fills} new fills recorded, {self.still_unresolved} still "
            "unresolved",
            NOT_ATOMIC,
            *super().header_lines(),
        ]


def _fill_id(f: Fill) -> str:
    key = f"{f.order_id}|{f.symbol}|{f.side}|{f.quantity:.6f}|{f.price:.6f}|{f.at.isoformat()}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def _pull_fills(ctx: Context, broker: Broker) -> int:
    trades = ctx.storage.trades
    by_broker_id = {
        o.broker_order_id: o.id for o in trades.list_orders(limit=10000) if o.broker_order_id
    }
    records = [
        TradeFill(
            id=_fill_id(f),
            broker_order_id=f.order_id,
            symbol=f.symbol,
            side=f.side,
            quantity=f.quantity,
            price=f.price,
            filled_at=f.at,
            source="broker" if f.order_id in by_broker_id else "external",
            order_id=by_broker_id.get(f.order_id),
        )
        for f in broker.fills()
    ]
    return trades.add_fills(records)


@register(
    "trade.status",
    "Ask the broker about every open or unresolved order and record what it says.",
    result=StatusResult,
    example="trade status",
)
def status(p: StatusParams, ctx: Context) -> StatusResult:
    broker = _broker(ctx, p.live)
    trades = ctx.storage.trades
    rows: list[dict[str, Any]] = []
    changed = 0
    unresolved = 0
    pending = [o for o in trades.list_orders(open_only=True, limit=10000) if o.status != "failed"]
    for order in pending:
        answer: BrokerOrder | None
        if order.broker_order_id:
            answer = broker.get_order(order.broker_order_id)
        else:
            answer = broker.find_order(order.id)
        if answer is None:
            if order.status == "unresolved":
                # The broker never saw it: only now is "failed" honest.
                updated = trades.update_order(
                    order.id, status="failed", raw={"reason": "broker has no such order"}
                )
                rows.append({**_order_row(updated), "was": order.status})
                changed += 1
            else:
                rows.append({**_order_row(order), "was": order.status})
            continue
        updated = _apply_broker_order(trades, order.id, answer)
        if updated.status != order.status or updated.filled_quantity != order.filled_quantity:
            changed += 1
        if updated.status == "unresolved":
            unresolved += 1
        rows.append({**_order_row(updated), "was": order.status})
    new_fills = _pull_fills(ctx, broker)
    for intent in trades.list_intents(limit=10000):
        if intent.state == "submitted" and all(
            o.status in TERMINAL_ORDER_STATUSES or o.status == "failed"
            for o in trades.list_orders(intent.id)
        ):
            trades.update_intent(intent.id, state="reconciled")
    return StatusResult(
        rows=rows,
        columns=[*EXECUTION_COLUMNS, "was"],
        checked=len(pending),
        changed=changed,
        new_fills=new_fills,
        still_unresolved=unresolved,
    )


class HistoryParams(Params):
    live: bool = Field(default=False, description="Address the live account (gated).")
    symbol: Ticker | None = Field(default=None, description="Only this symbol's fills.")


class HistoryResult(TradeReport, RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {
        "symbol": "text",
        "side": "text",
        "source": "text",
        "filled_at": "text",
        "quantity": "value",
        "price": "price",
    }
    realized: dict[str, float]
    realized_total: float
    unrealized: dict[str, float]
    unrealized_total: float
    cash_flows: list[dict[str, Any]]
    external_fills: int
    accounting: str

    def header_lines(self) -> list[str]:
        flows = sum(f["amount"] for f in self.cash_flows)
        return [
            f"realized P&L {self.realized_total:,.2f} ({self.accounting}); unrealized "
            f"{self.unrealized_total:,.2f} at the broker's current prices; "
            f"{len(self.cash_flows)} cash flows totalling {flows:,.2f} are not profit",
            f"{len(self.rows)} fills recorded, {self.external_fills} from outside sobres; "
            "backtested and optimized figures are never mixed in here",
            *super().header_lines(),
        ]


@register(
    "trade.history",
    "Fills, realized and unrealized P&L (average cost) and cash flows kept apart.",
    result=HistoryResult,
    example="trade history",
)
def history(p: HistoryParams, ctx: Context) -> HistoryResult:
    broker = _broker(ctx, p.live)
    _pull_fills(ctx, broker)
    fills = ctx.storage.trades.list_fills(p.symbol)
    ledger = tr.average_cost_ledger(
        [tr.FillLike(f.symbol, f.side, f.quantity, f.price, f.filled_at) for f in fills]
    )
    marks = {x.symbol: x.current_price for x in broker.positions()}
    unrealized = {
        s: (marks[s] - h.average_cost) * h.quantity
        for s, h in ledger.positions.items()
        if s in marks
    }
    flows = [
        {"at": f.at.isoformat(), "amount": f.amount, "kind": f.kind} for f in broker.cash_flows()
    ]
    rows = [
        {
            "filled_at": f.filled_at.isoformat(),
            "symbol": f.symbol,
            "side": f.side,
            "quantity": f.quantity,
            "price": f.price,
            "source": f.source,
            "order_id": f.order_id or "",
        }
        for f in fills
    ]
    return HistoryResult(
        rows=rows,
        columns=["filled_at", "symbol", "side", "quantity", "price", "source", "order_id"],
        realized=ledger.realized,
        realized_total=ledger.realized_total,
        unrealized=unrealized,
        unrealized_total=sum(unrealized.values()),
        cash_flows=flows,
        external_fills=sum(1 for f in fills if f.source == "external"),
        accounting="average cost; tax lots are not modelled",
    )


# --------------------------------------------------------------------------- #
# trade close
# --------------------------------------------------------------------------- #


class CloseParams(Params):
    symbol: Ticker = positional(description="The position to close.")
    quantity: float | None = Field(
        default=None, gt=0, description="Shares to sell (default: the whole position)."
    )
    live: bool = Field(default=False, description="Address the live account (gated).")
    yes: bool = Field(default=False, description="Skip the confirmation prompt (paper only).")


@register(
    "trade.close",
    "Preview, confirm and submit a sell that closes part or all of a position.",
    result=ExecutionResult,
    emits_data=True,
    example="trade close AAPL --quantity 4 --yes",
)
def close(p: CloseParams, ctx: Context) -> ExecutionResult:
    _terminal_only(ctx, "trade close")
    broker = _broker(ctx, p.live)
    account = broker.account()
    held = {x.symbol: x for x in broker.positions()}
    if p.symbol not in held:
        raise UsageError(f"no open position in {p.symbol}", hint="run: sobres trade positions")
    quantity = p.quantity if p.quantity is not None else held[p.symbol].quantity
    if quantity > held[p.symbol].quantity + 1e-9:
        raise UsageError(
            f"--quantity {quantity:g} exceeds the {held[p.symbol].quantity:g} shares held"
        )
    if not broker.capabilities.fractional_shares and quantity != int(quantity):
        raise UsageError(f"{broker.name} sells whole shares here; {quantity:g} is fractional")
    quote = broker.quotes([p.symbol])[p.symbol]
    plan = tr.OrderPlan(
        budget=quantity * quote.price,
        orders=[
            tr.PlannedOrder(
                symbol=p.symbol,
                side="sell",
                quantity=float(quantity),
                price=quote.price,
                notional=quantity * quote.price,
                target_weight=0.0,
                target_value=0.0,
                current_value=held[p.symbol].market_value,
                resulting_weight=0.0,
                drift=0.0,
            )
        ],
        residual_cash=0.0,
        quotes_as_of=quote.as_of,
        fractional=broker.capabilities.fractional_shares,
    )
    fingerprint = plan.fingerprint(
        account_id=account.id, environment=account.environment, broker=broker.name
    )
    ctx.note(
        f"close {p.symbol}: sell {quantity:g} @ {quote.price:.2f} "
        f"(quote {quote.as_of.isoformat()}) ≈ {quantity * quote.price:,.2f} "
        f"{account.currency} on the {account.environment} account"
    )
    _confirm_live(ctx, account, p.yes)
    paper_unconfirmed = account.environment != "live" and not p.yes
    if paper_unconfirmed and not ctx.ask_confirm(f"Submit the closing order for {p.symbol}?"):
        raise UsageError("close cancelled", hint="pass --yes to skip the prompt")
    trades = ctx.storage.trades
    intent = TradeIntent(
        id=uuid.uuid4().hex[:12],
        kind="close",
        broker=broker.name,
        account_id=account.id,
        environment=account.environment,
        plan_hash=fingerprint,
        plan={"symbol": p.symbol, "quantity": quantity, "price": quote.price},
    )
    try:
        intent = trades.save_intent(intent)
    except StorageConflictError:
        raise UsageError(
            f"an identical close of {p.symbol} at this quote was already confirmed",
            hint="run: sobres trade status",
        ) from None
    order = trades.save_order(
        TradeOrder(
            id=f"sobres-{intent.id}-01",
            intent_id=intent.id,
            symbol=p.symbol,
            side="sell",
            quantity=float(quantity),
        )
    )
    done = _submit_all(ctx, broker, intent, [order])
    _pull_fills(ctx, broker)
    return ExecutionResult(
        rows=[_order_row(o) for o in done],
        columns=EXECUTION_COLUMNS,
        intent_id=intent.id,
        plan_hash=fingerprint,
        environment=account.environment,
        account_id=account.id,
        submitted=sum(1 for o in done if o.status not in ("unresolved", "rejected")),
        unresolved=sum(1 for o in done if o.status == "unresolved"),
        rejected=sum(1 for o in done if o.status == "rejected"),
    )
