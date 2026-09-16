# 0016 — Tasks

Each task names the test that proves it. Checked = on `main`.

## Wave A — port, adapters, conformance

- [x] **A1. Broker port and owned models** — `data/brokers/base.py`.
      → `tests/data/broker_conformance.py`
- [x] **A2. FakeBroker** — deterministic fills at given quotes, partial fills and a
      timeout switch for tests. → `tests/data/test_brokers.py::test_fake_partial_fill_and_timeout_are_observable`
- [x] **A3. AlpacaBroker** — httpx source, paper/live URLs, payload mapping, error
      translation (401/403 → config, 422 → usage, 5xx → provider, timeout → unresolved).
      → `tests/data/test_brokers.py::TestConformance` (alpaca-fixture), `::test_alpaca_error_translation`
- [x] **A4. Conformance** — the same suite over both adapters. → `tests/data/test_brokers.py`
- [x] **A5. Vendor isolation** — nothing outside `data/brokers/` imports the Alpaca module.
      → `tests/cli/test_trade.py::test_vendor_stays_in_its_adapter`

## Wave B — core accounting

- [x] **B1. Sizing** — known allocation, holdings/pending, rounding, insufficient funds,
      stale quote. → `tests/core/test_trading.py`
- [x] **B2. Average-cost P&L and deposits** — 40/30 known answer, deposit not profit,
      time-weighted return. → `tests/core/test_trading.py`

## Wave C — storage

- [x] **C1. Migration v3 and records** — `trade_intent`, `trade_order`, `trade_fill`;
      `tests/fixtures/schema/v2.sql` recorded. → `tests/data/test_migrations.py`
- [x] **C2. TradeRepository in the conformance suite; cache clear preserves it.**
      → `tests/data/storage_conformance.py::ApplicationStateConformance`

## Wave D — commands, settings, doctor, docs

- [x] **D1. Settings and provider spec** — four settings, `alpaca` provider, doctor
      checks. → `tests/cli/test_doctor.py::test_every_setting_and_provider_has_a_check`
- [x] **D2. `trade preview|execute|positions|orders|status|history|close`** with the
      lifecycle above; `execute`/`close` terminal-only. → `tests/cli/test_trade.py`
- [x] **D3. Live gate** — setting + flag + typed confirmation; paper records cannot
      address live. → `tests/cli/test_trade.py::test_live_requires_setting_flag_and_confirmation`
- [x] **D4. Docs** — README quickstart, CHANGELOG, ROADMAP exclusion revised, 0002
      proposal note, live workflow reads paper credentials by name.
- [ ] **D5 (owner)** — bounded real-money verification with the owner's live account;
      record the evidence on #22.
