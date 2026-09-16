"""``sobres econ`` end to end, offline.

Scenarios: Tests reported; ACF and PACF; Default stock forecast; Removed
univariate selection; Keyless basic preset; Sector input; Invalid system;
Splits, dividends and unsupported currency; Market revisions and gaps;
Intervals are mandatory; Comparable models; Shrinkage and prior are visible;
Insufficient evaluation history; Reproducible run; Catalog source resolution;
Named source; GARCH fit; Annualized output; Robust standard errors;
Multicollinearity; Diagnostics reported; Missing extra; Forecasting is exposed
like every command.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import pytest

from sobres.cli.commands.econ import FRED_CATALOG, resolve_source
from sobres.core.timeseries import ECON_HINT
from tests.conftest import SENTINEL_KEY

pytest.importorskip("statsmodels")
pytest.importorskip("arch")
KEY = {"SOBRES_FRED_API_KEY": SENTINEL_KEY}
WINDOW = ["--start", "2015-01-01", "--end", "2024-12-31"]
FAST = ["--draws", "100", "--refits", "5"]  # small simulation budgets keep the suite quick
FORECAST_COLUMNS = [
    "date",
    "forecast",
    "mean_price",
    "lower80",
    "upper80",
    "lower95",
    "upper95",
    "log_return_point",
]


def _json(result: Any) -> dict[str, Any]:
    assert result.exit_code == 0, result.stderr
    return json.loads(result.stdout)


def test_diagnose_reports_both_tests_and_the_acf_pacf_table(cli: Callable[..., Any]) -> None:
    doc = _json(cli("econ", "diagnose", "DEXUSEU", *WINDOW, "--format", "json", env_extra=KEY))
    assert doc["adf"]["conclusion"] in ("stationary", "non-stationary")
    assert doc["kpss"]["conclusion"] in ("stationary", "non-stationary")
    assert isinstance(doc["agree"], bool) and doc["verdict"]
    assert [r["lag"] for r in doc["rows"]] == list(range(1, 21))
    assert all(
        {"acf", "pacf", "acf_significant", "pacf_significant"} <= set(r) for r in doc["rows"]
    )
    table = cli("econ", "diagnose", "DEXUSEU", *WINDOW, "--format", "table", env_extra=KEY)
    assert "ADF (H0 unit root)" in table.stdout and "KPSS (H0 stationary)" in table.stdout
    assert "significance bound" in table.stdout
    if not doc["agree"]:
        assert "the tests disagree" in table.stdout
    ticker = _json(cli("econ", "diagnose", "ticker:AAPL", *WINDOW, "--format", "json"))
    assert ticker["series"] == "AAPL"


def test_catalog_source_resolution_never_guesses_from_shape() -> None:
    """Scenario: Catalog source resolution. Scenario: Named source."""
    assert resolve_source("fred:CPIAUCSL") == ("fred", "CPIAUCSL")
    assert resolve_source("ticker:SPY") == ("ticker", "SPY")
    assert resolve_source("DGS10") == ("fred", "DGS10")  # in the catalog
    assert "DGS10" in FRED_CATALOG and "VIXCLS" in FRED_CATALOG
    # Long, digit-bearing symbols used to be guessed as FRED; now only the catalog decides.
    assert resolve_source("BRK.B") == ("ticker", "BRK.B")
    assert resolve_source("ABCDEFGH") == ("ticker", "ABCDEFGH")
    assert resolve_source("XYZ12") == ("ticker", "XYZ12")
    assert resolve_source("XYZ12", "fred") == ("fred", "XYZ12")
    assert resolve_source("ticker:DGS10", "fred") == ("ticker", "DGS10")  # the prefix wins


def test_default_stock_forecast_is_a_joint_model_with_held_out_evidence(
    cli: Callable[..., Any],
) -> None:
    """Scenario: Default stock forecast. Scenario: Keyless basic preset.
    Scenario: Intervals are mandatory. Scenario: Market revisions and gaps.
    Scenario: Reproducible run."""
    args = ["econ", "forecast", "ticker:AAPL", *WINDOW, *FAST]
    doc = _json(cli(*args, "--format", "json"))
    assert doc["model"] == "var" and doc["model_version"] == "var/v1"
    assert doc["preset"] == "equity-basic" and doc["catalog_version"] == "equity-basic/v1"
    assert doc["horizon"] == 20 and len(doc["rows"]) == 20
    assert doc["benchmark"] == "SPY" and doc["sector"] is None
    assert [p["column"] for p in doc["predictors"]] == [
        "AAPL_ret",
        "SPY_ret",
        "AAPL_logrv20",
        "AAPL_dlogdv20",
    ]
    assert all({"formula", "role", "source", "window"} <= set(p) for p in doc["predictors"])
    assert doc["lag"] in (1, 2, 5) and doc["penalty"] in (0.01, 0.1, 1.0, 10.0)
    assert len(doc["candidates"]) == 12 and all("loss" in c for c in doc["candidates"])
    assert doc["columns"] == FORECAST_COLUMNS
    for row in doc["rows"]:
        assert row["lower95"] <= row["lower80"] <= row["forecast"] <= row["upper80"]
        assert row["upper80"] <= row["upper95"]
    assert doc["anchor_price"] == pytest.approx(250.419998)  # the last split-only close
    assert doc["origin"] == "2024-12-31" and doc["currency"] == "USD"
    assert "split-only" in doc["price_basis"]
    ev = doc["evaluation"]
    assert ev["n_outcomes"] >= 12 and ev["controls"] == ["no_change", "training_mean"]
    assert set(ev["metrics"]) == {"var", "no_change", "training_mean"}
    for name in ("var", "no_change", "training_mean"):
        assert ev["metrics"][name]["n"] == ev["n_outcomes"]
    assert {"coverage80", "coverage95", "width80"} <= set(ev["metrics"]["var"])
    assert doc["draws"]["usable"] == 100 and doc["draws"]["rejected"] == 0
    assert doc["seed"] == 0
    notes = " ".join(doc["provenance"]["notes"])
    assert "revised-market-data" in notes and "gaps: policy raise" in notes
    assert any(
        f["symbol"] == "SPY" and f.get("kind") == "synthetic" for f in doc["provenance"]["flags"]
    )
    # Reproducible: the same inputs, cache and seed give the same document (the
    # cache's fetched_at stamp is the one value that legitimately differs).
    again = _json(cli(*args, "--format", "json"))
    for document in (doc, again):
        document["provenance"].pop("fetched_at", None)
        document["provenance"].pop("cache", None)
    assert again == doc
    different = _json(cli(*args, "--seed", "7", "--format", "json"))
    assert different["seed"] == 7 and different["rows"][-1] != doc["rows"][-1]
    table = cli(*args, "--format", "table")
    assert "VAR (var/v1)" in table.stdout and "held-out" in table.stdout
    assert "seed 0" in table.stdout and "median of the price draws" in table.stdout
    assert "outer dates never tune" in table.stdout
    assert "Not investment advice" in table.stdout
    csv = cli(*args, "--format", "csv")
    assert csv.stdout.splitlines()[0] == "step," + ",".join(FORECAST_COLUMNS)
    assert len(csv.stdout.splitlines()) == 21


def test_removed_arima_model_exits_2_with_the_new_example(cli: Callable[..., Any]) -> None:
    """Scenario: Removed univariate selection."""
    for model in ("arima", "ARIMA", "sarima"):
        out = cli("econ", "forecast", "ticker:AAPL", "--model", model, *WINDOW)
        assert out.exit_code == 2, out.stderr
        assert "removed" in out.stderr and "choose var or bvar" in out.stderr
        assert "econ forecast ticker:AAPL --model var --horizon 20" in out.stderr
    old_flag = cli("econ", "forecast", "ticker:AAPL", "--order", "1,1,0", *WINDOW)
    assert old_flag.exit_code == 2 and "--order" in old_flag.stderr + old_flag.stdout
    bad_horizon = cli("econ", "forecast", "ticker:AAPL", "--horizon", "7", *WINDOW)
    assert bad_horizon.exit_code == 2 and "1, 5, 20" in bad_horizon.stderr


def test_sector_joins_the_state_and_invalid_systems_are_refused(
    cli: Callable[..., Any],
) -> None:
    """Scenario: Sector input. Scenario: Invalid system."""
    doc = _json(
        cli(
            "econ",
            "forecast",
            "ticker:AAPL",
            "--sector",
            "ticker:XOM",
            "--horizon",
            "5",
            *WINDOW,
            *FAST,
            "--format",
            "json",
        )
    )
    assert doc["sector"] == "XOM" and doc["predictors"][-1]["column"] == "XOM_ret"
    assert doc["predictors"][-1]["role"] == "sector return"
    same = cli("econ", "forecast", "ticker:AAPL", "--sector", "ticker:SPY", *WINDOW, *FAST)
    assert same.exit_code == 2 and "duplicates" in same.stderr
    self_bench = cli("econ", "forecast", "ticker:AAPL", "--benchmark", "ticker:AAPL", *WINDOW)
    assert self_bench.exit_code == 2 and "also the benchmark" in self_bench.stderr
    fred = cli("econ", "forecast", "ticker:AAPL", "--benchmark", "DGS10", *WINDOW)
    assert fred.exit_code == 2 and "must be a price ticker" in fred.stderr


def test_mixed_currency_is_refused_before_fitting(cli: Callable[..., Any]) -> None:
    """Scenario: Splits, dividends and unsupported currency."""
    out = cli("econ", "forecast", "ticker:AAPL", "--benchmark", "ticker:VOD.L", *WINDOW, *FAST)
    assert out.exit_code == 2, out.stderr
    assert "different currencies" in out.stderr and "GBP" in out.stderr
    assert "no exchange rate is projected" in out.stderr


def test_bvar_reports_its_prior_and_selects_tightness_on_inner_blocks(
    cli: Callable[..., Any],
) -> None:
    """Scenario: Shrinkage and prior are visible."""
    doc = _json(
        cli(
            "econ",
            "forecast",
            "ticker:AAPL",
            "--model",
            "bvar",
            "--horizon",
            "5",
            *WINDOW,
            "--draws",
            "100",
            "--format",
            "json",
        )
    )
    assert doc["model"] == "bvar" and doc["refits"] is None
    assert doc["prior"]["tightness"] == doc["penalty"] in (0.1, 0.2, 0.5)
    assert doc["prior"]["nu0"] == len(doc["predictors"]) + 2
    assert doc["prior"]["b0"].startswith("zero")
    assert {c["penalty"] for c in doc["candidates"]} == {0.1, 0.2, 0.5}
    assert doc["selection"]["blocks"] == 3 and doc["selection"]["purge"] == 5
    assert "posterior" in doc["draws"]["method"]
    fixed = _json(
        cli(
            "econ",
            "forecast",
            "ticker:AAPL",
            "--model",
            "bvar",
            "--lag",
            "2",
            "--horizon",
            "5",
            *WINDOW,
            "--draws",
            "100",
            "--format",
            "json",
        )
    )
    assert fixed["lag"] == 2 and {c["lag"] for c in fixed["candidates"]} == {2}


def test_evaluate_scores_models_and_controls_on_identical_dates(
    cli: Callable[..., Any],
) -> None:
    """Scenario: Comparable models."""
    doc = _json(cli("econ", "evaluate", "ticker:AAPL", *WINDOW, *FAST, "--format", "json"))
    assert doc["models"] == ["var", "bvar"]
    assert [r["model"] for r in doc["rows"]] == ["var", "no_change", "training_mean", "bvar"]
    n = doc["n_outcomes"]
    assert n >= 12 and all(r["n"] == n for r in doc["rows"])
    assert [s["origin_row"] for s in doc["selections"]["var"]] == [
        s["origin_row"] for s in doc["selections"]["bvar"]
    ]
    by_model = {r["model"]: r for r in doc["rows"]}
    assert by_model["no_change"]["oos_r2_vs_no_change"] == 0.0
    assert by_model["no_change"]["coverage80"] is None  # controls carry no interval
    assert by_model["var"]["coverage95"] is not None
    table = cli("econ", "evaluate", "ticker:AAPL", *WINDOW, *FAST, "--format", "table")
    assert "identical held-out origins" in table.stdout
    assert "outer results never choose a winner" in table.stdout
    one = _json(
        cli(
            "econ", "evaluate", "ticker:AAPL", "--models", "var", *WINDOW, *FAST, "--format", "json"
        )
    )
    assert [r["model"] for r in one["rows"]] == ["var", "no_change", "training_mean"]


def test_insufficient_evaluation_history_names_counts(cli: Callable[..., Any]) -> None:
    """Scenario: Insufficient evaluation history."""
    out = cli(
        "econ",
        "forecast",
        "ticker:AAPL",
        "--start",
        "2022-01-01",
        "--end",
        "2024-12-31",
        *FAST,
    )
    assert out.exit_code == 5, out.stderr
    assert "training rows" in out.stderr or "held-out outcomes" in out.stderr
    assert "widen --start" in out.stderr


def test_volatility_is_annualized_with_intervals_and_a_printed_seed(
    cli: Callable[..., Any],
) -> None:
    args = [
        "econ",
        "volatility",
        "AAPL",
        "--horizon",
        "5",
        "--simulations",
        "150",
        "--start",
        "2022-01-01",
        "--end",
        "2024-12-31",
    ]
    doc = _json(cli(*args, "--seed", "1", "--format", "json"))
    assert doc["model"] == "garch" and doc["seed"] == 1 and doc["frequency"] == "daily"
    assert set(doc["params"]) >= {"omega", "alpha[1]", "beta[1]"}
    assert doc["columns"] == ["volatility", "lower80", "upper80", "lower95", "upper95"]
    assert 0.05 < doc["rows"][0]["volatility"] < 1.0  # annualized, not a daily number
    table = cli(*args, "--seed", "1", "--format", "table")
    assert "volatility is annualized" in table.stdout and "seed 1" in table.stdout
    auto = _json(cli(*args, "--format", "json"))
    assert isinstance(auto["seed"], int)
    for model in ("egarch", "ewma"):
        alt = _json(cli(*args, "--model", model, "--seed", "2", "--format", "json"))
        assert alt["model"] == model and len(alt["rows"]) == 5


def test_regress_names_the_covariance_and_reports_vif_and_diagnostics(
    cli: Callable[..., Any],
) -> None:
    base = [
        "econ",
        "regress",
        "--y",
        "AAPL",
        "--x",
        "MSFT",
        "fred:DEXUSEU",
        "--start",
        "2020-01-01",
        "--end",
        "2024-12-31",
    ]
    doc = _json(cli(*base, "--format", "json", env_extra=KEY))
    assert doc["robust"] == "hac" and isinstance(doc["hac_lags"], int)
    assert [r["term"] for r in doc["rows"]] == ["const", "MSFT", "DEXUSEU"]
    assert set(doc["vif"]) == {"MSFT", "DEXUSEU"} and isinstance(doc["vif_flags"], list)
    for key in ("r2", "adj_r2", "f_statistic", "f_pvalue", "durbin_watson"):
        assert key in doc
    assert {"statistic", "pvalue"} <= set(doc["breusch_pagan"])
    assert doc["transforms"] == {
        "AAPL": "simple returns",
        "MSFT": "simple returns",
        "DEXUSEU": "first differences",
    }
    table = cli(*base, "--format", "table", env_extra=KEY)
    assert "HAC (Newey-West" in table.stdout and "VIF:" in table.stdout
    assert "Durbin-Watson" in table.stdout and "Breusch-Pagan" in table.stdout
    for kind in ("hc0", "hc3", "none"):
        out = cli(*base, "--robust", kind, "--format", "table", env_extra=KEY)
        assert out.exit_code == 0
        assert ("classical OLS" in out.stdout) if kind == "none" else (kind.upper() in out.stdout)
    assert cli(*base, "--robust", "bootstrap", env_extra=KEY).exit_code == 2
    twice = cli(
        "econ",
        "regress",
        "--y",
        "AAPL",
        "--x",
        "MSFT",
        "MSFT",
        "--start",
        "2020-01-01",
        "--end",
        "2024-12-31",
        env_extra=KEY,
    )
    assert twice.exit_code == 2 and "appears twice" in twice.stderr


def test_missing_extra_exits_3_with_the_install_hint(
    cli: Callable[..., Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from sobres.core import timeseries as ts
    from sobres.core.errors import ConfigurationError

    def absent() -> None:
        raise ConfigurationError(ECON_HINT)

    monkeypatch.setattr(ts, "require_econ", absent)
    for args in (
        ["econ", "diagnose", "DEXUSEU", *WINDOW],
        ["econ", "forecast", "ticker:AAPL", *WINDOW, *FAST],
    ):
        result = cli(*args, env_extra=KEY)
        assert result.exit_code == 3
        assert (
            "This command needs the econ extra. Install it with: pip install 'sobres[econ]'"
            in result.stderr
        )
        assert "Traceback" not in result.stderr and "ImportError" not in result.stderr
