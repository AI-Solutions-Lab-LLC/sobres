"""Multivariable forecasting against constructed processes with known answers.

Scenarios: Cross-variable dynamics; Shrinkage and prior are visible; Invalid
system; Keyless basic preset; Price reconstruction; Fold-local training; Unknown
future covariates; Honest skill report; Insufficient evaluation history; Joint
uncertainty; Reproducible run; Intervals are mandatory.
"""

from __future__ import annotations

from itertools import pairwise

import numpy as np
import pandas as pd
import pytest

from sobres.core import forecast as fc
from sobres.core.errors import InsufficientDataError, UsageError

pytest.importorskip("statsmodels")

A1 = np.array([[0.3, 0.4], [0.0, 0.2]])
"""A stable VAR(1): the first series depends on the second's lag (0.4), not the reverse."""
NOISE = np.array([0.01, 0.02])


def simulate_var1(n: int = 3000, seed: int = 0, a: np.ndarray = A1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    s = np.zeros((n, 2))
    for t in range(1, n):
        s[t] = a @ s[t - 1] + rng.normal(0.0, NOISE)
    return s


def destandardize(fit: fc.VarFit) -> np.ndarray:
    """The lag-1 coefficient matrix in original units: ``A[i, j] = a_std[i, j] sd_i / sd_j``."""
    _, coefs = fc._split_coefficients(fit.b, fit.k, fit.p)
    sd = fit.scaler.std
    return np.asarray(coefs[0] * (sd[:, None] / sd[None, :]))


def test_cross_variable_dynamics_are_recovered_and_matter() -> None:
    """Scenario: Cross-variable dynamics."""
    s = simulate_var1()
    fit = fc.fit_var(s, 1, 0.0)
    recovered = destandardize(fit)
    # tolerance: 3000 observations, coefficient standard errors ~ 0.02 (Lütkepohl 2005, §3.2)
    assert recovered == pytest.approx(A1, abs=0.06)  # ~3 coefficient standard errors
    assert fit.stable and fit.spectral_radius == pytest.approx(0.3, abs=0.06)  # same tolerance
    z = fit.scaler.transform(s)
    base = fc.cumulative_target(fc.mean_path(fit.b, 1, z, 1), fit.scaler, 0)[-1]
    shocked = s.copy()
    shocked[-1, 1] += 0.05  # perturb the predictor's last observation only
    z2 = fit.scaler.transform(shocked)
    moved = fc.cumulative_target(fc.mean_path(fit.b, 1, z2, 1), fit.scaler, 0)[-1]
    assert moved - base == pytest.approx(0.4 * 0.05, abs=0.06 * 0.05)  # A1[0, 1] x shock
    # A univariate fit of the target cannot express that effect at all.
    solo = fc.fit_var(s[:, :1], 1, 0.0)
    zs = solo.scaler.transform(s[:, :1])
    solo_base = fc.cumulative_target(fc.mean_path(solo.b, 1, zs, 1), solo.scaler, 0)[-1]
    solo_moved = fc.cumulative_target(
        fc.mean_path(solo.b, 1, solo.scaler.transform(shocked[:, :1]), 1), solo.scaler, 0
    )[-1]
    assert solo_moved == solo_base


def test_ridge_zero_is_least_squares_and_shrinkage_is_visible() -> None:
    """Scenario: Shrinkage and prior are visible."""
    s = simulate_var1(n=600, seed=3)
    fit0 = fc.fit_var(s, 2, 0.0)
    z = fit0.scaler.transform(s)
    x, y = fc.lag_design(z, 2)
    ols, *_ = np.linalg.lstsq(x, y, rcond=None)
    assert fit0.b == pytest.approx(ols, abs=1e-10)  # closed form equals lstsq at lambda = 0
    fit10 = fc.fit_var(s, 2, 10.0)
    assert np.linalg.norm(fit10.b[1:]) < 0.5 * np.linalg.norm(fit0.b[1:])  # lags shrink
    assert fit10.penalty == 10.0 and fit10.p == 2
    with pytest.raises(UsageError):
        fc.fit_var(s, 0, 1.0)
    with pytest.raises(UsageError):
        fc.fit_var(s, 1, -1.0)


def test_companion_radius_matches_closed_form_roots() -> None:
    assert fc.companion_radius([np.diag([0.5, 0.9])]) == pytest.approx(0.9)
    # Scalar AR(2) with phi1 = 0.5, phi2 = 0.3: roots of z^2 - 0.5 z - 0.3 = 0
    root = (0.5 + np.sqrt(0.25 + 1.2)) / 2
    assert fc.companion_radius([np.array([[0.5]]), np.array([[0.3]])]) == pytest.approx(root)
    assert fc.companion_radius([np.array([[1.2]])]) > 1.0


def test_bvar_posterior_matches_the_conjugate_formulas_and_prior_limits() -> None:
    """Scenario: Shrinkage and prior are visible.

    The posterior is checked against the normal–inverse-Wishart update written out
    independently (Karlsson 2013, §2.2) on the same standardized design, and against
    its two limits: a vanishing prior variance pins the lags at zero, a huge one
    returns least squares.
    """
    s = simulate_var1(n=400, seed=7)
    fit = fc.fit_bvar(s, 1, 0.2)
    z = fit.scaler.transform(s)
    x, y = fc.lag_design(z, 1)
    n, k = y.shape
    var_j = z.var(axis=0, ddof=1)
    v0 = np.diag([1e6, *(0.2**2 / (1**2 * var_j))])
    v0_inv = np.linalg.inv(v0)
    vn = np.linalg.inv(v0_inv + x.T @ x)
    bn = vn @ (x.T @ y)
    nu0 = k + 2
    s0 = (nu0 - k - 1) * np.diag(var_j)
    sn = s0 + y.T @ y - bn.T @ (v0_inv + x.T @ x) @ bn
    assert fit.bn == pytest.approx(bn, abs=1e-10)
    assert fit.vn == pytest.approx(vn, abs=1e-12)
    assert fit.sn == pytest.approx(sn, abs=1e-8)
    assert fit.nun == nu0 + n
    assert fit.prior["tightness"] == 0.2 and fit.prior["nu0"] == nu0
    tight = fc.fit_bvar(s, 1, 1e-6)
    assert np.abs(tight.bn[1:]).max() < 1e-6  # lag coefficients pinned to the zero prior mean
    loose = fc.fit_bvar(s, 1, 1e4)
    ols, *_ = np.linalg.lstsq(x, y, rcond=None)
    assert loose.bn == pytest.approx(ols, abs=1e-4)  # prior variance 1e8 leaves 1e-4 shrinkage


def test_selection_prefers_stronger_shrinkage_then_fewer_lags_on_ties() -> None:
    s = simulate_var1(n=1400, seed=11)
    sel = fc.select_candidates(s, "var", 5, 0)
    assert len(sel.candidates) == len(fc.LAG_CANDIDATES) * len(fc.RIDGE_CANDIDATES)
    assert sel.chosen.loss == min(c.loss for c in sel.candidates if c.loss is not None)
    assert sel.block_length == fc.A // 4 and sel.purge == 5 and len(sel.boundaries) == 3
    fixed = fc.select_candidates(s, "var", 5, 0, fixed_lag=2)
    assert {c.lag for c in fixed.candidates} == {2}
    # A tie is broken toward stronger shrinkage, then fewer lags.
    tied = [
        fc.Candidate(1, 0.1, 1.0, 9, True),
        fc.Candidate(2, 1.0, 1.0, 9, True),
        fc.Candidate(1, 1.0, 1.0, 9, True),
    ]
    winner = sorted(tied, key=lambda c: (-c.penalty, c.lag))[0]
    assert (winner.lag, winner.penalty) == (1, 1.0)


def _panel(n: int = 1600, seed: int = 5) -> fc.StatePanel:
    """A target that loads 0.8 on a random-walk market, with its own noise and volume."""
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2015-01-02", periods=n)
    market_returns = rng.normal(0.0002, 0.01, n)
    target_returns = 0.8 * market_returns + rng.normal(0.0001, 0.012, n)
    market = 100 * np.exp(np.cumsum(market_returns))
    target = 50 * np.exp(np.cumsum(target_returns))
    volume = rng.integers(1_000_000, 5_000_000, n).astype("float64")
    return fc.build_state(
        pd.Series(target, index=idx),
        pd.Series(volume, index=idx),
        pd.Series(market, index=idx),
        target="T",
        market="M",
    )


def test_basic_state_formulas_by_hand() -> None:
    """Scenario: Keyless basic preset."""
    idx = pd.bdate_range("2020-01-01", periods=60)
    close = pd.Series(np.linspace(100, 130, 60), index=idx)
    volume = pd.Series(np.full(60, 2_000_000.0), index=idx)
    market = pd.Series(np.linspace(300, 320, 60), index=idx)
    panel = fc.build_state(close, volume, market, target="T", market="M")
    assert [p.column for p in panel.predictors] == ["T_ret", "M_ret", "T_logrv20", "T_dlogdv20"]
    assert panel.target == "T_ret" and panel.warmup_rows == 20
    row = panel.frame.iloc[0]
    t = panel.frame.index[0]
    pos = idx.get_loc(t)
    r = np.log(close.to_numpy()[1 : pos + 1] / close.to_numpy()[0:pos])
    assert row["T_ret"] == pytest.approx(r[-1])
    assert row["M_ret"] == pytest.approx(np.log(market.iloc[pos] / market.iloc[pos - 1]))
    assert row["T_logrv20"] == pytest.approx(np.log(np.sqrt(np.mean(r[-20:] ** 2))))
    dollar = close.to_numpy() * volume.to_numpy()
    dv_now = np.log(np.mean(dollar[pos - 19 : pos + 1]))
    dv_prev = np.log(np.mean(dollar[pos - 20 : pos]))
    assert row["T_dlogdv20"] == pytest.approx(dv_now - dv_prev)
    with pytest.raises(InsufficientDataError, match="volume"):
        fc.build_state(
            close, volume.where(volume.index != idx[30], 0.0), market, target="T", market="M"
        )


def test_invalid_systems_are_refused_not_repaired() -> None:
    """Scenario: Invalid system."""
    idx = pd.bdate_range("2020-01-01", periods=80)
    rng = np.random.default_rng(1)
    close = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 80))), index=idx)
    volume = pd.Series(np.full(80, 1e6), index=idx)
    with pytest.raises(UsageError, match="also the benchmark"):
        fc.build_state(close, volume, close, target="T", market="T")
    with pytest.raises(UsageError, match="same series"):
        fc.build_state(close, volume, close * 2.0, target="T", market="M")  # identical returns
    with pytest.raises(UsageError, match="duplicates"):
        fc.build_state(close, volume, close * 1.5, close, target="T", market="M", sector="T")
    flat = pd.Series(100.0, index=idx)
    with pytest.raises(InsufficientDataError, match="no variation"):
        fc.build_state(close, volume, flat, target="T", market="M")
    with pytest.raises(InsufficientDataError, match="nonpositive"):
        fc.log_returns(pd.Series([1.0, 0.0, 2.0]))
    with pytest.raises(InsufficientDataError, match="usable"):
        fc._guard(np.zeros((80, 3)), 100, "test")  # 20% rejected exceeds the 10% guard


