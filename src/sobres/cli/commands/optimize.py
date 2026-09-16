"""``sobres optimize`` — Markowitz weights, the efficient frontier, a walk-forward backtest.

Adapters only: fetch through the data layer, call ``core``, return typed
results. The loader below is the one place prices become returns for these
commands: it converts a multi-currency universe to ``--base`` *before* any
moment is estimated, applies the explicit gap policy, and resolves the
risk-free rate (FRED 3-month bill when a key is configured, else 0.0 with a
WARNING — an assumption that changes a number is always visible).
"""

from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, ClassVar

import pandas as pd
from pydantic import Field, FiniteFloat, model_validator

from sobres.cli.context import Context
from sobres.cli.metric_table import render_metric_table
from sobres.core import backtest as bt
from sobres.core import moments
from sobres.core import optimize as opt
from sobres.core.conventions import infer_frequency
from sobres.core.errors import UsageError
from sobres.core.rates import prior_rates, treasury_investment_yield
from sobres.core.returns import apply_nan_policy, portfolio_returns, simple_returns
from sobres.core.risk import RiskPanel, risk_metrics
from sobres.data.currency import (
    FxRates,
    convert_frame,
    frame_currencies,
    pairs_for,
    require_single_currency,
)
from sobres.data.gaps import FillPolicy, apply_fill_policy
from sobres.registry import Currency, Params, Ticker, TickerList, Weights, register
from sobres.results import FrameResult, Provenance, RecordsResult
from sobres.settings import FRED_API_KEY

SURVIVORSHIP_NOTE = (
    "survivorship: a ticker list chosen today reflects survivors, so results over past "
    "windows are biased upward; no free source provides point-in-time constituents"
)
IN_SAMPLE_NOTE = (
    "in-sample: estimated on the same data it is evaluated on; see `sobres optimize backtest`"
)


# --------------------------------------------------------------------------- #
# Shared parameters
# --------------------------------------------------------------------------- #


class UniverseParams(Params):
    tickers: TickerList | None = Field(
        default=None, description="Ticker symbols, e.g. AAPL MSFT NESN.SW (or use --portfolio)."
    )
    portfolio: str | None = Field(
        default=None, description="A saved portfolio's name in place of --tickers."
    )
    save_run: bool = Field(default=False, description="Record this run in the run history.")
    start: date = Field(description="First date, YYYY-MM-DD.")
    end: date | None = Field(default=None, description="Last date (default: today).")
    fill: FillPolicy = Field(description="Provider-gap policy: drop, ffill or raise. No default.")
    base: Currency | None = Field(
        default=None, description="Base currency for a multi-currency universe (e.g. USD)."
    )
    risk_free: FiniteFloat | None = Field(
        default=None,
        description=(
            "Annual decimal risk-free rate; default: FRED 3-month bill, or 0.0 without a key."
        ),
    )

    @model_validator(mode="after")
    def _window(self) -> UniverseParams:
        if self.tickers and (
            len(self.tickers) > 100 or len(set(self.tickers)) != len(self.tickers)
        ):
            raise ValueError("choose 1 to 100 distinct tickers, e.g. --tickers AAPL MSFT")
        if not date(1900, 1, 1) <= self.start <= date(2200, 1, 1) or (
            self.end is not None and not date(1900, 1, 1) <= self.end <= date(2200, 1, 1)
        ):
            raise ValueError("dates must be between 1900-01-01 and 2200-01-01")
        if self.end is not None and self.end < self.start:
            raise ValueError(f"end {self.end} precedes start {self.start}")
        if self.portfolio and self.tickers:
            raise ValueError("--portfolio and --tickers are mutually exclusive")
        if not self.portfolio and not self.tickers:
            raise ValueError("one of --tickers or --portfolio is required")
        return self

    @property
    def symbols(self) -> list[str]:
        """Tickers after ``--portfolio`` resolution (set by the loader)."""
        return list(self.tickers or [])


