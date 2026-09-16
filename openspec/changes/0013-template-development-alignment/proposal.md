---
change: 0013-template-development-alignment
milestone: development infrastructure, before resuming 0002–0010
depends_on: [0000-release-engineering, 0001-foundation-data-and-cli, 0011-rebrand-sobres, 0012-foundation-review-fixes]
status: superseded
---

# 0013 — Align development with the AISL project template

## Disposition — superseded on 2026-09-16

This change is **not implemented and no longer planned**. It stays in the tree as the
record of what was proposed and why it was set aside:

- The architectural intent — pure math in `core/`, owned provider and storage protocols,
  concrete I/O confined to adapters, transports that carry no business logic, one registry
  declaration per command — is already what `main` does. The layout is `core/`, `data/`
  (protocols in `data/base.py` and `data/storage/base.py`, adapters in `data/*_provider.py`
  and `data/storage/adapters/`), `cli/`, `api/` and `registry.py`, and it is enforced by
  `tests/architecture/test_layering.py`, not by review. The `ports/`, `application/` and
  `adapters/` package moves in this plan would have renamed those boundaries without
  changing any behavior or test.
- Waves A, B and D are tooling preferences of the template (Black/isort in place of ruff
  format, uv/Make manifests, PR-gate scripts, a private context-lake gitlink, a template
  update mechanism) that have no user-visible outcome for this project at its current
  stage; the commit gate in `CLAUDE.md` and `ci.yml` already runs the same checks.
- The R0/R1/R2 "alignment prerequisite" tasks that 0013 injected into 0002–0010, and the
  `Aligned development and application boundaries` requirement it added to their spec
  deltas, were removed the same day. Those capabilities are accepted against the tests
  that prove them on `main` (see each change's `tasks.md`).

Two items the plan named remain valid follow-ups outside 0013 and are tracked as an
issue: real-browser end-to-end checks for the SPA and the landing page (0004 R4, 0006 R4).
The scenarios below are historical and are not enforced by
`tests/architecture/test_scenarios.py` because the change is not `implemented`.

## Outcome

A contributor can clone Sobres without private context access, run `make install`
and `make check` from a fresh shell, and work one tested task at a time from a
merged OpenSpec plan. Claude and Codex read the same project procedures. New CLI,
API, persistence and deployment work follows one documented layout.

This planning commit prepares that work: it changes OpenSpec documents only.
At the user's explicit follow-up request, its PR also includes the four existing
foundation commits already on local `main`. No new template-alignment tool,
source migration, hook, submodule or deployment is implemented in this turn.

## Why

Sobres has a working foundation but predates the merged AISL template's shared
agent harness, contribution process and development conventions. Its open PR
stack still assumes transport-owned handlers, universal HTTP exposure and
interchangeable database engines. Updating only the harness would leave later
implementation plans sending contributors back to those assumptions.

## What Changes

- Adopt the template's root development structure, shared instruction entry point,
  linked skills/rules, local commands, issue/PR forms and reviewed update process.
- Preserve Sobres' stronger 90% branch coverage, operating-system matrix, recorded
  provider fixtures, independent math tests, base-wheel onboarding and review procedure.
- Propose an incremental package migration to the context blueprint's
  `core/`, `application/`, `ports/`, `adapters/` and composition root. This expanded
  layout is a **Sobres proposal**, not functionality already shipped by the template.
  Keep existing CLI commands, imports, data paths and schema versions compatible.
- Separate transport-neutral registry declarations and application services from
  CLI rendering; declare HTTP/UI exposure explicitly before 0004 generates routes.
- Pin optional private context; keep normal development, CI and artifacts independent
  of it. Record local decisions and deferred hosted profiles without importing private prose.
- Amend 0002–0010 together, supplying missing designs/tasks and explicit readiness,
  layout and verification requirements. Preserve implemented foundation history.
- Correct missing requirement bodies in the active planning set so strict validation
  can become a reliable development gate.

## Capabilities

### New Capabilities

- `development-workflow`: reproducible local checks, shared agent procedures,
  issue/merged-plan traceability and trustworthy merge gates.
- `template-alignment`: versioned adoption, compatible package boundaries,
  optional context access, protected downstream ownership and staged migration.

### Modified Capabilities

There are no canonical capabilities under `openspec/specs/` yet. Amendments to
the existing pending deltas stay in their owning changes: portfolio optimization
(0002), persistence (0003), HTTP API and UI (0004), deployment (0005), landing page
(0006), factors (0007), goals (0008), econometrics (0009), and FX/PPP (0010).
Their new alignment tasks remain unchecked. 0013 supplies the common prerequisite;
it does not absorb those features or claim them implemented.

## Impact

Future implementation touches repository tooling and package wiring; a complete
current-to-target map is in [design.md](design.md). [alignment-audit.md](alignment-audit.md)
records exact source revisions, all open PR heads, capability ownership and
conflicting/deferred decisions. [tasks.md](tasks.md) separates independent review units.

**Compatibility risk:** package moves can break imports, entry points, fixture
discovery and serialized identifiers. Retain compatibility facades and compare
installed artifacts before removing any path. Removing facades requires a later
versioned proposal. No public CLI or `sobres.core` break is planned here.

## Non-goals

- No new template-alignment feature implementation, merge, release, cloud
  provisioning or repository-setting change. Issue/PR publication and inclusion
  of the existing foundation commits were subsequently requested by the user.
- No automatic acceptance of every proposed context-lake ADR; no cloud, vector,
  Redis, DuckDB or PostgreSQL runtime dependency merely to resemble the blueprint.
- No rewrite of financial formulas, recorded observations or completed foundation
  scenarios. Existing analytics findings need their own acceptance review.
- No reduction of validation to the template's 85% threshold or path-only PR gate.

## Workflow and review

Issue and planning PR links are recorded in [tracking.md](tracking.md). The user
requested publication and explicitly asked to include the implementation already
on local `main`. This is a documented foundation-integration plus alignment-plan
exception to the normal separate planning PR process, not permission to implement
0013 before review. [review-draft.md](review-draft.md) makes that scope explicit.
Future alignment implementation branches start after this plan and its foundation
prerequisites are merged into default `main`.

## Risks and rollback

Formatter overlap, missing private context, untrusted PR policy edits and template
sync overwrites receive explicit scenarios. Adopt infrastructure before package
moves, then resume milestones. Revert an individual harness/tooling commit or
restore the prior template/lake pin to roll back. Package migration performs no
database migration; preserve data/config paths and immutable schema versions.

## Sources

- [Merged template foundation, 52e8426](https://github.com/AI-Solutions-Lab-LLC/project-template/tree/52e8426)
- [Pinned lake review, de42bd5](https://github.com/AI-Solutions-Lab-LLC/context-lake/tree/de42bd55f7b2268443fa4e46c13e74f99bdab144/docs/proposals/python-cli-template)
- [Sobres planning context](../../project.md) and [source/decision audit](alignment-audit.md)

## GitHub tracking

Implementation tracker: [#23](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/23).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. The plan merged in PR #33 at `b9792d72dad7217f7bb642c0c90a668afc501087`;
the 0013 package migration remains unimplemented.
