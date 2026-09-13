# Alignment audit — 2026-09-13

## Inspected revisions and limits

| Source | Revision | Meaning |
|---|---|---|
| Sobres local `main` / planning branch base | `e0432c507c6640efa02048db213b5348c8140506` | Includes foundation merge and fixture/reuse completion; four commits ahead of remote main |
| Sobres fetched `origin/main` | `2b844ebcf2df350a5cdc07133ab1e7056777e709` | Older than local foundation; do not reset local main to it |
| AISL project-template fetched `main` | `52e8426503964c78e6e23b639b20bb5d5753d159` | PR #1 merged; use this instead of stale local `feat/connect-context-lake` |
| Template's pinned context-lake | `de42bd55f7b2268443fa4e46c13e74f99bdab144` | Reviewed docs package, now reachable through merged lake PR #1 |
| Context-lake fetched default branch | `70c8fda` (`claude/adoring-volta-4x4xq6`) | Merge of PR #1; canonical ADR promotion is still proposed |

Read-only comparison includes tracked harness/config/workflow files, full active
specification scenarios, current registry/storage boundaries, proposal deltas and
newer tasks/designs from each open PR head. The template was inspected in a detached
worktree. No open PR #8–#16 implementation was merged as part of this task. The user
subsequently requested including the already reviewed foundation commits from
local main in the PR; validation distinguishes that existing code from new plans.
No cloud/API product behavior is inferred from documentation or checked task boxes.

## Open implementation stack

| Change | PR | Inspected head | Base branch | Amendment ownership |
|---|---|---|---|---|
| [0002-portfolio-optimization](../0002-portfolio-optimization/proposal.md) | #8 | `21724ce35c6a4b3f5d89db265517bf77a38d425f` | `claude/kind-sagan-4yakbc-0001-foundation` | Shared optimization services; preserve math/oracles and CLI contract |
| [0003-local-persistence](../0003-local-persistence/proposal.md) | #9 | `20654c1249aa7de32e3c35dbaa346c6929ef5b1b` | `claude/kind-sagan-4yakbc-0002-optimization` | Owned storage ports, adapter migrations, backups and transaction contracts |
| [0004-web-ui](../0004-web-ui/proposal.md) | #10 | `dbdfe69ecc4783aecd848637b07cf8b16a73fa69` | `claude/kind-sagan-4yakbc-0003-persistence` | Explicit HTTP exposure, shared services, optional web install, browser verification |
| [0005-docker-distribution](../0005-docker-distribution/proposal.md) | #11 | `eef53608b231e826f44edee9476aa4196bc20d77` | `claude/kind-sagan-4yakbc-0004-web-ui` | compose.yaml, non-root image, independent publication switches, private exclusions |
| [0006-landing-page](../0006-landing-page/proposal.md) | #12 | `a2f297c44ed61cc341c6da9778abf14acf6c4540` | `claude/kind-sagan-4yakbc-0005-docker` | One site, hosting inquiry, opt-in publication and accurate shipped claims |
| [0007-equity-factor-analysis](../0007-equity-factor-analysis/proposal.md) | #13 | `4a8a60d88f60dfe1fd1409b6c7890f9416f2f668` | `claude/kind-sagan-4yakbc-0006-landing` | Application factors service, provider adapter, base dependency decision |
| [0008-goal-planning](../0008-goal-planning/proposal.md) | #14 | `563caa73e049a18b69acca233299a73341f7c31c` | `claude/kind-sagan-4yakbc-0007-factors` | Application goals service, injectable clock/inflation/history, saved-state boundary |
| [0009-econometrics-forecasting](../0009-econometrics-forecasting/proposal.md) | #15 | `88df04e01a5993c24a0857ef387e0b03c24fbacc` | `claude/kind-sagan-4yakbc-0008-goals` | Application econometrics service, explicit source policy, optional dependencies |
| [0010-currency-and-ppp](../0010-currency-and-ppp/proposal.md) | #16 | `dc2ba7a31a322e73c2c5401aed77e07c4d6b41f1` | `claude/kind-sagan-4yakbc-0009-econ` | FX/PPP application services, provider ports, vintage and key/doctor coverage |