class EstimatorParams(UniverseParams):
    benchmark: Ticker | None = Field(
        default=None, description="Benchmark ticker required for CAPM, e.g. --benchmark SPY."
    )
    returns_estimator: moments.ReturnMethod = Field(
        default="mean_historical", description="Expected-return estimator."
    )
    covariance: moments.CovMethod = Field(
        default="ledoit_wolf", description="Covariance estimator; Ledoit-Wolf shrinkage by default."
    )
    max_weight: FiniteFloat | None = Field(
        default=None, gt=0, le=1, description="Cap on any single weight."
    )
    allow_short: bool = Field(default=False, description="Relax the lower bound from 0 to -1.")

    @model_validator(mode="after")
    def _estimator_inputs(self) -> EstimatorParams:
        if self.returns_estimator == "capm" and self.benchmark is None:
            raise ValueError(
                "CAPM needs --benchmark, e.g. --returns-estimator capm --benchmark SPY"
            )
        if self.benchmark is not None and self.returns_estimator != "capm":
            raise ValueError("--benchmark is used only with --returns-estimator capm")
        if (
            self.tickers
            and self.max_weight is not None
            and self.max_weight * len(self.tickers) < 1.0 - 1e-8
        ):
            raise ValueError(
                f"max_weight {self.max_weight} is infeasible for {len(self.tickers)} assets; "
                "raise --max-weight"
            )
        return self


# --------------------------------------------------------------------------- #
# Loader
# --------------------------------------------------------------------------- #


@dataclass
class Universe:
    returns: pd.DataFrame
    prices: pd.DataFrame
    frequency: str
    currency: str
    risk_free: float
    risk_free_source: str
    provenance: Provenance
    risk_free_rates: pd.Series
    benchmark: pd.Series | None = None


def resolve_symbols(p: UniverseParams, ctx: Context) -> tuple[list[str], list[float] | None]:
    """The ticker list and, from a saved portfolio, its weights."""
    if p.portfolio:
        from sobres.cli.commands.portfolio import resolve_portfolio

        record = resolve_portfolio(p.portfolio, ctx)
        tickers = list(record.tickers)
        if not tickers or len(tickers) > 100 or len(set(tickers)) != len(tickers):
            raise UsageError("choose 1 to 100 distinct tickers in the saved portfolio")
        if (
            isinstance(p, EstimatorParams)
            and p.max_weight is not None
            and p.max_weight * len(tickers) < 1.0 - 1e-8
        ):
            raise UsageError(
                f"max_weight {p.max_weight} is infeasible for {len(tickers)} assets; "
                "raise --max-weight"
            )
        if isinstance(p, BacktestParams) and parse_lookback(p.lookback, "daily") <= len(tickers):
            raise UsageError("lookback must have more observations than assets")
        return tickers, None if record.weights is None else list(record.weights)
    return list(p.tickers or []), None


def load_universe(p: UniverseParams, ctx: Context) -> Universe:
    started = time.perf_counter()
    end = p.end or ctx.today()
    tickers, _ = resolve_symbols(p, ctx)
    symbols = list(tickers)
    benchmark = p.benchmark if isinstance(p, EstimatorParams) else None
    if benchmark is not None and benchmark not in symbols:
        symbols.append(benchmark)
    prices = ctx.price_provider().get_prices(symbols, p.start, end)
    currencies = frame_currencies(prices)
    target = require_single_currency([currencies[t] for t in tickers], target=p.base)
    notes: list[str] = []
    if any(c != target for c in currencies.values()):
        pairs = pairs_for(list(currencies.values()), target)
        fx = ctx.fx_provider()
        rates_frame = fx.get_rates([pair.code for pair in pairs], p.start, end)
        rates = FxRates(rates_frame, target, source=f"{fx.name} reference rates")
        prices = convert_frame(prices, target, rates=rates)
        ctx.log.info(
            "currency.converted", to=target, from_currencies=currencies, source=rates.source
        )
        carried = prices.attrs.get("carry_forward") or {}
        if carried:
            ctx.log.warning(
                "currency.carry_forward", columns={k: len(v) for k, v in carried.items()}
            )
        notes.append(
            f"converted to {target} from {', '.join(sorted(set(currencies.values())))} "
            f"using {rates.source}; the optimum is specific to this base"
        )
    frequency = infer_frequency(pd.DatetimeIndex(prices.index)) if len(prices) >= 3 else "daily"
    filled = apply_fill_policy(prices, p.fill)
    info = filled.attrs.get("filled", {})
    if p.fill == "drop":
        # Restore missing price dates so the next ratio cannot bridge several sessions.
        filled = filled.reindex(prices.index)
    raw_returns = pd.DataFrame(simple_returns(filled))
    removed = raw_returns.index[raw_returns.isna().any(axis=1)]
    returns = pd.DataFrame(apply_nan_policy(raw_returns, "drop"))
    if len(removed) or info.get("filled"):
        dates = [str(t.date()) for t in removed]
        ctx.log.warning(
            "gaps.handled", policy=p.fill, filled=info.get("filled", 0), dropped_dates=dates
        )
        notes.append(
            f"gaps: policy {p.fill}, filled {info.get('filled', 0)}, "
            f"dropped return dates {', '.join(dates) or 'none'}"
        )
    if len(returns) < 3:
        raise UsageError("fewer than three return observations", hint="widen --start/--end")
    rf, rf_source, dated_rates = resolve_risk_free(p.risk_free, p.start, end, target, ctx)
    period_rates = (
        pd.Series(rf, index=returns.index)
        if p.risk_free is not None
        else prior_rates(dated_rates, pd.DatetimeIndex(returns.index))
    )
    rf = float(p.risk_free) if p.risk_free is not None else float(period_rates.mean())
    provenance = Provenance.from_attrs(
        prices.attrs,
        start=str(returns.index.min().date()),
        end=str(returns.index.max().date()),
        notes=[f"risk-free rate {rf:.4%} ({rf_source})", *notes, SURVIVORSHIP_NOTE],
    )
    provenance.currency = target
    ctx.log.info(
        "optimization.loaded",
        rows=len(returns),
        assets=len(tickers),
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
    )
    return Universe(
        returns[tickers],
        filled[tickers],
        frequency,
        target,
        rf,
        rf_source,
        provenance,
        period_rates,
        None if benchmark is None else returns[benchmark],
    )


