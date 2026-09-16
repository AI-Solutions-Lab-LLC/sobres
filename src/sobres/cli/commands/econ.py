"""``sobres econ`` — stationarity diagnostics, multivariable price forecasts, GARCH, regression.

Adapters only. A symbol names a FRED series when it carries a ``fred:`` prefix,
when ``--source fred`` is given, or when it is in the small catalog of known FRED
ids; every other bare symbol is a price ticker, and ``ticker:`` makes that
explicit. Symbol length or digits never decide. Prices become simple returns for
volatility and regression, stay levels for diagnosis, and become split-only log
returns for forecasting; macro levels are differenced for regression, and the
output says which transform was applied. ``statsmodels``/``arch`` are the econ
extra: without it every command exits 3 with the install hint, never a traceback.

Forecasting (revised 0009) models a joint state — the target's split-only log
return, a market return, log realized volatility and the change in log dollar-
volume activity, plus an optional sector return — with a ridge VAR or a
Minnesota-prior BVAR, selected on chronological inner blocks, evaluated on
held-out origins against no-change and training-mean controls, and rendered as
a price distribution with mandatory 80% and 95% bounds. The math is in
``sobres.core.forecast``.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date
from typing import Annotated, Any, ClassVar, Literal

import pandas as pd
from pydantic import BeforeValidator, Field, field_validator, model_validator

from sobres.cli.context import Context
from sobres.cli.window import years_before
from sobres.core import forecast as fc
from sobres.core import regression as rg
from sobres.core import timeseries as ts
from sobres.core.conventions import infer_frequency
from sobres.core.errors import UsageError
from sobres.core.returns import simple_returns
from sobres.data.currency import frame_currencies
from sobres.data.gaps import FillPolicy, apply_fill_policy
from sobres.registry import Params, positional, register
from sobres.results import FrameResult, Provenance, RecordsResult, Result

Source = Literal["auto", "fred", "ticker"]
DEFAULT_BENCHMARK = "ticker:SPY"
FORECAST_REQUEST_YEARS = 10
"""Calendar years of history requested when --start is not given (design.md)."""
PRICE_BASIS = "split-only close (dividends not reinvested; the quoted price basis)"
MARKET_DATA_NOTE = (
    "revised-market-data: keyless history is the vendor's current revision, not an "
    "archived point-in-time snapshot; held-out results are not tradability claims"
)
REMOVED_MODELS = ("arima", "ar", "arma", "sarima", "auto-arima", "auto_arima")
MIGRATION_EXAMPLE = "econ forecast ticker:AAPL --model var --horizon 20"

FRED_CATALOG: frozenset[str] = frozenset(
    {
        "BAA10Y",
        "CPIAUCSL",
        "DEXUSEU",
        "DFF",
        "DGS10",
        "DGS2",
        "DGS30",
        "DGS3MO",
        "DTB3",
        "FEDFUNDS",
        "GBRCPIALLMINMEI",
        "GDP",
        "GDPC1",
        "INDPRO",
        "IR3TIB01GBM156N",
        "PCEPI",
        "T10Y3M",
        "UNRATE",
        "VIXCLS",
    }
)
"""FRED ids a bare symbol may name. Anything else bare is a ticker; use ``fred:`` otherwise."""


class EconReport(Result):
    report: ClassVar[bool] = True


# --------------------------------------------------------------------------- #
# Symbol resolution
# --------------------------------------------------------------------------- #


def resolve_source(symbol: str, source: Source = "auto") -> tuple[str, str]:
    """``("fred", "DGS10")`` or ``("ticker", "SPY")``: prefix, then ``--source``, then the
    FRED catalog; a bare symbol outside the catalog is a ticker. No length/digit guess."""
    text = symbol.strip()
    lower = text.lower()
    if lower.startswith("fred:"):
        return "fred", text[5:].upper()
    if lower.startswith("ticker:"):
        return "ticker", text[7:].upper()
    if source != "auto":
        return source, text.upper()
    return ("fred" if text.upper() in FRED_CATALOG else "ticker"), text.upper()


def require_ticker(symbol: str, what: str) -> str:
    kind, name = resolve_source(symbol, "auto")
    if kind != "ticker":
        raise UsageError(
            f"{what} must be a price ticker, got the FRED series {name}",
            hint=f"pass ticker:{name} only if {name} is a quoted price series",
        )
    return name


def load_series(
    symbol: str, ctx: Context, start: date, end: date, *, source: Source = "auto"
) -> tuple[pd.Series, str, Provenance]:
    """One level series (prices or a macro series) with its kind and provenance."""
    kind, name = resolve_source(symbol, source)
    if kind == "fred":
        frame = ctx.macro_provider().get_series([name], start, end)
    else:
        frame = ctx.price_provider().get_prices([name], start, end)
    series = pd.Series(frame[name]).dropna()
    series.name = name
    provenance = Provenance.from_attrs(
        frame.attrs,
        start=str(series.index.min().date()) if len(series) else None,
        end=str(series.index.max().date()) if len(series) else None,
    )
    return series, kind, provenance


# --------------------------------------------------------------------------- #
# Shared parameters
# --------------------------------------------------------------------------- #


class WindowParams(Params):
    start: date = Field(default=date(2010, 1, 1), description="First date, YYYY-MM-DD.")
    end: date | None = Field(default=None, description="Last date (default: today).")
    source: Source = Field(
        default="auto",
        description=(
            "How to read bare symbols: auto (known FRED ids are FRED, anything else a ticker), "
            "fred, ticker. fred:/ticker: prefixes always win."
        ),
    )


# --------------------------------------------------------------------------- #
# econ diagnose
# --------------------------------------------------------------------------- #


class DiagnoseParams(WindowParams):
    series: str = positional(description="A FRED series (DGS10) or a ticker (SPY, or ticker:X).")
    lags: int = Field(default=ts.DEFAULT_LAGS, ge=1, le=100, description="ACF/PACF lags.")


class DiagnosisResult(EconReport, RecordsResult):
    """One row per lag (ACF, PACF, the bound); the tests in the header."""

    column_kinds: ClassVar[dict[str, str]] = {"lag": "int"}
    series: str
    n_obs: int
    adf: dict[str, Any]
    kpss: dict[str, Any]
    agree: bool
    verdict: str
    bound: float

    def header_lines(self) -> list[str]:
        a, k = self.adf, self.kpss
        return [
            f"{self.series}: {self.n_obs} observations",
            f"ADF (H0 unit root): statistic {a['statistic']:.3f}, p = {a['pvalue']:.3f}, "
            f"{a['lags']} lags -> {a['conclusion']}",
            f"KPSS (H0 stationary): statistic {k['statistic']:.3f}, p = {k['pvalue']:.3f}, "
            f"{k['lags']} lags -> {k['conclusion']}",
            self.verdict,
            f"ACF/PACF significance bound ±{self.bound:.4f} (1.96/√n)",
            *super().header_lines(),
        ]


@register(
    "econ.diagnose",
    "Stationarity tests (ADF, KPSS) and ACF/PACF through lag 20 for one series.",
    result=DiagnosisResult,
    example="econ diagnose DGS10",
)
def diagnose(p: DiagnoseParams, ctx: Context) -> DiagnosisResult:
    series, _kind, provenance = load_series(
        p.series, ctx, p.start, p.end or ctx.today(), source=p.source
    )
    d = ts.diagnose(series, lags=p.lags)
    rows = [
        {
            "lag": i + 1,
            "acf": a,
            "pacf": pc,
            "acf_significant": abs(a) > d.bound,
            "pacf_significant": abs(pc) > d.bound,
        }
        for i, (a, pc) in enumerate(zip(d.acf, d.pacf, strict=True))
    ]
    return DiagnosisResult(
        rows=rows,
        columns=["lag", "acf", "pacf", "acf_significant", "pacf_significant"],
        series=str(series.name),
        n_obs=d.n_obs,
        adf=d.adf.__dict__,
        kpss=d.kpss.__dict__,
        agree=d.agree,
        verdict=d.verdict,
        bound=d.bound,
        provenance=provenance,
    )


# --------------------------------------------------------------------------- #
# econ forecast / econ evaluate
# --------------------------------------------------------------------------- #


def _reject_removed_model(value: Any) -> Any:
    if isinstance(value, str) and value.strip().lower() in REMOVED_MODELS:
        raise ValueError(
            f"{value} was removed with the univariate forecasters (0009); "
            "the forecast is a joint model: choose var or bvar"
        )
    return value


ModelChoice = Annotated[fc.ForecastModel, BeforeValidator(_reject_removed_model)]


class ForecastWindow(Params):
    """Window, sources and simulation settings shared by forecast and evaluate."""

    horizon: int = Field(
        default=20, description="Target-market sessions ahead: 1, 5 or 20 (cumulative)."
    )
    preset: Literal["equity-basic"] = Field(
        default="equity-basic",
        description="Predictor preset: target return, market return, log realized volatility, "
        "change in log dollar-volume activity (keyless).",
    )
    benchmark: str = Field(
        default=DEFAULT_BENCHMARK, description="Market return series, ticker:<symbol>."
    )
    sector: str | None = Field(
        default=None,
        description="Optional sector series (ticker:XLK) joined to the state; never inferred.",
    )
    lag: int | None = Field(
        default=None,
        ge=1,
        le=fc.MAX_LAG,
        description="Fix the lag order (1-5) instead of selecting from 1, 2, 5 on inner blocks.",
    )
    start: date | None = Field(
        default=None,
        description=f"First date requested (default: {FORECAST_REQUEST_YEARS} calendar years "
        "before --end; an explicit start is never silently extended).",
    )
    end: date | None = Field(default=None, description="Last completed session (default: today).")
    fill: FillPolicy = Field(
        default="raise",
        description="Provider-gap policy: raise (default), drop or ffill. Closures are never "
        "filled and price gaps are never bridged.",
    )
    seed: int = Field(default=0, description="Seed for the predictive draws; always printed.")
    draws: int = Field(
        default=fc.DEFAULT_DRAWS, ge=100, le=20000, description="Predictive draws per forecast."
    )
    refits: int = Field(
        default=fc.DEFAULT_REFITS,
        ge=1,
        le=2000,
        description="Bootstrap parameter refits for var (ignored by bvar).",
    )

    @field_validator("horizon")
    @classmethod
    def _horizon(cls, value: int) -> int:
        if value not in fc.HORIZONS:
            raise ValueError(f"horizon must be one of {', '.join(map(str, fc.HORIZONS))}")
        return value

    @model_validator(mode="after")
    def _dates(self) -> ForecastWindow:
        if self.start is not None and self.end is not None and self.start >= self.end:
            raise ValueError("--start must be before --end")
        return self


class ForecastParams(ForecastWindow):
    ticker: str = positional(description="Target stock, ticker:AAPL (a bare symbol is a ticker).")
    model: ModelChoice = Field(
        default="var", description="var (ridge VAR) or bvar (Minnesota prior)."
    )


class EvaluateParams(ForecastWindow):
    ticker: str = positional(description="Target stock, ticker:AAPL (a bare symbol is a ticker).")
    models: list[ModelChoice] = Field(
        default_factory=lambda: list(fc.FORECAST_MODELS),  # type: ignore[arg-type]
        description="Models to score on identical held-out dates.",
    )


def _window(p: ForecastWindow, ctx: Context) -> tuple[date, date]:
    end = p.end or ctx.today()
    start = p.start or years_before(end, FORECAST_REQUEST_YEARS)
    return start, end


def _drop_reindexed(prices: pd.DataFrame, policy: FillPolicy) -> pd.DataFrame:
    """Apply the gap policy; under ``drop`` keep the missing dates as NaN so a log return can
    never bridge several sessions (the state builder drops incomplete rows)."""
    filled = apply_fill_policy(prices, policy)
    if policy == "drop":
        filled = filled.reindex(prices.index)
    return filled


def _load_panel(
    p: ForecastWindow, ticker: str, ctx: Context
) -> tuple[fc.StatePanel, pd.Series, Provenance, dict[str, str]]:
    ts.require_econ()
    target = require_ticker(ticker, "the target")
    market = require_ticker(p.benchmark, "--benchmark")
    sector = require_ticker(p.sector, "--sector") if p.sector else None
    symbols = [target, market] + ([sector] if sector and sector not in (target, market) else [])
    if target == market:
        raise UsageError(
            f"the target {target} is also the benchmark",
            hint="pass a different --benchmark ticker:<symbol>",
        )
    start, end = _window(p, ctx)
    provider = ctx.price_provider()
    closes = provider.get_prices(symbols, start, end, "close")
    currencies = frame_currencies(closes)
    if len(set(currencies.values())) > 1:
        pairs = ", ".join(f"{k} {v}" for k, v in sorted(currencies.items()))
        raise UsageError(
            f"the target, benchmark and sector are quoted in different currencies ({pairs})",
            hint="choose a benchmark quoted in the target's currency; no exchange rate is "
            "projected to manufacture a price forecast",
        )
    volume = provider.get_prices([target], start, end, "volume")
    closes = _drop_reindexed(closes, p.fill)
    panel = fc.build_state(
        pd.Series(closes[target]),
        pd.Series(volume[target]),
        pd.Series(closes[market]),
        pd.Series(closes[sector]) if sector else None,
        target=target,
        market=market,
        sector=sector,
    )
    gaps = closes.attrs.get("filled", {})
    provenance = Provenance.from_attrs(
        closes.attrs,
        start=str(panel.frame.index.min().date()),
        end=str(panel.frame.index.max().date()),
        notes=[
            f"price basis: {PRICE_BASIS}",
            MARKET_DATA_NOTE,
            f"gaps: policy {p.fill}, filled {gaps.get('filled', 0)}, "
            f"warmup rows dropped {panel.warmup_rows}",
        ],
    )
    return panel, pd.Series(closes[target]), provenance, currencies


def _metrics_rows(evaluations: Mapping[str, fc.Evaluation]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name, ev in evaluations.items():
        for series in (name, "no_change", "training_mean"):
            if series in seen:
                continue
            seen.add(series)
            m = ev.metrics[series]
            rows.append({"model": series, **m})
    return rows


class ForecastResult(EconReport, FrameResult):
    """One row per future session: the median price draw, its mean, 80% and 95% bounds and
    the conditional-mean cumulative log return. Never a point alone."""

    index_label: ClassVar[str | None] = "step"
    column_kinds: ClassVar[dict[str, str]] = {
        "date": "text",
        "forecast": "price",
        "mean_price": "price",
        "lower80": "price",
        "upper80": "price",
        "lower95": "price",
        "upper95": "price",
        "log_return_point": "return",
    }
    ticker: str
    model: str
    model_version: str
    preset: str
    catalog_version: str
    horizon: int
    origin: str
    anchor_price: float
    currency: str
    price_basis: str
    benchmark: str
    sector: str | None
    predictors: list[dict[str, Any]]
    lag: int
    penalty: float
    candidates: list[dict[str, Any]]
    selection: dict[str, Any]
    prior: dict[str, Any] | None
    diagnostics: dict[str, Any]
    evaluation: dict[str, Any]
    draws: dict[str, Any]
    refits: int | None
    seed: int
    point_statistic: str
    n_state_rows: int
    training_rows: int

    def header_lines(self) -> list[str]:
        m = self.evaluation["metrics"]
        own = m[self.model]
        nc = m["no_change"]
        shrink = (
            f"ridge λ={self.penalty:g}"
            if self.model == "var"
            else f"prior tightness {self.penalty:g}"
        )
        r2 = own["oos_r2_vs_no_change"]
        r2_text = "undefined (zero-denominator)" if r2 is None else f"{r2:+.3f}"
        acc = own["direction_accuracy"]
        direction = "undefined" if acc is None else f"{acc:.0%}"
        lines = [
            f"{self.ticker}: {self.model.upper()} ({self.model_version}) on "
            f"{len(self.predictors)} joint series, lag {self.lag}, {shrink}; "
            f"origin {self.origin}, anchor {self.anchor_price:.2f} {self.currency}, "
            f"{self.horizon}-session horizon",
            "state: "
            + "; ".join(f"{d['column']} = {d['formula']}" for d in self.predictors)
            + f" (catalog {self.catalog_version})",
            f"selection: {len(self.candidates)} candidates on {self.selection['blocks']} inner "
            f"blocks of {self.selection['block_length']} sessions, "
            f"purge {self.selection['purge']}; outer dates never tune",
            f"held-out ({own['n']} origins spaced {self.horizon} sessions): return RMSE "
            f"{own['return_rmse']:.4f} vs no-change {nc['return_rmse']:.4f}, direction "
            f"{direction}, OOS R² vs no-change {r2_text}, "
            f"80%/95% coverage {own['coverage80']:.0%}/{own['coverage95']:.0%}",
            f"intervals: 80% and 95% bounds from {self.draws['usable']} of "
            f"{self.draws['requested']} draws ({self.draws['method']}), seed {self.seed}; "
            f"the point is the {self.point_statistic}",
            f"price basis: {self.price_basis}",
        ]
        stab = self.diagnostics.get("stationarity", {})
        disagree = [k for k, v in stab.items() if not v.get("agree", True)]
        if disagree:
            lines.append(
                "stationarity tests disagree for "
                + ", ".join(disagree)
                + "; the fit is reported, not resolved by fiat"
            )
        if not self.diagnostics.get("stable", True):
            lines.append("WARNING: the fitted system is not stable")
        return [*lines, *super().header_lines()]


def _run_evaluation(
    panel: fc.StatePanel,
    close: pd.Series,
    model: str,
    p: ForecastWindow,
    ctx: Context,
    label: str,
) -> fc.Evaluation:
    def progress(done: int, total: int) -> None:
        ctx.report_progress(done / total, f"{label} held-out origin {done} of {total}")

    return fc.evaluate(
        panel,
        model,
        p.horizon,
        seed=p.seed,
        draws=p.draws,
        refits=p.refits,
        fixed_lag=p.lag,
        anchors=close.reindex(panel.frame.index).to_numpy(dtype="float64"),
        progress=progress,
    )


def _evaluation_payload(ev: fc.Evaluation, model: str) -> dict[str, Any]:
    return {
        "horizon": ev.horizon,
        "n_outcomes": len(ev.outcomes),
        "window_rows": ev.window_rows,
        "training_rows": ev.training_rows,
        "boundaries": ev.boundaries,
        "metrics": ev.metrics,
        "controls": ["no_change", "training_mean"],
        "selections": [
            {"origin_row": o.origin_row, "lag": o.lag, "penalty": o.penalty} for o in ev.outcomes
        ],
        "model": model,
    }


@register(
    "econ.forecast",
    "Multivariable price forecast (ridge VAR or BVAR) with held-out evidence and 80%/95% bounds.",
    result=ForecastResult,
    long_running=True,
    example=MIGRATION_EXAMPLE,
)
def forecast(p: ForecastParams, ctx: Context) -> ForecastResult:
    panel, close, provenance, currencies = _load_panel(p, p.ticker, ctx)
    target = panel.target.removesuffix("_ret")
    evaluation = _run_evaluation(panel, close, p.model, p, ctx, p.model)
    values = panel.frame.to_numpy(dtype="float64")
    target_col = list(panel.frame.columns).index(panel.target)
    one = fc.forecast_from(
        values,
        len(values) - 1,
        p.model,
        p.horizon,
        target_col,
        training_rows=fc.TRAINING_YEARS * fc.A,
        seed=p.seed,
        draws=p.draws,
        refits=p.refits,
        fixed_lag=p.lag,
    )
    origin = panel.frame.index[-1]
    anchor = float(close.loc[origin])
    table = fc.price_distribution(anchor, one.draws, one.point)
    sessions = pd.bdate_range(origin + pd.Timedelta(days=1), periods=p.horizon)
    table.insert(0, "date", [d.date().isoformat() for d in sessions])
    start_row = max(0, len(values) - fc.TRAINING_YEARS * fc.A)
    diagnostics = fc.system_diagnostics(panel, one.fit, values[start_row:])
    ctx.log.warning(
        "forecast.selected",
        ticker=target,
        model=p.model,
        lag=one.selection.chosen.lag,
        penalty=one.selection.chosen.penalty,
        seed=p.seed,
    )
    provenance.notes.append(
        "future dates are expected business days; exchange holidays are not modelled"
    )
    return ForecastResult(
        frame=table,
        ticker=target,
        model=p.model,
        model_version=fc.MODEL_VERSIONS[p.model],
        preset=p.preset,
        catalog_version=fc.CATALOG_VERSION,
        horizon=p.horizon,
        origin=str(origin.date()),
        anchor_price=anchor,
        currency=currencies[target],
        price_basis=PRICE_BASIS,
        benchmark=require_ticker(p.benchmark, "--benchmark"),
        sector=require_ticker(p.sector, "--sector") if p.sector else None,
        predictors=[d.__dict__ for d in panel.predictors],
        lag=one.selection.chosen.lag,
        penalty=one.selection.chosen.penalty,
        candidates=[c.as_dict() for c in one.selection.candidates],
        selection={
            "blocks": fc.INNER_BLOCKS,
            "block_length": one.selection.block_length,
            "purge": one.selection.purge,
            "boundaries": one.selection.boundaries,
            "loss": "mean squared error of the cumulative target log return",
            "ties": "stronger shrinkage, then fewer lags",
        },
        prior=one.fit.prior if isinstance(one.fit, fc.BvarFit) else None,
        diagnostics=diagnostics,
        evaluation=_evaluation_payload(evaluation, p.model),
        draws={
            "requested": one.draws.requested,
            "usable": one.draws.usable,
            "rejected": one.draws.rejected,
            "method": one.draws.method,
        },
        refits=p.refits if p.model == "var" else None,
        seed=p.seed,
        point_statistic="median of the price draws (not the exponentiated mean log return)",
        n_state_rows=len(values),
        training_rows=min(len(values), fc.TRAINING_YEARS * fc.A),
        provenance=provenance,
    )


class EvaluationResult(EconReport, RecordsResult):
    """One row per model and control, scored on identical held-out dates."""

    column_kinds: ClassVar[dict[str, str]] = {"model": "text", "n": "int"}
    ticker: str
    horizon: int
    models: list[str]
    n_outcomes: int
    boundaries: dict[str, Any]
    selections: dict[str, list[dict[str, Any]]]
    candidates_note: str
    seed: int
    draws: int
    refits: int
    predictors: list[dict[str, Any]]
    price_basis: str

    def header_lines(self) -> list[str]:
        return [
            f"{self.ticker}: {', '.join(m.upper() for m in self.models)} against no-change and "
            f"training-mean controls on {self.n_outcomes} identical held-out origins "
            f"({self.horizon}-session horizon, spaced {self.horizon})",
            f"draws {self.draws}, refits {self.refits}, seed {self.seed}; per-origin lag and "
            "penalty are in `selections`; outer results never choose a winner",
            "OOS R² is 1 - SSE(model)/SSE(no-change); null when that denominator is zero",
            f"price basis: {self.price_basis}",
            *super().header_lines(),
        ]


@register(
    "econ.evaluate",
    "Score var and bvar against no-change and training-mean controls on held-out dates.",
    result=EvaluationResult,
    long_running=True,
    example="econ evaluate ticker:AAPL --models var bvar --horizon 20",
)
def evaluate(p: EvaluateParams, ctx: Context) -> EvaluationResult:
    models: list[str] = list(dict.fromkeys(p.models))
    panel, close, provenance, _currencies = _load_panel(p, p.ticker, ctx)
    evaluations = {m: _run_evaluation(panel, close, m, p, ctx, m) for m in models}
    first = evaluations[models[0]]
    rows = _metrics_rows(evaluations)
    columns = [
        "model",
        "n",
        "return_rmse",
        "return_mae",
        "price_rmse",
        "price_mae",
        "direction_accuracy",
        "oos_r2_vs_no_change",
        "coverage80",
        "coverage95",
        "width80",
        "width95",
    ]
    for row in rows:
        for column in columns:
            row.setdefault(column, None)
    return EvaluationResult(
        rows=rows,
        columns=columns,
        ticker=panel.target.removesuffix("_ret"),
        horizon=p.horizon,
        models=models,
        n_outcomes=len(first.outcomes),
        boundaries=first.boundaries,
        selections={
            m: [
                {"origin_row": o.origin_row, "lag": o.lag, "penalty": o.penalty}
                for o in ev.outcomes
            ]
            for m, ev in evaluations.items()
        },
        candidates_note="every candidate and its inner-validation loss is visible in "
        "`sobres econ forecast --format json`",
        seed=p.seed,
        draws=p.draws,
        refits=p.refits,
        predictors=[d.__dict__ for d in panel.predictors],
        price_basis=PRICE_BASIS,
        provenance=provenance,
    )


# --------------------------------------------------------------------------- #
# econ volatility
# --------------------------------------------------------------------------- #


class VolatilityParams(WindowParams):
    ticker: str = positional(description="A ticker whose returns are modelled.")
    horizon: int = Field(default=30, ge=1, le=250, description="Steps ahead.")
    model: ts.VolModel = Field(default="garch", description="garch, egarch or ewma.")
    simulations: int = Field(default=1000, ge=100, description="Paths for the intervals.")
    seed: int | None = Field(default=None, description="Seed; printed even when auto-generated.")


class VolatilityResult(EconReport, FrameResult):
    index_label: ClassVar[str | None] = "step"
    ticker: str
    model: str
    frequency: str
    n_obs: int
    seed: int
    simulations: int
    params: dict[str, float]
    last_observed: float

    def header_lines(self) -> list[str]:
        params = ", ".join(f"{k}={v:.4g}" for k, v in self.params.items())
        return [
            f"{self.ticker}: {self.model.upper()} on {self.n_obs} {self.frequency} returns; "
            "volatility is annualized (sqrt of periods per year from the conventions table)",
            f"parameters: {params}",
            f"last observed conditional volatility {self.last_observed:.4%} annualized",
            f"intervals: 80% and 95% bands from {self.simulations} simulated paths, "
            f"seed {self.seed}",
            *super().header_lines(),
        ]


@register(
    "econ.volatility",
    "GARCH, EGARCH or EWMA conditional volatility forecast, annualized, with intervals.",
    result=VolatilityResult,
    example="econ volatility SPY --model garch --horizon 30",
)
def volatility(p: VolatilityParams, ctx: Context) -> VolatilityResult:
    series, _kind, provenance = load_series(
        p.ticker, ctx, p.start, p.end or ctx.today(), source="ticker"
    )
    returns = pd.Series(simple_returns(series)).dropna()
    frequency = infer_frequency(pd.DatetimeIndex(returns.index))
    fit = ts.volatility_forecast(
        returns,
        p.horizon,
        model=p.model,
        frequency=frequency,
        seed=p.seed,
        simulations=p.simulations,
    )
    return VolatilityResult(
        frame=fit.frame(),
        ticker=str(series.name),
        model=fit.model,
        frequency=fit.frequency,
        n_obs=fit.n_obs,
        seed=fit.seed,
        simulations=fit.simulations,
        params=fit.params,
        last_observed=fit.last_observed,
        provenance=provenance,
    )


# --------------------------------------------------------------------------- #
# econ regress
# --------------------------------------------------------------------------- #


class RegressParams(WindowParams):
    y: str = Field(description="Dependent series: a ticker (returns) or fred:SERIES (differences).")
    x: list[str] = Field(min_length=1, description="Regressors, same conventions.")
    robust: rg.Robust = Field(default="hac", description="Covariance: hac, hc0-hc3 or none.")
    hac_lags: int | None = Field(
        default=None, ge=0, description="Newey-West lags for --robust hac."
    )


class RegressionResult(EconReport, RecordsResult):
    column_kinds: ClassVar[dict[str, str]] = {"term": "text", "transform": "text"}
    y: str
    robust: str
    hac_lags: int | None
    n_obs: int
    r2: float
    adj_r2: float
    f_statistic: float
    f_pvalue: float
    durbin_watson: float
    breusch_pagan: dict[str, float]
    vif: dict[str, float]
    vif_flags: list[str]
    transforms: dict[str, str]

    def header_lines(self) -> list[str]:
        cov = (
            f"HAC (Newey-West, {self.hac_lags} lags)"
            if self.robust == "hac"
            else self.robust.upper()
        )
        if self.robust == "none":
            cov = "classical OLS (no robust correction)"
        lines = [
            f"{self.y} on {', '.join(k for k in self.transforms if k != self.y)}: "
            f"{self.n_obs} observations; standard errors: {cov}",
            "transforms: " + ", ".join(f"{k} = {v}" for k, v in self.transforms.items()),
            f"R² {self.r2:.4f}, adjusted R² {self.adj_r2:.4f}; F = {self.f_statistic:.2f} "
            f"(p = {self.f_pvalue:.3g}); Durbin-Watson {self.durbin_watson:.3f}",
            f"Breusch-Pagan {self.breusch_pagan['statistic']:.2f} "
            f"(p = {self.breusch_pagan['pvalue']:.3f}): "
            + (
                "heteroskedastic residuals; prefer a robust covariance"
                if self.breusch_pagan["pvalue"] < 0.05
                else "no evidence of heteroskedasticity"
            ),
        ]
        if len(self.vif) > 1:
            vif = ", ".join(f"{k} {v:.2f}" for k, v in self.vif.items())
            lines.append(
                f"VIF: {vif}"
                + (
                    f"; above 10 (multicollinear): {', '.join(self.vif_flags)}"
                    if self.vif_flags
                    else ""
                )
            )
        return [*lines, *super().header_lines()]


def _regressor(
    symbol: str, ctx: Context, start: date, end: date, source: Source
) -> tuple[pd.Series, str]:
    series, kind, _ = load_series(symbol, ctx, start, end, source=source)
    if kind == "ticker":
        out = pd.Series(simple_returns(series)).dropna()
        return out, "simple returns"
    out = series.diff().dropna()
    return out, "first differences"


@register(
    "econ.regress",
    "OLS with robust standard errors, VIF and residual diagnostics.",
    result=RegressionResult,
    example="econ regress --y AAPL --x SPY DGS10 --robust hac",
)
def regress(p: RegressParams, ctx: Context) -> RegressionResult:
    end = p.end or ctx.today()
    y, y_transform = _regressor(p.y, ctx, p.start, end, p.source)
    columns: dict[str, pd.Series] = {}
    transforms = {str(y.name): y_transform}
    for symbol in p.x:
        series, transform = _regressor(symbol, ctx, p.start, end, p.source)
        name = str(series.name)
        if name in columns or name == y.name:
            raise UsageError(f"{name} appears twice")
        columns[name] = series
        transforms[name] = transform
    x = pd.DataFrame(columns)
    fit = rg.regress(y, x, robust=p.robust, hac_lags=p.hac_lags)
    rows = [{"term": name, **term.as_dict()} for name, term in fit.terms.items()]
    return RegressionResult(
        rows=rows,
        columns=["term", "coefficient", "se", "t", "p"],
        y=str(y.name),
        robust=fit.robust,
        hac_lags=fit.hac_lags,
        n_obs=fit.n_obs,
        r2=fit.r2,
        adj_r2=fit.adj_r2,
        f_statistic=fit.f_statistic,
        f_pvalue=fit.f_pvalue,
        durbin_watson=fit.durbin_watson,
        breusch_pagan={
            "statistic": fit.breusch_pagan_statistic,
            "pvalue": fit.breusch_pagan_pvalue,
        },
        vif=fit.vif,
        vif_flags=fit.vif_flags,
        transforms=transforms,
        provenance=Provenance(notes=["returns and differences are aligned on their common dates"]),
    )