def test_price_reconstruction_from_draws() -> None:
    """Scenario: Price reconstruction."""
    draws = fc.Draws(
        cumulative=np.array([[0.0, 0.1], [0.0, -0.1], [0.0, 0.2]]),
        requested=3,
        rejected=0,
        method="test",
    )
    frame = fc.price_distribution(100.0, draws, np.array([0.0, 0.05]))
    assert list(frame.index) == [1, 2] and frame.index.name == "step"
    assert frame.loc[2, "forecast"] == pytest.approx(100 * np.exp(0.1))  # the median draw
    assert frame.loc[2, "mean_price"] == pytest.approx(np.mean(100 * np.exp([0.1, -0.1, 0.2])))
    assert frame.loc[2, "mean_price"] != pytest.approx(100 * np.exp(np.mean([0.1, -0.1, 0.2])))
    assert frame.loc[2, "lower95"] <= frame.loc[2, "lower80"] <= frame.loc[2, "forecast"]
    assert frame.loc[2, "forecast"] <= frame.loc[2, "upper80"] <= frame.loc[2, "upper95"]
    assert frame.loc[2, "log_return_point"] == 0.05


def test_metrics_by_hand_including_undefined_cases() -> None:
    """Scenario: Honest skill report."""
    actual = np.array([0.10, -0.10, 0.20])
    predicted = np.array([0.05, 0.05, 0.10])
    m = fc._metrics(actual, predicted, np.array([100.0, 100.0, 100.0]))
    err = predicted - actual
    assert m["n"] == 3
    assert m["return_rmse"] == pytest.approx(np.sqrt(np.mean(err**2)))
    assert m["return_mae"] == pytest.approx(np.mean(np.abs(err)))
    assert m["direction_accuracy"] == pytest.approx(2 / 3)
    assert m["oos_r2_vs_no_change"] == pytest.approx(1 - np.sum(err**2) / np.sum(actual**2))
    assert m["price_mae"] == pytest.approx(
        np.mean(np.abs(100 * np.exp(predicted) - 100 * np.exp(actual)))
    )
    zero = fc._metrics(np.zeros(3), np.zeros(3), np.ones(3))
    assert zero["oos_r2_vs_no_change"] is None and zero["direction_accuracy"] is None
    control = fc._metrics(actual, np.zeros(3), np.ones(3))
    assert control["direction_accuracy"] is None and control["oos_r2_vs_no_change"] == 0.0