def resolve_risk_free(
    override: float | None, start: date, end: date, currency: str, ctx: Context
) -> tuple[float, str, pd.Series]:
    if override is not None:
        return float(override), "given annual simple proxy", pd.Series(dtype="float64")
    reason = "no FRED key configured"
    if currency != "USD":
        reason = f"no automatic {currency} risk-free proxy; supply --risk-free in {currency}"
    elif ctx.config.get(FRED_API_KEY.key):
        from sobres.data.fred_provider import get_risk_free_rate

        try:
            discount = get_risk_free_rate(ctx.macro_provider(), start, end, "3m").dropna()  # type: ignore[arg-type]
            if not discount.empty:
                rates = treasury_investment_yield(discount)
                source = (
                    "FRED DTB3: prior-date 91-day investment-yield approximation; "
                    "latest historical observations, not point-in-time vintages; "
                    "0.0 before first available quote"
                )
                return float(rates.mean()), source, rates
            reason = "FRED returned no usable risk-free observations"
        except Exception as exc:
            reason = f"FRED unavailable ({type(exc).__name__})"
    ctx.log.warning("risk_free.fallback", rate=0.0, reason=reason)
    return 0.0, f"0.0 fallback: {reason}", pd.Series(dtype="float64")


def estimate(u: Universe, p: EstimatorParams, ctx: Context) -> tuple[pd.Series, pd.DataFrame]:
    started = time.perf_counter()
    mu = moments.expected_returns(
        u.returns, u.frequency, p.returns_estimator, benchmark=u.benchmark, risk_free=u.risk_free
    )
    sigma = moments.covariance(u.returns, u.frequency, p.covariance)
    repair = sigma.attrs.get("psd_repair")
    if repair:
        ctx.log.warning("covariance.repaired", **repair)
    ctx.log.info(
        "optimization.estimated",
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
        returns_estimator=p.returns_estimator,
        covariance=p.covariance,
    )
    return mu, sigma


def constraints_for(p: EstimatorParams) -> opt.Constraints:
    return opt.Constraints(max_weight=p.max_weight, allow_short=p.allow_short)


# --------------------------------------------------------------------------- #
# Results
# --------------------------------------------------------------------------- #


class PortfolioResult(RecordsResult):
    report: ClassVar[bool] = True
    column_kinds: ClassVar[dict[str, str]] = {
        "ticker": "text",
        "weight": "weight",
        "risk_contribution": "weight",
    }
    expected_return: float
    volatility: float
    sharpe: float
    objective: str
    estimators: dict[str, Any]
    risk_free: float
    currency: str
    warnings: list[str] = Field(default_factory=list)

    def header_lines(self) -> list[str]:
        est = self.estimators
        shrink = f", shrinkage {est['shrinkage']:.3f}" if est.get("shrinkage") is not None else ""
        return [
            f"objective: {self.objective}",
            f"estimators: {est['expected_return']} expected returns, "
            f"{est['covariance']} covariance{shrink}",
            f"expected return {self.expected_return:.4%}, volatility {self.volatility:.4%}, "
            f"sharpe {self.sharpe:.2f} (risk-free {self.risk_free:.4%})",
            *[f"warning: {w}" for w in self.warnings],
            *super().header_lines(),
        ]


