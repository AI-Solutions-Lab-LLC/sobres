---
name: openspec-pr-review
description: Review a pull request against its OpenSpec and intended user outcome, question the spec before judging implementation, reproduce behavior in an isolated checkout, and deliver prioritized findings plus hands-on testing instructions. Use for requested PR reviews, especially in spec-driven repositories.
---

# OpenSpec pull request review

Deliver an evidence-backed merge recommendation, a spec assessment, and a reproducible user test plan. Read the repository's `AGENTS.md` and its review conventions first.

## Establish the review target

- Resolve the repository, PR number, state, current head SHA, base SHA, and merge base. For “first PR,” distinguish the oldest open PR from historical PR #1; state the interpretation or clarify if it changes the work.
- Read the PR body, complete changed-file list, existing reviews, unresolved discussions, CI outcomes, and linked issues/specs. Paginate APIs rather than trusting a truncated file list.
- For stacked PRs, compare against the actual base branch and record upstream dependencies. Check whether the base's tree differs from the current merge destination. Do not blame inherited problems on this diff; still report inherited issues that prevent the claimed outcome.
- Keep the user's working tree intact. Clone or use an isolated detached worktree at the exact head. Recheck the remote head before delivering findings; disclose any later commits not reviewed.

## Review the contract before the implementation

Most behavior-changing PRs should have an OpenSpec change. Find the change under `openspec/changes/`, including archive entries, and read proposal, design, tasks, spec deltas, project conventions, and relevant accepted specs under `openspec/specs/` from both base and head.

If none exists, identify the missing contract and reconstruct provisional acceptance criteria from the PR/issue. Continue reviewing; do not invent an approved spec. A narrow documentation, maintenance, dependency, or mechanical change can have a justified exception. Judge the actual impact, not its title.

Ask whether the spec itself describes the right outcome: is it coherent, testable, appropriately scoped, compatible with other specs, and realistic for a new user? Identify contradictions, missing failure cases, ambiguous units/calendars, impossible invariants, and misleading completion status early. Separate:

1. Implementation defects against a sound requirement.
2. Spec defects or decisions requiring a contract update.
3. Deferred scope and justified exceptions.

Do not weaken a requirement merely to match broken code. Explain proposed spec amendments and preserve the intended outcome. Run the installed OpenSpec validator, record its version and results, and distinguish inherited validation failures from new ones.

Build a traceability matrix connecting requirement/scenario, implementation path, meaningful test assertion, independently observed result, and any gap. A scenario name in a test comment is a reference, not proof. A checked task or green coverage percentage is not proof either. Mark evidence as verified, contradicted, reference-only, deferred, or untested.

## Exercise the actual product

- Read install/build instructions and CI before executing. Install the head in a fresh environment. If packaging changes or installation is part of the promise, build wheel/sdist and smoke-test the base artifact separately from an editable development install; extras can hide missing runtime dependencies.
- Use explicit temporary config/data paths and dummy credentials. Do not overwrite the user's existing config, caches, fixture corpus, or source changes. Separate fixture-backed storage from live-provider storage.
- Run required checks, then reproduce the documented happy path through the actual CLI, UI, or API. Exercise real terminal prompts when interactivity matters. Check return values and units, stdout/stderr, exit codes, persisted state, restart behavior, and repeated runs.
- Choose additional probes from the changed boundaries: cold/warm cache equality, missing rows and range extensions, empty/error inputs, precedence, unsupported dependencies, date edges, partial failure and rollback, migration backups, secrets on success/error paths, or concurrent access. Compare with independent known answers and the base when applicable.
- Existing tests may replace the very integration that is broken. Inspect fixture provenance, monkeypatches, filtered fields, mocks, and the assertions. Test beyond sample-command lists when parameters change behavior.
- For external providers, run authorized, bounded read-only live checks where feasible. Shape-only tests do not prove the full provider → cache → renderer path. Record skips, credentials unavailable, outages, and environment failures accurately; never turn “untested” into “passes.” Re-recorded fixtures require their own deliberate diff.
- Keep durable minimal reproductions when they materially help the author fix the problem. Follow the repository's formatting rules for every Python file edited. Do not repair PR implementation during a review unless requested.

## Report and communicate

Lead with approve / request changes / blocked and the reviewed SHA. Order actionable findings by severity. Each finding needs a concise title, PR-head file and narrow line range, trigger, expected versus observed behavior, user impact, spec scenario when present, and suggested fix plus regression test. Cite changed lines where possible and label inherited issues separately. Avoid speculative bugs, stylistic preferences, duplicate symptoms, and severity inflation.

Include a separate spec assessment, the traceability matrix, check outcomes with platform/tool versions, and material limits of verification. Provide copy-paste user testing steps with setup, exact revision, safe test state, commands/actions, expected output and exit codes, known current failures, and useful workarounds. Identify synthetic data as synthetic.

Prepare an exact draft PR review with inline-comment locations and the recommendation. Publishing comments, submitting a GitHub review, merging, or changing the PR requires session authorization for that action. If authorized, recheck head and existing comments, post once against the reviewed commit, and report the link; otherwise leave a local draft and deliver the full report to the user. Reviewing alone never implies a merge or production operation.
