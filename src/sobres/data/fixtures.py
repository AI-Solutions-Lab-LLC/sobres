"""Provider sources that replay recorded payloads from ``tests/fixtures/``.

Each source reads exactly what ``scripts/record_fixtures.py`` writes and feeds
it to the same parser the live source feeds, so the offline suite exercises the
real parsing path. ``SOBRES_FIXTURE_DIR`` points a whole run at a directory of
them — the test suite and CI's clean-install smoke test use that.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from sobres.core.errors import InsufficientDataError, ProviderError, UnknownTickerError
from sobres.data.yfinance_provider import RawHistory


class FixtureYahooSource:
    """``<dir>/yfinance/<TICKER>.csv`` plus ``<dir>/yfinance/meta.json``."""

    def __init__(self, root: Path) -> None:
        self.root = root / "yfinance"
        self.calls: list[tuple[str, date, date]] = []

    def history(self, ticker: str, start: date, end: date) -> RawHistory:
        self.calls.append((ticker, start, end))
        path = self.root / f"{ticker.upper()}.csv"
        meta_root = self.root
        if not path.exists():
            # The explicitly separated synthetic corpus (a market proxy); its meta says so.
            synthetic = self.root.parent / "synthetic" / "yfinance"
            path = synthetic / f"{ticker.upper()}.csv"
            meta_root = synthetic
        if not path.exists():
            raise UnknownTickerError(ticker, provider="yfinance")
        frame = pd.read_csv(path, index_col=0)
        # CSV timestamps retain numeric offsets, which vary over DST. Parse
        # each independently and preserve its local date, just as the live
        # provider does; converting through UTC would shift some market dates.
        frame.index = pd.DatetimeIndex(
            [pd.Timestamp(value).tz_localize(None) for value in frame.index], name="Date"
        ).normalize()
        frame = frame.loc[str(start) : str(end)]
        meta_all = json.loads((meta_root / "meta.json").read_text(encoding="utf-8"))
        meta = dict(meta_all.get("tickers", {}).get(ticker.upper(), {}))
        if meta_root is not self.root:
            meta["synthetic"] = True
        return RawHistory(frame=frame, currency=meta.get("currency"), meta=meta)

    def fundamentals(self, ticker: str) -> dict[str, Any] | None:
        """Recorded fundamentals, or the explicitly separated synthetic fixture corpus."""
        path = self.root / "fundamentals.json"
        if not path.exists():
            path = self.root.parent / "synthetic" / "yfinance" / "fundamentals.json"
        if not path.exists():
            return None
        docs = json.loads(path.read_text(encoding="utf-8")).get("tickers", {})
        info = docs.get(ticker.upper())
        return dict(info) if info else None


class FixtureFredSource:
    """``<dir>/fred/<SERIES>.json`` — the API's JSON response body."""

    def __init__(self, root: Path) -> None:
        self.root = root / "fred"
        self.calls: list[tuple[str, date, date]] = []

    def observations(self, series_id: str, start: date, end: date) -> list[dict[str, Any]]:
        self.calls.append((series_id, start, end))
        path = self.root / f"{series_id.upper()}.json"
        if not path.exists():
            path = self.root.parent / "synthetic" / "fred" / f"{series_id.upper()}.json"
        if not path.exists():
            raise UnknownTickerError(series_id, provider="fred")
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("observations")
        if not isinstance(rows, list):
            raise ProviderError("fixture has no 'observations' list", provider="fred")
        return [r for r in rows if start.isoformat() <= r["date"] <= end.isoformat()]


class FixtureEcbSource:
    """``<dir>/ecb/<CCY>.csv`` — the SDMX csvdata body."""

    def __init__(self, root: Path) -> None:
        self.root = root / "ecb"
        self.calls: list[tuple[str, date, date]] = []

    def csv(self, currency: str, start: date, end: date) -> str:
        self.calls.append((currency, start, end))
        path = self.root / f"{currency.upper()}.csv"
        if not path.exists():
            raise ProviderError(
                f"the ECB publishes no reference rate for {currency}", provider="ecb"
            )
        lines = path.read_text(encoding="utf-8").splitlines()
        header, rows = lines[0], lines[1:]
        columns = header.split(",")
        period = columns.index("TIME_PERIOD")
        kept = [r for r in rows if start.isoformat() <= r.split(",")[period] <= end.isoformat()]
        return "\n".join([header, *kept]) + "\n"


