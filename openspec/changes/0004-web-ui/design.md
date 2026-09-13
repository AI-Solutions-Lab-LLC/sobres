# 0004 — Design

## The registry, one level down

0001 declares every command once and generates the CLI from it. This change adds
two more consumers of the same declarations:

```
                    registry.py
                         │
        ┌────────────────┼──────────────────┐
        ▼                ▼                  ▼
   adapters/cli/    adapters/api/     frontend/ (React)
   options from     routes from        forms from
   param model      param model        OpenAPI schema
        │                │                  │
        └────────────────┴──────────────────┘
                         │
                 same application service, same validated result
```

A command is `Command(name, help, params: type[BaseModel], result: type,
handler, http_exposed=False, ui_exposed=False)`. From explicitly enabled entries:

| Surface | Generated | Mechanism |
|---|---|---|
| CLI | `sobres <group> <name> --field ...` | Typer options from `params.model_fields` |
| API | `POST /api/v1/<group>/<name>` | FastAPI route with `params` as the body model |
| OpenAPI | schema entry | FastAPI, for free |
| UI | form + result view | TypeScript types generated from OpenAPI; a form renderer keyed on field type |

**Why POST for everything, including reads.** Parameter models carry ticker
lists, date ranges, and weight vectors; encoding those in query strings would
mean a second serialization the CLI does not have. One body model, one
validation path, one set of error messages. The UI is behind a token, not a
public REST API, so resource-style verbs buy nothing here.

**Why the UI's types come from OpenAPI rather than being hand-written.** The
generated client is committed; CI regenerates it and fails on a diff. An API
change that would break the UI therefore breaks the build, not the user.

## Parity as a test

```python
@pytest.mark.parametrize("command", registry.http_exposed())
def test_every_exposed_command_has_a_route(command, app): ...

@pytest.mark.parametrize("command", registry.http_exposed())
def test_every_exposed_command_has_a_view(command, frontend_manifest): ...
```

The frontend build emits a manifest of which registry names it renders a view
for. The second test reads it. Adding an exposed command without a view fails Python CI. A separate test
asserts excluded commands have no route, OpenAPI entry or actionable view.

## Long-running work

Optimizations and backtests can run for seconds to minutes. The rule is that no
HTTP request waits on a computation.

```
POST /api/v1/optimize/backtest   →  202 { job_id }        (< 200 ms)
GET  /api/v1/jobs/{id}           →  { state, progress, result? }
GET  /api/v1/jobs/{id}/events    →  text/event-stream
POST /api/v1/jobs/{id}/cancel
```

The job record lives in 0003's `jobs` repository, so it survives a server
restart and a page reload. A single in-process worker drains a queue; the
process is single-user, so one worker is the right number but still requires transaction, cancellation and crash-recovery tests. It is
not a durable multi-replica hosted worker.

**Progress comes from the core function's optional callback** (0001
observability design), which the job runner turns into an event and a row
update. `core/` still emits nothing itself.

SSE over websockets: one direction is all that is needed, it works through every
proxy, and reconnection is a browser primitive rather than a protocol to write.

## `sobres open`: terminal to browser in one command

```
sobres open [target]
   │
   ├─ server answering on the port and it is ours?  → launch browser, exit 0
   ├─ something else on the port?                    → error, suggest --port
   └─ nothing?                                       → serve on loopback
                                                        wait for /health
                                                        launch browser
                                                        run until Ctrl-C
```

Launching goes through Python's `webbrowser` module, which honors `BROWSER`
and knows each platform's opener. Its failure is the signal for headless:
no display, an SSH session, or the container all end the same way — the URL is
printed and the command exits 0. The URL is printed *before* the launch attempt
in every case, so a user whose browser opens on the wrong monitor still has
it. Printing a URL is never an error; the command's job is to get the user to
the app, and the URL is the app.

Targets map to the frontend view manifest — the same file the parity test
reads — so `sobres open` can reach exactly the views that exist and rejects
others with the list. `sobres init --web` is `sobres open settings`; `sobres serve --open`
is `sobres serve` plus the launch. One mechanism, three entry points.

## Access model

| Bind address | Token |
|---|---|
| loopback (default) | not required — the socket is unreachable remotely |
| anything else | required; generated if absent; printed once with a warning |

Tokens are 32 random bytes, base64url, stored as a salted hash, compared in
constant time. Presented as a bearer header by the CLI and the generated client,
and set as an httpOnly cookie by the SPA after a one-time paste — never in a
query string, where proxies and browser history would keep it.

There is deliberately no login page in the sense of a username field. The token
authenticates *the deployment*. Multi-user is out of scope, and a fake account
model would be the first thing a later multi-user change had to remove.

## Frontend

```
frontend/
├── src/
│   ├── api/           # generated client + types; regenerated in CI
│   ├── forms/         # one renderer per field type, keyed off the schema
│   ├── views/         # one per registry group; results + charts
│   ├── charts/        # ECharts wrappers with theme tokens
│   └── theme/         # tokens shared with site/ (0006)
└── manifest.json      # registry names this build renders — read by the parity test
```

Built assets are copied into the wheel at `sobres/adapters/api/static/` by the
release pipeline. `pip install sobres[web]` therefore needs no Node; only
a contributor changing `frontend/` does.

**The equivalent command is always shown.** Every form renders the `sobres` command
line it would run, live. The UI is a way of learning the CLI, not a replacement
for it — and it keeps the two surfaces honest with each other in the user's eyes,
not just in the test suite.

## Alternatives considered

| Choice | Rejected alternative | Why |
|---|---|---|
| Registry from 0001 | Hand-written Typer commands, registry added in 0004 | Would mean rewriting every command here; adding surfaces to declarations is cheap, retrofitting declarations onto surfaces is not |
| POST for every command | REST resources | One body model matches the CLI's one parameter model; no second serialization |
| Generated TypeScript client | Hand-written API types | Drift becomes a build failure instead of a runtime one |
| Single in-process worker | Worker pool, Celery, RQ | Single-user scope; concurrency and restart behavior still require explicit tests |
| SSE | WebSockets | One direction suffices; proxies and reconnection are solved problems |
| Deployment token | User accounts | Multi-user is out of scope; a fake account model is debt |
| `sobres open` targets from the view manifest | A hand-maintained target list | The manifest already exists for parity; a second list would drift from it |
| Headless prints the URL and exits 0 | Error when no browser | The URL *is* the app; failing to launch a browser is not failing the user |
| Frontend manifest for parity | Trusting the view list | Parity must fail Python CI, where the registry is |

## Alignment amendment (0013)

Use `adapters/api/` with an app factory, `application/` services and explicit HTTP/UI exposure metadata. Keep `frontend/`; build assets into `src/sobres/adapters/api/static/`. Administrative CLI commands are absent from routes/forms. Browser-safe settings have an explicit allowlist. Local deployment tokens do not provide enterprise tenancy.

The [common package map](../0013-template-development-alignment/design.md) is authoritative
for future locations. This amendment does not accept proposed cloud profiles.
Use named task proofs, installed-artifact checks and explicit rollback: revert
application wiring with compatibility facades intact; never rewrite a released
schema migration or delete user state to roll back a module move.
