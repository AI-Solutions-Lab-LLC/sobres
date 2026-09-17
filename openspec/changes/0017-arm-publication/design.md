# 0017 — design

## The decision

Delete the arming variables rather than flip them to `true`.

A variable set to `true` and a variable that does not exist behave identically
today. They differ tomorrow: a variable can be reset, lost in a repository
transfer, or absent on a fork, and in every one of those cases the pipeline goes
quiet and green instead of loud and red. A gate whose failure mode is silence is
not a safety feature.

The version gate is the better control because it cannot drift from reality: it
asks the index what exists and compares it to `__about__.py`. Two states, both
correct, neither dependent on repository configuration.

## Where the stop button went

Holding a release is still supported, through a mechanism that fails loudly:
required reviewers on the `pypi` GitHub environment. The publish job already
declares `environment: pypi`, so adding reviewers turns every publish into an
approval prompt with a named approver and an audit trail. A pending approval is
visible in the run; an unset variable is not.

Revoking the `PYPI_PROD` organization token is the harder stop, and the publish
job's "Check upload credential" step turns a missing token into an explicit
error rather than a skip.

## Rejected

**Set the three variables to `true` and keep the code.** Keeps the drift
problem, keeps the silent-skip failure mode, and leaves three places where the
documented behavior and the actual behavior can disagree.

**Keep `RELEASE_ENABLED` only for PyPI, since it is the irreversible one.**
Immutability is an argument for review before merge, which `main`'s protection
already provides, not for a second switch after it. The asymmetry would also make
the pipeline harder to explain: two gates for one artifact, one for the others.

**Publish from a tag instead of a version bump.** A larger change than this one,
and it moves the trigger without removing the switches. The existing
version-on-main model is working; 0000 chose it deliberately.