class FixtureKenFrenchSource:
    """``<dir>/ken_french/<FILE_STEM>.CSV`` — the CSV inside the published zip."""

    def __init__(self, root: Path) -> None:
        self.root = root / "ken_french"
        self.calls: list[str] = []

    def csv_text(self, file_stem: str) -> str:
        self.calls.append(file_stem)
        path = self.root / f"{file_stem}.CSV"
        if not path.exists():
            raise ProviderError(f"no fixture for {file_stem}", provider="ken_french")
        return path.read_text(encoding="utf-8")


class FixtureDocumentSource:
    """``<dir>/<provider>/<COUNTRY>.<ext>``: one raw document per country (WB, OECD, BIS)."""

    def __init__(self, root: Path, provider: str, ext: str) -> None:
        self.root = root / provider
        self.provider = provider
        self.ext = ext
        self.calls: list[str] = []

    def payload(self, country: str) -> str:
        self.calls.append(country)
        path = self.root / f"{country.upper()}.{self.ext}"
        if not path.exists():
            raise InsufficientDataError(
                f"{self.provider} has no series for {country}",
                hint="check the ISO 3166-1 alpha-3 code",
            )
        return path.read_text(encoding="utf-8")


def fixture_source(provider: str, root: Path) -> Any:
    sources: dict[str, Any] = {
        "yfinance": FixtureYahooSource,
        "fred": FixtureFredSource,
        "ecb": FixtureEcbSource,
        "ken_french": FixtureKenFrenchSource,
        "worldbank": lambda r: FixtureDocumentSource(r, "worldbank", "json"),
        "oecd": lambda r: FixtureDocumentSource(r, "oecd", "csv"),
        "bis": lambda r: FixtureDocumentSource(r, "bis", "csv"),
    }
    return sources[provider](root)


