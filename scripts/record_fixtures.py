#!/usr/bin/env python3
"""Re-record ``tests/fixtures/`` from the live providers, deliberately.

Run with network access and commit the result on its own so a fixture change
is a reviewable diff, never an incidental one::

    python scripts/record_fixtures.py [--start 2015-01-02] [--end 2024-12-31]

Each provider directory gets a ``meta.json`` carrying the recording date and
the provider/library version. The offline suite parses exactly these files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, date, datetime
from importlib.metadata import version
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
TICKERS = ("AAPL", "MSFT", "NVDA", "JNJ", "XOM", "GLD", "VOD.L")
FRED_SERIES = ("DGS10", "DTB3", "DEXUSEU", "CPIAUCSL")
ECB_CURRENCIES = ("USD", "GBP", "JPY", "CHF")
KEN_FRENCH_FILES = (
    "F-F_Research_Data_Factors",
    "F-F_Research_Data_Factors_daily",
    "F-F_Research_Data_5_Factors_2x3",
    "F-F_Research_Data_5_Factors_2x3_daily",
    "F-F_Momentum_Factor",
    "F-F_Momentum_Factor_daily",
)


def _meta(provider: str, **extra: object) -> str:
    return (
        json.dumps(
            {
                "recorded_at": datetime.now(UTC).isoformat(),
                "provider": provider,
                "provider_version": (
                    version("yfinance") if provider == "yfinance" else "unversioned"
                ),
                "client": "yfinance" if provider == "yfinance" else "httpx",
                "client_version": version("yfinance" if provider == "yfinance" else "httpx"),
                "sha256": {
                    path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in sorted((ROOT / provider).iterdir())
                    if path.is_file() and path.name != "meta.json"
                },
                **extra,
            },
            indent=2,
        )
        + "\n"
    )


def record_yfinance(start: date, end: date) -> None:
    from sobres.data.yfinance_provider import LiveYahooSource

    out = ROOT / "yfinance"
    out.mkdir(parents=True, exist_ok=True)
    source = LiveYahooSource()
    tickers: dict[str, object] = {}
    for ticker in TICKERS:
        raw = source.history(ticker, start, end)
        raw.frame.round(6).to_csv(out / f"{ticker}.csv")
        tickers[ticker] = {k: raw.meta.get(k) for k in ("currency", "exchangeName", "symbol")}
    (out / "meta.json").write_text(
        _meta(
            "yfinance",
            source="https://query2.finance.yahoo.com/v8/finance/chart/{ticker}",
            start=start.isoformat(),
            end=end.isoformat(),
            serialization="history(auto_adjust=False, actions=False); CSV rounded to six decimals",
            tickers=tickers,
        ),
        encoding="utf-8",
    )


def record_fred(start: date, end: date, api_key: str) -> None:
    import httpx

    out = ROOT / "fred"
    out.mkdir(parents=True, exist_ok=True)
    for series_id in FRED_SERIES:
        response = httpx.get(
            "https://api.stlouisfed.org/fred/series/observations",
            params={
                "series_id": series_id,
                "api_key": api_key,
                "file_type": "json",
                "observation_start": start.isoformat(),
                "observation_end": end.isoformat(),
            },
            timeout=30,
        )
        if response.status_code != 200:
            # HTTPStatusError includes the request URL and its API key.
            raise RuntimeError(f"FRED recording failed (HTTP {response.status_code})")
        payload = response.json()
        (out / f"{series_id}.json").write_text(
            json.dumps(payload, indent=1) + "\n", encoding="utf-8"
        )
    (out / "meta.json").write_text(
        _meta(
            "fred",
            source="https://api.stlouisfed.org/fred/series/observations",
            api="fred/series/observations file_type=json",
            start=start.isoformat(),
            end=end.isoformat(),
        ),
        encoding="utf-8",
    )


def record_ecb(start: date, end: date) -> None:
    import httpx

    from sobres.data.ecb_provider import LiveEcbSource

    out = ROOT / "ecb"
    out.mkdir(parents=True, exist_ok=True)
    # Recording a decade is larger than an interactive data request.
    with httpx.Client(timeout=60.0) as client:
        source = LiveEcbSource(client)
        for currency in ECB_CURRENCIES:
            (out / f"{currency}.csv").write_text(source.csv(currency, start, end), encoding="utf-8")
    (out / "meta.json").write_text(
        _meta(
            "ecb",
            source="https://data-api.ecb.europa.eu/service/data/EXR",
            api="EXR/D.<CCY>.EUR.SP00.A?format=csvdata",
            start=start.isoformat(),
            end=end.isoformat(),
        ),
        encoding="utf-8",
    )


def record_ken_french() -> None:
    from sobres.data.ken_french import LiveKenFrenchSource

    out = ROOT / "ken_french"
    out.mkdir(parents=True, exist_ok=True)
    source = LiveKenFrenchSource()
    for stem in KEN_FRENCH_FILES:
        (out / f"{stem}.CSV").write_text(source.csv_text(stem), encoding="utf-8")
    (out / "meta.json").write_text(
        _meta(
            "ken_french",
            source="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp",
            provider_version=(out / f"{KEN_FRENCH_FILES[0]}.CSV")
            .read_text(encoding="utf-8")
            .splitlines()[0],
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    from sobres.config import resolve

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2015, 1, 2))
    parser.add_argument("--end", type=date.fromisoformat, default=date(2024, 12, 31))
    parser.add_argument(
        "--fred-api-key",
        default=None,
        help="defaults to the declared FRED setting; prefer sobres init",
    )
    parser.add_argument("--only", nargs="*", choices=["yfinance", "fred", "ecb", "ken_french"])
    args = parser.parse_args(argv)
    if args.end < args.start:
        parser.error("--end must be on or after --start")
    wanted = set(args.only or ["yfinance", "fred", "ecb", "ken_french"])
    if "yfinance" in wanted:
        record_yfinance(args.start, args.end)
    if "fred" in wanted:
        key = args.fred_api_key or resolve().get("fred_api_key")
        if not key:
            print(
                "FRED needs SOBRES_FRED_API_KEY or a configured fred_api_key; skipping",
                file=sys.stderr,
            )
        else:
            try:
                record_fred(args.start, args.end, str(key))
            except Exception as exc:
                # Transport errors may also contain a URL with the key.
                print(
                    f"FRED recording failed ({type(exc).__name__}); check key/network",
                    file=sys.stderr,
                )
                return 1
    if "ecb" in wanted:
        record_ecb(args.start, args.end)
    if "ken_french" in wanted:
        record_ken_french()
    print(f"fixtures written under {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
