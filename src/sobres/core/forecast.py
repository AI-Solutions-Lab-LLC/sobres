"""Multivariable stock-price forecasting: a regularized joint VAR and a Bayesian VAR.

The target is the future split-only log-price return ``y(t,h) = log(P(t+h)/P(t))``,
modelled jointly with a small state of economically motivated series (revised
0009, ``equity-basic/v1``): the target return, the market return, log realized
volatility and the change in log dollar-volume activity, plus an optional sector
return. Everything here is a pure function over arrays and frames; the caller
loads the data, chooses the seed and renders.

Math and sources:

    VAR(p)     s_t = c + Σ_l A_l s_(t-l) + e_t; Lütkepohl, *New Introduction to
               Multiple Time Series Analysis* (2005), ch. 2-3. Ridge on the lag
               block: minimise ||Y - X B||²_F / n + λ ||B_lags||²_F on training-
               standardized columns (Hoerl & Kennard 1970), closed form
               B = (X'X/n + λ D)⁻¹ X'Y/n with D zero on the intercept.
    Stability  the companion matrix' spectral radius must be < 1 (Lütkepohl §2.1).
    BVAR       conjugate normal-inverse-Wishart with a Minnesota-style prior
               (Litterman 1986; Bańbura, Giannone & Reichlin 2010): B|Σ ~ MN(B0,V0,Σ),
               Σ ~ IW(S0,nu0); posterior Vn=(V0⁻¹+X'X)⁻¹, Bn=Vn(V0⁻¹B0+X'Y),
               nun=nu0+n, Sn=S0+Y'Y+B0'V0⁻¹B0-Bn'Vn⁻¹Bn (Karlsson 2013, §2.2).
               Prior means are zero for these stationary transformed series.
    Bootstrap  residual moving-block bootstrap with parameter refits
               (Künsch 1989; Kilian & Lütkepohl 2017, ch. 12), block max(5, h).
    Evaluation chronological inner validation blocks inside each training window
               with horizon purging (Bergmeir & Benítez 2012; López de Prado 2018,
               ch. 7), outer origins spaced by h; no-change and training-mean
               controls (Goyal, Welch & Zafirov 2024); out-of-sample R² as in
               Campbell & Thompson (2008).
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

import numpy as np
import pandas as pd

from sobres.core.conventions import PERIODS_PER_YEAR
from sobres.core.errors import InsufficientDataError, UsageError

CATALOG_VERSION = "equity-basic/v1"
MODEL_VERSIONS: dict[str, str] = {"var": "var/v1", "bvar": "bvar/v1"}
ForecastModel = Literal["var", "bvar"]
FORECAST_MODELS: tuple[str, ...] = ("var", "bvar")
HORIZONS: tuple[int, ...] = (1, 5, 20)
LAG_CANDIDATES: tuple[int, ...] = (1, 2, 5)
MAX_LAG = 5
RIDGE_CANDIDATES: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0)
TIGHTNESS_CANDIDATES: tuple[float, ...] = (0.1, 0.2, 0.5)
VOLATILITY_WINDOW = 20
ACTIVITY_WINDOW = 20
TRAINING_YEARS = 5
INNER_BLOCKS = 3
MIN_COLUMNS = 2
MAX_COLUMNS = 12
MIN_OUTER_OUTCOMES = 12
DEFAULT_DRAWS = 1000
DEFAULT_REFITS = 200
MIN_USABLE_DRAW_FRACTION = 0.9
INTERCEPT_PRIOR_VARIANCE = 1e6
TIE_TOLERANCE = 1e-12
A = PERIODS_PER_YEAR["daily"]
"""Sessions per year; window lengths derive from it, calendars decide actual dates."""


# --------------------------------------------------------------------------- #
# The state: predictors from prices and volume
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Predictor:
    """One catalog entry: what the column is, how it was computed and where it came from."""

    column: str
    role: str
    formula: str
    window: int | None
    source: str


@dataclass(frozen=True)
class StatePanel:
    frame: pd.DataFrame = field(repr=False)
    """Joint state, one row per completed session; warmup rows already dropped."""
    predictors: list[Predictor]
    target: str
    """Name of the target-return column."""
    warmup_rows: int


def log_returns(close: pd.Series) -> pd.Series:
    """``log(P_t / P_(t-1))`` of a split-only price series."""
    clean = pd.Series(close).astype("float64")
    if (clean <= 0).any():
        raise InsufficientDataError(
            "a nonpositive price cannot be log-transformed",
            hint="check the symbol; prices must be quoted in the major unit and positive",
        )
    logged = pd.Series(np.log(clean.to_numpy()), index=clean.index, dtype="float64")
    return logged.diff()


def build_state(
    target_close: pd.Series,
    target_volume: pd.Series,
    market_close: pd.Series,
    sector_close: pd.Series | None = None,
    *,
    target: str,
    market: str,
    sector: str | None = None,
) -> StatePanel:
    """The ``equity-basic`` joint state (plus an optional sector return).

    Columns, in catalog order: target log return; market log return; log realized
    volatility ``log(sqrt(mean(r² over 20 sessions)))``; change in log 20-session
    mean dollar volume ``Δ log(mean(close x volume))``; sector log return.
    Dollar volume multiplies the *raw* close by the *raw* share volume — the same
    basis, never an adjusted price against raw volume.
    """
    if target == market:
        raise UsageError(
            f"the target {target} is also the benchmark; the state would repeat a column",
            hint="pass a different --benchmark ticker:<symbol>",
        )
    if sector is not None and sector in (target, market):
        raise UsageError(
            f"the sector series {sector} duplicates "
            + ("the target" if sector == target else "the benchmark"),
            hint="pass a sector ETF or index that differs from both",
        )
    idx = target_close.index.intersection(market_close.index)
    if sector_close is not None:
        idx = idx.intersection(sector_close.index)
    idx = idx.sort_values()
    close = target_close.reindex(idx).astype("float64")
    volume = target_volume.reindex(idx).astype("float64")
    if volume.isna().any() or (volume <= 0).any():
        bad = volume.index[volume.isna() | (volume <= 0)][0]
        raise InsufficientDataError(
            f"{target} has missing or nonpositive share volume on {pd.Timestamp(bad).date()}",
            hint="the activity predictor needs positive volume on every session; "
            "choose another window or symbol",
        )
    r = log_returns(close)
    m = log_returns(market_close.reindex(idx).astype("float64"))
    squared = r.pow(2)
    rv = pd.Series(np.log(np.sqrt(squared.rolling(VOLATILITY_WINDOW).mean().to_numpy())), index=idx)
    dollar = (close * volume).rolling(ACTIVITY_WINDOW).mean()
    activity = pd.Series(np.log(dollar.to_numpy()), index=idx).diff()
    columns = {
        f"{target}_ret": r,
        f"{market}_ret": m,
        f"{target}_logrv{VOLATILITY_WINDOW}": rv,
        f"{target}_dlogdv{ACTIVITY_WINDOW}": activity,
    }
    predictors = [
        Predictor(f"{target}_ret", "target return", "log(P_t / P_(t-1))", None, f"ticker:{target}"),
        Predictor(f"{market}_ret", "market return", "log(M_t / M_(t-1))", None, f"ticker:{market}"),
        Predictor(
            f"{target}_logrv{VOLATILITY_WINDOW}",
            "realized volatility",
            "log(sqrt(mean(r² over the window)))",
            VOLATILITY_WINDOW,
            f"ticker:{target}",
        ),
        Predictor(
            f"{target}_dlogdv{ACTIVITY_WINDOW}",
            "trading activity",
            "Δ log(mean(raw close x raw volume over the window))",
            ACTIVITY_WINDOW,
            f"ticker:{target}",
        ),
    ]
    if sector_close is not None and sector is not None:
        columns[f"{sector}_ret"] = log_returns(sector_close.reindex(idx).astype("float64"))
        predictors.append(
            Predictor(
                f"{sector}_ret", "sector return", "log(S_t / S_(t-1))", None, f"ticker:{sector}"
            )
        )
    frame = pd.DataFrame(columns)
    with np.errstate(invalid="ignore"):
        frame = frame.replace([np.inf, -np.inf], np.nan)
    complete = frame.dropna()
    warmup = len(frame) - len(complete)
    if len(complete) < 3:
        raise InsufficientDataError(
            f"{len(complete)} complete state rows after a {warmup}-row warmup",
            hint="widen --start/--end",
        )
    _validate_columns(complete)
    return StatePanel(
        frame=complete, predictors=predictors, target=f"{target}_ret", warmup_rows=warmup
    )


def _validate_columns(frame: pd.DataFrame) -> None:
    k = frame.shape[1]
    if k < MIN_COLUMNS or k > MAX_COLUMNS:
        raise UsageError(
            f"the state has {k} columns; between {MIN_COLUMNS} and {MAX_COLUMNS} are supported"
        )
    values = frame.to_numpy(dtype="float64")
    stds = values.std(axis=0, ddof=1)
    for name, sd in zip(frame.columns, stds, strict=True):
        if not np.isfinite(sd) or sd == 0.0:
            raise InsufficientDataError(
                f"{name} has no variation over the window; it cannot be modelled",
                hint="widen --start/--end or choose another series",
            )
    for i in range(k):
        for j in range(i + 1, k):
            if np.allclose(values[:, i], values[:, j]):
                raise UsageError(
                    f"{frame.columns[i]} and {frame.columns[j]} are the same series",
                    hint="every state column must be a distinct input",
                )


# --------------------------------------------------------------------------- #
# Linear algebra
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Scaler:
    mean: np.ndarray
    std: np.ndarray

    def transform(self, values: np.ndarray) -> np.ndarray:
        return np.asarray((values - self.mean) / self.std, dtype="float64")

    def inverse_column(self, standardized: np.ndarray, column: int) -> np.ndarray:
        return np.asarray(standardized * self.std[column] + self.mean[column], dtype="float64")


def fit_scaler(training: np.ndarray) -> Scaler:
    """Means and standard deviations (ddof 1) of the training rows only."""
    mean = training.mean(axis=0)
    std = training.std(axis=0, ddof=1)
    if not np.all(np.isfinite(std)) or np.any(std == 0.0):
        raise InsufficientDataError(
            "a state column has zero variance in the training window",
            hint="widen the window or remove the constant series",
        )
    return Scaler(mean=mean, std=std)


def lag_design(values: np.ndarray, p: int) -> tuple[np.ndarray, np.ndarray]:
    """``X`` (intercept, then lags 1..p of every column) and ``Y`` for a VAR(p)."""
    n, k = values.shape
    if n <= p:
        raise InsufficientDataError(f"{n} rows cannot support {p} lags")
    rows = n - p
    x = np.ones((rows, 1 + k * p))
    for lag in range(1, p + 1):
        x[:, 1 + (lag - 1) * k : 1 + lag * k] = values[p - lag : n - lag]
    y = values[p:]
    return x, y


def companion_radius(coefs: Sequence[np.ndarray]) -> float:
    """Spectral radius of the VAR(p) companion matrix; stable iff < 1."""
    p = len(coefs)
    k = coefs[0].shape[0]
    top = np.hstack(coefs)
    if p == 1:
        companion = top
    else:
        below = np.hstack([np.eye(k * (p - 1)), np.zeros((k * (p - 1), k))])
        companion = np.vstack([top, below])
    return float(np.max(np.abs(np.linalg.eigvals(companion))))


def _split_coefficients(b: np.ndarray, k: int, p: int) -> tuple[np.ndarray, list[np.ndarray]]:
    intercept = np.asarray(b[0], dtype="float64")
    coefs = [
        np.asarray(b[1 + (lag - 1) * k : 1 + lag * k].T, dtype="float64") for lag in range(1, p + 1)
    ]
    return intercept, coefs


@dataclass(frozen=True)
class VarFit:
    """A ridge VAR(p) on standardized columns."""

    p: int
    penalty: float
    b: np.ndarray = field(repr=False)
    """(1 + K p) x K: intercept row, then lag blocks; ``s_t = [1, s_(t-1), …] @ b``."""
    sigma: np.ndarray = field(repr=False)
    residuals: np.ndarray = field(repr=False)
    scaler: Scaler
    n: int
    spectral_radius: float
    condition_number: float

    @property
    def k(self) -> int:
        return int(self.b.shape[1])

    @property
    def stable(self) -> bool:
        return self.spectral_radius < 1.0


def fit_var(
    training: np.ndarray, p: int, penalty: float, *, scaler: Scaler | None = None
) -> VarFit:
    """Ridge VAR(p): ``B = (X'X/n + λ D)⁻¹ X'Y/n`` with ``D`` zero for the intercept."""
    if p < 1 or p > MAX_LAG:
        raise UsageError(f"lag order must be between 1 and {MAX_LAG}, got {p}")
    if penalty < 0:
        raise UsageError("the ridge penalty cannot be negative")
    scale = scaler or fit_scaler(training)
    z = scale.transform(training)
    x, y = lag_design(z, p)
    n = x.shape[0]
    gram = x.T @ x / n
    d = np.eye(gram.shape[0])
    d[0, 0] = 0.0
    lhs = gram + penalty * d
    condition = float(np.linalg.cond(gram))
    try:
        b = np.linalg.solve(lhs, x.T @ y / n)
    except np.linalg.LinAlgError as exc:
        raise InsufficientDataError(
            "the lag design is singular; the state has collinear columns",
            hint="remove a redundant series or use a positive ridge penalty",
        ) from exc
    resid = y - x @ b
    dof = max(n - b.shape[0], 1)
    sigma = resid.T @ resid / dof
    _, coefs = _split_coefficients(b, z.shape[1], p)
    return VarFit(
        p=p,
        penalty=penalty,
        b=b,
        sigma=sigma,
        residuals=resid,
        scaler=scale,
        n=n,
        spectral_radius=companion_radius(coefs),
        condition_number=condition,
    )


@dataclass(frozen=True)
class BvarFit:
    """Normal-inverse-Wishart posterior of a VAR(p) under a Minnesota-style prior."""

    p: int
    tightness: float
    bn: np.ndarray = field(repr=False)
    vn: np.ndarray = field(repr=False)
    sn: np.ndarray = field(repr=False)
    nun: float
    prior: dict[str, Any]
    scaler: Scaler
    n: int
    spectral_radius: float
    """Of the posterior mean coefficients."""
    condition_number: float

    @property
    def k(self) -> int:
        return int(self.bn.shape[1])

    @property
    def stable(self) -> bool:
        return self.spectral_radius < 1.0

    @property
    def b(self) -> np.ndarray:
        return self.bn


def fit_bvar(
    training: np.ndarray, p: int, tightness: float, *, scaler: Scaler | None = None
) -> BvarFit:
    """Conjugate NIW posterior. Prior: ``B0 = 0``; ``V0`` diagonal with ``1e6`` for the
    intercept and ``λ² / (lag² · var_j)`` for the coefficient on lag ``lag`` of column
    ``j``; ``nu0 = K + 2``; ``S0 = (nu0 - K - 1) · diag(training variances)``."""
    if p < 1 or p > MAX_LAG:
        raise UsageError(f"lag order must be between 1 and {MAX_LAG}, got {p}")
    if tightness <= 0:
        raise UsageError("the prior tightness must be positive")
    scale = scaler or fit_scaler(training)
    z = scale.transform(training)
    x, y = lag_design(z, p)
    n, k = y.shape
    var_j = z.var(axis=0, ddof=1)
    v0_diag = np.empty(1 + k * p)
    v0_diag[0] = INTERCEPT_PRIOR_VARIANCE
    for lag in range(1, p + 1):
        v0_diag[1 + (lag - 1) * k : 1 + lag * k] = tightness**2 / (lag**2 * var_j)
    v0_inv = np.diag(1.0 / v0_diag)
    nu0 = k + 2.0
    s0 = (nu0 - k - 1.0) * np.diag(var_j)
    gram = x.T @ x
    condition = float(np.linalg.cond(gram / n))
    vn_inv = v0_inv + gram
    vn = np.linalg.inv(vn_inv)
    vn = (vn + vn.T) / 2.0
    bn = vn @ (x.T @ y)  # B0 = 0
    nun = nu0 + n
    sn = s0 + y.T @ y - bn.T @ vn_inv @ bn
    sn = (sn + sn.T) / 2.0
    _, coefs = _split_coefficients(bn, k, p)
    prior = {
        "b0": "zero for every lag coefficient and the intercept",
        "v0_intercept": INTERCEPT_PRIOR_VARIANCE,
        "v0_lag_rule": "tightness² / (lag² x training variance of the predictor)",
        "tightness": tightness,
        "nu0": nu0,
        "s0": "(nu0 - K - 1) x diag(training variances, ddof 1)",
    }
    return BvarFit(
        p=p,
        tightness=tightness,
        bn=bn,
        vn=vn,
        sn=sn,
        nun=nun,
        prior=prior,
        scaler=scale,
        n=n,
        spectral_radius=companion_radius(coefs),
        condition_number=condition,
    )


Fit = VarFit | BvarFit


def _stack_history(z: np.ndarray, p: int) -> np.ndarray:
    """The regressor row ``[1, s_t, s_(t-1), …, s_(t-p+1)]`` from the last ``p`` rows."""
    return np.concatenate([[1.0], *[z[-lag] for lag in range(1, p + 1)]])


def mean_path(b: np.ndarray, p: int, history_std: np.ndarray, horizon: int) -> np.ndarray:
    """Recursive conditional means, standardized units; ``horizon x K``."""
    k = b.shape[1]
    hist = list(history_std[-p:])
    out = np.empty((horizon, k))
    for step in range(horizon):
        row = np.concatenate([[1.0], *[hist[-lag] for lag in range(1, p + 1)]])
        nxt = row @ b
        out[step] = nxt
        hist.append(nxt)
    return out


def cumulative_target(path_std: np.ndarray, scaler: Scaler, target_col: int) -> np.ndarray:
    """Cumulative target log return along the path, original units; length = horizon."""
    original = scaler.inverse_column(path_std[..., target_col], target_col)
    return np.asarray(np.cumsum(original, axis=-1), dtype="float64")


# --------------------------------------------------------------------------- #
# Candidate selection on chronological inner blocks
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Candidate:
    lag: int
    penalty: float
    """Ridge λ for ``var``; prior tightness for ``bvar``."""
    loss: float | None
    """Mean squared error of the cumulative target log return on the inner blocks."""
    n_outcomes: int
    stable: bool
    rejected: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "lag": self.lag,
            "penalty": self.penalty,
            "loss": self.loss,
            "n_outcomes": self.n_outcomes,
            "stable": self.stable,
            "rejected": self.rejected,
        }


@dataclass(frozen=True)
class Selection:
    chosen: Candidate
    candidates: list[Candidate]
    block_length: int
    purge: int
    boundaries: list[dict[str, int]]
    """Inner block row ranges relative to the training window."""


def _fit(model: str, training: np.ndarray, lag: int, penalty: float) -> Fit:
    if model == "var":
        return fit_var(training, lag, penalty)
    if model == "bvar":
        return fit_bvar(training, lag, penalty)
    raise UsageError(f"model must be one of {', '.join(FORECAST_MODELS)}, got {model!r}")


def minimum_training_rows(k: int, p: int) -> int:
    """``max(3A, 10(Kp + 1))`` usable rows per fold."""
    return max(3 * A, 10 * (k * p + 1))


def select_candidates(
    training: np.ndarray,
    model: str,
    horizon: int,
    target_col: int,
    *,
    fixed_lag: int | None = None,
) -> Selection:
    """Pick lag and penalty on three forward validation blocks inside the training
    window; the outer test never enters. Ties within relative 1e-12 prefer stronger
    shrinkage, then fewer lags."""
    n, k = training.shape
    block = A // 4
    purge = horizon
    boundaries: list[dict[str, int]] = []
    for i in range(INNER_BLOCKS):
        start = n - (INNER_BLOCKS - i) * block
        boundaries.append(
            {"fit_end": start - purge, "validate_start": start, "validate_end": start + block}
        )
    lags = (fixed_lag,) if fixed_lag is not None else LAG_CANDIDATES
    penalties = RIDGE_CANDIDATES if model == "var" else TIGHTNESS_CANDIDATES
    candidates: list[Candidate] = []
    for lag in lags:
        for penalty in penalties:
            errors: list[float] = []
            stable = True
            reason: str | None = None
            for bound in boundaries:
                fit_rows = training[: bound["fit_end"]]
                if len(fit_rows) < minimum_training_rows(k, lag):
                    reason = (
                        f"{len(fit_rows)} fit rows before the inner block; "
                        f"{minimum_training_rows(k, lag)} are needed"
                    )
                    break
                fit = _fit(model, fit_rows, lag, penalty)
                if not fit.stable:
                    stable = False
                    reason = f"companion spectral radius {fit.spectral_radius:.4f} ≥ 1"
                    break
                z = fit.scaler.transform(training)
                origin = bound["validate_start"] - 1
                while origin + horizon < bound["validate_end"]:
                    path = mean_path(fit.b, lag, z[: origin + 1], horizon)
                    predicted = cumulative_target(path, fit.scaler, target_col)[-1]
                    actual = float(training[origin + 1 : origin + 1 + horizon, target_col].sum())
                    errors.append((predicted - actual) ** 2)
                    origin += horizon
            if reason is not None:
                candidates.append(Candidate(lag, penalty, None, len(errors), stable, reason))
                continue
            if not errors:
                candidates.append(
                    Candidate(lag, penalty, None, 0, stable, "no complete inner-validation outcome")
                )
                continue
            candidates.append(Candidate(lag, penalty, float(np.mean(errors)), len(errors), stable))
    usable = [c for c in candidates if c.loss is not None and c.stable]
    if not usable:
        reasons = "; ".join(
            f"lag {c.lag} penalty {c.penalty}: {c.rejected}" for c in candidates[:3]
        )
        raise InsufficientDataError(
            f"no {model} candidate passed the sample and stability guards ({reasons})",
            hint="widen --start/--end, lower --lag, or choose a different state",
        )
    best = min(c.loss for c in usable if c.loss is not None)
    tied = [
        c
        for c in usable
        if c.loss is not None and c.loss <= best * (1 + TIE_TOLERANCE) + TIE_TOLERANCE
    ]
    chosen = sorted(tied, key=lambda c: (-c.penalty, c.lag))[0]
    return Selection(
        chosen=chosen, candidates=candidates, block_length=block, purge=purge, boundaries=boundaries
    )


# --------------------------------------------------------------------------- #
# Predictive draws
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Draws:
    cumulative: np.ndarray = field(repr=False)
    """``usable x horizon`` cumulative target log returns."""
    requested: int
    rejected: int
    method: str

    @property
    def usable(self) -> int:
        return int(self.cumulative.shape[0])


def _block_indices(
    rng: np.random.Generator, n: int, length: int, block: int, count: int
) -> np.ndarray:
    """``count x length`` residual row indices, drawn as contiguous blocks of ``block``."""
    blocks = math.ceil(length / block)
    starts = rng.integers(0, max(n - block + 1, 1), size=(count, blocks))
    offsets = np.arange(block)
    idx = (starts[:, :, None] + offsets[None, None, :]).reshape(count, blocks * block)
    return np.asarray(idx[:, :length] % n, dtype="int64")


def _simulate_paths(
    b: np.ndarray, p: int, history_std: np.ndarray, innovations: np.ndarray
) -> np.ndarray:
    """Recursive paths for many draws at once: ``b`` is ``D x (1+Kp) x K`` or ``(1+Kp) x K``;
    ``innovations`` is ``D x horizon x K``. Returns ``D x horizon x K`` standardized states."""
    draws, horizon, k = innovations.shape
    hist = [np.broadcast_to(history_std[-lag], (draws, k)).copy() for lag in range(1, p + 1)]
    out = np.empty((draws, horizon, k))
    per_draw = b.ndim == 3
    for step in range(horizon):
        row = np.concatenate([np.ones((draws, 1)), *hist[:p]], axis=1)
        nxt = np.einsum("dj,djk->dk", row, b) if per_draw else row @ b
        nxt = nxt + innovations[:, step, :]
        out[:, step, :] = nxt
        hist.insert(0, nxt)
    return out


def var_draws(
    fit: VarFit,
    history: np.ndarray,
    horizon: int,
    *,
    seed: int,
    draws: int = DEFAULT_DRAWS,
    refits: int = DEFAULT_REFITS,
    target_col: int,
) -> Draws:
    """Joint residual moving-block bootstrap with parameter refits.

    Each refit rebuilds a pseudo-history from the fitted model and block-resampled
    residuals, re-estimates the VAR, then simulates ``draws / refits`` paths from
    the observed last ``p`` states with block-resampled innovations. Draws whose
    refit is explosive or whose path is not finite are rejected and counted.
    """
    rng = np.random.default_rng(seed)
    p, k = fit.p, fit.k
    z = fit.scaler.transform(history)
    resid = fit.residuals
    n_res = resid.shape[0]
    block = max(5, horizon)
    refits = max(1, min(refits, draws))
    # Pseudo-histories, one per refit, generated jointly step by step.
    boot_idx = _block_indices(rng, n_res, n_res, block, refits)
    pseudo = np.empty((refits, n_res + p, k))
    pseudo[:, :p, :] = z[:p]
    for t in range(n_res):
        row = np.concatenate(
            [np.ones((refits, 1)), *[pseudo[:, p + t - lag, :] for lag in range(1, p + 1)]], axis=1
        )
        pseudo[:, p + t, :] = row @ fit.b + resid[boot_idx[:, t]]
    # Batched refit with the same lag and penalty on the same objective.
    xs = np.ones((refits, n_res, 1 + k * p))
    for lag in range(1, p + 1):
        xs[:, :, 1 + (lag - 1) * k : 1 + lag * k] = pseudo[:, p - lag : p + n_res - lag, :]
    ys = pseudo[:, p:, :]
    gram = np.einsum("rni,rnj->rij", xs, xs) / n_res
    d = np.eye(1 + k * p)
    d[0, 0] = 0.0
    rhs = np.einsum("rni,rnk->rik", xs, ys) / n_res
    b_star = np.linalg.solve(gram + fit.penalty * d, rhs)
    radii = np.array(
        [companion_radius(_split_coefficients(b_star[r], k, p)[1]) for r in range(refits)]
    )
    per_draw_refit = np.arange(draws) % refits
    inno_idx = _block_indices(rng, n_res, horizon, block, draws)
    innovations = resid[inno_idx]
    paths = _simulate_paths(b_star[per_draw_refit], p, z, innovations)
    cumulative = cumulative_target(paths, fit.scaler, target_col)
    ok = np.isfinite(cumulative).all(axis=1) & (radii[per_draw_refit] < 1.0)
    return _guard(
        cumulative[ok], draws, "joint residual moving-block bootstrap with parameter refits"
    )


def bvar_draws(
    fit: BvarFit,
    history: np.ndarray,
    horizon: int,
    *,
    seed: int,
    draws: int = DEFAULT_DRAWS,
    target_col: int,
) -> Draws:
    """Posterior-predictive paths: ``Σ ~ IW(Sn, nun)``, ``B | Σ ~ MN(Bn, Vn, Σ)``, then
    joint Gaussian innovations along a recursive path. Unstable coefficient draws
    are rejected and counted."""
    from scipy.stats import invwishart

    rng = np.random.default_rng(seed)
    p, k = fit.p, fit.k
    z = fit.scaler.transform(history)
    sigmas = np.asarray(invwishart(df=fit.nun, scale=fit.sn).rvs(size=draws, random_state=rng))
    sigmas = sigmas.reshape(draws, k, k)
    chol_v = np.linalg.cholesky(fit.vn)
    chol_s = np.linalg.cholesky(sigmas)
    noise = rng.standard_normal((draws, fit.bn.shape[0], k))
    b_draws = fit.bn[None, :, :] + chol_v[None, :, :] @ noise @ np.transpose(chol_s, (0, 2, 1))
    radii = np.array(
        [companion_radius(_split_coefficients(b_draws[d], k, p)[1]) for d in range(draws)]
    )
    eps = rng.standard_normal((draws, horizon, k))
    innovations = np.einsum("dhk,djk->dhj", eps, chol_s)
    paths = _simulate_paths(b_draws, p, z, innovations)
    cumulative = cumulative_target(paths, fit.scaler, target_col)
    ok = np.isfinite(cumulative).all(axis=1) & (radii < 1.0)
    return _guard(
        cumulative[ok], draws, "posterior-predictive draws with joint Gaussian innovations"
    )


def _guard(cumulative: np.ndarray, requested: int, method: str) -> Draws:
    usable = int(cumulative.shape[0])
    if usable < MIN_USABLE_DRAW_FRACTION * requested:
        raise InsufficientDataError(
            f"only {usable} of {requested} predictive draws were usable "
            f"({requested - usable} rejected as unstable or non-finite)",
            hint="the fitted system is near the stability boundary; widen the window, "
            "raise the penalty or lower --lag",
        )
    return Draws(
        cumulative=cumulative, requested=requested, rejected=requested - usable, method=method
    )


# --------------------------------------------------------------------------- #
# One forecast from one origin
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class OriginForecast:
    origin_row: int
    selection: Selection
    fit: Fit
    point: np.ndarray = field(repr=False)
    """Cumulative target log return per step, from the recursive conditional mean."""
    draws: Draws


def forecast_from(
    state: np.ndarray,
    origin_row: int,
    model: str,
    horizon: int,
    target_col: int,
    *,
    training_rows: int,
    seed: int,
    draws: int,
    refits: int,
    fixed_lag: int | None = None,
) -> OriginForecast:
    """Train on the trailing window ending at ``origin_row`` (inclusive) and forecast."""
    start = max(0, origin_row + 1 - training_rows)
    training = state[start : origin_row + 1]
    k = state.shape[1]
    if len(training) < minimum_training_rows(k, fixed_lag or 1):
        raise InsufficientDataError(
            f"{len(training)} training rows at the forecast origin; "
            f"at least {minimum_training_rows(k, fixed_lag or 1)} are needed",
            hint="widen --start/--end",
        )
    selection = select_candidates(training, model, horizon, target_col, fixed_lag=fixed_lag)
    chosen = selection.chosen
    fit = _fit(model, training, chosen.lag, chosen.penalty)
    if not fit.stable:
        raise InsufficientDataError(
            f"the selected {model} (lag {chosen.lag}, penalty {chosen.penalty}) is unstable on the "
            f"full training window (spectral radius {fit.spectral_radius:.4f})",
            hint="raise the penalty or lower --lag",
        )
    z = fit.scaler.transform(training)
    point = cumulative_target(mean_path(fit.b, chosen.lag, z, horizon), fit.scaler, target_col)
    if isinstance(fit, VarFit):
        sims = var_draws(
            fit, training, horizon, seed=seed, draws=draws, refits=refits, target_col=target_col
        )
    else:
        sims = bvar_draws(fit, training, horizon, seed=seed, draws=draws, target_col=target_col)
    return OriginForecast(
        origin_row=origin_row, selection=selection, fit=fit, point=point, draws=sims
    )


def price_distribution(anchor: float, draws: Draws, point: np.ndarray) -> pd.DataFrame:
    """Per step: the median and mean of ``anchor x exp(z)`` over the draws, the 10/90 and
    2.5/97.5 percentiles, and the conditional-mean point in return terms. The point
    statistic is the median price draw; ``anchor x exp(mean log return)`` is not
    presented as an arithmetic expected price."""
    prices = anchor * np.exp(draws.cumulative)
    frame = pd.DataFrame(
        {
            "forecast": np.median(prices, axis=0),
            "mean_price": prices.mean(axis=0),
            "lower80": np.percentile(prices, 10, axis=0),
            "upper80": np.percentile(prices, 90, axis=0),
            "lower95": np.percentile(prices, 2.5, axis=0),
            "upper95": np.percentile(prices, 97.5, axis=0),
            "log_return_point": point,
        }
    )
    frame.index = pd.RangeIndex(1, len(frame) + 1, name="step")
    return frame


# --------------------------------------------------------------------------- #
# Chronological held-out evaluation
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Outcome:
    origin_row: int
    actual: float
    """Realized cumulative target log return over the horizon."""
    anchor: float
    predictions: dict[str, float]
    """Cumulative log-return prediction per model / control."""
    lower80: float
    upper80: float
    lower95: float
    upper95: float
    lag: int
    penalty: float


@dataclass(frozen=True)
class Evaluation:
    horizon: int
    outcomes: list[Outcome]
    metrics: dict[str, dict[str, float | int | None]]
    """Per model / control: return and price RMSE/MAE, direction accuracy, out-of-sample
    R² against the no-change control (None when its denominator is zero), and for the
    modelled series interval coverage and width."""
    window_rows: int
    training_rows: int
    boundaries: dict[str, Any]


def _metrics(
    actual: np.ndarray, predicted: np.ndarray, anchors: np.ndarray
) -> dict[str, float | int | None]:
    """Return errors in log-return units, price errors in the anchor's currency units,
    direction accuracy over the predictions that take a side (None when none does) and
    the out-of-sample R² against the no-change control (None on a zero denominator)."""
    err = predicted - actual
    price_err = anchors * np.exp(predicted) - anchors * np.exp(actual)
    no_change_sse = float(np.sum(actual**2))
    sse = float(np.sum(err**2))
    sided = predicted != 0.0
    direction = (
        None
        if not sided.any()
        else float(np.mean(np.sign(predicted[sided]) == np.sign(actual[sided])))
    )
    return {
        "n": len(actual),
        "return_rmse": float(np.sqrt(np.mean(err**2))),
        "return_mae": float(np.mean(np.abs(err))),
        "price_rmse": float(np.sqrt(np.mean(price_err**2))),
        "price_mae": float(np.mean(np.abs(price_err))),
        "direction_accuracy": direction,
        "oos_r2_vs_no_change": None if no_change_sse == 0.0 else 1.0 - sse / no_change_sse,
    }


def evaluate(
    panel: StatePanel,
    model: str,
    horizon: int,
    *,
    seed: int,
    draws: int,
    refits: int,
    fixed_lag: int | None = None,
    window_rows: int = A,
    training_rows: int = TRAINING_YEARS * A,
    anchors: np.ndarray | None = None,
    progress: Callable[[int, int], None] | None = None,
) -> Evaluation:
    """Outer origins spaced by ``horizon`` over the last ``window_rows`` sessions, each
    forecast with only prior data (selection included); no-change and training-mean
    controls on identical dates. ``anchors`` are the target's prices aligned with the
    panel rows, so price errors are in currency units; without them the anchor is 1."""
    if horizon not in HORIZONS:
        raise UsageError(f"horizon must be one of {', '.join(map(str, HORIZONS))}")
    values = panel.frame.to_numpy(dtype="float64")
    target_col = list(panel.frame.columns).index(panel.target)
    n = len(values)
    first_origin = n - window_rows - 1
    origins = list(range(max(first_origin, 0), n - horizon, horizon))
    origins = [o for o in origins if o + horizon <= n - 1]
    if len(origins) < MIN_OUTER_OUTCOMES:
        raise InsufficientDataError(
            f"{len(origins)} complete held-out outcomes at horizon {horizon}; "
            f"at least {MIN_OUTER_OUTCOMES} are needed",
            hint=(
                f"widen --start/--end so the last {window_rows} sessions hold "
                f"{MIN_OUTER_OUTCOMES} non-overlapping {horizon}-session outcomes after a "
                f"{training_rows}-session training window"
            ),
        )
    k = values.shape[1]
    needed = (
        minimum_training_rows(k, fixed_lag or max(LAG_CANDIDATES))
        + INNER_BLOCKS * (A // 4)
        + horizon
    )
    if origins[0] + 1 < needed:
        raise InsufficientDataError(
            f"{origins[0] + 1} training rows before the first held-out origin; "
            f"at least {needed} are needed for the inner validation blocks",
            hint="widen --start (the default request is ten calendar years)",
        )
    if anchors is not None and len(anchors) != n:
        raise UsageError("anchors must align with the state rows")
    cum = np.cumsum(values[:, target_col])
    outcomes: list[Outcome] = []
    for i, origin in enumerate(origins):
        one = forecast_from(
            values,
            origin,
            model,
            horizon,
            target_col,
            training_rows=training_rows,
            seed=seed + i,
            draws=draws,
            refits=refits,
            fixed_lag=fixed_lag,
        )
        start = max(0, origin + 1 - training_rows)
        train_mean = float(values[start : origin + 1, target_col].mean()) * horizon
        actual = float(cum[origin + horizon] - cum[origin])
        last = one.draws.cumulative[:, -1]
        outcomes.append(
            Outcome(
                origin_row=origin,
                actual=actual,
                anchor=1.0 if anchors is None else float(anchors[origin]),
                predictions={
                    model: float(one.point[-1]),
                    "no_change": 0.0,
                    "training_mean": train_mean,
                },
                lower80=float(np.percentile(last, 10)),
                upper80=float(np.percentile(last, 90)),
                lower95=float(np.percentile(last, 2.5)),
                upper95=float(np.percentile(last, 97.5)),
                lag=one.selection.chosen.lag,
                penalty=one.selection.chosen.penalty,
            )
        )
        if progress is not None:
            progress(i + 1, len(origins))
    actual_arr = np.array([o.actual for o in outcomes])
    anchors = np.array([o.anchor for o in outcomes])
    metrics: dict[str, dict[str, float | int | None]] = {}
    for name in (model, "no_change", "training_mean"):
        predicted = np.array([o.predictions[name] for o in outcomes])
        metrics[name] = _metrics(actual_arr, predicted, anchors)
    lower80 = np.array([o.lower80 for o in outcomes])
    upper80 = np.array([o.upper80 for o in outcomes])
    lower95 = np.array([o.lower95 for o in outcomes])
    upper95 = np.array([o.upper95 for o in outcomes])
    metrics[model].update(
        {
            "coverage80": float(np.mean((actual_arr >= lower80) & (actual_arr <= upper80))),
            "coverage95": float(np.mean((actual_arr >= lower95) & (actual_arr <= upper95))),
            "width80": float(np.mean(upper80 - lower80)),
            "width95": float(np.mean(upper95 - lower95)),
        }
    )
    return Evaluation(
        horizon=horizon,
        outcomes=outcomes,
        metrics=metrics,
        window_rows=window_rows,
        training_rows=training_rows,
        boundaries={
            "first_origin_row": origins[0],
            "last_origin_row": origins[-1],
            "n_state_rows": n,
            "origin_spacing": horizon,
        },
    )


# --------------------------------------------------------------------------- #
# Diagnostics on the fitted system
# --------------------------------------------------------------------------- #


def system_diagnostics(panel: StatePanel, fit: Fit, training: np.ndarray) -> dict[str, Any]:
    """Per-series ADF/KPSS conclusions (statsmodels), design conditioning, the companion
    spectral radius and per-equation Ljung-Box p-values on the residuals."""
    from sobres.core.timeseries import stationarity

    out: dict[str, Any] = {
        "condition_number": fit.condition_number,
        "spectral_radius": fit.spectral_radius,
        "stable": fit.stable,
        "stationarity": {},
        "residual_ljung_box_p": {},
    }
    frame = pd.DataFrame(training, columns=list(panel.frame.columns))
    for column in frame.columns:
        adf, kp = stationarity(frame[column])
        out["stationarity"][str(column)] = {
            "adf": adf.conclusion,
            "kpss": kp.conclusion,
            "agree": adf.conclusion == kp.conclusion,
        }
    if isinstance(fit, VarFit):
        from statsmodels.stats.diagnostic import acorr_ljungbox

        lags = min(10, max(1, fit.residuals.shape[0] // 5))
        for j, column in enumerate(frame.columns):
            lb = acorr_ljungbox(fit.residuals[:, j], lags=[lags], return_df=True)
            out["residual_ljung_box_p"][str(column)] = float(lb["lb_pvalue"].iloc[0])
    return out
