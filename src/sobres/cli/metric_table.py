"""Human risk panels: per-row units; JSON and CSV retain numeric decimals."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

from rich.table import Table

PERCENT_METRICS = {
    "annualized_return",
    "arithmetic_return",
    "volatility",
    "max_drawdown",
    "var_95",
    "cvar_95",
    "risk_free",
}


def render_metric_table(console: Any, rows: list[dict[str, Any]], columns: Sequence[str]) -> None:
    table = Table(show_header=True)
    for column in [*columns, "unit"]:
        table.add_column(column)
    for row in rows:
        metric = str(row["metric"])
        unit = "percent" if metric in PERCENT_METRICS else "unitless"
        if metric in ("var_95", "cvar_95"):
            unit = "percent per observation; loss negative"
        elif metric == "n_obs":
            unit = "observations"
        elif metric.startswith("drawdown_"):
            unit = "date; initial capital if peak is blank"
        cells = [metric]
        for column in columns[1:]:
            value = row[column]
            if value is None or (isinstance(value, float) and not math.isfinite(value)):
                cells.append("—")
            elif isinstance(value, float):
                cells.append(f"{value:.2%}" if metric in PERCENT_METRICS else f"{value:.2f}")
            else:
                cells.append(str(value))
        table.add_row(*cells, unit)
    console.print(table)
