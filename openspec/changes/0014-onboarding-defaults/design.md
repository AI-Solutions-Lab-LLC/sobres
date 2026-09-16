# Design

## Settings tiering

`Setting` gains `advanced: bool = False`. The wizard's loop skips
`setting.advanced` unless `InitParams.advanced` is set or the key was given
with `--set`. Skipped settings are neither prompted nor written, so existing
values survive a re-run byte-for-byte (the idempotence scenario still holds).
One line at the end of the walk says how many were skipped and how to reach
them, so nothing is hidden.

Rejected: a hard-coded list of "essential" keys in `init.py`. The registry is
the one declaration; a second list drifts.

## Default window

`sobres.cli.window.default_start(end)` returns five years before `end`
(or before today when `end` is None), clamping 29 February to 28 February.
Parameter models declare `start: date = Field(default=None, ...)` and fill it
in an `after` validator, so the annotation stays `date` for the 28 call sites
and the CLI, API and UI generators see an optional field. The window's
ordering check still runs after the fill.

Rejected: a fixed calendar date such as `2015-01-01`. It is reproducible but
ages badly and means something different for every command. Rejected:
`default_factory`, which cannot see `end`.

## Examples in the declaration

`Command.example` and `register(example=...)`. `validate_params` prefixes the
hint with `try: sobres <example>` when one is declared and keeps the `--help`
pointer. The example is free text so it can carry real tickers and dates; the
invariant test only requires that it exists for commands with required fields
and starts with the command's own CLI name.
