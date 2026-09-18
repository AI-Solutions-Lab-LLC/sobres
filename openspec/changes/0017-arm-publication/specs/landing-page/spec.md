# landing-page. spec delta (0017)

## MODIFIED Requirements

### Requirement: Published automatically on merge

The landing page SHALL deploy from `main` with no additional configuration step.
Deployment SHALL be gated on the build and its audits, and on nothing else.

#### Scenario: Published automatically
- **WHEN** a commit lands on `main` that changes `site/`
- **THEN** GitHub Actions SHALL build, verify and deploy only the site output to
  GitHub Pages
- **AND** no repository variable SHALL be required to enable the upload
- **AND** the deploy job SHALL hold `pages: write` and `id-token: write` while the
  workflow default remains `contents: read`, per 0000's least-privilege rule

#### Scenario: Pull requests build but do not deploy
- **WHEN** the change arrives as a pull request
- **THEN** the build and the Lighthouse audit SHALL run
- **AND** nothing SHALL be uploaded

#### Scenario: Broken builds do not deploy
- **WHEN** the site build, its content checks, or the Lighthouse audit fail
- **THEN** nothing SHALL be deployed and the previous version SHALL remain live
