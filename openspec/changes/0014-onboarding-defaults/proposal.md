---
change: 0014-onboarding-defaults
depends_on: [0001-foundation-data-and-cli, 0012-foundation-review-fixes]
status: implemented
---

# Onboarding defaults: one question, a default window, and worked examples

## Outcome

`sobres init` asks for the one thing a user can only supply themselves — the
FRED key — and stops. Every command that takes a date window runs without
`--start`, on an opinionated five-year default that the output records. A usage
error carries a runnable example of the command, not just a pointer to `--help`.

```bash
$ sobres init                      # asks for fred_api_key, then runs doctor
$ sobres data prices AAPL MSFT     # last five years; provenance says so
$ sobres analyze stock
error: invalid parameters for `analyze stock`: ticker: Field required
  next: try: sobres analyze stock NVDA --fill drop  (or: sobres analyze stock --help)
```

Issues: [#18](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/18) (long
setup), [#19](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/19)
(unhelpful errors, no date defaults). Predecessors: 0001 declared the settings
registry and the error contract; 0012 made optional prompts skippable. This
change was implemented directly against `main` after the 0003–0010 stack merged;
there was no separate planning PR.

## Why

The first run of `sobres init` walked all fourteen declared settings. Thirteen
of them are backend or diagnostic knobs with sound defaults; only the FRED key
unlocks something a new user wants. Asking for the rest at first contact reads
as a chore and buries the one question that matters.

`sobres data prices AAPL` failed with `start: Field required` and a `--help`
pointer. A user who has just installed the tool should get prices, and when
they do get an error it should show them a working command.

## What changes

- **Settings carry an `advanced` tier.** Declared once, like `secret` and
  `required`. `init` prompts only non-advanced settings unless `--advanced` is
  passed; advanced settings keep working through `--set`, `sobres config set`,
  the environment and the settings page. Only `fred_api_key` is non-advanced.
- **A shared default window.** `--start` defaults to five years before `--end`
  (which defaults to today) on every window-taking command; the resolved dates
  are already recorded in provenance. Commands that carried their own fixed
  defaults (`econ`, `analyze stock`, `ppp`) are unchanged.
- **Commands declare a worked example.** `register(example=...)` is part of the
  declaration; a usage error's hint leads with it. A test fails the build when a
  command with a required parameter declares none.

## Non-goals

No change to non-interactive `init` (containers still take everything from the
environment and fail on a missing required value). No change to `doctor`,
`config` or the settings page, which continue to show every setting. No new
setting, provider or dependency. The default window is a convenience, not a
research recommendation, and it does not alter any computation once dates are
given explicitly.

## Risks

A five-year default silently shortens or lengthens a window a user meant to be
different; the provenance block and the help text both state the resolved
default so the assumption is visible. Making `--start` optional changes the
OpenAPI schema for those commands; the client is regenerated in the same change
and the drift gate proves it.