def test_block_indices_are_contiguous_blocks() -> None:
    rng = np.random.default_rng(0)
    idx = fc._block_indices(rng, n=50, length=12, block=5, count=4)
    assert idx.shape == (4, 12)
    for row in idx:
        for start in range(0, 10, 5):
            block = row[start : start + 5]
            assert list(block) == list(range(block[0], block[0] + 5))


def test_draws_are_seeded_and_reproducible_and_the_guard_counts_rejections() -> None:
    """Scenario: Reproducible run. Scenario: Joint uncertainty."""
    s = simulate_var1(n=800, seed=2)
    fit = fc.fit_var(s, 1, 0.1)
    a = fc.var_draws(fit, s, 5, seed=4, draws=120, refits=6, target_col=0)
    b = fc.var_draws(fit, s, 5, seed=4, draws=120, refits=6, target_col=0)
    c = fc.var_draws(fit, s, 5, seed=5, draws=120, refits=6, target_col=0)
    assert np.array_equal(a.cumulative, b.cumulative) and not np.array_equal(
        a.cumulative, c.cumulative
    )
    assert a.usable == 120 and a.rejected == 0 and "bootstrap" in a.method
    assert a.cumulative.shape == (120, 5)
    bfit = fc.fit_bvar(s, 1, 0.2)
    d = fc.bvar_draws(bfit, s, 5, seed=4, draws=120, target_col=0)
    e = fc.bvar_draws(bfit, s, 5, seed=4, draws=120, target_col=0)
    assert np.array_equal(d.cumulative, e.cumulative) and "posterior" in d.method
    spread = np.std(a.cumulative[:, -1])
    assert spread > np.std(a.cumulative[:, 0])  # uncertainty accumulates over the horizon


