"""Independent PR 8 probes; run with its installed package, from its checkout.

Only synthetic prices/dummy credentials are used. All state is temporary.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pandas as pd

from sobres.cli.commands.optimize import BacktestParams, UniverseParams, backtest, load_universe
from sobres.core.optimize import Constraints, efficient_frontier, optimize
from sobres.core.returns import portfolio_returns
from sobres.core.risk import max_drawdown


def core_probes() -> dict:
    idx = pd.bdate_range("2020-01-01", periods=8)
    dd = max_drawdown(pd.Series([-0.5, 0.1, 0.1], index=idx[:3]))
    labels = ["A", "B"]
    mu = pd.Series([0.08, 0.13], index=labels)
    sigma = pd.DataFrame([[0.0144, 0.0072], [0.0072, 0.04]], index=labels, columns=labels)
    f = efficient_frontier(mu, sigma, n_points=5, risk_free=0.05)
    indefinite = pd.DataFrame([[1.0, 2.0], [2.0, 1.0]], index=labels, columns=labels)
    p = optimize(mu, indefinite, "min_variance", Constraints(allow_short=True))
    missing = portfolio_returns(
        pd.DataFrame({"A": [0.1, np.nan], "B": [0.0, 0.2]}), {"A": 0.5, "B": 0.5}
    )
    prices = pd.DataFrame(
        {"A": [100, 110, np.nan, 133.1, 146.41, 161.051, 177.1561, 194.87171]}, index=idx
    )
    prices.attrs = {"currency": {"A": "USD"}, "provider": "synthetic"}
    ctx = SimpleNamespace(
        price_provider=lambda: SimpleNamespace(get_prices=lambda *a: prices), log=Mock()
    )
    u = load_universe(
        UniverseParams(
            tickers=["A"], start=idx[0].date(), end=idx[-1].date(), fill="drop", risk_free=0.0
        ),
        ctx,
    )
    return {
        "initial_loss_drawdown": {"observed": dd.__dict__, "expected": -0.5},
        "frontier_count": {"requested": 5, "returned": len(f.points)},
        "non_psd_solve": {
            "eigenvalues": np.linalg.eigvalsh(indefinite).tolist(),
            "returned_weights": p.weights,
            "repair": p.estimators.psd_repair,
        },
        "implicit_missing_as_zero": missing.tolist(),
        "gap_bridge_daily_returns": {"frequency": u.frequency, "returns": u.returns["A"].tolist()},
    }


def lookahead_probe() -> dict:
    """Change only rates on/after the first trade; use the real CLI handler and solver."""
    index = pd.bdate_range("2020-01-01", periods=180)
    rng = np.random.default_rng(123)
    r = rng.normal([0.0004, 0.0007], [0.01, 0.02], (len(index), 2))
    prices = pd.DataFrame(100 * np.cumprod(1 + r, axis=0), index=index, columns=["A", "B"])
    prices.attrs = {"currency": {"A": "USD", "B": "USD"}, "provider": "synthetic"}
    start = index[100].date()
    p = BacktestParams(
        tickers=["A", "B"],
        start=start,
        end=index[-1].date(),
        fill="raise",
        lookback="60",
        rebalance="monthly",
    )
    reports = []
    for future_rate in [0.0, 20.0]:
        rates = pd.DataFrame({"DTB3": np.where(index.date >= start, future_rate, 0.0)}, index=index)
        ctx = SimpleNamespace(
            price_provider=lambda: SimpleNamespace(get_prices=lambda *a: prices.copy()),
            macro_provider=lambda rates=rates: SimpleNamespace(get_series=lambda *a: rates),
            config={"fred_api_key": "REVIEW-DUMMY-KEY"},
            log=Mock(),
            note=lambda *a: None,
        )
        report = backtest(p, ctx)
        first = min(report.weights_history)
        reports.append(
            {
                "future_dtb3_percent": future_rate,
                "first_trade": first,
                "first_weights": report.weights_history[first],
                "risk_free_note": report.provenance.notes[0],
            }
        )
    return {"prior_prices_and_rates_identical": True, "runs": reports}


def cli_probes(out: Path) -> list[dict]:
    with tempfile.TemporaryDirectory(prefix="sobres-pr8-probe-") as state:
        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith(("SOBRES_", "OTEL_")) and k != "FRED_API_KEY"
        }
        env.update(
            SOBRES_CONFIG_FILE=f"{state}/config.toml",
            SOBRES_DB_URL=f"sqlite:///{state}/db.sqlite",
            SOBRES_FIXTURE_DIR=str(Path.cwd() / "tests/fixtures"),
        )
        exe = str(Path(sys.executable).parent / "sobres")
        base = [
            "--tickers",
            "AAPL",
            "MSFT",
            "--start",
            "2019-01-01",
            "--end",
            "2020-12-31",
            "--fill",
            "ffill",
            "--risk-free",
            "0",
        ]
        cases = {
            "capm": ["optimize", "markowitz", *base, "--returns-estimator", "capm"],
            "target-backtest": [
                "optimize",
                "backtest",
                *base,
                "--lookback",
                "60",
                "--objective",
                "target_return",
            ],
            "target-backtest-option": [
                "optimize",
                "backtest",
                *base,
                "--lookback",
                "60",
                "--objective",
                "target_return",
                "--target",
                "0.1",
            ],
            "duplicate-risk": [
                "optimize",
                "risk",
                "--tickers",
                "AAPL",
                "AAPL",
                *base[3:],
                "--weights",
                "0.6",
                "0.4",
                "--format",
                "json",
            ],
            "nan-risk": ["optimize", "risk", *base, "--weights", "nan", "nan", "--format", "json"],
            "negative-seed": ["optimize", "markowitz", *base, "--seed", "-1"],
            "nan-riskfree": ["optimize", "markowitz", *base[:-1], "nan", "--format", "json"],
        }
        summary = []
        for name, args in cases.items():
            t = time.perf_counter()
            result = subprocess.run(
                [exe, *args], env=env, capture_output=True, text=True, timeout=60
            )
            (out / f"{name}.stdout").write_text(result.stdout, encoding="utf-8")
            (out / f"{name}.stderr").write_text(result.stderr, encoding="utf-8")
            summary.append(
                {
                    "case": name,
                    "exit": result.returncode,
                    "seconds": time.perf_counter() - t,
                    "stderr_tail": result.stderr[-450:],
                }
            )
        for command, extra in [
            ("markowitz", []),
            ("frontier", ["--points", "5"]),
            ("backtest", ["--lookback", "60"]),
            ("risk", ["--weights", "0.6", "0.4"]),
        ]:
            for fmt in ["table", "json", "csv"]:
                for level in ["ERROR", "WARNING", "INFO", "DEBUG"]:
                    name = f"{command}-{fmt}-{level}"
                    args = [
                        exe,
                        "--log-level",
                        level,
                        "optimize",
                        command,
                        *base,
                        *extra,
                        "--format",
                        fmt,
                    ]
                    t = time.perf_counter()
                    result = subprocess.run(
                        args, env=env, capture_output=True, text=True, timeout=60
                    )
                    (out / f"{name}.stdout").write_text(result.stdout, encoding="utf-8")
                    (out / f"{name}.stderr").write_text(result.stderr, encoding="utf-8")
                    summary.append(
                        {
                            "case": name,
                            "exit": result.returncode,
                            "seconds": time.perf_counter() - t,
                            "rows": (
                                len(json.loads(result.stdout).get("rows", []))
                                if fmt == "json" and result.returncode == 0
                                else None
                            ),
                        }
                    )
            print(f"completed {command} formats/log levels", flush=True)
        return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-cli", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    result = {"core": core_probes(), "lookahead": lookahead_probe()}
    (args.output / "independent.json").write_text(
        json.dumps(result, indent=2, default=str), encoding="utf-8"
    )
    print(json.dumps(result, indent=2, default=str), flush=True)
    if not args.skip_cli:
        summary = cli_probes(args.output)
        (args.output / "cli-summary.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8"
        )
        print(json.dumps(summary[:7], indent=2), flush=True)
