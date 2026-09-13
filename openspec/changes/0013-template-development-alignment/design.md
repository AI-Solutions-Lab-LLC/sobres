# 0013 — Design

## Decision and boundaries

Use the merged template for repository structure and the pinned lake blueprint
as the source of proposed architectural extensions. They are distinct baselines:
the template implements `core/` and `cli/`, not a working hosted application.
This plan adopts an expanded layout for Sobres because its open API and storage
work already needs shared orchestration. No placeholder packages for unused
services are created. [The audit](alignment-audit.md) records applicability and
conflicts; the decisions here are proposed until this planning change merges.

The future instruction update must amend the old `AGENTS.md`/`CLAUDE.md` path rules
in the same implementation PR as the first applicable move. Until then their
current driver boundary remains the rule for the current source. A planning edit
does not make today's implementation satisfy tomorrow's architecture tests.

## Repository layout

```text
AGENTS.md                       concise shared entry; preserve review requirements
CLAUDE.md                       imports AGENTS, Claude runtime note only
CONTRIBUTING.md / SECURITY.md
.claude/{rules,skills,agents,hooks}/
.agents/skills/<name>            relative links to individual shared skill directories
.agents/rules                   relative link to shared rules
.codex/config.toml              runtime settings only, no duplicated policy
.github/{ISSUE_TEMPLATE,workflows,scripts}/
Makefile / .editorconfig / .pre-commit-config.yaml
pyproject.toml / uv.lock         exact development resolution; package ranges retained
package.json / package-lock.json  pinned OpenSpec dev tooling, not wheel dependencies
template-manifest.toml / .templatesyncignore
.gitmodules / context-lake/     optional private gitlink at reviewed SHA
docs/{standards.md,architecture.md,adr/,AGENT-HARNESS.md,CONTEXT-LAKE.md}
docs/RELEASING.md               preserve established Sobres document path
docs/DEPLOYING.md               0005 owns container operations
openspec/{project.md,config.yaml,changes/,specs/}
src/sobres/                     detailed map below
tests/{core,application,contracts,cli,api,architecture,invariants,packaging,integration,network}/
tests/fixtures/                 existing recorded payloads and provenance retained
frontend/                      0004 owns React app and build lock
site/                          0006 owns one project home page and build lock
Dockerfile / compose.yaml       0005 owns real container profile
templates/{github,scripts}/     inactive, reviewed hosting/mirror examples only if needed
```

Keep `legacy_code/`, `skills/openspec-pr-review/`, existing release docs and
review artifacts as Sobres-owned content. Do not run the template rename script
over an existing product. Preserve the version at `src/sobres/__about__.py`.

## Package map and ownership

All paths below are relative to `src/sobres/`. New features use the target
locations only after 0013's package migration is implemented. References in
completed 0001/0012 remain historical evidence, not instructions to add old paths.

| Current location | Target | Migration rule |
|---|---|---|
| `core/` | `core/` | Pure financial math, deterministic types; retain public imports and conventions |
| `registry.py` including Typer generation | `registry.py` declarations + `adapters/cli/registry.py` generation | Neutral registry imports no transport; aliases/defaults/validation retained |
| `cli/commands/{data,cache,config,doctor,init,upgrade,commands}.py` | `application/commands/` declarations/use cases and `adapters/cli/` prompting/presentation | Service input/output cannot contain a Typer context or prompt callback with CLI types |
| `cli/context.py` provider/cache construction | `application/context.py` owned dependencies + `bootstrap.py` construction | Inject settings, clock, repositories, providers and progress; no global connection in services |
| `cli/main.py`, `cli/render.py` | `adapters/cli/main.py`, `adapters/cli/render.py` | `cli/` remains thin compatibility facades; entry point transition tested in built wheel |
| `data/base.py` | `ports/providers.py` and `core/market_types.py` | Move protocols separately from plain data types; preserve imports through facades |
| `data/storage/base.py` | `ports/storage.py` | Domain repository and transaction interfaces; no SQL/driver types |
| `data/storage/adapters/{sqlite,schema,migrations}.py` | `adapters/storage/sqlite.py`, `adapters/storage/schema.py`, `adapters/storage/migrations/` | Preserve released migration IDs/content; keep SQLite migration lineage behind its adapter |
| `data/{yfinance_provider,fred_provider,ken_french,ecb_provider,fixtures}.py` | `adapters/providers/` | Vendor/network details and fixture readers remain outside application/core |
| `data/providers.py` composition | `bootstrap.py` + `adapters/providers/` | Settings choose implementations; services consume ports |
| `data/{cache,currency}.py` | `application/{cache,currency}.py` | I/O orchestration through ports; pure conversion identities/types in core |
| `data/{align,gaps}.py` | `core/market_data/` for pure frame rules | Separate any I/O wrapper first; retain closure/listing/missing-value distinctions |
| `config.py`, `settings.py`, `doctor.py` | retain settings declarations; config I/O in `adapters/config.py`, health orchestration in `application/doctor.py` | `config.py`/`doctor.py` compatibility imports; preserve precedence, defaults and check registry |
| `observability/`, `results.py` | retain | Adapter-only instrumentation; neutral result types with no renderer imports |
| planned `api/` | `adapters/api/` | Optional FastAPI app factory; built assets at `adapters/api/static/` |
| planned `cli/commands/{optimize,portfolio,plan,...}.py` | `application/commands/` + minimal `adapters/cli/` rendering | No newly authored use cases in compatibility directories |

