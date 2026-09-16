"""Time-series diagnostics and volatility: stationarity tests, ACF/PACF, GARCH.

Honest uncertainty is the point. A volatility forecast carries 80% and 95%
bands from seeded simulation; ADF and KPSS are reported together with their
disagreement stated. Everything is a pure function over a series; ``statsmodels``
and ``arch`` are imported lazily so the base install imports this module and only
a call fails, with the install hint. Price forecasting lives in
``sobres.core.forecast`` (a joint VAR/BVAR, revised 0009); the univariate
ARIMA forecaster that used to be here was removed with that revision.

Math and sources:

    ADF   Dickey & Fuller (1979), Said & Dickey (1984): H0 unit root
    KPSS  Kwiatkowski, Phillips, Schmidt & Shin (1992): H0 stationarity
    GARCH(1,1) Bollerslev (1986); EGARCH Nelson (1991); EWMA RiskMetrics (1996, λ=0.94)
    CCC covariance  Bollerslev (1990): Σ = D R D with GARCH variances on the diagonal
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

from sobres.core.conventions import periods_per_year
from sobres.core.errors import ConfigurationError, InsufficientDataError, UsageError

ECON_HINT = "This command needs the econ extra. Install it with: pip install 'sobres[econ]'"
SIGNIFICANCE = 0.05
DEFAULT_LAGS = 20
MIN_OBS = 30
VolModel = Literal["garch", "egarch", "ewma"]
VOL_MODELS: tuple[str, ...] = ("garch", "egarch", "ewma")
EWMA_LAMBDA = 0.94


def require_econ() -> None:
    """Raise the documented exit-3 error when the econ extra is absent."""
    try:
        import arch  # noqa: F401
        import statsmodels  # noqa: F401
    except ImportError as exc:
        raise ConfigurationError(ECON_HINT) from exc


def _clean(series: pd.Series) -> pd.Series:
    clean = pd.Series(series).dropna().astype("float64")
    if len(clean) < MIN_OBS:
        raise InsufficientDataError(
            f"{len(clean)} observations; at least {MIN_OBS} are needed",
            hint="widen --start/--end",
        )
    if float(clean.std(ddof=0)) == 0.0:
        raise InsufficientDataError(
            "the series is constant over the window; there is nothing to test or forecast",
            hint="widen --start/--end or choose another series",
        )
    return clean


# --------------------------------------------------------------------------- #
# Stationarity and correlation structure
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class StationarityTest:
    name: str
    statistic: float
    pvalue: float
    null: str
    conclusion: Literal["stationary", "non-stationary"]
    lags: int


@dataclass(frozen=True)
class Diagnostics:
    n_obs: int
    adf: StationarityTest
    kpss: StationarityTest
    agree: bool
    verdict: str
    acf: list[float]
    pacf: list[float]
    bound: float
    """The ±1.96/√n significance bound for a single autocorrelation."""

    @property
    def stationary(self) -> bool:
        return self.adf.conclusion == "stationary" and self.kpss.conclusion == "stationary"


def _adf(series: pd.Series) -> StationarityTest:
    import warnings

    from statsmodels.tsa.stattools import adfuller

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)  # the 0.16 result-object transition
        stat, p, lags, *_ = adfuller(series.to_numpy(), autolag="AIC")
    return StationarityTest(
        "ADF",
        float(stat),
        float(p),
        "unit root (non-stationary)",
        "stationary" if p < SIGNIFICANCE else "non-stationary",
        int(lags),
    )


def _kpss(series: pd.Series) -> StationarityTest:
    import warnings

    from statsmodels.tools.sm_exceptions import InterpolationWarning
    from statsmodels.tsa.stattools import kpss

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InterpolationWarning)
        warnings.simplefilter("ignore", FutureWarning)  # the 0.16 result-object transition
        stat, p, lags, _ = kpss(series.to_numpy(), regression="c", nlags="auto")
    return StationarityTest(
        "KPSS",
        float(stat),
        float(p),
        "stationary",
        "non-stationary" if p < SIGNIFICANCE else "stationary",
        int(lags),
    )


def stationarity(series: pd.Series) -> tuple[StationarityTest, StationarityTest]:
    require_econ()
    clean = _clean(series)
    return _adf(clean), _kpss(clean)


def diagnose(series: pd.Series, lags: int = DEFAULT_LAGS) -> Diagnostics:
    """ADF and KPSS with their disagreement stated, plus ACF/PACF through ``lags``."""
    require_econ()
    from statsmodels.tsa.stattools import acf, pacf

    clean = _clean(series)
    adf, kp = _adf(clean), _kpss(clean)
    agree = adf.conclusion == kp.conclusion
    if agree:
        verdict = f"both tests conclude {adf.conclusion}"
    elif adf.conclusion == "stationary":
        verdict = (
            "the tests disagree: ADF rejects a unit root but KPSS rejects stationarity — "
            "consistent with a trend-stationary or near-integrated series; do not resolve by fiat"
        )
    else:
        verdict = (
            "the tests disagree: KPSS does not reject stationarity but ADF cannot reject a "
            "unit root — the sample may be too short to tell; do not resolve by fiat"
        )
    max_lag = min(lags, len(clean) // 2 - 1)
    return Diagnostics(
        n_obs=len(clean),
        adf=adf,
        kpss=kp,
        agree=agree,
        verdict=verdict,
        acf=[float(v) for v in acf(clean.to_numpy(), nlags=max_lag, fft=True)[1:]],
        pacf=[float(v) for v in pacf(clean.to_numpy(), nlags=max_lag)[1:]],
        bound=float(1.96 / np.sqrt(len(clean))),
    )


# --------------------------------------------------------------------------- #
# Volatility
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class VolatilityForecast:
    model: str
    horizon: int
    n_obs: int
    frequency: str
    seed: int
    simulations: int
    params: dict[str, float]
    point: pd.Series = field(repr=False)
    """Annualized conditional volatility per step ahead."""
    lower80: pd.Series = field(repr=False)
    upper80: pd.Series = field(repr=False)
    lower95: pd.Series = field(repr=False)
    upper95: pd.Series = field(repr=False)
    last_observed: float
    """Annualized conditional volatility at the last observation."""

    def frame(self) -> pd.DataFrame:
        out = pd.DataFrame(
            {
                "volatility": self.point,
                "lower80": self.lower80,
                "upper80": self.upper80,
                "lower95": self.lower95,
                "upper95": self.upper95,
            }
        )
        out.index.name = "step"
        return out


def _arch_model(returns_pct: np.ndarray, model: str) -> Any:
    from arch.univariate import EGARCH, GARCH, ConstantMean, EWMAVariance, Normal

    am = ConstantMean(returns_pct)
    if model == "garch":
        am.volatility = GARCH(p=1, q=1)
    elif model == "egarch":
        am.volatility = EGARCH(p=1, o=1, q=1)
    elif model == "ewma":
        am.volatility = EWMAVariance(EWMA_LAMBDA)
    else:
        raise UsageError(f"model must be one of {', '.join(VOL_MODELS)}, got {model!r}")
    am.distribution = Normal()
    return am


def volatility_forecast(
    returns: pd.Series,
    horizon: int,
    *,
    model: VolModel | str = "garch",
    frequency: str = "daily",
    seed: int | None = None,
    simulations: int = 1000,
) -> VolatilityForecast:
    """Conditional volatility ``horizon`` steps ahead, annualized, with simulated intervals.

    Returns enter in percent (the ``arch`` convention for numerical stability) and
    leave as annualized decimal volatility: ``sqrt(variance) / 100 * sqrt(periods)``.
    Intervals are the 10/90 and 2.5/97.5 percentiles of the variance across
    simulated paths from the fitted model.
    """
    require_econ()
    if horizon <= 0:
        raise UsageError("--horizon must be at least 1")
    clean = _clean(returns)
    seed_used = int(np.random.SeedSequence().generate_state(1)[0]) if seed is None else int(seed)
    am = _arch_model(clean.to_numpy() * 100.0, model)
    fit = am.fit(disp="off")
    # The shocks come from our own seeded generator: arch's random_state argument does not
    # make its simulation reproducible, a shock callable does.
    generator = np.random.default_rng(seed_used)

    def shocks(size: int | tuple[int, ...]) -> np.ndarray:
        return generator.standard_normal(size)

    forecast = fit.forecast(
        horizon=horizon, method="simulation", simulations=simulations, rng=shocks
    )
    paths = np.asarray(forecast.simulations.variances[-1], dtype="float64")  # paths by horizon
    scale = np.sqrt(periods_per_year(frequency)) / 100.0
    vol_paths = np.sqrt(paths) * scale
    index = pd.RangeIndex(1, horizon + 1, name="step")
    point = pd.Series(
        np.sqrt(np.asarray(forecast.variance.iloc[-1], dtype="float64")) * scale, index=index
    )

    def q(p: float) -> pd.Series:
        return pd.Series(np.percentile(vol_paths, p, axis=0), index=index)

    return VolatilityForecast(
        model=model,
        horizon=horizon,
        n_obs=len(clean),
        frequency=frequency,
        seed=seed_used,
        simulations=simulations,
        params={k: float(v) for k, v in fit.params.items()},
        point=point,
        lower80=q(10),
        upper80=q(90),
        lower95=q(2.5),
        upper95=q(97.5),
        last_observed=float(fit.conditional_volatility[-1]) * scale,
    )


def garch_covariance(returns: pd.DataFrame, frequency: str) -> np.ndarray:
    """One-step-ahead GARCH(1,1) variances on the diagonal, sample correlation off it.

    Bollerslev's constant-conditional-correlation construction, ``Σ = D R D``,
    annualized. The caller (``moments.covariance``) applies the PSD conditioning
    every estimator gets.
    """
    require_econ()
    clean = returns.dropna()
    if len(clean) < MIN_OBS:
        raise InsufficientDataError(
            f"{len(clean)} observations; GARCH needs at least {MIN_OBS}", hint="widen --start/--end"
        )
    variances = []
    for column in clean.columns:
        fit = _arch_model(clean[column].to_numpy(dtype="float64") * 100.0, "garch").fit(disp="off")
        one_step = float(fit.forecast(horizon=1).variance.iloc[-1, 0]) / 100.0**2
        variances.append(one_step)
    d = np.diag(np.sqrt(np.asarray(variances)))
    corr = np.corrcoef(clean.to_numpy(dtype="float64"), rowvar=False)
    corr = np.atleast_2d(corr)
    sigma = d @ corr @ d
    return np.asarray(sigma * periods_per_year(frequency), dtype="float64")
