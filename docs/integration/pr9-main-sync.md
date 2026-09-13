# PR #9 synchronization

Original head: `20654c1249aa7de32e3c35dbaa346c6929ef5b1b` (use the PR history for the full original ref).
Base integration: `f69e2c3`, including main `b9792d7` (PR #33) and accepted PR #8 `7f59d01`.

Preserve the current 0013/0003 plans and all reviewed optimization corrections.
Saved portfolios resolve before provider access, retain benchmark-aware loading,
and enforce the optimizer's universe and weight limits. Tests prove invalid saved
constraints fail before provider access. Persistence repositories/migrations,
registry commands, run recording and their behavioral tests remain included.

Validation: 648 non-network tests passed, four live tests excluded, 96.13% branch
coverage; Ruff lint/format, mypy, actionlint and all 14 strict OpenSpec checks passed.
Black/isort ran at 100 columns on resolved Python files. All existing main recorded
provider payloads and corrected core modules remain unchanged.

The new 0013 layout and R1/R2 acceptance remain pending under #23/#25. Updated
ancestry and passing tests do not implement that package migration or accept the
unmerged persistence feature. No direct main push or release was performed.
