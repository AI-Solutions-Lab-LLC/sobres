#!/usr/bin/env python3
"""Synthesize ``tests/fixtures/synthetic/yfinance/SPY.csv``: a market proxy for offline tests.

The recording environment cannot reach Yahoo for a real SPY history, and the
forecasting default benchmark is ``ticker:SPY``. This proxy is the equal-weight,
daily-rebalanced basket of the six USD tickers that *were* recorded
(AAPL, MSFT, NVDA, JNJ, XOM, GLD), normalized to 200 on the first common date;
its volume is the sum of their share volumes. It exercises the parser and the
forecasting pipeline with a plausible broad-market series; it is not SPY and
``meta.json`` says so (``synthesized_at``, ``synthetic: true``), which the fixture
source surfaces as a provenance flag. Replace it with a recording by adding
``SPY`` to ``scripts/record_fixtures.py`` when network access exists.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "tests" / "fixtures"
RECORDED = ROOT / "yfinance"
OUT = ROOT / "synthetic" / "yfinance"
BASKET = ("AAPL", "MSFT", "NVDA", "JNJ", "XOM", "GLD")
BASE = 200.0


def main() -> None:
    frames = {t: pd.read_csv(RECORDED / f"{t}.csv", index_col=0) for t in BASKET}
    common = None
    for frame in frames.values():
        common = frame.index if common is None else common.intersection(frame.index)
    assert common is not None
    closes = pd.DataFrame({t: f.loc[common, "Close"] for t, f in frames.items()})
    adjusted = pd.DataFrame({t: f.loc[common, "Adj Close"] for t, f in frames.items()})
    volumes = pd.DataFrame({t: f.loc[common, "Volume"] for t, f in frames.items()})
    close = (closes / closes.iloc[0]).mean(axis=1) * BASE
    # One constant adjustment factor: the basket pays no modelled dividend, so the
    # adjusted series is proportional to the close (no spurious adjustment flags).
    adj = close * float(adjusted.iloc[0].mean() / closes.iloc[0].mean())
    out = pd.DataFrame(
        {
            "Open": close,
            "High": close,
            "Low": close,
            "Close": close,
            "Adj Close": adj,
            "Volume": volumes.sum(axis=1).astype("int64"),
        },
        index=common,
    ).round(6)
    out.index.name = "Date"
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "SPY.csv", lineterminator="\n")
    meta_path = OUT / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    meta.update(
        {
            "recorded_at": None,
            "synthesized_at": datetime.now(UTC).isoformat(),
            "provider": "yfinance",
            "note": (
                "SPY is an equal-weight daily-rebalanced basket of the recorded USD tickers "
                f"{', '.join(BASKET)}, normalized to {BASE:.0f}; volume is their summed share "
                "volume. A market proxy for offline tests, not a recording of SPY."
            ),
            "tickers": {
                **meta.get("tickers", {}),
                "SPY": {
                    "currency": "USD",
                    "exchangeName": "synthetic",
                    "symbol": "SPY",
                    "synthetic": True,
                },
            },
        }
    )
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"synthesized SPY proxy: {len(out)} rows -> {OUT / 'SPY.csv'}")


if __name__ == "__main__":
    main()
