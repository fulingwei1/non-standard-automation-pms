#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archive and retire legacy approval tables.

This script is intentionally conservative: importing it does nothing, and the
CLI defaults to archive-only mode. Use --drop-legacy-tables only after reviewing
the archive row counts and taking a database backup.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LEGACY_APPROVAL_TABLES = (
    "approval_history",
    "approval_records",
    "approval_workflow_steps",
    "approval_workflows",
    "contract_approvals",
    "invoice_approvals",
    "quotation_approvals",
    "quote_approvals",
    "quote_cost_approvals",
    "role_assignment_approvals",
    "task_approval_workflows",
)


TABLE_MAPPINGS: dict[str, dict[str, str]] = {
    "approval_history": {
        "entity_type": "APPROVAL_RECORD",
        "entity_id_column": "approval_record_id",
        "status_column": "action",
        "action_column": "action",
        "approver_column": "approver_id",
    },
    "approval_records": {
        "entity_type_column": "entity_type",
        "entity_id_column": "entity_id",
        "status_column": "status",
        "approver_column": "initiator_id",
    },
    "approval_workflow_steps": {
        "entity_type": "APPROVAL_WORKFLOW_STEP",
        "entity_id_column": "workflow_id",
        "status_column": "is_required",
        "approver_column": "approver_id",
    },
    "approval_workflows": {
        "entity_type": "APPROVAL_WORKFLOW",
        "entity_id_column": "id",
        "status_column": "is_active",
    },
    "contract_approvals": {
        "entity_type": "CONTRACT",
        "entity_id_column": "contract_id",
        "status_column": "approval_status",
        "approver_column": "approver_id",
    },
    "invoice_approvals": {
        "entity_type": "INVOICE",
        "entity_id_column": "invoice_id",
        "status_column": "status",
        "action_column": "approval_result",
        "approver_column": "approver_id",
    },
    "quotation_approvals": {
        "entity_type": "PRESALE_AI_QUOTATION",
        "entity_id_column": "quotation_id",
        "status_column": "status",
        "approver_column": "approver_id",
    },
    "quote_approvals": {
        "entity_type": "QUOTE",
        "entity_id_column": "quote_id",
        "status_column": "status",
        "action_column": "approval_result",
        "approver_column": "approver_id",
    },
    "quote_cost_approvals": {
        "entity_type": "QUOTE",
        "entity_id_column": "quote_id",
        "status_column": "approval_status",
        "approver_column": "current_approver_id",
    },
    "role_assignment_approvals": {
        "entity_type": "ROLE_ASSIGNMENT",
        "entity_id_column": "id",
        "status_column": "status",
        "approver_column": "approver_id",
    },
    "task_approval_workflows": {
        "entity_type": "TASK",
        "entity_id_column": "task_id",
        "status_column": "approval_status",
        "approver_column": "approver_id",
    },
}


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")')}


def _read_value(row: sqlite3.Row, columns: set[str], column_name: str | None) -> Any:
    if not column_name or column_name not in columns:
        return None
    return row[column_name]


def _json_default(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _create_archive_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS legacy_approval_archives (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            source_id INTEGER,
            entity_type TEXT,
            entity_id INTEGER,
            status TEXT,
            action TEXT,
            approver_id INTEGER,
            approval_level INTEGER,
            tenant_id INTEGER,
            created_at TEXT,
            updated_at TEXT,
            snapshot_json TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            UNIQUE(source_table, source_id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_legacy_approval_archives_source
        ON legacy_approval_archives(source_table, source_id)
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_legacy_approval_archives_entity
        ON legacy_approval_archives(entity_type, entity_id)
        """
    )


def _archive_table(conn: sqlite3.Connection, table_name: str) -> int:
    columns = _table_columns(conn, table_name)
    mapping = TABLE_MAPPINGS[table_name]
    rows = conn.execute(f'SELECT rowid AS __rowid__, * FROM "{table_name}" ORDER BY rowid').fetchall()
    archived_at = datetime.now(timezone.utc).isoformat()
    inserted = 0

    for row in rows:
        row_dict = {column: row[column] for column in columns}
        source_id = row_dict.get("id", row["__rowid__"])
        entity_type = mapping.get("entity_type")
        entity_type_column = mapping.get("entity_type_column")
        if entity_type_column in columns:
            entity_type = row[entity_type_column]

        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO legacy_approval_archives (
                source_table,
                source_id,
                entity_type,
                entity_id,
                status,
                action,
                approver_id,
                approval_level,
                tenant_id,
                created_at,
                updated_at,
                snapshot_json,
                archived_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                table_name,
                source_id,
                entity_type,
                _read_value(row, columns, mapping.get("entity_id_column")),
                str(_read_value(row, columns, mapping.get("status_column"))),
                _read_value(row, columns, mapping.get("action_column")),
                _read_value(row, columns, mapping.get("approver_column")),
                _read_value(row, columns, "approval_level"),
                _read_value(row, columns, "tenant_id"),
                _read_value(row, columns, "created_at"),
                _read_value(row, columns, "updated_at"),
                json.dumps(row_dict, ensure_ascii=False, default=_json_default, sort_keys=True),
                archived_at,
            ),
        )
        inserted += max(cursor.rowcount, 0)

    return inserted


def consolidate_legacy_approval_tables(
    conn: sqlite3.Connection,
    *,
    drop_legacy_tables: bool = False,
) -> dict[str, Any]:
    """Archive legacy approval rows and optionally drop their source tables."""

    conn.row_factory = sqlite3.Row
    _create_archive_table(conn)

    existing_tables = [
        table_name
        for table_name in LEGACY_APPROVAL_TABLES
        if _table_exists(conn, table_name)
    ]
    archived_rows = 0
    dropped_tables: list[str] = []

    original_foreign_keys = conn.execute("PRAGMA foreign_keys").fetchone()[0]
    try:
        if drop_legacy_tables:
            conn.execute("PRAGMA foreign_keys = OFF")

        for table_name in existing_tables:
            archived_rows += _archive_table(conn, table_name)

        if drop_legacy_tables:
            for table_name in sorted(existing_tables):
                conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                dropped_tables.append(table_name)

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.execute(f"PRAGMA foreign_keys = {int(bool(original_foreign_keys))}")

    return {
        "archive_table": "legacy_approval_archives",
        "archived_rows": archived_rows,
        "dropped_tables": dropped_tables,
        "existing_tables": existing_tables,
        "skipped_tables": [
            table_name
            for table_name in LEGACY_APPROVAL_TABLES
            if table_name not in existing_tables
        ],
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("database", type=Path, help="SQLite database path")
    parser.add_argument(
        "--drop-legacy-tables",
        action="store_true",
        help="Drop legacy tables after archiving them",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if not args.database.exists():
        raise SystemExit(f"database not found: {args.database}")

    with sqlite3.connect(args.database) as conn:
        report = consolidate_legacy_approval_tables(
            conn,
            drop_legacy_tables=args.drop_legacy_tables,
        )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