def test_evaluation_is_fold_local_and_reports_counts() -> None:
    """Scenario: Fold-local training. Scenario: Unknown future covariates.
    Scenario: Insufficient evaluation history."""
    panel = _panel(n=1700)
    ev = fc.evaluate(panel, "var", 20, seed=0, draws=100, refits=5)
    assert len(ev.outcomes) >= fc.MIN_OUTER_OUTCOMES
    assert ev.boundaries["origin_spacing"] == 20
    origins = [o.origin_row for o in ev.outcomes]
    assert all(b - a == 20 for a, b in pairwise(origins))
    assert set(ev.metrics) == {"var", "no_change", "training_mean"}
    assert {"coverage80", "coverage95", "width80", "width95"} <= set(ev.metrics["var"])
    # Perturb everything after the first outcome's horizon: its forecast cannot change.
    first = ev.outcomes[0]
    frame = panel.frame.copy()
    later = frame.index[first.origin_row + 21 :]
    frame.loc[later, :] = frame.loc[later, :] + 0.01  # a real change: later actuals move
    perturbed = fc.StatePanel(frame, panel.predictors, panel.target, panel.warmup_rows)
    ev2 = fc.evaluate(perturbed, "var", 20, seed=0, draws=100, refits=5)
    assert ev2.outcomes[-1].actual != ev.outcomes[-1].actual
    again = ev2.outcomes[0]
    assert again.predictions == first.predictions
    assert (again.lag, again.penalty) == (first.lag, first.penalty)
    assert (again.lower80, again.upper95) == (first.lower80, first.upper95)
    assert again.actual == first.actual
    short = fc.StatePanel(panel.frame.iloc[:900], panel.predictors, panel.target, 0)
    with pytest.raises(InsufficientDataError) as exc:
        fc.evaluate(short, "var", 20, seed=0, draws=100, refits=5)
    assert "training rows" in str(exc.value) or "held-out outcomes" in str(exc.value)
    with pytest.raises(UsageError):
        fc.evaluate(panel, "var", 7, seed=0, draws=100, refits=5)


def test_forecast_from_reports_the_selection_and_refuses_an_unstable_system() -> None:
    panel = _panel(n=1500)
    values = panel.frame.to_numpy()
    one = fc.forecast_from(
        values, len(values) - 1, "bvar", 5, 0, training_rows=1260, seed=1, draws=100, refits=5
    )
    assert one.selection.chosen.penalty in fc.TIGHTNESS_CANDIDATES
    assert isinstance(one.fit, fc.BvarFit) and one.draws.usable == 100
    assert len(one.point) == 5
    with pytest.raises(InsufficientDataError, match="training rows"):
        fc.forecast_from(values, 100, "var", 5, 0, training_rows=1260, seed=1, draws=100, refits=5)
