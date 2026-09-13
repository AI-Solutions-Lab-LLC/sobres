# Design

Preserve series identifiers in shared cache code; ticker adapters own uppercase
normalization. Persist NaN as SQL NULL, retain all-missing dates, and replace
withdrawn values in refreshed intervals while preserving unrelated rows. A valid
empty calendar window is different from a nonexistent ticker.

Keep redaction in the formatter and use the declared setting to recognize secret
values held in generic key/value parameters. Never redact only the setting name.
Human-facing config output uses a constant marker for set secrets: suffix masking
exposes complete credentials of four or fewer characters. Centralize this in
`display_value` for both config commands and idempotent setup.
Use SQLite online backup to capture committed WAL state, with driver operations
confined to the adapter. Validate complete currency metadata before any fast path.

Keep optional empty prompt defaults, generate negative boolean options, propagate
init's doctor exit status, and repair config permissions on idempotent setup.
Make the Yahoo client a base runtime dependency and verify the built artifact.

Verification includes real prompt input, known factor values through cold/warm
cache, null revisions, weekend tails, backup restoration with an open writer,
secret-valued commands through log sinks, and actual CLI exit status. Existing
fixtures remain labelled synthetic; these regressions do not validate their market
values except for the explicitly documented known-answer factor row.