Migrate one provider/command group at a time. During transition, architecture tests
use an explicit shrinking legacy allowlist; new code cannot extend it. Final
acceptance allows forwarding imports only in old directories, no second body or
driver imports. `core/`, `ports/`, `application/` and the neutral registry cannot
import concrete adapters; `application/` can perform I/O only through injected
ports. `bootstrap.py` owns construction/lifecycle and never computes finance.

Move `tests/data/contracts.py` and `storage_conformance.py` to `tests/contracts/`;
provider parsing tests to `tests/integration/providers/`, cache/use-case tests to
`tests/application/`, pure alignment/gaps tests to `tests/core/market_data/`, and
migration/WAL/backup tests to `tests/integration/storage/`. Keep transport tests
in `tests/cli/`/`tests/api/`, behavioral invariants in `tests/invariants/`, and
recordings under `tests/fixtures/`. Update imports and scenario mappings with the
move. Temporary test-import facades cannot duplicate collection or inflate coverage.

## Local development loop

`make install` explicitly uses the repository `.venv`, locks the Python development
resolution and separately pins OpenSpec 1.13.0 in a development-only Node manifest.
Document supported Node/uv versions and bootstrap commands. Make recipes execute
the environment's interpreter/tools explicitly; shell activation is unnecessary.
Test the first install and an idempotent repeat from a clean clone. Provide
equivalent commands for Windows without Make; WSL or Git symlink support is needed
for linked agent procedures, but ordinary Python use remains supported natively.

`make check` = formatter checks, Ruff lint, strict mypy, offline tests with 90%
branch coverage, strict OpenSpec validation, workflow lint and harness-link checks.
`make test-fast` runs affected offline tests for feedback; it never substitutes
for the full merge gate. Separate `make build` and `make audit` complete CI parity.
Keep artifact installation/onboarding/data smoke tests in reusable `ci.yml`.
Docker/frontend/site jobs join its aggregator when 0004–0006 introduce them.

Black (100) and isort (Black profile, 100) are formatting authorities. Retain Ruff
lint with overlapping import-sort rules disabled and remove the Ruff formatter
gate in the same future tooling PR. Explicitly update old commit-gate scripts,
pre-commit config and documentation together. Never change files outside that
PR's scope simply to format the entire repository. Test a second formatter pass
as a no-op. Do not lower coverage from 90 to the template's 85.

## Shared agent harness and contribution gates

Keep one instruction body per topic, read progressively. Extract the current
Sobres architectural, data, currency, observability, testing and release rules
into shared rules/docs without dropping their meaning. Preserve the versioned
OpenSpec review skill as authoritative for Sobres; wrap/link it from the shared
review procedure instead of replacing it with the template's shorter checklist.
Use relative links and verify targets stay in the checkout. Link checks prove
file discovery only; record real Claude/Codex startup and skill-discovery checks
separately. Claude hooks and tool permissions do not enforce Codex behavior.
Runtime defaults must respect user/machine policy and never broaden access.
Keep the explicit organization-token release contract from 0000 and issue #21
as a local template exception; its correction and accurate skip reporting remain
owned by #21. Do not copy the template's OIDC publisher over that decision.

