# PR #13 synchronization

The updated #12 base carries main `b9792d7`, #33's plans/fixes, and accepted #8
optimization through #35. Factor analysis remains included; amended 0007/0013
plans and pending layout acceptance remain tracked under #29.

Preserve main's opaque case-sensitive cache identifiers and withdrawal handling,
not the older uppercase-key workaround. The mixed-case regression still proves
cold/warm factor values. Stock risk uses the shared dated risk-free series.
Synthetic fundamentals are explicitly separated under `fixtures/synthetic/`;
all recorded-provider payloads/manifests from main remain byte-identical. Fixture
mode prefers recorded fundamentals, with the labelled synthetic corpus only when
absent; live providers never load it. The recorder regression verifies future
fundamentals payloads are bound by the primary manifest, without a self-hash.

Validation: 905 non-network tests passed, four live tests excluded, 95.73% branch
coverage. Black/isort, Ruff lint/format, mypy, actionlint and all 14 strict OpenSpec
checks passed. OpenAPI/client regeneration and frontend build/bundle checks passed.
The fundamentals fixture proves parser behavior only, not vendor truth; live
fundamentals acquisition and further feature acceptance are not claimed here.
