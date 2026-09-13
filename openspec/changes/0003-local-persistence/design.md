# 0003 — Design

## Approach

Define user-state ports in `ports/storage.py`, use cases in `application/`, and concrete SQLite migrations/repositories in `adapters/storage/`. Preserve immutable migration IDs, WAL-safe backup and transaction rollback. PostgreSQL needs its own later real-engine and data-cutover plan; DuckDB is analytics, not an operational substitute.

Use 0013's composition root, owned ports and explicit environment checks.
Feature behavior remains defined by this change's scenarios. Keep the CLI and
base package usable without private context or unused optional services.

## Rejected alternatives

Do not copy the template over Sobres, introduce an unused hosted backend, or
duplicate application logic in transport handlers. Preserve the feature's
existing scope and implement only the adapters it exercises.

## Alignment amendment (0013)

Define user-state ports in `ports/storage.py`, use cases in `application/`, and concrete SQLite migrations/repositories in `adapters/storage/`. Preserve immutable migration IDs, WAL-safe backup and transaction rollback. PostgreSQL needs its own later real-engine and data-cutover plan; DuckDB is analytics, not an operational substitute.

The [common package map](../0013-template-development-alignment/design.md) is authoritative
for future locations. This amendment does not accept proposed cloud profiles.
Use named task proofs, installed-artifact checks and explicit rollback: revert
application wiring with compatibility facades intact; never rewrite a released
schema migration or delete user state to roll back a module move.
