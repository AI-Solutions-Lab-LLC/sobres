---
change: 0004-web-ui
milestone: v1.2
depends_on: [0001-foundation-data-and-cli, 0002-portfolio-optimization, 0003-local-persistence, 0013-template-development-alignment]
status: proposed
planning_depth: proposal + design + tasks + spec deltas; amended by 0013
---

# 0004 — Web UI

## Outcome

```bash
sobres open                       # starts the server if needed, opens the browser
sobres open doctor                # straight to a view: settings, doctor, runs, run 42, ...
sobres serve                      # http://127.0.0.1:8787, no browser
sobres serve --host 0.0.0.0 --port 8787   # prints a token; required to bind non-local
```

A dark, fast single-page app with **every explicitly web-exposed analytical capability** behind a form: pick or
build a portfolio, optimize it, drag along the efficient frontier, run a
walk-forward backtest and watch it progress, and read the full run history from
0003. Shared product operations have the same behavior through CLI and UI. Local
administration and unsafe settings remain terminal-only.

## Why

The CLI is the right interface for someone who already knows what
`--objective max-sharpe --max-weight 0.35` means. Everything this tool computes is
also visual — an efficient frontier is a *curve*, a drawdown is a *shape*, a
correlation matrix is a *heatmap*. Reading those as ASCII tables discards most of
the information.

It also makes the tool demonstrable. The landing page in 0006 needs something to
show, and "watch the frontier solve" is the demo.

## What changes

- **New capability `http-api`** — FastAPI app at `src/sobres/adapters/api/`, a thin adapter
  over shared `application/` services, like `adapters/cli/`, holding no business logic.
- **New capability `web-ui`** — React + TypeScript SPA under `frontend/`, built to
  static assets and served by the same process.
- **Two new consumers of the command registry.** 0001 declares every command
  once and generates the CLI from it; this change generates the HTTP API and the
  UI's forms from explicitly exposed declarations. This makes parity for
  reviewed web capabilities a tested invariant — and why the
  registry landed in 0001 rather than here: adding consumers to declarations is
  a generator each; retrofitting declarations onto hand-written commands would
  have been a rewrite of every one.
- **Job execution** — optimizations and backtests run as jobs persisted through
  0003's repositories, with progress streamed over SSE. Trace context and run id
  are persisted with the job, so work that outlives its request stays traceable.
- `sobres serve` as the entry point and `sobres open` as the one-command path from
  terminal to browser; `[web]` extra for FastAPI and uvicorn.

## The parity problem, and how it is solved

"A UI with all the features of the CLI" decays the moment someone adds a CLI flag
and forgets the form field. Three ways to prevent it, and only one survives
contact with a year of feature work:

| Approach | Why it fails |
|---|---|
| Write the UI to match the CLI, carefully | Drifts on the first hurried PR |
| Generate the UI from the OpenAPI schema | Fixes API↔UI drift but not CLI↔API drift, which is the one that matters |
| **One registry; CLI, API and UI all derive from it** | Adding a parameter in one place makes it appear in all three, and a parity test fails if an exposed command lacks a route/view or an excluded command has one |

The registry is the design decision this whole change rests on. Everything else is
presentation.

## Non-goals

- **No multi-user accounts.** One deployment is one person (see the access model).
  A shared token authenticates *the deployment*, not a user.
- No account recovery, email, or password flows — there are no passwords.
- No mobile-native app. The SPA is responsive; that is the extent of it.
- No server-side rendering or SEO. This is a tool behind a token, not a website;
  0006 is the public-facing page.
- No websocket bidirectional protocol. Jobs stream one way; SSE is sufficient and
  survives proxies that websockets do not.
- No charting of anything the CLI cannot compute. The UI visualizes results; it
  never becomes a second place where analysis logic lives.

## Risks

| Risk | Mitigation |
|---|---|
| Business logic leaks into the API or the frontend | Shared application services call core through injected data dependencies; architecture tests reject computation in `adapters/api/` and `adapters/cli/` |
| The UI drifts from the CLI | A parity test asserts exact route/view equality with the explicit exposure set, including absence of local-only commands |
| Exposing the UI on a LAN exposes someone's financial data | Binding a non-loopback address requires a token; the token is generated, not chosen; requests without it get 401; the first run prints an explicit warning about what exposure means |
| A long backtest ties up a request and times out behind a proxy | Work runs as a job; the request returns an id immediately; progress streams over SSE and survives a page reload because state is in the database |
| A Node build step makes the Python package hard to build | Built assets are committed to the wheel at release time by the pipeline, so `pip install` needs no Node; only contributors touching the frontend need it |
| Animation and chart libraries bloat the bundle | A hard bundle budget is a CI gate, not a guideline |

## Development alignment and review readiness (0013)

Use `adapters/api/` with an app factory, `application/` services and explicit HTTP/UI exposure metadata. Keep `frontend/`; build assets into `src/sobres/adapters/api/static/`. Administrative CLI commands are absent from routes/forms. Browser-safe settings have an explicit allowlist. Local deployment tokens do not provide enterprise tenancy.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #10 at `dbdfe69ecc4783aecd848637b07cf8b16a73fa69` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge commit remains pending.
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#26](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/26).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. This plan is not yet merged.
