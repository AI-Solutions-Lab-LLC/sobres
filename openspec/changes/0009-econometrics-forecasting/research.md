# Research basis and predictor decisions

Checked 2026-09-13. This is a focused primary-source review, not an exhaustive
ranking or a replication. Recent preprints below are distinguished from established
journal results. No Sobres forecasting experiment was run for this planning change.
The numerical defaults in design.md are proposed engineering settings, not values
claimed to be optimal by the cited authors.

## Influential evidence

| Source | Finding and applicability | Sobres decision |
|---|---|---|
| Campbell & Shiller, *Stock Prices, Earnings and Expected Dividends* (1988), [NBER paper](https://www.nber.org/papers/w2511) | A classic stock-market application of VAR with valuation, earnings and dividend information; aggregate historical present-value analysis, not a daily single-stock trading guarantee. | Include dated valuation/earnings/dividend candidates in the extended catalog; require publication history and test horizon transfer. |
| Bańbura, Giannone & Reichlin, *Large Bayesian VARs*, ECB WP 966 (2008), published in JAE (2010), [author-institution paper](https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp966.pdf) | Shrinkage makes larger joint systems tractable and useful in their macroeconomic forecasting experiments. It is not evidence of guaranteed stock-price skill. | Include a small regularized VAR and optional BVAR; tune shrinkage chronologically, report dimension and stability. |
| Gu, Kelly & Xiu, *Empirical Asset Pricing via Machine Learning*, RFS (2020), [paper](https://doi.org/10.1093/rfs/hhaa009) | Their broad stock panel identifies price trends, liquidity and volatility as important predictor families. Nonlinear interactions and regularization matter. The study forecasts risk premiums across stocks, not a daily quoted price for one stock. | Use those families as candidates, include elastic-net/boosted trees, and test their transfer to the actual Sobres target. Do not copy reported Sharpe ratios into product claims. |
| Goyal, Welch & Zafirov, *A Comprehensive 2022 Look at the Empirical Performance of Equity Premium Prediction*, RFS (2024), [paper](https://doi.org/10.1093/rfs/hhae044) | Reexamining old and newer predictors through 2021 weakens many published results, including out-of-sample performance. Aggregate equity-premium evidence is not a single-stock causal variable list. | Treat macro/valuation features as optional hypotheses; require historical-mean and no-change benchmarks and report negative skill honestly. |
| Stock & Watson, *Forecasting Using Principal Components from a Large Number of Predictors*, JASA (2002), [author paper](https://www.princeton.edu/~mwatson/papers/Stock_Watson_JASA_2002.pdf) | Low-dimensional factors can summarize a large predictor panel under an approximate factor structure. | PCR/FAVAR is a bounded future extension for genuinely broad panels; fit PCA inside each training fold. Do not pad the first VAR with hundreds of series. |
| Kelly & Xiu, *Financial Machine Learning* (2023), [NBER survey](https://www.nber.org/papers/w31502) | Surveys financial applications and methodological opportunities; not a benchmark crowning one model. | Keep a shared evaluation protocol and a model port so useful later methods can compete without changing data/validation semantics. |

## Recent frontier, with limited claims

- **Chronos-2** (Ansari et al., October 2025), [primary report](https://arxiv.org/abs/2510.15821): multivariate and covariate-informed pretrained forecasting with strong general benchmark results. Its cited energy/retail results do not establish stock-return profitability. Consider an optional adapter only after model-weight licensing, training-data cutoff/contamination, compute and finance-specific evaluation are documented.
- **Kronos** (Shi et al., August 2025), [primary report](https://arxiv.org/abs/2508.02739): pretrained financial OHLCV modeling with authors' reported forecasting/volatility results. It uses an autoregressive pretraining objective. It is not a default in this amendment; owner scope and independent held-out evidence would be needed before inclusion.
- **Benchmarking Deep Time Series Models for Equity Portfolios** (Zhang, Cheng & Leung, June 2026), [preprint v1](https://arxiv.org/abs/2606.09420v1): rankings depend on market state, constraints and costs; no architecture dominates its raw comparison. This is recent evidence for evaluating the intended decision, not a proof that a named architecture generalizes to Sobres.
- **FinVerse** (Lee et al., August 2026), [preprint v2](https://arxiv.org/abs/2608.03259v2): finance-specific evaluation finds that generic forecast accuracy need not translate into useful financial predictions. Its recent benchmark motivates directional and decision-relevant evaluation alongside error/calibration; results are not replicated here.

These are relevant recent examples, not a claim of exhaustive coverage through
September 2026 or universal state of the art. Older influential statistical models
remain serious comparators. A foundation model is not promoted solely for recency.

## Predictor catalog v1

All features use information available by the forecast origin. `r_t` is the
one-session log change of split-only price in the target's quote currency.
Windows below count complete target-market sessions, not calendar days. Market
returns use the same price convention; these are return predictors, not a
Fama–French attribution regression. Design.md specifies the exact model inputs.

| Feature / role | Proposed definition | Source and availability | Evidence and default decision |
|---|---|---|---|
| Target return, joint endogenous variable | `log(P_t/P_(t-1))` | `ticker:<target>` close + split actions, known by origin | Required target dynamics in VAR; no standalone AR model. |
| Market return, joint endogenous variable | Same log change for `ticker:SPY` | Keyless price provider, completed US session | Required in `equity-basic` for USD US equities. A transparent broad-market proxy, not a universal benchmark or a paper's uniquely optimal choice. |
| Realized volatility, joint endogenous variable | `log(sqrt(mean(r^2 over 20 sessions)))`, unannualized | Derived from target returns available at origin | Basic preset; volatility is research-motivated, this exact transform/window is a Sobres choice. Zero variance is invalid, not fixed with an undocumented epsilon. |
| Trading activity, joint endogenous variable | First difference of `log(mean(raw_close * raw_volume over 20 sessions))` | Raw close and matching raw share-volume units; no adjusted-close/raw-volume multiplication | Basic preset; practical liquidity/activity proxy, not actual bid-ask spread or turnover. Reject missing/nonpositive volume. |
| Sector return / relative return | Sector log return; optional sector-minus-market return replaces it rather than duplicating both | Explicit `--sector ticker:XLK`, etc.; never infer historical membership from today's classification | Optional for VAR and direct models. Sector momentum evidence motivates testing, not a default guess for every company. |
| Momentum and short-term reversal | Trailing log return from 12 months ago to 1 month ago; most recent month's log return | Price history; windows derived from conventions, not future observations | Direct-model preset additions. Do not place redundant overlapping target transforms into the default VAR. |
| Illiquidity and beta | Mean `abs(simple return)/raw dollar volume` over 20 sessions; rolling covariance/market variance over one year | Price/volume history and market proxy | Optional direct-model additions; estimate entirely before origin, reject zero denominators. |
| Short rate and yield-curve slope | First differences of `DGS3MO/100` and `T10Y3M/100` | Explicit FRED source, publication availability and vintage | `equity-macro` additions; percent-to-decimal is a quote transform, not an investment-return calculation. These do not resolve #36 risk-free policy. |
| Implied volatility | `log(VIXCLS)` | Explicit FRED/CBOE series, released value available before origin | Optional macro profile; market risk state, not a guaranteed return signal. |
| Inflation and activity | Released CPI and industrial-production log growth, with period and release date retained | FRED `CPIAUCSL`, `INDPRO`; point-in-time vintages | Optional extended catalog, not the basic daily preset; repeated daily values are not independent macro observations. |
| Credit spread | Change in an explicitly licensed corporate-minus-Treasury yield series, decimal units | Candidate [BAA10Y](https://fred.stlouisfed.org/series/BAA10Y) has restrictive source terms | Research candidate only until acquisition/storage/fixture rights are resolved; do not assume FRED access grants redistribution rights. |
| Valuation, size, profitability, investment | Book/market, earnings yield, market cap, profitability, asset growth with precise definitions | Historical filing/publication timestamps and unrevised-as-of fundamentals required | Extended direct/panel candidates. Current Yahoo fundamentals must never be pasted backward over history; unavailable inputs are not silently synthesized. |
| Factor states | Lagged available FF5/MOM returns, optional rolling exposures | Ken French release availability; dated coefficient estimation | Optional, not contemporaneous explanatory factors from the target's future return period. Preserve the separate 0007 attribution contract. |

Official series references: [term slope T10Y3M](https://fred.stlouisfed.org/series/T10Y3M),
[VIXCLS](https://fred.stlouisfed.org/series/VIXCLS), and
[FRED/ALFRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html).
FRED's ordinary request defaults to information available today; a date on an
observation alone is not a publication timestamp or a vintage guarantee.

## Model inclusion decisions

Ship VAR/ridge, BVAR, direct elastic-net, direct boosted trees and retained GARCH
under the revised acceptance tasks. Include unregularized VAR only as an explicit
small-system comparator with rank/sample-size guards. No ARIMA-family fallback.

Defer VECM until users provide economically justified cointegrating level series,
rank/deterministic-term selection and error-correction validation; share prices
moving together do not establish cointegration. Defer PCR/FAVAR until a broad
licensed panel and fold-local factor tests exist. Defer foundation/neural models
until the same baseline, provenance and calibration gates plus contamination and
runtime checks pass in a separately accepted extension. No forecast may predict
future FX rates or PPP convergence through an indirect model output.