PRs #8–#16 remain open and are stacked on feature branches, not default main.
The new work supplies updated plans only. At the user's explicit request the PR
also integrates existing local-main foundation commits into remote main. Review
that foundation-integration plus planning scope, merge it, then implement 0013. Reconcile #8 first and #9–#16 in order onto the resulting
base. Do not merge the whole stack, force-push it or label it compliant by editing
these documents. Recheck heads before acting: this table is a dated snapshot.

The amended tasks carry forward task IDs from those branch heads but reset their
checkboxes: the previous checks described old branch behavior, not acceptance of
the new contract. Original claims remain accessible at the pinned source commits.
The architecture amendments are R0/R1/R2 in each change; feature tests and any
outstanding review findings must be reverified as well.

## Every active change accounted for

| Change | Current evidence | Treatment |
|---|---|---|
| 0000 release | Scaffold merged; owner actions and token/OIDC docs conflict remain | Preserve history, repair requirement bodies, amend unfinished auth/setup expectations; actual changes owned by 0013/0005 |
| 0001 foundation | Implemented on local main, PR #7 and #17 merged to their stack base | Preserve scenarios and completed tasks; target layout compatibility governed by 0013 |
| 0002–0010 | Nine open implementation PRs; no default-main acceptance | Amend all proposal/design/task/spec contracts and dependency order |
| 0011 rebrand | Package rename merged; image/page/release owner actions remain | Keep historical names as migration evidence; pending image/page tasks follow 0005/0006 and 0013 |
| 0012 review fixes | Implemented in foundation; real recordings/audit subsequently completed | Preserve regression scenarios; correct stale follow-up wording only |
| 0013 alignment | New local plan | All implementation tasks unchecked |

No canonical accepted specs have been synced under `openspec/specs/` yet.
Do not create MODIFIED deltas against nonexistent canonical requirements. Pending
feature deltas are amended in place; completed foundation scenarios retain their
identity until a deliberate tested sync/archive. Requirement-body repairs in
0000 and 0002–0010 restate their existing scenario intent, not new financial rules.

## Capability comparison and local decisions

| Area | Observed template / context | Sobres decision and implementation owner |
|---|---|---|
| Harness | Template has shared AGENTS, Claude import and individual Codex skill links | Adopt root structure; retain detailed Sobres review skill, rules and commit gate; 0013 B1/B2 |
| Development | Template Make targets exist but use ambient executables; template coverage is 85% | Explicit clone-local environment, lock tools, preserve 90% and cross-platform matrix; 0013 A2–A5 |
| Formatting | Template runtime still uses Ruff format despite Black/isort instruction; blueprint removes overlap | Black/isort authority, compatible Ruff lint and one non-conflicting gate; 0013 A3 |
| Governance | Shared process specifies merged plans; current PR checker only checks changed paths | Separate trusted metadata/ancestry gate, no fake spec edit in implementation PR; 0013 B4–B6 |
| API | Template does not implement API; blueprint proposes services and explicit exposure | Migrate common application boundary in 0013; 0004 exposes reviewed subset and app factory |
| Storage | Template has no SQLite/Postgres application; lake distinguishes capabilities | Preserve actual Sobres SQLite, protocols, WAL/backup semantics; backend-specific migration ownership; 0013 C2/C3, 0003 |
| Package layout | Template has core/cli; blueprint proposes application/ports/adapters | Proposed local expansion with legacy import facades, unchanged external CLI/core API; 0013 C1–C9 |
| Context | Real optional gitlink at de42bd5, packaging exclusions and missing-access fallback | Adopt pin/access model; no lake fetch during ordinary CI; 0013 B3 |
| Template upgrades | Existing sync opens PRs with blanket skip labels and limited ignores | Manual/pinned review first; protect Sobres overlays and all OpenSpec config; 0013 B7 |
| Release | Template uses OIDC and independent image switches; Sobres workflow still uses OIDC despite the agreed org-token spec and issue #21 | Keep org-token auth as a documented Sobres exception; issue #21 owns correcting the workflow and accurate skipped-release reporting; 0000/0005 |
| Containers | Template CLI-only Dockerfile cannot serve Sobres UI | 0005 owns multi-stage real Sobres image, compose.yaml, wheel parity and live container smoke |
| Home page | Template ships a static page and hosting inquiry; activation is opt-in | 0006 enhances the same site/ with real financial demonstrations and opt-in publication; no second marketing site |
| Hosted services | Template docs/examples exist, adapters and tenancy do not | Cloud Run/Supabase/GCS/BigQuery/cache/vectors and mirrors deferred to dedicated changes |

