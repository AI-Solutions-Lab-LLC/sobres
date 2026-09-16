"""``sobres trade`` end to end against the synthetic paper account, offline.

Scenarios: Known allocation; Holdings and pending orders reduce the delta;
Plan must match; Durable intent before submission; Duplicate confirmation is
refused; Submission timeout leaves the order unresolved; Partial fill is
reported as observed; Paper by default; Live requires setting, flag and
confirmation; Credentials are secrets; Positions are read without side effects;
Close previews then submits a closing order; Known P&L; Durable history;
Mutations are terminal-only; Reads are exposed; Vendor stays in its adapter.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from sobres.cli.commands import trade as trade_mod
from sobres.data.brokers.base import OrderRequest
from sobres.data.brokers.fake import FakeBroker

SAVE = ["portfolio", "save", "core", "--tickers", "AAPL", "MSFT", "--weights", "0.6", "0.4"]


def _json(result: Any) -> dict[str, Any]:
    assert result.exit_code == 0, result.stderr
    return json.loads(result.stdout)


def _plan(cli: Callable[..., Any], *extra: str) -> dict[str, Any]:
    return _json(cli("trade", "preview", "core", "--budget", "1000", *extra, "--format", "json"))


def test_preview_is_the_known_allocation_with_no_side_effects(cli: Callable[..., Any]) -> None:
    """Scenario: Known allocation. Scenario: Paper by default."""
    cli(*SAVE)
    doc = _plan(cli)
    assert doc["environment"] == "paper" and doc["broker"] == "alpaca"
    assert doc["account_id"] == "PA3SYNTH01" and doc["currency"] == "USD"
    assert [(r["symbol"], r["side"], r["quantity"], r["notional"]) for r in doc["rows"]] == [
        ("AAPL", "buy", 6.0, 600.0),
        ("MSFT", "buy", 8.0, 400.0),
    ]
    assert doc["residual_cash"] == 0.0 and doc["buy_notional"] == 1000.0
    assert doc["rows"][0]["target_weight"] == 0.6 and doc["rows"][0]["drift"] == 0.0
    assert len(doc["plan_hash"]) == 12 and doc["next_step"].endswith(doc["plan_hash"])
    assert doc["quotes_as_of"].startswith("2026-09-16T19:59")
    # No side effects: nothing recorded, nothing held, the same plan again.
    assert _json(cli("trade", "orders", "--format", "json"))["rows"] == []
    assert _json(cli("trade", "positions", "--format", "json"))["rows"] == []
    assert _plan(cli)["plan_hash"] == doc["plan_hash"]
    table = cli("trade", "preview", "core", "--budget", "1000", "--format", "table")
    assert "no side effects; to submit: sobres trade execute core" in table.stdout
    assert "paper" in table.stdout and "Not investment advice" in table.stdout
    unweighted = cli("portfolio", "save", "plain", "--tickers", "AAPL")
    assert unweighted.exit_code == 0
    no_weights = cli("trade", "preview", "plain", "--budget", "1000")
    assert no_weights.exit_code == 2 and "has no weights" in no_weights.stderr
    too_big = cli("trade", "preview", "core", "--budget", "1000000000")
    assert too_big.exit_code == 2 and "cash" in too_big.stderr


def test_execute_records_the_intent_then_each_order_and_refuses_duplicates(
    cli: Callable[..., Any],
) -> None:
    """Scenario: Durable intent before submission. Scenario: Duplicate confirmation is
    refused. Scenario: Plan must match. Scenario: Holdings and pending orders reduce
    the delta. Scenario: Durable history."""
    cli(*SAVE)
    plan = _plan(cli)["plan_hash"]
    stale = cli("trade", "execute", "core", "--budget", "1000", "--plan", "nope", "--yes")
    assert stale.exit_code == 2 and "plan changed" in stale.stderr
    done = _json(
        cli(
            "trade",
            "execute",
            "core",
            "--budget",
            "1000",
            "--plan",
            plan,
            "--yes",
            "--format",
            "json",
        )
    )
    assert done["submitted"] == 2 and done["unresolved"] == 0 and done["rejected"] == 0
    assert [(r["symbol"], r["status"], r["filled_quantity"]) for r in done["rows"]] == [
        ("AAPL", "filled", 6.0),
        ("MSFT", "filled", 8.0),
    ]
    assert all(r["order_id"].startswith(f"sobres-{done['intent_id']}-") for r in done["rows"])
    assert all(r["broker_order_id"] for r in done["rows"])
    orders = _json(cli("trade", "orders", "--format", "json"))["rows"]
    assert len(orders) == 2 and {o["intent_id"] for o in orders} == {done["intent_id"]}
    again = cli("trade", "execute", "core", "--budget", "1000", "--plan", plan, "--yes")
    assert again.exit_code == 2 and (
        "already confirmed" in again.stderr or "plan changed" in again.stderr
    )
    # Holdings now count toward the target: the next preview has nothing left to buy.
    after = _plan(cli)
    assert after["rows"] == [] and after["plan_hash"] != plan
    positions = _json(cli("trade", "positions", "--format", "json"))
    assert [(p["symbol"], p["quantity"], p["origin"]) for p in positions["rows"]] == [
        ("AAPL", 6.0, "sobres"),
        ("MSFT", 8.0, "sobres"),
    ]
    assert positions["cash"] == pytest.approx(99_000.0)
    # Cache clearing never touches the trading records.
    assert cli("cache", "clear", "--yes").exit_code == 0
    assert len(_json(cli("trade", "orders", "--format", "json"))["rows"]) == 2
    history = _json(cli("trade", "history", "--format", "json"))
    assert len(history["rows"]) == 2 and history["realized_total"] == 0.0
    assert all(r["source"] == "broker" for r in history["rows"])
    table = cli("trade", "execute", "core", "--budget", "2000", "--plan", "x", "--format", "table")
    assert table.exit_code == 2  # the hash never matches a plan built for a different budget


def test_close_sells_part_of_a_position_and_history_reports_known_pnl(
    cli: Callable[..., Any],
) -> None:
    """Scenario: Close previews then submits a closing order. Scenario: Known P&L."""
    cli(*SAVE)
    plan = _plan(cli)["plan_hash"]
    cli("trade", "execute", "core", "--budget", "1000", "--plan", plan, "--yes")
    too_many = cli("trade", "close", "AAPL", "--quantity", "7", "--yes")
    assert too_many.exit_code == 2 and "exceeds" in too_many.stderr
    absent = cli("trade", "close", "XOM", "--yes")
    assert absent.exit_code == 2 and "no open position" in absent.stderr
    closed = _json(cli("trade", "close", "AAPL", "--quantity", "4", "--yes", "--format", "json"))
    assert closed["rows"][0]["side"] == "sell" and closed["rows"][0]["filled_quantity"] == 4.0
    positions = _json(cli("trade", "positions", "--format", "json"))["rows"]
    assert [(p["symbol"], p["quantity"]) for p in positions] == [("AAPL", 2.0), ("MSFT", 8.0)]
    history = _json(cli("trade", "history", "--format", "json"))
    assert [(r["symbol"], r["side"], r["quantity"], r["price"]) for r in history["rows"]] == [
        ("AAPL", "buy", 6.0, 100.0),
        ("MSFT", "buy", 8.0, 50.0),
        ("AAPL", "sell", 4.0, 100.0),
    ]
    assert history["realized"] == {"AAPL": 0.0}  # sold at the buy price: nothing realized
    assert history["unrealized"] == {"AAPL": 0.0, "MSFT": 0.0}
    assert "average cost" in history["accounting"]
    table = cli("trade", "history", "--format", "table")
    assert "are not profit" in table.stdout and "never mixed" in table.stdout
    prompt = cli("trade", "close", "MSFT", input="n\n")
    assert prompt.exit_code == 2 and "cancelled" in prompt.stderr


def test_known_pnl_through_the_command_with_a_fake_broker(
    make_context: Callable[..., Any],
) -> None:
    """Scenario: Known P&L. Scenario: Adapter replacement."""
    from sobres.cli.commands.trade import HistoryParams, history

    broker = FakeBroker({"AAPL": 100.0})
    ctx = make_context(sources={"broker": broker})
    broker.submit_order(OrderRequest("ext-1", "AAPL", "buy", 10.0))
    broker.set_quote("AAPL", 110.0)
    broker.submit_order(OrderRequest("ext-2", "AAPL", "sell", 4.0))
    broker.set_quote("AAPL", 105.0)
    broker.deposit(1000.0)
    result = history(HistoryParams(), ctx)
    assert result.realized == {"AAPL": pytest.approx(40.0)}
    assert result.unrealized == {"AAPL": pytest.approx(30.0)}
    assert result.external_fills == 2  # no Sobres order explains them
    assert result.cash_flows[0]["amount"] == 1000.0 and result.cash_flows[0]["kind"] == "deposit"
    lines = result.header_lines()
    assert "realized P&L 40.00" in lines[0] and "are not profit" in lines[0]


def test_unresolved_submission_is_never_called_failed_until_the_broker_says_so(
    make_context: Callable[..., Any],
) -> None:
    """Scenario: Submission timeout leaves the order unresolved. Scenario: Partial fill
    is reported as observed."""
    from sobres.cli.commands.trade import (
        ExecuteParams,
        PreviewParams,
        StatusParams,
        execute,
        preview,
        status,
    )
    from sobres.data.storage.base import PortfolioRecord

    broker = FakeBroker({"AAPL": 100.0, "MSFT": 50.0}, partial_fill_symbols={"MSFT": 3.0})
    ctx = make_context(sources={"broker": broker})
    ctx.storage.portfolios.save(PortfolioRecord("core", ("AAPL", "MSFT"), (0.6, 0.4)))
    plan = preview(PreviewParams(portfolio="core", budget=1000.0), ctx)
    broker.timeout_next_submission = True  # the first order's answer never arrives
    done = execute(
        ExecuteParams(portfolio="core", budget=1000.0, plan=plan.plan_hash, yes=True), ctx
    )
    by_symbol = {r["symbol"]: r for r in done.rows}
    assert by_symbol["AAPL"]["status"] == "unresolved" and done.unresolved == 1
    assert by_symbol["MSFT"]["status"] == "partially_filled"
    assert by_symbol["MSFT"]["filled_quantity"] == 3.0 and by_symbol["MSFT"]["quantity"] == 8.0
    intent = ctx.storage.trades.get_intent(done.intent_id)
    assert intent is not None and intent.state == "submitted"
    # Reconciliation asks the broker by client order id: it did fill.
    reconciled = status(StatusParams(), ctx)
    assert reconciled.checked == 2 and reconciled.still_unresolved == 0
    rows = {r["symbol"]: r for r in reconciled.rows}
    assert rows["AAPL"]["was"] == "unresolved" and rows["AAPL"]["status"] == "filled"
    assert rows["AAPL"]["broker_order_id"] and rows["MSFT"]["status"] == "partially_filled"
    # An unresolved order the broker never saw becomes failed only at reconciliation.
    from sobres.data.storage.base import TradeOrder

    ctx.storage.trades.save_order(
        TradeOrder(
            id="ghost-1",
            intent_id=done.intent_id,
            symbol="AAPL",
            side="buy",
            quantity=1.0,
            status="unresolved",
        )
    )
    again = status(StatusParams(), ctx)
    ghost = next(r for r in again.rows if r["order_id"] == "ghost-1")
    assert ghost["status"] == "failed" and ghost["was"] == "unresolved"


def test_live_requires_setting_flag_and_confirmation(cli: Callable[..., Any]) -> None:
    """Scenario: Live requires setting, flag and confirmation. Scenario: Paper by default."""
    cli(*SAVE)
    flag_only = cli("trade", "preview", "core", "--budget", "1000", "--live")
    assert flag_only.exit_code == 3
    assert "SOBRES_ALPACA_ENVIRONMENT=live" in flag_only.stderr
    assert "SOBRES_TRADING_LIVE_ENABLED=true" in flag_only.stderr
    env_only = cli(
        "trade",
        "preview",
        "core",
        "--budget",
        "1000",
        env_extra={"SOBRES_ALPACA_ENVIRONMENT": "live"},
    )
    assert env_only.exit_code == 3 and "--live was not passed" in env_only.stderr
    enabled = {"SOBRES_ALPACA_ENVIRONMENT": "live", "SOBRES_TRADING_LIVE_ENABLED": "true"}
    live_preview = cli("trade", "preview", "core", "--budget", "1000", "--live", env_extra=enabled)
    assert live_preview.exit_code == 0, live_preview.stderr
    plan = json.loads(
        cli(
            "trade",
            "preview",
            "core",
            "--budget",
            "1000",
            "--live",
            "--format",
            "json",
            env_extra=enabled,
        ).stdout
    )
    assert plan["environment"] == "live"
    wrong_id = cli(
        "trade",
        "execute",
        "core",
        "--budget",
        "1000",
        "--plan",
        plan["plan_hash"],
        "--live",
        "--yes",
        input="not-the-account\n",
        env_extra=enabled,
    )
    assert wrong_id.exit_code == 2 and "did not match" in wrong_id.stderr
    assert (
        json.loads(cli("trade", "orders", "--format", "json", env_extra=enabled).stdout)["rows"]
        == []
    )
    # Records are scoped by environment: the paper preview's hash cannot address live.
    paper_plan = _plan(cli)["plan_hash"]
    assert paper_plan != plan["plan_hash"]


def test_mutations_are_terminal_only_and_reads_are_exposed(
    make_context: Callable[..., Any],
) -> None:
    """Scenario: Mutations are terminal-only. Scenario: Reads are exposed."""
    from sobres.cli.commands.trade import CloseParams, ExecuteParams, close, execute
    from sobres.core.errors import UsageError
    from sobres.registry import all_commands

    ctx = make_context(surface="api", sources={"broker": FakeBroker({"AAPL": 100.0})})
    with pytest.raises(UsageError, match="terminal"):
        execute(ExecuteParams(portfolio="core", budget=1.0, plan="x"), ctx)
    with pytest.raises(UsageError, match="terminal"):
        close(CloseParams(symbol="AAPL"), ctx)
    names = {c.name for c in all_commands()}
    assert {
        "trade.preview",
        "trade.positions",
        "trade.orders",
        "trade.status",
        "trade.history",
    } <= names
    assert {"trade.execute", "trade.close"} <= names  # declared once; parity gives them routes too


def test_credentials_are_secrets_and_missing_keys_are_actionable(
    cli: Callable[..., Any], tmp_path: Any
) -> None:
    """Scenario: Credentials are secrets."""
    from sobres.settings import get_setting

    for key in ("alpaca_key_id", "alpaca_secret_key"):
        setting = get_setting(key)
        assert setting.secret and not setting.browser_editable and setting.advanced
    assert get_setting("alpaca_environment").choices == ("paper", "live")
    assert get_setting("trading_live_enabled").default is False
    shown = cli("config", "set", "alpaca_secret_key", "SENTINEL-alpaca-secret")
    assert shown.exit_code == 0 and "SENTINEL-alpaca-secret" not in shown.stdout + shown.stderr
    listing = cli("config", "show", "--format", "json")
    assert "SENTINEL-alpaca-secret" not in listing.stdout
    # Without a fixture directory the real adapter needs both keys, and says how to get them.
    no_keys = cli(
        "trade", "positions", env_extra={"SOBRES_FIXTURE_DIR": "", "SOBRES_ALPACA_KEY_ID": ""}
    )
    assert no_keys.exit_code == 3
    assert "SOBRES_ALPACA_KEY_ID" in no_keys.stderr and "alpaca.markets" in no_keys.stderr
    assert "Traceback" not in no_keys.stderr


def test_vendor_stays_in_its_adapter() -> None:
    """Scenario: Vendor stays in its adapter."""
    import ast
    from pathlib import Path

    src = Path(trade_mod.__file__).resolve().parents[2]
    offenders = []
    for path in src.rglob("*.py"):
        if path.name == "alpaca.py" and path.parent.name == "brokers":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and "brokers.alpaca" in node.module:
                if path.name in ("context.py",):  # composition root: the one allowed importer
                    continue
                offenders.append(path.name)
    assert offenders == [], offenders
    text = Path(trade_mod.__file__).read_text(encoding="utf-8")
    assert "alpaca" not in text.lower().replace("alpaca_environment", "").replace("alpaca_key", "")
