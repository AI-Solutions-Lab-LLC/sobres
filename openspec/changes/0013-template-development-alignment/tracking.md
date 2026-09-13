# GitHub tracking and readiness

Ten changes have complete proposal/design/tasks/spec artifacts and pass strict
validation. Their issues track implementation after plan merge and prerequisite
completion; complete planning does not mean all ten can begin at once.

| Change | Issue | Start condition |
|---|---|---|
| [0013-template-development-alignment](../0013-template-development-alignment/proposal.md) | [#23](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/23) | This PR and the included foundation merge into default main |
| [0002-portfolio-optimization](../0002-portfolio-optimization/proposal.md) | [#24](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/24) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0003-local-persistence](../0003-local-persistence/proposal.md) | [#25](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/25) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0004-web-ui](../0004-web-ui/proposal.md) | [#26](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/26) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0005-docker-distribution](../0005-docker-distribution/proposal.md) | [#27](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/27) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0006-landing-page](../0006-landing-page/proposal.md) | [#28](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/28) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0007-equity-factor-analysis](../0007-equity-factor-analysis/proposal.md) | [#29](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/29) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0008-goal-planning](../0008-goal-planning/proposal.md) | [#30](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/30) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |
| [0009-econometrics-forecasting](../0009-econometrics-forecasting/proposal.md) | [#31](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/31) | Accept/merge the docs-only multivariable planning PR linked from #31; implemented 0013 and feature prerequisites |
| [0010-currency-and-ppp](../0010-currency-and-ppp/proposal.md) | [#32](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/32) | Merged plan, implemented 0013, and the feature prerequisites in proposal.md |

Existing release issue [#21](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/21)
is reused for 0000's unfinished token-auth/skip-reporting/activation work.
0011's pending container/site surfaces are covered by the 0005/0006 trackers.
Completed 0001/0012 do not receive duplicate implementation issues. Existing
#18/#19/#20 remain separate UX reports needing their own scoped plan revisions.

The user explicitly requested including the four existing foundation commits
from local main in the PR, so its stage is foundation integration plus planning.
The new template-alignment implementation is still deferred until plan review.

Planning/integration PR: [#33](https://github.com/AI-Solutions-Lab-LLC/sobres/pull/33) against `main`.
Merge commit: pending maintainer review and merge.

[Issue #34](https://github.com/AI-Solutions-Lab-LLC/sobres/issues/34) tracks the
CodeQL findings reported against the included foundation and the subsequent
authorized fixes; check its recorded head SHA and GitHub results for verification. It is a remediation tracker,
separate from the ten implementation-planning issues above.