## Context decisions: selected, adapted, deferred

All lake references below are relative to the reviewed package at the exact
[pin](https://github.com/AI-Solutions-Lab-LLC/context-lake/tree/de42bd55f7b2268443fa4e46c13e74f99bdab144/docs/proposals/python-cli-template).
This document is a Sobres-authored decision summary; no private ADR bodies are
copied into public standards. Merging the lake review package did not promote its
proposal-local ADRs into accepted canonical policy.

| Sources | Disposition / reason | Revisit trigger |
|---|---|---|
| `template-blueprint.md`, decisions 0002/0004 | Propose shared application/ports/adapters and bootstrap; preserve existing imports | 0013 implementation and 0004 route/transport tests |
| decisions 0001/0006/0019; `submodule-contract.md` | Adopt optional pin, reviewed upgrades and shared harness | Template/lake pin update or platform discovery failure |
| decision 0018 | Adopt issue then merged-plan sequence; acknowledge historical bootstrap and local-only request | Real issue/planning PR and stronger gate rollout |
| decisions 0003/0009/0010/0011/0012/0013 | SQLite operational default; postpone Postgres, analytics, external caches, documents/vectors | Measured feature requirement plus engine-specific conformance/migration plan |
| decisions 0005/0007/0008 | Preserve hosted extension path, not a cloud requirement for local users | Approved hosted use case with auth/tenancy/restore/cost ownership |
| decision 0014 | Retain Typer/Rich and machine-output contracts; no CLI library replacement | Concrete accessibility or presentation gap |
| decisions 0015/0016 | Preserve one canonical AISL repo; mirrors/remote settings are separate activation | Explicit owner setup and authorized mirror/release rollout |
| decision 0017 | Single accurate page and visible hosting inquiry | 0006 acceptance and reviewed Pages visibility |

Conflicts resolved in pending specs: universal API parity becomes exposure-aware
parity; all-settings UI becomes an explicit safe-field projection; one universal
SQL migration becomes adapter-owned operational migrations; DuckDB no longer
claims operational interchangeability; default automatic publication becomes
opt-in activation. Financial formulas and model acceptance are not silently
changed to implement a folder convention.

Context items still needing engineering evidence: no second database has proven
portability; no enterprise identity/tenant boundary exists; the template's stronger
workflow gate is planned; a SQLite URL switch does not transfer data; an in-process
worker is single-user only. These are explicitly not 0013's completion criteria.

Branch-specific cautions carried into tasks: #8's R oracle was independently
reconstructed without running R; #10's browser acceptance was source-only; later
branches used synthetic provider fixtures and can overwrite the real foundation
recordings if merged carelessly. #13's numpy/HAC choice is retained as a proposed
design, while its cache fix must be checked against the already corrected foundation.
#15's implicit symbol heuristic is not adopted as a universal source rule; its
replacement requires explicit source metadata/prefixes and ambiguity tests.
No financial review finding is resolved merely by relocating a module.

## Verification for this planning branch

OpenSpec CLI 1.13.0; telemetry disabled with `OPENSPEC_TELEMETRY=0`.
Baseline strict validation: 13 changes, 3 passed, 10 failed (missing requirement
bodies and four normative-text warnings). Final results and reproduction commands
are recorded in [validation.md](validation.md). Code verification of the included foundation is recorded separately from the
planning checks. No test result implies that the proposed alignment was implemented.

## Existing GitHub issues and contract precedence

Read issues #18–#21 before creating new milestone trackers. Issue #21 already owns
release authentication/setup and states the agreed `PYPI_PROD`/`PYPI_TEST` token
contract; the current workflow is still OIDC. Preserve that explicit project
choice as an exception to the template's OIDC default. Do not silently migrate to
OIDC or arm publishing as part of environment alignment. Reuse #21 rather than
create a duplicate. Issues #18 (init), #19 (errors), #20 (factor date/refresh UX)
are separate user behavior reports; they are not closed or implicitly fixed by
a structural refactor. No new ready-to-implement spec is claimed for those reports.
