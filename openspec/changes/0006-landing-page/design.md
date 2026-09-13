# 0006 — Design

## Approach

Own the existing `site/` home page, accurate install/demo content, shared frontend tokens and a hosting inquiry route. Keep richer animation in this milestone. Publication requires explicit enablement and reviewed access; only site output is uploaded. No login, payment, hosted SLA or second home page.

Use 0013's composition root, owned ports and explicit environment checks.
Feature behavior remains defined by this change's scenarios. Keep the CLI and
base package usable without private context or unused optional services.

## Rejected alternatives

Do not copy the template over Sobres, introduce an unused hosted backend, or
duplicate application logic in transport handlers. Preserve the feature's
existing scope and implement only the adapters it exercises.

## Alignment amendment (0013)

Own the existing `site/` home page, accurate install/demo content, shared frontend tokens and a hosting inquiry route. Keep richer animation in this milestone. Publication requires explicit enablement and reviewed access; only site output is uploaded. No login, payment, hosted SLA or second home page.

The [common package map](../0013-template-development-alignment/design.md) is authoritative
for future locations. This amendment does not accept proposed cloud profiles.
Use named task proofs, installed-artifact checks and explicit rollback: revert
application wiring with compatibility facades intact; never rewrite a released
schema migration or delete user state to roll back a module move.
