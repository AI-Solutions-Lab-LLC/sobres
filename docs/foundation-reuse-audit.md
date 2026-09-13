# Foundation provider reuse audit (0001 D4)

Compared on 2026-09-13:

- `espin086/NewsWaveMetrics` at `e8382d2fc48ae284da86e092f0dad4a54994afb4`.
- Sobres foundation at `13b0a13ba8317d477cc71ad010a8a76c0d5420c9`, the PR #7 merge.

The earlier access blocker is resolved. Both files were read in full without
executing that application or reading its credentials.

| Prior implementation | Comparison and disposition | Evidence in Sobres |
|---|---|---|
| [`fetch_yfinance.py`](https://github.com/espin086/NewsWaveMetrics/blob/e8382d2fc48ae284da86e092f0dad4a54994afb4/fetch_yfinance.py): `Ticker.history(interval=...)` | Thin vendor call; no timeout/error translation, currency normalization, cache, explicit date bounds, or special handling to lift. Keep the source protocol and explicit adjusted-close selection. | `test_adjusted_close_is_the_default`, `test_cached_weekend_extension`, `test_live_source_reads_currency_from_metadata` |
| Same file: info, actions, financial statements, holders, recommendations | Useful endpoint catalogue for later equity analysis (0007); outside the foundation contract. | Deferred in original milestone; no claim these endpoints are shipped. |
| [`extract_economic_data.py`](https://github.com/espin086/NewsWaveMetrics/blob/e8382d2fc48ae284da86e092f0dad4a54994afb4/extract_economic_data.py): `get_series` and outer merge | Preserve the useful invariant that combining different native frequencies retains the union of observation dates. Foundation already does this; added a recorded daily DGS10/monthly CPI regression through cold and warm cache. | `tests/data/test_fred.py::test_mixed_frequency_preserves_native_dates`: values and CPI weekend dates survive, daily missing observations stay missing. |
| Same file: hardcoded metric→frequency mapping | Do not port: unknown series default to monthly and request vendor aggregation. Foundation returns native observations; explicit frequency conversion belongs in analytics. | Mixed-frequency regression checks no implicit aggregation/fill. |
| Same file: module-level `Fred(...)`, dotenv, global config, direct env access | Do not port: import-time clients and a second settings path conflict with declared settings, keyless startup, provider protocols, and secret handling. The recorder now reads the existing FRED setting. | `test_missing_key_exits_3_with_guidance`, `test_recorder_reads_declared_key_without_echo`, `test_recording_http_failure_never_prints_key` |
| Same file: date normalization after merging | Already present as timezone-naive dates. Recorded Yahoo payloads exposed a separate CSV replay issue across DST, corrected without shifting local dates through UTC. | `test_recorded_dates_survive_dst_and_include_endpoints` |

No implementation needs copying verbatim. The useful native-date retention
behavior is already present and now has explicit regression coverage. D4 is
complete; the deferred equity endpoints remain in their original milestone.

See [`tests/fixtures/README.md`](../tests/fixtures/README.md) for provenance,
revised known answers, and recording commands.
