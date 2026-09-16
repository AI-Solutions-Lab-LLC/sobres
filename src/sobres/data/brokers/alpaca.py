"""``AlpacaBroker``: the Alpaca Trading API v2 behind the ``Broker`` port.

Only ``LiveAlpacaSource`` talks HTTP (``httpx``, no vendor SDK). The broker maps
the documented JSON shapes — ``/v2/account``, ``/v2/positions``, ``/v2/orders``,
``/v2/account/activities`` and the market-data ``/v2/stocks/{symbol}/trades/latest``
— into the owned models, so a fixture source replaying those shapes exercises
the same code as production. Paper and live are different hosts and different
credentials; the environment is part of every request and every record.

Sources: https://docs.alpaca.markets/reference/getaccount-1,
https://docs.alpaca.markets/reference/postorder, https://docs.alpaca.markets/reference/getallorders,
https://docs.alpaca.markets/reference/getaccountactivities-1,
https://docs.alpaca.markets/reference/stocklatesttradesingle (checked 2026-09-16).
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any, Protocol

import httpx

from sobres.core.errors import ConfigurationError, ProviderError, UsageError
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
from sobres.settings import LiveResult

PROVIDER_NAME = "alpaca"
TRADING_URLS: dict[str, str] = {
    "paper": "https://paper-api.alpaca.markets",
    "live": "https://api.alpaca.markets",
}
DATA_URL = "https://data.alpaca.markets"
OBTAIN_URL = "https://app.alpaca.markets/paper/dashboard/overview"
TIMEOUT_S = 10.0
STATUS_MAP: dict[str, str] = {
    "new": "new",
    "pending_new": "new",
    "accepted": "accepted",
    "accepted_for_bidding": "accepted",
    "partially_filled": "partially_filled",
    "filled": "filled",
    "done_for_day": "expired",
    "canceled": "cancelled",
    "pending_cancel": "accepted",
    "pending_replace": "accepted",
    "replaced": "cancelled",
    "expired": "expired",
    "rejected": "rejected",
    "stopped": "expired",
    "suspended": "rejected",
    "calculated": "accepted",
    "held": "accepted",
}
CASH_FLOW_KINDS: dict[str, str] = {"CSD": "deposit", "CSW": "withdrawal", "DIV": "dividend"}


class AlpacaSource(Protocol):
    """The HTTP boundary: ``(status, json)`` for a request; fixtures replay it."""

    def request(
        self, method: str, url: str, *, params: dict[str, Any] | None = None, json: Any = None
    ) -> tuple[int, Any]: ...


class LiveAlpacaSource:
    def __init__(self, key_id: str, secret_key: str, client: httpx.Client | None = None) -> None:
        self._headers = {"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret_key}
        self._client = client or httpx.Client(timeout=TIMEOUT_S)

    def request(
        self, method: str, url: str, *, params: dict[str, Any] | None = None, json: Any = None
    ) -> tuple[int, Any]:
        try:
            response = self._client.request(
                method, url, params=params, json=json, headers=self._headers
            )
        except httpx.TimeoutException as exc:
            # The request may have reached the broker: the caller decides what that means.
            raise TimeoutError(type(exc).__name__) from exc
        except httpx.HTTPError as exc:
            raise ProviderError(
                f"request failed: {type(exc).__name__}",
                provider=PROVIDER_NAME,
                hint="check your network and retry",
            ) from exc
        try:
            body = response.json() if response.content else None
        except ValueError:
            body = response.text
        return response.status_code, body


def validate_credentials(
    key_id: str, secret_key: str, environment: str = "paper", client: httpx.Client | None = None
) -> LiveResult:
    """One cheap request to confirm the pair works. Never raises."""
    try:
        status, _ = LiveAlpacaSource(key_id, secret_key, client).request(
            "GET", f"{TRADING_URLS.get(environment, TRADING_URLS['paper'])}/v2/account"
        )
    except (ProviderError, TimeoutError) as exc:
        return LiveResult(False, f"could not reach Alpaca ({exc})")
    if status == 200:
        return LiveResult(True, f"Alpaca accepted the {environment} credentials")
    return LiveResult(False, f"Alpaca rejected the credentials (HTTP {status})")


def _when(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _num(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_order(doc: dict[str, Any]) -> BrokerOrder:
    status = STATUS_MAP.get(str(doc.get("status", "")), "unresolved")
    return BrokerOrder(
        id=str(doc["id"]),
        client_order_id=str(doc.get("client_order_id", "")),
        symbol=str(doc["symbol"]).upper(),
        side=str(doc.get("side", "")),
        quantity=_num(doc.get("qty"), 0.0) or 0.0,
        filled_quantity=_num(doc.get("filled_qty"), 0.0) or 0.0,
        filled_avg_price=_num(doc.get("filled_avg_price")),
        status=status,
        submitted_at=_when(doc.get("submitted_at")),
        updated_at=_when(doc.get("updated_at")),
        raw=dict(doc),
    )


class AlpacaBroker:
    name = PROVIDER_NAME

    def __init__(self, source: AlpacaSource, environment: str = "paper") -> None:
        if environment not in TRADING_URLS:
            raise ConfigurationError(
                f"alpaca environment must be paper or live, got {environment!r}",
                hint="run: sobres config set alpaca_environment paper",
            )
        self.environment = environment
        self._source = source
        self._base = TRADING_URLS[environment]

    @property
    def capabilities(self) -> BrokerCapabilities:
        # Fractional orders exist at Alpaca but only for market/day orders on eligible
        # assets; whole shares are the contract here until eligibility is modelled.
        return BrokerCapabilities(
            name=self.name, environments=("paper", "live"), fractional_shares=False
        )

    # ------------------------------------------------------------------ plumbing
    def _get(self, path: str, *, base: str | None = None, **params: Any) -> Any:
        status, body = self._source.request("GET", (base or self._base) + path, params=params)
        return self._check(status, body, path)

    def _check(self, status: int, body: Any, path: str) -> Any:
        if status in (401, 403):
            raise ConfigurationError(
                f"Alpaca rejected the {self.environment} credentials (HTTP {status})",
                hint="check SOBRES_ALPACA_KEY_ID / SOBRES_ALPACA_SECRET_KEY and the environment; "
                f"paper and live keys differ ({OBTAIN_URL})",
            )
        if status == 404:
            return None
        if status == 422:
            message = body.get("message") if isinstance(body, dict) else str(body)
            raise UsageError(f"Alpaca refused the request: {message}")
        if status == 429:
            raise ProviderError("rate limited", provider=self.name, hint="wait a minute and retry")
        if status >= 400:
            raise ProviderError(f"HTTP {status} for {path}", provider=self.name, hint="retry later")
        return body

    # --------------------------------------------------------------------- reads
    def account(self) -> BrokerAccount:
        doc = self._get("/v2/account")
        if not isinstance(doc, dict):
            raise ProviderError("account payload is not an object", provider=self.name)
        return BrokerAccount(
            id=str(doc.get("account_number") or doc.get("id")),
            environment=self.environment,
            currency=str(doc.get("currency", "USD")),
            cash=_num(doc.get("cash"), 0.0) or 0.0,
            buying_power=_num(doc.get("buying_power"), 0.0) or 0.0,
            equity=_num(doc.get("equity"), 0.0) or 0.0,
            as_of=datetime.now(UTC),
        )

    def positions(self) -> list[BrokerPosition]:
        docs = self._get("/v2/positions") or []
        out = []
        for doc in docs:
            out.append(
                BrokerPosition(
                    symbol=str(doc["symbol"]).upper(),
                    quantity=_num(doc.get("qty"), 0.0) or 0.0,
                    average_cost=_num(doc.get("avg_entry_price"), 0.0) or 0.0,
                    current_price=_num(doc.get("current_price"), 0.0) or 0.0,
                    market_value=_num(doc.get("market_value"), 0.0) or 0.0,
                    unrealized_pl=_num(doc.get("unrealized_pl"), 0.0) or 0.0,
                )
            )
        return sorted(out, key=lambda p: p.symbol)

    def quotes(self, symbols: Sequence[str]) -> dict[str, Quote]:
        out: dict[str, Quote] = {}
        for symbol in symbols:
            doc = self._get(f"/v2/stocks/{symbol.upper()}/trades/latest", base=DATA_URL)
            trade = doc.get("trade") if isinstance(doc, dict) else None
            if not trade or _num(trade.get("p")) is None:
                raise ProviderError(
                    f"no latest trade for {symbol}",
                    provider=self.name,
                    hint="check the symbol and the market-data entitlement",
                )
            when = _when(trade.get("t")) or datetime.now(UTC)
            out[symbol.upper()] = Quote(symbol.upper(), float(trade["p"]), when, source=self.name)
        return out

    # -------------------------------------------------------------------- orders
    def submit_order(self, request: OrderRequest) -> BrokerOrder:
        if not self.capabilities.fractional_shares and request.quantity != int(request.quantity):
            raise UsageError(f"{self.name} orders here are whole shares ({request.quantity})")
        body = {
            "symbol": request.symbol.upper(),
            "qty": str(int(request.quantity)),
            "side": request.side,
            "type": request.order_type,
            "time_in_force": request.time_in_force,
            "client_order_id": request.client_order_id,
        }
        try:
            status, doc = self._source.request("POST", self._base + "/v2/orders", json=body)
        except TimeoutError as exc:
            raise SubmissionUnresolvedError(request.client_order_id, str(exc)) from exc
        doc = self._check(status, doc, "/v2/orders")
        if not isinstance(doc, dict):
            raise ProviderError("order payload is not an object", provider=self.name)
        return parse_order(doc)

    def get_order(self, broker_order_id: str) -> BrokerOrder | None:
        doc = self._get(f"/v2/orders/{broker_order_id}")
        return None if doc is None else parse_order(doc)

    def find_order(self, client_order_id: str) -> BrokerOrder | None:
        doc = self._get("/v2/orders:by_client_order_id", client_order_id=client_order_id)
        return None if doc is None else parse_order(doc)

    def cancel_order(self, broker_order_id: str) -> BrokerOrder:
        status, body = self._source.request("DELETE", f"{self._base}/v2/orders/{broker_order_id}")
        if status not in (204, 404):
            self._check(status, body, "/v2/orders")
        order = self.get_order(broker_order_id)
        if order is None:
            raise UsageError(f"no order {broker_order_id} at Alpaca")
        return order

    def fills(self, since: datetime | None = None) -> list[Fill]:
        params: dict[str, Any] = {"activity_types": "FILL"}
        if since is not None:
            params["after"] = since.astimezone(UTC).isoformat()
        docs = self._get("/v2/account/activities", **params) or []
        out = []
        for doc in docs:
            when = _when(doc.get("transaction_time"))
            if when is None:
                continue
            out.append(
                Fill(
                    order_id=str(doc.get("order_id", "")),
                    symbol=str(doc.get("symbol", "")).upper(),
                    side=str(doc.get("side", "")),
                    quantity=_num(doc.get("qty"), 0.0) or 0.0,
                    price=_num(doc.get("price"), 0.0) or 0.0,
                    at=when,
                    source="broker",
                )
            )
        return sorted(out, key=lambda f: f.at)

    def cash_flows(self, since: datetime | None = None) -> list[CashFlow]:
        params: dict[str, Any] = {"activity_types": ",".join(CASH_FLOW_KINDS)}
        if since is not None:
            params["after"] = since.astimezone(UTC).isoformat()
        docs = self._get("/v2/account/activities", **params) or []
        out = []
        for doc in docs:
            when = _when(doc.get("date")) or _when(doc.get("transaction_time"))
            kind = CASH_FLOW_KINDS.get(str(doc.get("activity_type", "")))
            amount = _num(doc.get("net_amount"))
            if when is None or kind is None or amount is None:
                continue
            out.append(CashFlow(when, amount, kind))
        return sorted(out, key=lambda f: f.at)