Adopt issue → separate merged plan → small implementation PRs. Tasks are ≤2h,
one coherent commit each, normally 1–3 tasks and ~300 handwritten lines per PR.
Explain atomic exceptions; do not split tests away to meet a size target.
Retain `All checks passed`; add policy/security checks as appropriate with
explicit aggregation. CI must fail on failed/cancelled/skipped mandatory jobs.

The template's current path-only check is insufficient for separate planning PRs.
Implement the stronger gate as its own task: trust policy from the protected base,
read issue/plan metadata with read-only credentials, require merge into this
repository's default branch and ancestry, reject code in planning PRs and semantic
spec amendments bundled with implementation. Do not require a new spec edit in
every implementation PR when its approved plan is already merged. A maintainer
exception needs substantive recorded scope, not a bypass label alone. Secretless
fork checks must never execute head policy code with privileged credentials.

AI review is an optional, explicitly configured integration; a missing credential
must not break mandatory public checks unless the maintainer has deliberately
enabled that required integration. Keep no credential values in planning or artifacts.

## Registry exposure and persistence decisions

0013 extracts declarations/services and adds exposure metadata without shipping an
HTTP server. All existing commands retain their CLI behavior. `http_exposed=false`
is the default; 0004 explicitly enables reviewed analysis/state operations and
offers narrow settings/health endpoints. Excluded operations have no generated
route, OpenAPI entry or actionable UI form, not merely a handler returning 400.
Local upgrade, shell/browser launch, arbitrary path export/repair, deployment and
token administration remain CLI-only. UI settings use a separate allowlist; no
browser modification of database paths, exporter URLs or provider credentials.

SQLite remains the sole runtime backend. Owned ports and common behavioral tests
remain mandatory, but a URL change neither migrates records nor proves another
engine works. Operational PostgreSQL needs a separate plan, real-engine contracts,
export/import, identity/count/invariant checks, cutover and rollback including
post-cutover writes. DuckDB is an optional analytical store, not a promised
transactional substitute. Adapter-owned migrations preserve immutable SQLite
history; no artificial SQLite/PostgreSQL/DuckDB SQL intersection is required.

## Template/context update ownership

Record full template/lake SHAs, profile decisions and exceptions in
`template-manifest.toml`. Pin the lake at the template-reviewed reachable commit;
initialization is an explicit maintainer action. Public clone/build/check/review
does not fetch it, and reports context checks unavailable when absent. Never
vendor private review prose as public rules. Author sufficient local standards.

Protect `src/`, tests, all OpenSpecs including config, identity, fixtures, docs,
local review skills, lake pin and runtime-specific configuration from blind sync.
Harness and CI files require three-way/manual reconciliation of Sobres overlays.
Template updates are review PRs with pin diffs, affected decisions and checks;
no scheduled auto-merge or magic skip labels. Start manual, enable an update bot
only after dry-run overwrite/rollback tests. New template dependency PRs are not
part of the selected merged baseline until separately reviewed.

## Rollout, rollback and deferred profiles

1. Review and merge the explicitly requested foundation-integration plus planning
   PR. It includes local `main`'s four existing foundation commits and the new
   OpenSpec amendment. This recorded exception does not authorize implementing
   the new alignment before its plan merges.
2. Implement harness and reproducible checks in small PRs, preserving current paths.
3. Implement package/service extraction with import facades and compatibility tests.
   No schema bump, database relocation or data copy belongs to a path refactor.
4. Restack 0002–0010 onto the merged migration, bottom-up. Use amended task plans;
   retained branch code is a candidate implementation requiring fresh evidence.
5. Archive completed foundation changes only after canonical spec sync and scenario
   coverage remain correct. Historical statuses are not inferred from task boxes.

Rollback individual implementation commits, then run artifact/fixture checks.
Keep forward-only released DB migrations intact; roll back code only when its
schema reader is compatible. Pin reverts never delete local context or user state.

Cloud Run/Supabase, GCS, BigQuery, vectors, external cache, tenancy, billing and
personal mirrors remain separate profiles with their own approval and tests.
0005 ships the local single-user container; 0006 owns the home page/inquiry route.
Do not call a deployment token enterprise authorization or publish a hosted SLA.