class FixtureAlpacaSource:
    """``<dir>/synthetic/alpaca/*.json`` — a simulated paper account in Alpaca's shapes.

    Market orders fill at once at the fixture quote; positions, orders, fills and
    cash update in ``state`` (a plain dict the caller persists between processes, so
    successive CLI invocations see one account). It is explicitly synthetic and says
    so in ``meta.json``; the parser it feeds is the production one.
    """

    def __init__(
        self,
        root: Path,
        *,
        state: dict[str, Any] | None = None,
        on_change: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.root = root / "synthetic" / "alpaca"
        self._on_change = on_change
        self.calls: list[tuple[str, str]] = []
        self.timeout_next_post = False
        base = json.loads((self.root / "account.json").read_text(encoding="utf-8"))
        self.state: dict[str, Any] = state or {
            "cash": float(base["cash"]),
            "positions": {},  # symbol -> {"qty", "avg"}
            "orders": [],
            "fills": [],
            "flows": [],
            "seq": 0,
        }
        self._account = base
        self._quotes = json.loads((self.root / "quotes.json").read_text(encoding="utf-8"))

    def _save(self) -> None:
        if self._on_change is not None:
            self._on_change(self.state)

    def _order_doc(self, order: dict[str, Any]) -> dict[str, Any]:
        return dict(order)

    def request(
        self, method: str, url: str, *, params: dict[str, Any] | None = None, json: Any = None
    ) -> tuple[int, Any]:
        self.calls.append((method, url))
        path = url.split(".markets", 1)[-1]
        params = params or {}
        if method == "GET" and path == "/v2/account":
            positions = self.state["positions"]
            equity = self.state["cash"] + sum(
                p["qty"] * self._price(sym) for sym, p in positions.items()
            )
            return 200, {
                **self._account,
                "cash": f"{self.state['cash']:.2f}",
                "buying_power": f"{self.state['cash']:.2f}",
                "equity": f"{equity:.2f}",
            }
        if method == "GET" and path == "/v2/positions":
            out = []
            for sym, p in sorted(self.state["positions"].items()):
                if p["qty"] == 0:
                    continue
                price = self._price(sym)
                out.append(
                    {
                        "symbol": sym,
                        "qty": str(p["qty"]),
                        "avg_entry_price": str(p["avg"]),
                        "current_price": str(price),
                        "market_value": str(p["qty"] * price),
                        "unrealized_pl": str((price - p["avg"]) * p["qty"]),
                    }
                )
            return 200, out
        if method == "GET" and path.startswith("/v2/stocks/") and path.endswith("/trades/latest"):
            symbol = path.split("/")[3].upper()
            doc = self._quotes.get(symbol)
            if not doc:
                return 404, {"message": "symbol not found"}
            # The simulated clock advances with every order, so a new preview after a
            # fill carries a new quote time (and therefore a new plan hash), as in life.
            stamped = {**doc, "trade": {**doc["trade"], "t": self._stamp(doc["trade"]["t"])}}
            return 200, stamped
        if method == "POST" and path == "/v2/orders":
            return self._submit(json or {})
        if method == "GET" and path == "/v2/orders:by_client_order_id":
            cid = params.get("client_order_id")
            for order in self.state["orders"]:
                if order["client_order_id"] == cid:
                    return 200, self._order_doc(order)
            return 404, {"message": "order not found"}
        if method in ("GET", "DELETE") and path.startswith("/v2/orders/"):
            oid = path.rsplit("/", 1)[-1]
            for order in self.state["orders"]:
                if order["id"] == oid:
                    if method == "DELETE" and order["status"] not in ("filled", "canceled"):
                        order["status"] = "canceled"
                        self._save()
                        return 204, None
                    return (200, self._order_doc(order)) if method == "GET" else (204, None)
            return 404, {"message": "order not found"}
        if method == "GET" and path == "/v2/account/activities":
            kinds = str(params.get("activity_types", "")).split(",")
            after = str(params.get("after", "")).replace("+00:00", "Z")
            docs: list[dict[str, Any]] = []
            if "FILL" in kinds:
                docs.extend(self.state["fills"])
            for flow in self.state["flows"]:
                if flow["activity_type"] in kinds:
                    docs.append(flow)
            if after:
                docs = [d for d in docs if str(d.get("transaction_time") or d.get("date")) > after]
            return 200, docs
        return 404, {"message": f"no fixture route for {method} {path}"}

    def _stamp(self, base: str) -> str:
        from datetime import datetime, timedelta

        when = datetime.fromisoformat(base.replace("Z", "+00:00"))
        return (when + timedelta(seconds=int(self.state.get("seq", 0)))).strftime(
            "%Y-%m-%dT%H:%M:%S.%fZ"
        )

    def _price(self, symbol: str) -> float:
        doc = self._quotes.get(symbol.upper())
        return float(doc["trade"]["p"]) if doc else 0.0

    def _submit(self, body: dict[str, Any]) -> tuple[int, Any]:
        symbol = str(body.get("symbol", "")).upper()
        if symbol not in self._quotes:
            return 422, {"code": 40010001, "message": f"asset {symbol} not found"}
        if any(o["client_order_id"] == body.get("client_order_id") for o in self.state["orders"]):
            return 422, {"code": 40010001, "message": "client_order_id must be unique"}
        qty = float(body.get("qty", 0))
        price = self._price(symbol)
        self.state["seq"] += 1
        oid = f"synthetic-order-{self.state['seq']:04d}"
        when = self._stamp("2026-09-16T20:00:00.000000Z")
        pos = self.state["positions"].setdefault(symbol, {"qty": 0.0, "avg": 0.0})
        status = "filled"
        if body.get("side") == "buy":
            cost = qty * price
            if cost > self.state["cash"] + 1e-9:
                status = "rejected"
            else:
                self.state["cash"] -= cost
                new_qty = pos["qty"] + qty
                pos["avg"] = (pos["qty"] * pos["avg"] + qty * price) / new_qty
                pos["qty"] = new_qty
        else:
            if qty > pos["qty"] + 1e-9:
                status = "rejected"
            else:
                self.state["cash"] += qty * price
                pos["qty"] -= qty
        filled = qty if status == "filled" else 0.0
        order = {
            "id": oid,
            "client_order_id": body.get("client_order_id", ""),
            "symbol": symbol,
            "side": body.get("side"),
            "qty": str(qty),
            "filled_qty": str(filled),
            "filled_avg_price": str(price) if filled else None,
            "status": status,
            "type": body.get("type", "market"),
            "time_in_force": body.get("time_in_force", "day"),
            "submitted_at": when,
            "updated_at": when,
        }
        self.state["orders"].append(order)
        if filled:
            self.state["fills"].append(
                {
                    "activity_type": "FILL",
                    "id": f"{when}::{oid}",
                    "order_id": oid,
                    "symbol": symbol,
                    "side": body.get("side"),
                    "qty": str(qty),
                    "price": str(price),
                    "transaction_time": when,
                    "type": "fill",
                }
            )
        self._save()
        if self.timeout_next_post:
            self.timeout_next_post = False
            raise TimeoutError("ReadTimeout")
        return 200, self._order_doc(order)
