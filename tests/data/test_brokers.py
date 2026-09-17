"""Broker adapters: the conformance suite over both, plus Alpaca's HTTP translation.

Scenarios: Adapter replacement; Vendor stays in its adapter; Unsupported
capability fails before side effects; Submission timeout leaves the order
unresolved; Partial fill is reported as observed; Credentials are secrets.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest

from sobres.core.errors import ConfigurationError, ProviderError, UsageError
from sobres.data.brokers.alpaca import (
    AlpacaBroker,
    LiveAlpacaSource,
    parse_order,
    validate_credentials,
)
from sobres.data.brokers.base import Broker, OrderRequest, SubmissionUnresolvedError
from sobres.data.brokers.fake import FakeBroker
from sobres.data.fixtures import FixtureAlpacaSource
from tests.data.broker_conformance import BrokerConformance

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
QUOTES = {"AAPL": 100.0, "MSFT": 50.0, "JNJ": 150.0, "NVDA": 120.0}


def _fake() -> FakeBroker:
    return FakeBroker(QUOTES)


def _alpaca_fixture() -> AlpacaBroker:
    return AlpacaBroker(FixtureAlpacaSource(FIXTURES), "paper")


# One entry per adapter; adding a broker means adding here and nothing else in the suite.
ADAPTERS: dict[str, Any] = {"fake": _fake, "alpaca-fixture": _alpaca_fixture}


@pytest.fixture(params=sorted(ADAPTERS))
def broker(request: pytest.FixtureRequest) -> Iterator[Broker]:
    yield ADAPTERS[request.param]()


class TestConformance(BrokerConformance):
    pass


# ----------------------------------------------------------------- lifecycle honesty


def test_fake_partial_fill_and_timeout_are_observable() -> None:
    """Scenario: Partial fill is reported as observed. Scenario: Submission timeout
    leaves the order unresolved."""
    broker = FakeBroker(QUOTES, partial_fill_symbols={"AAPL": 2.0})
    order = broker.submit_order(OrderRequest("p1", "AAPL", "buy", 6.0))
    assert order.status == "partially_filled" and order.filled_quantity == 2.0
    assert broker.positions()[0].quantity == 2.0
    broker.timeout_next_submission = True
    with pytest.raises(SubmissionUnresolvedError) as exc:
        broker.submit_order(OrderRequest("p2", "MSFT", "buy", 1.0))
    assert exc.value.client_order_id == "p2"
    # The request did reach the broker: a lookup by client id finds it filled.
    found = broker.find_order("p2")
    assert found is not None and found.status == "filled"


def test_fixture_source_persists_state_and_models_a_timeout(tmp_path: Path) -> None:
    saved: list[dict[str, Any]] = []
    source = FixtureAlpacaSource(FIXTURES, on_change=saved.append)
    broker = AlpacaBroker(source, "paper")
    broker.submit_order(OrderRequest("s1", "AAPL", "buy", 1.0))
    assert saved and saved[-1]["positions"]["AAPL"]["qty"] == 1.0
    reopened = AlpacaBroker(
        FixtureAlpacaSource(FIXTURES, state=json.loads(json.dumps(saved[-1]))), "paper"
    )
    assert reopened.positions()[0].quantity == 1.0  # one account across processes
    source.timeout_next_post = True
    with pytest.raises(SubmissionUnresolvedError):
        broker.submit_order(OrderRequest("s2", "MSFT", "buy", 1.0))
    assert broker.find_order("s2") is not None
    meta = json.loads((FIXTURES / "synthetic" / "alpaca" / "meta.json").read_text(encoding="utf-8"))
    assert meta["synthesized_at"] and meta["recorded_at"] is None  # labelled, never a recording


# ------------------------------------------------------------------ Alpaca over HTTP


class _Transport(httpx.BaseTransport):
    def __init__(self, status: int, body: Any, *, raise_exc: Exception | None = None) -> None:
        self.status, self.body, self.raise_exc = status, body, raise_exc
        self.requests: list[httpx.Request] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.raise_exc is not None:
            raise self.raise_exc
        content = json.dumps(self.body) if isinstance(self.body, dict | list) else self.body
        return httpx.Response(self.status, content=content, request=request)


def _source(transport: _Transport) -> LiveAlpacaSource:
    return LiveAlpacaSource("KEY", "SECRET", httpx.Client(transport=transport))


def test_live_source_sends_credentials_as_headers_never_in_the_url() -> None:
    """Scenario: Credentials are secrets."""
    t = _Transport(200, {"account_number": "PA1", "cash": "1", "buying_power": "2", "equity": "1"})
    AlpacaBroker(_source(t), "paper").account()
    request = t.requests[0]
    assert request.headers["APCA-API-KEY-ID"] == "KEY"
    assert request.headers["APCA-API-SECRET-KEY"] == "SECRET"
    assert "KEY" not in str(request.url) and "SECRET" not in str(request.url)
    assert str(request.url).startswith("https://paper-api.alpaca.markets/v2/account")
    live = AlpacaBroker(_source(_Transport(200, {"account_number": "L1", "cash": "1"})), "live")
    assert live.environment == "live"
    with pytest.raises(ConfigurationError):
        AlpacaBroker(_source(t), "sandbox")


@pytest.mark.parametrize(
    ("status", "body", "exc_type"),
    [
        (401, {"message": "unauthorized"}, ConfigurationError),
        (403, {"message": "forbidden"}, ConfigurationError),
        (422, {"code": 40010001, "message": "insufficient buying power"}, UsageError),
        (429, {"message": "too many requests"}, ProviderError),
        (500, "server error", ProviderError),
    ],
)
def test_alpaca_error_translation(status: int, body: Any, exc_type: type[Exception]) -> None:
    broker = AlpacaBroker(_source(_Transport(status, body)), "paper")
    with pytest.raises(exc_type):
        broker.submit_order(OrderRequest("c1", "AAPL", "buy", 1.0))


def test_alpaca_timeout_on_submission_is_unresolved_and_elsewhere_a_provider_error() -> None:
    """Scenario: Submission timeout leaves the order unresolved."""
    timeout = _Transport(200, {}, raise_exc=httpx.ReadTimeout("slow"))
    broker = AlpacaBroker(_source(timeout), "paper")
    with pytest.raises(SubmissionUnresolvedError) as exc:
        broker.submit_order(OrderRequest("c2", "AAPL", "buy", 1.0))
    assert exc.value.client_order_id == "c2" and "ReadTimeout" in exc.value.reason
    down = AlpacaBroker(_source(_Transport(200, {}, raise_exc=httpx.ConnectError("down"))), "paper")
    with pytest.raises(ProviderError, match="ConnectError"):
        down.account()
    missing = AlpacaBroker(_source(_Transport(404, {"message": "order not found"})), "paper")
    assert missing.get_order("x") is None and missing.find_order("y") is None


def test_alpaca_payloads_map_to_owned_models() -> None:
    doc = {
        "id": "61e69015-8549-4bfd-b9c3-01e75843f47d",
        "client_order_id": "sobres-1",
        "symbol": "aapl",
        "side": "buy",
        "qty": "6",
        "filled_qty": "2",
        "filled_avg_price": "100.5",
        "status": "partially_filled",
        "submitted_at": "2026-09-16T19:59:58.123456Z",
        "updated_at": "2026-09-16T19:59:59Z",
    }
    order = parse_order(doc)
    assert order.symbol == "AAPL" and order.status == "partially_filled"
    assert (
        order.quantity == 6.0 and order.filled_quantity == 2.0 and order.filled_avg_price == 100.5
    )
    assert order.submitted_at == datetime(2026, 9, 16, 19, 59, 58, 123456, tzinfo=UTC)
    assert parse_order({**doc, "status": "canceled"}).status == "cancelled"
    assert parse_order({**doc, "status": "something_new"}).status == "unresolved"
    assert parse_order({**doc, "filled_avg_price": None}).filled_avg_price is None
    quote_doc = {"symbol": "AAPL", "trade": {"t": "2026-09-16T19:59:58Z", "p": 101.25}}
    broker = AlpacaBroker(_source(_Transport(200, quote_doc)), "paper")
    quote = broker.quotes(["AAPL"])["AAPL"]
    assert quote.price == 101.25 and quote.as_of.tzinfo is not None
    activities = [
        {
            "activity_type": "FILL",
            "order_id": "o1",
            "symbol": "AAPL",
            "side": "sell",
            "qty": "4",
            "price": "110",
            "transaction_time": "2026-09-17T14:30:00Z",
        },
        {"activity_type": "CSD", "net_amount": "1000", "date": "2026-09-15"},
    ]
    broker = AlpacaBroker(_source(_Transport(200, activities)), "paper")
    fills = broker.fills()
    assert len(fills) == 1 and fills[0].quantity == 4.0 and fills[0].price == 110.0
    flows = broker.cash_flows()
    assert len(flows) == 1 and flows[0].amount == 1000.0 and flows[0].kind == "deposit"


def test_validate_credentials_never_raises() -> None:
    ok = validate_credentials("k", "s", client=httpx.Client(transport=_Transport(200, {"id": "x"})))
    assert ok.ok
    bad = validate_credentials("k", "s", client=httpx.Client(transport=_Transport(401, "no")))
    assert not bad.ok and "401" in bad.message
    down = validate_credentials(
        "k",
        "s",
        client=httpx.Client(transport=_Transport(200, {}, raise_exc=httpx.ConnectError("x"))),
    )
    assert not down.ok


def test_the_fixture_account_is_stamped_from_the_fixture_not_the_wall_clock() -> None:
    """A simulated account must not age: its quotes would go stale on a date nobody picked.

    `size_orders` rejects a quote older than five minutes relative to
    `account.as_of`. When the account was stamped with the wall clock and the
    quotes came from a file, every `trade` command and every test over them
    started failing five minutes after the fixture's newest quote -- which is
    what happened once real time passed it.
    """
    source = FixtureAlpacaSource(FIXTURES)
    broker = AlpacaBroker(source, "paper")

    account = broker.account()
    newest_quote = max(q.as_of for q in broker.quotes(["AAPL", "MSFT"]).values())

    assert account.as_of == source.as_of
    assert account.as_of >= newest_quote
    assert account.as_of - newest_quote < timedelta(minutes=5)
    # Two reads a moment apart report the same instant: nothing here follows a clock.
    assert broker.account().as_of == account.as_of


def test_a_live_source_still_stamps_the_account_with_the_wall_clock() -> None:
    """Only a source that knows the instant it represents overrides the clock."""
    source = _source(_Transport(200, {"account_number": "L1", "cash": "1", "currency": "USD"}))
    assert not hasattr(source, "as_of")

    before = datetime.now(UTC)
    account = AlpacaBroker(source, "paper").account()

    assert before <= account.as_of <= datetime.now(UTC)


def test_an_explicit_clock_wins_over_both() -> None:
    frozen = datetime(2020, 1, 1, tzinfo=UTC)
    broker = AlpacaBroker(FixtureAlpacaSource(FIXTURES), "paper", clock=lambda: frozen)
    assert broker.account().as_of == frozen
