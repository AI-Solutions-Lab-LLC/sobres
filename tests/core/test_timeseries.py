"""Stationarity diagnostics and GARCH against constructed series with known properties.

Scenarios: Tests reported; ACF and PACF; GARCH fit; Annualized output; Feeds
the optimizer; Missing extra.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from sobres.core.conventions import PERIODS_PER_YEAR
from sobres.core.errors import ConfigurationError, InsufficientDataError, UsageError
from sobres.core.moments import covariance, is_psd
from sobres.core.timeseries import (
    ECON_HINT,
    diagnose,
    garch_covariance,
    volatility_forecast,
)

pytest.importorskip("statsmodels")
pytest.importorskip("arch")
INDEX = pd.date_range("2015-01-31", periods=240, freq="ME")


def white_noise(n: int = 240, seed: int = 0) -> pd.Series:
    return pd.Series(np.random.default_rng(seed).normal(0, 1, n), index=INDEX[:n])


def random_walk(n: int = 240, seed: int = 0) -> pd.Series:
    return white_noise(n, seed).cumsum() + 100


def ar1(phi: float, n: int = 240, seed: int = 1) -> pd.Series:
    rng = np.random.default_rng(seed)
    x = np.zeros(n)
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.normal()
    return pd.Series(x, index=INDEX[:n])


def test_tests_reported_and_disagreement_stated() -> None:
    noise = diagnose(white_noise())
    assert noise.adf.conclusion == "stationary" and noise.kpss.conclusion == "stationary"
    assert noise.agree and "both tests conclude stationary" in noise.verdict
    assert noise.adf.null.startswith("unit root") and noise.kpss.null == "stationary"
    walk = diagnose(random_walk())
    assert walk.adf.conclusion == "non-stationary" and walk.kpss.conclusion == "non-stationary"
    assert 0.0 <= walk.adf.pvalue <= 1.0 and walk.adf.lags >= 0
    # A near-unit-root AR(1) is where the two tests can part ways; whatever they say,
    # the verdict must state disagreement rather than resolve it.
    edge = diagnose(ar1(0.97, seed=5))
    if not edge.agree:
        assert "the tests disagree" in edge.verdict and "do not resolve by fiat" in edge.verdict
    with pytest.raises(InsufficientDataError, match="constant"):
        diagnose(pd.Series(1.0, index=INDEX))
    with pytest.raises(InsufficientDataError):
        diagnose(white_noise(10))


def test_acf_and_pacf_through_lag_20_with_bounds() -> None:
    d = diagnose(ar1(0.8))
    assert len(d.acf) == 20 and len(d.pacf) == 20
    assert d.bound == pytest.approx(1.96 / np.sqrt(240))
    assert 0.5 < d.acf[0] < 0.95  # AR(1): ρ₁ ≈ φ = 0.8, biased down in a 240-point sample
    assert abs(d.pacf[0]) > d.bound and abs(d.pacf[5]) < d.bound  # PACF cuts off after lag 1


def _garch_returns(n: int = 1500, seed: int = 2) -> pd.Series:
    # GARCH(1,1): σ²_t = ω + α ε²_{t-1} + β σ²_{t-1}, ω=1e-6, α=0.08, β=0.9 (daily, decimal)
    rng = np.random.default_rng(seed)
    omega, alpha, beta = 1e-6, 0.08, 0.90
    var = omega / (1 - alpha - beta)
    out = np.zeros(n)
    for t in range(n):
        out[t] = rng.normal(0, np.sqrt(var))
        var = omega + alpha * out[t] ** 2 + beta * var
    return pd.Series(out, index=pd.bdate_range("2018-01-01", periods=n))


def test_garch_fit_recovers_persistence_and_offers_egarch_and_ewma() -> None:
    returns = _garch_returns()
    fit = volatility_forecast(
        returns, 10, model="garch", frequency="daily", seed=1, simulations=300
    )
    assert fit.params["alpha[1]"] + fit.params["beta[1]"] == pytest.approx(
        0.98, abs=0.03
    )  # persistence
    assert fit.frame().shape == (10, 5) and fit.seed == 1
    for model in ("egarch", "ewma"):
        alt = volatility_forecast(
            returns, 5, model=model, frequency="daily", seed=1, simulations=200
        )
        assert alt.model == model and len(alt.point) == 5
    with pytest.raises(UsageError):
        volatility_forecast(returns, 5, model="stochastic")


def test_annualized_output_uses_the_conventions_table() -> None:
    returns = _garch_returns()
    daily = volatility_forecast(
        returns, 5, model="garch", frequency="daily", seed=3, simulations=200
    )
    unconditional = np.sqrt(1e-6 / (1 - 0.08 - 0.90)) * np.sqrt(PERIODS_PER_YEAR["daily"])
    assert daily.point.iloc[-1] == pytest.approx(unconditional, rel=0.5)  # same order of magnitude
    assert daily.last_observed > 0.05  # annualized daily vol of this process is ~0.35, not ~0.02
    frame = daily.frame()
    assert (frame["lower95"].iloc[1:] <= frame["volatility"].iloc[1:]).all()
    assert (frame["volatility"].iloc[1:] <= frame["upper95"].iloc[1:]).all()


def test_feeds_the_optimizer_through_the_estimator_registry() -> None:
    a = _garch_returns(600, seed=4)
    b = 0.5 * a + _garch_returns(600, seed=5) * 0.8
    returns = pd.DataFrame({"A": a, "B": b})
    raw = garch_covariance(returns, "daily")
    assert raw.shape == (2, 2) and is_psd(pd.DataFrame(raw))
    sigma = covariance(returns, "daily", method="garch")
    assert sigma.attrs["estimator"] == "garch" and is_psd(sigma)
    assert sigma.loc["A", "B"] > 0  # the constructed correlation survives
    sample = covariance(returns, "daily", method="sample")
    assert np.corrcoef(returns.to_numpy(), rowvar=False)[0, 1] == pytest.approx(
        sigma.loc["A", "B"] / np.sqrt(sigma.loc["A", "A"] * sigma.loc["B", "B"]), abs=1e-6
    )
    assert sigma.loc["A", "A"] == pytest.approx(sample.loc["A", "A"], rel=1.0)  # both annualized


def test_missing_extra_is_an_exit_3_with_the_install_hint(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    real_import = builtins.__import__

    def no_arch(name: str, *args: object, **kwargs: object) -> object:
        if name == "arch" or name.startswith("arch."):
            raise ImportError("No module named 'arch'")
        return real_import(name, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(builtins, "__import__", no_arch)
    with pytest.raises(ConfigurationError) as exc:
        diagnose(white_noise())
    assert str(exc.value) == ECON_HINT and exc.value.exit_code == 3
    assert (
        ECON_HINT
        == "This command needs the econ extra. Install it with: pip install 'sobres[econ]'"
    )
