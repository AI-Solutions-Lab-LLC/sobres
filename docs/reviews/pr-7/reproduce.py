"""Independent, offline probes for PR #7; run with the reviewed checkout's Python.

Usage: <checkout>/.venv/bin/python reproduce.py --checkout <checkout>
Optional: --base-python <clean-base-venv>/bin/python
These probes report observations, leave product code alone, and use temporary state.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd

from sobres.data.cache import ObservationCache
from sobres.data.currency import convert_frame
from sobres.data.fixtures import FixtureKenFrenchSource, FixtureYahooSource
from sobres.data.ken_french import KenFrenchProvider
from sobres.data.storage.base import OpenOptions, open_storage
from sobres.data.yfinance_provider import YFinanceProvider


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--base-python", type=Path)
    args = parser.parse_args()
    fixtures = args.checkout.resolve() / "tests" / "fixtures"
    findings = {}
    with tempfile.TemporaryDirectory(prefix="sobres-pr7-probes-") as directory:
        root = Path(directory)
        env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith(("SOBRES_", "OTEL_")) and key != "FRED_API_KEY"
        }
        env.update(
            SOBRES_CONFIG_FILE=str(root / "config.toml"),
            SOBRES_DB_URL=f"sqlite:///{root / 'cli.db'}",
        )

        def cli(*argv: str, python: Path | None = None) -> subprocess.CompletedProcess[str]:
            executable = (python or Path(sys.executable)).parent / "sobres"
            return subprocess.run(
                [str(executable), *argv],
                env=env,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )

        if args.base_python:
            result = cli(
                "data",
                "prices",
                "AAPL",
                "--start",
                "2024-01-02",
                "--end",
                "2024-01-10",
                python=args.base_python,
            )
            findings["base_install_prices"] = {
                "exit": result.returncode,
                "missing_yfinance": "yfinance is not installed" in result.stderr,
            }

        sentinel = "REVIEW-DUMMY-NOT-A-REAL-KEY-987654321"
        result = cli("--log-level", "DEBUG", "config", "set", "fred_api_key", sentinel)
        findings["config_set_secret"] = {
            "exit": result.returncode,
            "dummy_secret_in_stderr": sentinel in result.stderr,
            "dummy_secret_in_stdout": sentinel in result.stdout,
        }

        store = open_storage(f"sqlite:///{root / 'factors.db'}", OpenOptions())
        source = FixtureKenFrenchSource(fixtures)
        direct = KenFrenchProvider(source=source).get_factors(
            "ff3", "monthly", date(1926, 7, 1), date(1926, 7, 31)
        )
        cached = KenFrenchProvider(source=source, cache=ObservationCache(store.observations))
        cold = cached.get_factors("ff3", "monthly", date(1926, 7, 1), date(1926, 7, 31))
        warm = cached.get_factors("ff3", "monthly", date(1926, 7, 1), date(1926, 7, 31))
        findings["market_factor"] = {
            "direct": float(direct.iloc[0]["Mkt-RF"]),
            "cold_cache_missing": bool(cold["Mkt-RF"].isna().all()),
            "warm_cache_missing": bool(warm["Mkt-RF"].isna().all()),
        }
        store.close()

        store = open_storage(f"sqlite:///{root / 'revisions.db'}", OpenOptions())
        cache = ObservationCache(store.observations)
        first, last = date(2024, 1, 2), date(2024, 1, 3)

        def payload(values: list[float]) -> pd.DataFrame:
            return pd.DataFrame({"AAPL": values}, index=pd.to_datetime([first, last]))

        cache.get("test", "prices", ["AAPL"], first, last, lambda *_: payload([10.0, 11.0]))
        revised = cache.get(
            "test",
            "prices",
            ["AAPL"],
            first,
            last,
            lambda *_: payload([10.0, float("nan")]),
            refresh=True,
        )
        findings["refresh_withdrawn_observation"] = {
            "expected": "missing",
            "actual": float(revised.iloc[-1]["AAPL"]),
        }
        missing = cache.get(
            "test",
            "macro",
            ["GAP"],
            first,
            last,
            lambda *_: pd.DataFrame(
                {"GAP": [1.0, float("nan")]}, index=pd.to_datetime([first, last])
            ),
        )
        findings["all_missing_date"] = {"input_rows": 2, "cached_rows": len(missing)}
        store.close()

        store = open_storage(f"sqlite:///{root / 'weekend.db'}", OpenOptions())
        yahoo = YFinanceProvider(
            source=FixtureYahooSource(fixtures), cache=ObservationCache(store.observations)
        )
        yahoo.get_prices(["AAPL"], date(2024, 1, 2), date(2024, 1, 5))
        try:
            yahoo.get_prices(["AAPL"], date(2024, 1, 2), date(2024, 1, 7))
            findings["weekend_extension"] = {"error": None}
        except Exception as exc:
            findings["weekend_extension"] = {"error": type(exc).__name__, "message": str(exc)}
        store.close()

        frame = pd.DataFrame({"UNKNOWN": [100.0]}, index=pd.to_datetime([first]))
        converted = convert_frame(frame, "USD", rates=None)
        findings["unknown_currency"] = {
            "input_currency": frame.attrs.get("currency"),
            "output_currency": converted.attrs.get("currency"),
            "output_value": float(converted.iloc[0, 0]),
        }

        # Simulate an existing pre-migration database whose committed rows remain in WAL.
        db_path = root / "migration.db"
        writer = sqlite3.connect(db_path)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE user_authored (value TEXT)")
        writer.execute("INSERT INTO user_authored VALUES ('keep me')")
        writer.commit()
        backups = []
        store = open_storage(f"sqlite:///{db_path}", OpenOptions(on_backup=backups.append))
        backup = sqlite3.connect(backups[0])
        try:
            rows = backup.execute("SELECT value FROM user_authored").fetchall()
            findings["migration_backup"] = {"rows": rows}
        except sqlite3.Error as exc:
            findings["migration_backup"] = {"error": str(exc)}
        finally:
            backup.close()
            store.close()
            writer.close()

        # Real CLI: re-running unchanged init leaves an insecure config mode uncorrected.
        cli("init", "--non-interactive", "--offline", "--format", "json")
        Path(env["SOBRES_CONFIG_FILE"]).chmod(0o644)
        result = cli("init", "--non-interactive", "--offline", "--format", "json")
        report = json.loads(result.stdout)
        findings["init_failed_doctor"] = {
            "report_exit": report["exit_code"],
            "process_exit": result.returncode,
            "failed_checks": [c["name"] for c in report["checks"] if c["status"] == "fail"],
        }

    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    main()