class FrontierResult(FrameResult):
    seed: int

    def header_lines(self) -> list[str]:
        return [f"estimators: {self.estimators}; seed: {self.seed}", *super().header_lines()]

    report: ClassVar[bool] = True
    index_label: ClassVar[str | None] = None
    column_kinds: ClassVar[dict[str, str]] = {"ret": "return", "vol": "return", "sharpe": "tstat"}
    default_kind: ClassVar[str] = "weight"
    estimators: dict[str, Any]
    n_points: int


class BacktestReport(RecordsResult):
    report: ClassVar[bool] = True
    column_kinds: ClassVar[dict[str, str]] = {
        "metric": "text",
        "strategy": "return",
        "benchmark": "return",
    }
    oos_start: str
    oos_end: str
    total_turnover: float
    total_cost: float
    total_cost_rate: float
    settings: dict[str, Any]
    decisions: list[dict[str, Any]]
    warnings: list[str]
    n_rebalances: int
    rebalance: str
    lookback: int
    cost_bps: float
    shifted_start: bool
    equity_curve: dict[str, float]
    benchmark_curve: dict[str, float]
    weights_history: dict[str, dict[str, float]]

    def header_lines(self) -> list[str]:
        shift = (
            " (shifted from the requested start to the first date with a full lookback)"
            if self.shifted_start
            else ""
        )
        return [
            f"out-of-sample window: {self.oos_start} → {self.oos_end}{shift}",
            f"rebalance {self.rebalance}, lookback {self.lookback} observations, "
            f"{self.n_rebalances} rebalances",
            f"transaction costs {self.cost_bps:g} bps: total turnover {self.total_turnover:.4f}, "
            f"total cost {self.total_cost:.4%} of initial capital",
            f"settings: {self.settings}",
            *[f"warning: {message}" for message in self.warnings],
            "benchmark: equal weight on the same schedule and costs",
            "interpretation: https://github.com/AI-Solutions-Lab-LLC/sobres/blob/claude/kind-sagan-4yakbc-0002-optimization/docs/why-your-backtest-looks-too-good.md",
            *super().header_lines(),
        ]

    def render_rich(self, console: Any) -> None:
        render_metric_table(console, self.rows, self.columns)


class RiskPanelResult(RecordsResult):
    report: ClassVar[bool] = True
    column_kinds: ClassVar[dict[str, str]] = {"metric": "text", "value": "return"}
    weights: dict[str, float]
    currency: str

    def render_rich(self, console: Any) -> None:
        render_metric_table(console, self.rows, self.columns)

    def header_lines(self) -> list[str]:
        weights = ", ".join(f"{k} {v:.4f}" for k, v in self.weights.items())
        return [f"weights: {weights}", *super().header_lines()]


def _panel_rows(panels: dict[str, RiskPanel]) -> list[dict[str, Any]]:
    keys = [
        "annualized_return",
        "arithmetic_return",
        "volatility",
        "sharpe",
        "sortino",
        "calmar",
        "max_drawdown",
        "drawdown_peak",
        "drawdown_trough",
        "drawdown_recovery",
        "var_95",
        "cvar_95",
        "skew",
        "kurtosis",
        "n_obs",
    ]
    rows = []
    for key in keys:
        row: dict[str, Any] = {"metric": key}
        for name, panel in panels.items():
            value = panel.as_dict()[key]
            row[name] = value
        rows.append(row)
    return rows


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def validate_target(objective: str, target: float | None) -> None:
    if objective in ("target_return", "target_risk") and target is None:
        raise ValueError(f"{objective} needs --target, e.g. --target 0.10 (annual decimal)")
    if objective not in ("target_return", "target_risk") and target is not None:
        raise ValueError("--target requires --objective target_return or target_risk")
    if objective == "target_risk" and target is not None and target <= 0:
        raise ValueError("target risk must be positive, e.g. --target 0.15")


