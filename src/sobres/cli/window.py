"""The default analysis window: five years ending today.

Every window-taking command accepts ``--start`` and ``--end``; ``end`` has
always defaulted to today. ``default_start`` supplies ``start`` when it is not
given, so a first command works without dates. The resolved window is recorded
in the result's provenance, which keeps a defaulted run reproducible from its
output.
"""

from __future__ import annotations

from datetime import date

DEFAULT_WINDOW_YEARS = 5


def years_before(day: date, years: int) -> date:
    """``day`` moved back ``years`` calendar years; 29 February clamps to 28 February."""
    try:
        return day.replace(year=day.year - years)
    except ValueError:  # 29 February in a target year that is not a leap year
        return day.replace(year=day.year - years, day=28)


def default_start(end: date | None) -> date:
    """Five years before ``end`` (or before today when ``end`` is None)."""
    return years_before(end or date.today(), DEFAULT_WINDOW_YEARS)
