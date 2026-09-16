"""One forward-only migration set, applied by the adapter, no branching on backend.

Lives under ``adapters/`` because it is expressed through SQLAlchemy Core, the
dialect layer that must never be imported above the port.

A migration is never edited after release; a correction is a new migration.
Each step receives a SQLAlchemy Core connection and creates or alters tables
through the shared ``schema`` metadata, so it runs unchanged on every backend.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sobres.data.storage.adapters import schema


@dataclass(frozen=True)
class Migration:
    version: int
    name: str
    apply: Callable[[Any], None]


def _v1_initial(conn: Any) -> None:
    schema.metadata.create_all(
        conn,
        tables=[
            schema.schema_version,
            schema.observation,
            schema.fetch_log,
            schema.series_meta,
            schema.kv,
        ],
    )


def _v2_application_state(conn: Any) -> None:
    """0003: saved portfolios, watchlists, goals, run history and job records."""
    schema.metadata.create_all(
        conn,
        tables=[schema.portfolio, schema.watchlist, schema.goal, schema.run, schema.job],
    )


def _v3_trading_records(conn: Any) -> None:
    """0016: trade intents, orders and fills behind the broker port."""
    schema.metadata.create_all(
        conn, tables=[schema.trade_intent, schema.trade_order, schema.trade_fill]
    )


MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "initial-cache-and-kv", _v1_initial),
    Migration(2, "application-state", _v2_application_state),
    Migration(3, "trading-records", _v3_trading_records),
)

CURRENT_VERSION = MIGRATIONS[-1].version