def report_progress(ctx: Context, operation: str, done: int, total: int) -> None:
    ctx.log.info(f"{operation}.progress", done=done, total=total)
    if getattr(ctx, "interactive", False) and (
        done == 1 or done == total or done % max(1, total // 10) == 0
    ):
        ctx.note(f"{operation}: {done}/{total}")


class MarkowitzParams(EstimatorParams):
    objective: opt.Objective = Field(default="max_sharpe", description="Optimization objective.")
    target: FiniteFloat | None = Field(
        default=None, description="Target return or risk for target_* objectives."
    )
    seed: int = Field(
        default=0,
        ge=0,
        description="Seed for the max-Sharpe random restarts (printed for reproducibility).",
    )

    @model_validator(mode="after")
    def _target(self) -> MarkowitzParams:
        validate_target(self.objective, self.target)
        return self


@register(
    "optimize.markowitz",
    "Optimal weights for one objective, with the risk/return profile that produced them.",
    result=PortfolioResult,
    uses_providers=True,
)
def markowitz(p: MarkowitzParams, ctx: Context) -> PortfolioResult:
    u = load_universe(p, ctx)
    mu, sigma = estimate(u, p, ctx)
    started = time.perf_counter()
    portfolio = opt.optimize(
        mu,
        sigma,
        p.objective,
        constraints_for(p),
        risk_free=u.risk_free,
        target=p.target,
        seed=p.seed,
        explicit_max_weight=p.max_weight is not None,
    )
    ctx.log.info(
        "optimization.solved",
        objective=p.objective,
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
    )
    for warning in portfolio.warnings:
        ctx.log.warning("optimize.concentration", message=warning)
    u.provenance.notes.append(IN_SAMPLE_NOTE)
    u.provenance.notes.append(f"seed: {p.seed}")
    rows = [
        {"ticker": t, "weight": w, "risk_contribution": portfolio.risk_contributions.get(t, 0.0)}
        for t, w in portfolio.weights.items()
    ]
    return PortfolioResult(
        rows=rows,
        columns=["ticker", "weight", "risk_contribution"],
        expected_return=portfolio.expected_return,
        volatility=portfolio.volatility,
        sharpe=portfolio.sharpe,
        objective=portfolio.objective,
        estimators=portfolio.estimators.__dict__,
        risk_free=portfolio.risk_free,
        currency=u.currency,
        warnings=list(portfolio.warnings),
        provenance=u.provenance,
    )


class FrontierParams(EstimatorParams):
    points: int = Field(default=50, ge=2, le=500, description="Number of frontier points.")
    seed: int = Field(default=0, ge=0, description="Seed for the max-Sharpe random restarts.")


@register(
    "optimize.frontier",
    "The efficient frontier: one row per portfolio from min variance to max return.",
    result=FrontierResult,
    uses_providers=True,
)
def frontier(p: FrontierParams, ctx: Context) -> FrontierResult:
    u = load_universe(p, ctx)
    mu, sigma = estimate(u, p, ctx)
    started = time.perf_counter()
    result = opt.efficient_frontier(
        mu,
        sigma,
        p.points,
        constraints_for(p),
        risk_free=u.risk_free,
        seed=p.seed,
        progress=lambda done, total: report_progress(ctx, "frontier", done, total),
    )
    ctx.log.info(
        "frontier.solved",
        points=p.points,
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
    )
    rows = []
    for point in result.points:
        row: dict[str, Any] = {
            "ret": point.expected_return,
            "vol": point.volatility,
            "sharpe": point.sharpe,
        }
        row.update(point.weights)
        row["min_variance"] = point.is_min_variance
        row["max_sharpe"] = point.is_max_sharpe
        rows.append(row)
    tickers, _ = resolve_symbols(p, ctx)
    frame = pd.DataFrame(
        rows, columns=["ret", "vol", "sharpe", *tickers, "min_variance", "max_sharpe"]
    )
    u.provenance.notes.append(IN_SAMPLE_NOTE)
    return FrontierResult(
        frame=frame,
        estimators=result.estimators.__dict__,
        n_points=len(result.points),
        seed=p.seed,
        provenance=u.provenance,
    )


class BacktestParams(EstimatorParams):
    target: FiniteFloat | None = Field(
        default=None, description="Annual decimal target for target_return or target_risk."
    )
    objective: opt.Objective = Field(
        default="max_sharpe", description="Objective re-solved at each rebalance."
    )
    rebalance: bt.Rebalance = Field(default="quarterly", description="Rebalance schedule.")
    lookback: str = Field(
        default="36m", description="Estimation window: Nm months, Ny years or N observations."
    )
    cost_bps: FiniteFloat = Field(
        default=bt.DEFAULT_COST_BPS,
        ge=0,
        le=10000,
        description="Fee bps per unit of one-way turnover, including initial cash.",
    )
    seed: int = Field(default=0, ge=0, description="Seed for the max-Sharpe random restarts.")

    @model_validator(mode="after")
    def _backtest_inputs(self) -> BacktestParams:
        validate_target(self.objective, self.target)
        days = lookback_calendar_days(self.lookback)
        if self.start - timedelta(days=days) < date(1800, 1, 1):
            raise ValueError("lookback reaches before supported history")
        if self.tickers and parse_lookback(self.lookback, "daily") <= len(self.tickers):
            raise ValueError("lookback must have more observations than assets")
        return self


def _curve(series: pd.Series) -> dict[str, float]:
    index = pd.DatetimeIndex(series.index)
    return {str(k.date()): float(v) for k, v in zip(index, series.to_numpy(), strict=True)}


def lookback_calendar_days(text: str) -> int:
    """Calendar days to fetch ahead of --start for a lookback of ``text`` (with slack)."""
    value = text.strip().lower()
    if not re.fullmatch(r"[1-9][0-9]{0,4}[my]?", value):
        raise ValueError("lookback must be positive, e.g. 36m, 3y or 500")
    count = int(value.rstrip("my"))
    if (
        (value.endswith("y") and count > 100)
        or (value.endswith("m") and count > 1200)
        or (value[-1].isdigit() and not 2 <= count <= 25000)
    ):
        raise ValueError("lookback supports 2-25000 observations or at most 100 years")
    try:
        if value.endswith("m"):
            months = int(value[:-1])
            return int(months * 31) + 14
        if value.endswith("y"):
            return int(value[:-1]) * 366 + 14
        observations = int(value)
    except ValueError:
        raise UsageError(f"lookback {text!r} must look like 36m, 3y or 500") from None
    return int(observations * 7 / 5 * 1.1) + 14  # daily bars: ~5 per calendar week


def parse_lookback(text: str, frequency: str) -> int:
    """``36m`` / ``3y`` in periods of ``frequency``, or a bare observation count."""
    from sobres.core.conventions import periods_per_year

    value = text.strip().lower()
    per_year = periods_per_year(frequency)
    try:
        if value.endswith("m"):
            return max(2, round(int(value[:-1]) * per_year / 12))
        if value.endswith("y"):
            return max(2, int(value[:-1]) * per_year)
        return int(value)
    except ValueError:
        raise UsageError(f"lookback {text!r} must look like 36m, 3y or 500") from None


@register(
    "optimize.backtest",
    "Walk-forward test: re-solve at each rebalance on prior data only, versus equal weight.",
    result=BacktestReport,
    uses_providers=True,
)
def backtest(p: BacktestParams, ctx: Context) -> BacktestReport:
    # Fetch enough history before --start for the first rebalance to have a full
    # lookback, so the out-of-sample window begins where the user asked.
    lookback_days = lookback_calendar_days(p.lookback)
    data_params = p.model_copy(update={"start": p.start - timedelta(days=lookback_days)})
    u = load_universe(data_params, ctx)
    lookback = parse_lookback(p.lookback, u.frequency)
    cons = constraints_for(p)
    decisions: list[dict[str, Any]] = []
    warning_messages: set[str] = set()
    started = time.perf_counter()

    def strategy(window: pd.DataFrame) -> pd.Series:
        # Rates attached to a return date are already lagged strictly before that date.
        position = int(u.returns.index.searchsorted(window.index[-1], side="right"))
        trade_date = pd.Timestamp(u.returns.index[position])
        rate = float(u.risk_free_rates.iloc[position])
        benchmark = None if u.benchmark is None else u.benchmark.reindex(window.index)
        mu = moments.expected_returns(
            window, u.frequency, p.returns_estimator, benchmark=benchmark, risk_free=rate
        )
        sigma = moments.covariance(window, u.frequency, p.covariance)
        portfolio = opt.optimize(
            mu,
            sigma,
            p.objective,
            cons,
            risk_free=rate,
            target=p.target,
            seed=p.seed,
            explicit_max_weight=p.max_weight is not None,
        )
        warning_messages.update(portfolio.warnings)
        repair = portfolio.estimators.psd_repair
        if repair:
            warning_messages.add(f"covariance repaired: {repair}")
        decisions.append(
            {
                "trade_date": str(trade_date.date()),
                "training_start": str(window.index[0].date()),
                "training_end": str(window.index[-1].date()),
                "risk_free": rate,
                "estimators": portfolio.estimators.__dict__,
            }
        )
        return pd.Series(portfolio.weights)

    def progress(done: int, total: int) -> None:
        report_progress(ctx, "backtest", done, total)

    result = bt.walk_forward(
        u.returns,
        strategy,
        frequency=u.frequency,
        rebalance=p.rebalance,
        lookback=lookback,
        cost_bps=p.cost_bps,
        start=p.start,
        risk_free=u.risk_free_rates,
        progress=progress,
    )
    ctx.log.info(
        "backtest.solved",
        rebalances=result.n_rebalances,
        elapsed_ms=round((time.perf_counter() - started) * 1000, 3),
    )
    for message in sorted(warning_messages):
        ctx.log.warning("backtest.assumption", message=message)
    if result.shifted_start:
        ctx.log.warning(
            "backtest.start_shifted", requested=str(p.start), actual=str(result.oos_start)
        )
        ctx.note(
            f"note: backtest starts {result.oos_start}, the first date with a full "
            f"{lookback}-observation lookback"
        )
    return BacktestReport(
        rows=_panel_rows({"strategy": result.strategy, "benchmark": result.benchmark}),
        columns=["metric", "strategy", "benchmark"],
        oos_start=result.oos_start.isoformat(),
        oos_end=result.oos_end.isoformat(),
        total_turnover=result.total_turnover,
        total_cost=result.total_cost,
        total_cost_rate=result.total_cost_rate,
        settings=p.model_dump(mode="json"),
        decisions=decisions,
        warnings=sorted(warning_messages),
        n_rebalances=result.n_rebalances,
        rebalance=result.rebalance,
        lookback=result.lookback,
        cost_bps=result.cost_bps,
        shifted_start=result.shifted_start,
        equity_curve=_curve(result.equity_curve),
        benchmark_curve=_curve(result.benchmark_curve),
        weights_history={
            str(k.date()): {str(c): float(v) for c, v in row.items()}
            for k, (_, row) in zip(
                pd.DatetimeIndex(result.weights_history.index),
                result.weights_history.iterrows(),
                strict=True,
            )
        },
        provenance=u.provenance,
    )


class RiskParams(UniverseParams):
    weights: Weights = Field(
        default_factory=list,
        description="Portfolio weights, one per ticker, summing to 1 (from --portfolio if saved).",
    )

    @model_validator(mode="after")
    def _weights_match(self) -> RiskParams:
        if self.tickers and not self.weights:
            raise ValueError("--weights is required with --tickers")
        if self.weights and self.tickers and len(self.weights) != len(self.tickers):
            raise ValueError(f"{len(self.weights)} weights for {len(self.tickers)} tickers")
        if not all(math.isfinite(w) for w in self.weights):
            raise ValueError("weights must be finite, e.g. --weights 0.6 0.4")
        if self.weights:
            total = sum(self.weights)
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"weights sum to {total:.6f}, not 1.0")
        return self


@register(
    "optimize.risk",
    "The full risk panel for a fixed-weight portfolio.",
    result=RiskPanelResult,
    uses_providers=True,
)
def risk(p: RiskParams, ctx: Context) -> RiskPanelResult:
    tickers, saved_weights = resolve_symbols(p, ctx)
    weight_values = list(p.weights) if p.weights else saved_weights
    if weight_values is None:
        raise UsageError(
            f"portfolio {p.portfolio!r} has no weights",
            hint="pass --weights or save it with weights",
        )
    if len(weight_values) != len(tickers):
        raise UsageError(f"{len(weight_values)} weights for {len(tickers)} tickers")
    u = load_universe(p, ctx)
    weights = dict(zip(tickers, weight_values, strict=True))
    series = portfolio_returns(u.returns, weights)
    panel = risk_metrics(series, u.risk_free_rates, u.frequency)
    rows = [
        {"metric": k, "value": v} for k, v in panel.as_dict().items() if k not in ("frequency",)
    ]
    return RiskPanelResult(
        rows=rows,
        columns=["metric", "value"],
        weights=weights,
        currency=u.currency,
        provenance=u.provenance,
    )
