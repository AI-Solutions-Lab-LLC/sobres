---
change: 0005-docker-distribution
milestone: v1.2
depends_on: [0003-local-persistence, 0004-web-ui, 0000-release-engineering, 0013-template-development-alignment]
status: proposed
---

# 0005 — Docker distribution

## Outcome

One command, one image, the whole tool:

```bash
docker run -p 8787:8787 -v sobres:/data aisolutionslab/sobres serve --host 0.0.0.0
```

The CLI is the image's entrypoint, so the container runs anything the tool can do:

```bash
docker run -v sobres:/data aisolutionslab/sobres optimize markowitz --portfolio core
docker run -v sobres:/data aisolutionslab/sobres db info
```

And the CLI generates the deployment rather than the user hand-writing it:

```bash
sobres deploy compose > compose.yaml    # generated from current config
sobres deploy check                           # what would run, with what config
```

## Why

"Install Python 3.11+, then pip install, then set env vars" is a real barrier for
something whose audience includes people who want to look at a chart. An image
with the UI, API, CLI and database in it reduces that to one command.

It also makes the deployment reproducible. The interesting failure mode for this
kind of tool is a working local install and a broken server install, because
configuration drifted between them. Generating the compose file from the same
config resolution chain the CLI already uses keeps those the same thing.

## What changes

- **New capability `deployment`.**
- Multi-stage `Dockerfile`: Node builds the 0004 frontend, Python builds the
  wheel, and a slim runtime stage carries neither toolchain.
- `compose.yaml`, `.dockerignore`.
- **New CLI group `sobres deploy`** — `compose`, `check`, `env`.
- Docker Hub publishing added to 0000's release pipeline, on the same version gate,
  for `linux/amd64` and `linux/arm64`. Authentication is `docker/login-action` with
  the repository secrets `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`; the push is
  `docker/build-push-action` to `aisolutionslab/sobres`.

## The CLI is the entrypoint

`ENTRYPOINT ["sobres"]` rather than a shell or a server command. This is the decision
that keeps the image honest: there is no container-only code path, no separate
server binary, and no way for the containerized tool to diverge from the installed
one. `docker run <image> <anything the CLI accepts>` works, and `serve` is just one
of those things.

Configuration follows the same precedence chain the CLI already resolves — flag,
then environment variable, then config file, then default — so an environment
variable set in compose behaves exactly as it does in a shell.

## Non-goals

- **No Kubernetes manifests or Helm chart.** A single-user tool with a single
  SQLite file does not benefit from an orchestrator, and shipping a chart would
  imply a horizontal-scaling story that the storage model cannot support.
- No multi-replica deployment. One SQLite file means one writer.
- No bundled reverse proxy or TLS termination. The image serves HTTP; putting a
  proxy in front is the operator's choice and is documented, not vendored.
- No `latest`-only tagging. Every image is tagged with its exact version.
- No database server. Postgres remains off the roadmap, as in 0003.
- No image for the landing page. 0006 is static hosting.

## Risks

| Risk | Mitigation |
|---|---|
| The container writes the database to its own filesystem and the user loses everything on `docker rm` | `SOBRES_DB_URL` defaults to `sqlite:////data/sobres.db`; the image declares `/data` as a volume; startup fails loudly if `/data` is not writable, rather than silently persisting into the container layer |
| Root-owned files in a mounted volume become unusable from the host | The image runs as a non-root user with a fixed, documented uid/gid |
| Secrets baked into an image layer | Nothing is copied into the image but built artifacts; the build is proven secret-free by scanning the published image, and API keys arrive only as runtime environment or a mounted config |
| Image bloat from a Node toolchain and scientific wheels | Multi-stage build discards both toolchains; a size budget is a CI gate |
| A user exposes the container to the internet with no token | The image's default bind is loopback, which is useless in a container — so exposing it requires `--host 0.0.0.0`, which 0004 already gates on a token; the published docs lead with the token |
| Docker Hub and PyPI versions drift | Both publish from the same gated job on the same commit; the image tag is asserted equal to the wheel version before push |

## Development alignment and review readiness (0013)

Own `Dockerfile`, `compose.yaml`, `.dockerignore` and `docs/DEPLOYING.md`. Use the same wheel and application bootstrap, with non-root runtime and explicit state mounts. Adopt independent publication switches and exclude private context/state. This is a single-user container profile, not Cloud Run or enterprise deployment.

Follow [0013's design](../0013-template-development-alignment/design.md),
[workflow contract](../0013-template-development-alignment/specs/development-workflow/spec.md)
and [dated source/decision audit](../0013-template-development-alignment/alignment-audit.md).
The shared plan must be merged and its package migration implemented before new
work targets those locations. Keep the existing feature dependencies too.

PR #11 at `eef53608b231e826f44edee9476aa4196bc20d77` contains an older candidate
implementation. It is open and stacked, not accepted default-main behavior.
Its newer tasks/design decisions were inspected for this amendment; checked boxes
from that branch are not carried over as proof. The amended plan and actual branch
must be reconciled, reverified and reviewed before it is considered complete.
The issue is recorded below; the planning merge commit remains pending.
Publication of the tracker/plan does not authorize implementation before merge.

## GitHub tracking

Implementation tracker: [#27](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/27).
See [the readiness ledger](../0013-template-development-alignment/tracking.md)
for the planning PR and prerequisite status. This plan is not yet merged.
