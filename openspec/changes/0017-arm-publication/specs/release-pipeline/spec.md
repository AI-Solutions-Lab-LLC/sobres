# release-pipeline. spec delta (0017)

## REMOVED Requirements

### Requirement: Publishing is armed explicitly

**Reason**: The arming switch existed so that merging the pipeline could not fire
a publish before upload credentials were configured. The credentials now exist as
organization secrets and the pipeline has been merged, so the switch only adds a
failure mode where a release silently does nothing and reports success.

**Migration**: Delete the `RELEASE_ENABLED` and `DOCKER_RELEASE_ENABLED`
repository variables. Publishing is governed by the version gate alone. To hold a
release for a human, add required reviewers to the `pypi` environment.

## ADDED Requirements

### Requirement: The declared version is the only publication gate

Publication to PyPI and to Docker Hub SHALL be decided by the version in
`src/sobres/__about__.py` against the target index, and by nothing else. No
repository variable SHALL be able to suppress a publish.

#### Scenario: A version bump publishes
- **WHEN** a push to `main` declares a version the target index does not have
- **THEN** the pipeline SHALL verify, build and publish it
- **AND** SHALL do so whether or not any `*_ENABLED` variable is set

#### Scenario: No silent no-op
- **WHEN** the release workflow completes without publishing
- **THEN** the reported reason SHALL be `already-published`
- **AND** `disabled` SHALL NOT be a reachable outcome

#### Scenario: The container image rides the same gate
- **WHEN** a version is published to PyPI
- **THEN** the container image SHALL be built from that exact wheel and pushed
- **AND** SHALL be gated only on that publish succeeding and on its own scans

### Requirement: A release can be held by a reviewer, not by a variable

The pipeline SHALL support holding a publish for human approval through the
`pypi` GitHub environment, so that a hold is visible in the run.

#### Scenario: Required reviewers hold a publish
- **WHEN** the `pypi` environment has required reviewers configured
- **THEN** the publish job SHALL wait for an approval before uploading
- **AND** the pending approval SHALL be visible on the workflow run

#### Scenario: A missing credential fails loudly
- **WHEN** the upload secret for the target index is unavailable
- **THEN** the publish job SHALL fail with an explicit error
- **AND** SHALL NOT be skipped or reported as a successful no-op
