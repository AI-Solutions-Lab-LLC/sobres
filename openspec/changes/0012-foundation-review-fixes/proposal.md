---
change: 0012-foundation-review-fixes
depends_on: [0001-foundation-data-and-cli]
status: proposed
---

# Foundation review corrections

## Outcome

A base install can fetch keyless prices, optional setup prompts can be skipped,
and cached values match provider values. Diagnostics keep secrets private and
migration backups restore committed data. This change addresses findings F1–F10
from the independent review of PR #7 at dd5d6f0.

## Scope

Correct the ten reproduced defects and add regression assertions at their actual
boundaries. Validate the foundation spec and resolve naming, calendar, and
readiness ambiguities without weakening the intended user experience.

## Non-goals

No merge or release, no later-milestone analytics, no new backend, and no FRED FX
adapter. Replacing the synthetic fixture corpus and the cross-repository D4 audit
remain explicit foundation follow-ups; no real API key is required for these fixes.
