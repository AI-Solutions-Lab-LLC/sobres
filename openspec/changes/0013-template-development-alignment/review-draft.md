# Review scope

Sobres predates the merged AISL template's shared development procedures and
newer context decisions. This change prepares the compatible environment/package
migration and reconciles every pending feature plan, so subsequent work follows
one contract. All new changes authored in this task are OpenSpec documents.

At the user's explicit request, this PR also includes the four foundation commits
already on local main, previously reviewed through #6/#7/#17. This is an explicit
foundation-integration plus planning exception, not a claim that the entire PR
contains only documentation. No template-alignment implementation is added.

Refs #23. Follow-up implementation trackers #24–#32; existing release issue #21.
The alignment proposal is `openspec/changes/0013-template-development-alignment/`.
Full scope, source revisions, active PR heads and exceptions are in alignment-audit.md;
commands/results are in validation.md; readiness and links are in tracking.md.

Review the package/compatibility map and template exceptions first, then the
0002–0010 amendments. The large planning diff is intentional: changing the common
layout without amending the dependent plans would preserve contradictory contracts.
The existing foundation history remains separate from the new planning commit.
Future implementation PRs use the bounded tasks and normal small-review process.

Merge does not implement 0013, enable publication or provision cloud services.
After merge, implement 0013 in task-sized PRs, then reconcile #8–#16 bottom-up.
Preserve source recordings and known review findings; old task checkboxes are not
acceptance evidence on a new base. Reverting planning restores prior documents;
reverting included foundation code requires its own compatibility/data review.
