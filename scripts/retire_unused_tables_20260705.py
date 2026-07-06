#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Archive and drop confirmed unused/generated-residue tables.

The CLI is conservative: it archives schemas and rows into a separate SQLite
file first. It drops tables only when --drop-tables is passed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


RETIRABLE_TABLES = (
    "lead_requirement_facility_v2",
    "lead_requirement_technical_v2",
    "lead_requirement_basic_v2",
    "funding_records",
    "equity_structures",
    "funding_usages",
    "funding_rounds",
    "investors",
    "department_default_roles",
    "department_role_admins",
    "role_template_permissions",
    "role_audits",
    "currency_rates",
    "currency_history",
    "ecn_records",
    "ecn_approvals",
    "ecn_approval_matrix",
    "shortage_alerts",
    "mat_shortage_alert",
    "quote_cost_histories",
    "quotation_templates",
    "after_sales_support_tickets",
    "change_approval_records",
    "timesheet_approval_log",
    "presale_solution_templates",
    "role_exclusions",
    "user_role_assignments",
    "legacy_approval_archives",
    "tasks_deprecated",
    "task_id_map",
    "solution_versions",
    "role_data_scopes",
    "data_scope_rules",
    "target_breakdown_logs",
    "sales_targets_v2",
    "role_permissions",
    "permissions",
)

RETIRABLE_VIEWS = (
    "v_user_active_roles",
)

AFTER_SALES_TICKET_DEPENDENT_TABLES = (
    "after_sales_satisfaction",
    "after_sales_sla",
    "after_sales_field_services",
)

SALES_TARGET_V2_METRICS = (
    ("sales_target", "CONTRACT_AMOUNT"),
    ("payment_target", "COLLECTION_AMOUNT"),
    ("lead_target", "LEAD_COUNT"),
    ("opportunity_target", "OPPORTUNITY_COUNT"),
)

SALES_TARGET_V2_REQUIRED_COLUMNS = {
    "id",
    "tenant_id",
    "target_year",
    "target_month",
    "target_quarter",
    "target_type",
    "team_id",
    "user_id",
    "sales_target",
    "payment_target",
    "lead_target",
    "opportunity_target",
    "description",
    "created_by",
    "created_at",
    "updated_at",
}

LEGACY_PERMISSION_REQUIRED_COLUMNS = {
    "id",
    "perm_code",
    "perm_name",
    "module",
    "action",
    "resource",
    "description",
    "is_active",
    "created_at",
    "updated_at",
    "permission_type",
    "group_id",
}

LEGACY_ROLE_PERMISSION_REQUIRED_COLUMNS = {
    "id",
    "role_id",
    "permission_id",
}

PRESALE_AI_TEMPLATE_REQUIRED_COLUMNS = {
    "id",
    "name",
    "code",
    "industry",
    "equipment_type",
    "complexity_level",
    "solution_content",
    "architecture_diagram",
    "bom_template",
    "technical_specs",
    "equipment_list",
    "usage_count",
    "typical_cost_range_min",
    "typical_cost_range_max",
    "tags",
    "keywords",
    "is_active",
    "created_by",
    "created_at",
    "updated_at",
    "tenant_id",
}

LEGACY_PERMISSION_MERGE_REPORT = {
    "source_permissions": 0,
    "source_role_permissions": 0,
    "assigned_permissions": 0,
    "unassigned_permissions": 0,
    "existing_api_permissions": 0,
    "inserted_api_permissions": 0,
    "inserted_role_api_permissions": 0,
    "duplicate_role_api_permissions": 0,
    "skipped_role_permissions": 0,
    "cache_revisions_bumped": 0,
}

PRESALE_AI_TEMPLATE_MERGE_REPORT = {
    "source_rows": 0,
    "inserted_templates": 0,
    "updated_existing_templates": 0,
    "duplicate_templates": 0,
    "skipped_templates": 0,
}

PROJECT_CHANGE_APPROVAL_ENTITY_TYPE = "PROJECT_CHANGE_REQUEST"
PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES = (
    "TPL_PROJECT_CHANGE",
    "PROJECT_CHANGE_REQUEST",
    "TPL_PROJECT",
)
PROJECT_CHANGE_APPROVAL_ACTION_BY_DECISION = {
    "APPROVED": "APPROVE",
    "REJECTED": "REJECT",
    "RETURNED": "RETURN",
}
PROJECT_CHANGE_APPROVAL_STATUS_BY_DECISION = {
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "RETURNED": "PENDING",
}
PROJECT_CHANGE_APPROVAL_ACTION_BY_STATUS = {
    "APPROVED": "APPROVE",
    "COMPLETED": "APPROVE",
    "IMPLEMENTING": "APPROVE",
    "VERIFYING": "APPROVE",
    "CLOSED": "APPROVE",
    "REJECTED": "REJECT",
    "ASSESSING": "RETURN",
}
PROJECT_CHANGE_APPROVAL_STATUS_BY_ACTION = {
    "APPROVE": "APPROVED",
    "REJECT": "REJECTED",
    "RETURN": "PENDING",
    "COMMENT": "PENDING",
}
CHANGE_APPROVAL_RECORD_REQUIRED_COLUMNS = {
    "id",
    "change_request_id",
    "approver_id",
    "approval_date",
    "decision",
    "comments",
    "attachments",
    "created_at",
    "updated_at",
}

TIMESHEET_APPROVAL_ENTITY_TYPE = "TIMESHEET"
TIMESHEET_APPROVAL_TEMPLATE_CODES = (
    "TIMESHEET_APPROVAL",
    "TPL_TIMESHEET",
    "TIMESHEET",
)
TIMESHEET_APPROVAL_ACTION_ALIASES = {
    "APPROVE": "APPROVE",
    "APPROVED": "APPROVE",
    "PASS": "APPROVE",
    "PASSED": "APPROVE",
    "REJECT": "REJECT",
    "REJECTED": "REJECT",
    "RETURN": "RETURN",
    "RETURNED": "RETURN",
    "SUBMIT": "SUBMIT",
    "SUBMITTED": "SUBMIT",
    "WITHDRAW": "WITHDRAW",
    "WITHDRAWN": "WITHDRAW",
    "CANCEL": "CANCEL",
    "CANCELLED": "CANCEL",
}
TIMESHEET_APPROVAL_STATUS_BY_ACTION = {
    "APPROVE": "APPROVED",
    "REJECT": "REJECTED",
    "RETURN": "PENDING",
    "SUBMIT": "PENDING",
    "WITHDRAW": "CANCELLED",
    "CANCEL": "CANCELLED",
    "COMMENT": "PENDING",
}
TIMESHEET_APPROVAL_STATUS_BY_TIMESHEET_STATUS = {
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "SUBMITTED": "PENDING",
    "PENDING": "PENDING",
    "DRAFT": "DRAFT",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
}
TIMESHEET_APPROVAL_LOG_REQUIRED_COLUMNS = {
    "id",
    "tenant_id",
    "timesheet_id",
    "batch_id",
    "approver_id",
    "approver_name",
    "action",
    "comment",
    "approved_at",
    "created_at",
    "updated_at",
}
TIMESHEET_REQUIRED_COLUMNS_FOR_APPROVAL_MIGRATION = {
    "id",
    "tenant_id",
    "timesheet_no",
    "user_id",
    "user_name",
    "work_date",
    "hours",
    "project_id",
    "project_name",
    "submit_time",
    "approve_time",
    "status",
}

ECN_APPROVAL_ENTITY_TYPE = "ECN"
ECN_APPROVAL_TEMPLATE_CODES = (
    "ECN_STANDARD",
    "TPL_ECN",
    "ECN",
)
ECN_APPROVAL_ACTION_BY_RESULT = {
    "APPROVED": "APPROVE",
    "APPROVE": "APPROVE",
    "PASSED": "APPROVE",
    "PASS": "APPROVE",
    "REJECTED": "REJECT",
    "REJECT": "REJECT",
    "RETURNED": "RETURN",
    "RETURN": "RETURN",
    "WITHDRAWN": "WITHDRAW",
    "WITHDRAW": "WITHDRAW",
    "CANCELLED": "CANCEL",
    "CANCELED": "CANCEL",
    "CANCEL": "CANCEL",
}
ECN_APPROVAL_STATUS_BY_ACTION = {
    "APPROVE": "APPROVED",
    "REJECT": "REJECTED",
    "RETURN": "PENDING",
    "WITHDRAW": "CANCELLED",
    "CANCEL": "CANCELLED",
    "COMMENT": "PENDING",
}
ECN_APPROVAL_STATUS_BY_ECN_STATUS = {
    "APPROVED": "APPROVED",
    "REJECTED": "REJECTED",
    "APPROVING": "PENDING",
    "EVALUATED": "PENDING",
    "EVALUATING": "PENDING",
    "SUBMITTED": "PENDING",
    "DRAFT": "DRAFT",
    "CANCELLED": "CANCELLED",
    "CANCELED": "CANCELLED",
    "EXECUTING": "APPROVED",
    "EXECUTED": "APPROVED",
    "CLOSED": "APPROVED",
}
ECN_APPROVAL_REQUIRED_COLUMNS = {
    "id",
    "tenant_id",
    "ecn_id",
    "approval_level",
    "approval_role",
    "approver_id",
    "approver_name",
    "approval_result",
    "approval_opinion",
    "status",
    "approved_at",
    "due_date",
    "is_overdue",
    "created_at",
    "updated_at",
}
ECN_REQUIRED_COLUMNS_FOR_APPROVAL_MIGRATION = {
    "id",
    "tenant_id",
    "ecn_no",
    "ecn_title",
    "ecn_type",
    "project_id",
    "applicant_id",
    "applicant_name",
    "applied_at",
    "status",
}


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        is not None
    )


def _view_exists(conn: sqlite3.Connection, view_name: str) -> bool:
    return (
        conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='view' AND name=?",
            (view_name,),
        ).fetchone()
        is not None
    )


def _all_tables(conn: sqlite3.Connection) -> set[str]:
    return {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }


def _unsafe_incoming_fks(conn: sqlite3.Connection, drop_tables: set[str]) -> list[str]:
    unsafe: list[str] = []
    for table_name in sorted(_all_tables(conn) - drop_tables):
        for fk in conn.execute(f'PRAGMA foreign_key_list("{table_name}")'):
            parent_table = fk[2]
            if parent_table in drop_tables:
                if (
                    parent_table == "after_sales_support_tickets"
                    and table_name in AFTER_SALES_TICKET_DEPENDENT_TABLES
                ):
                    continue
                unsafe.append(f"{table_name}.{fk[3]} -> {parent_table}.{fk[4]}")
    return unsafe


def _table_row_count(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f'SELECT COUNT(*) FROM "{table_name}"').fetchone()[0])


def _replace_after_sales_ticket_reference(schema_sql: str) -> str:
    replacements = (
        ("REFERENCES after_sales_support_tickets (id)", "REFERENCES service_tickets (id)"),
        ("REFERENCES after_sales_support_tickets(id)", "REFERENCES service_tickets(id)"),
        ('REFERENCES "after_sales_support_tickets" (id)', 'REFERENCES service_tickets (id)'),
        ('REFERENCES "after_sales_support_tickets"(id)', 'REFERENCES service_tickets(id)'),
    )
    updated = schema_sql
    for old, new in replacements:
        updated = updated.replace(old, new)
    return updated


def _rebuild_after_sales_ticket_dependents(conn: sqlite3.Connection) -> list[str]:
    if not _table_exists(conn, "after_sales_support_tickets"):
        return []
    if not _table_exists(conn, "service_tickets"):
        raise RuntimeError("service_tickets must exist before retiring after_sales_support_tickets")

    existing_dependents = [
        table_name
        for table_name in AFTER_SALES_TICKET_DEPENDENT_TABLES
        if _table_exists(conn, table_name)
    ]
    for table_name in existing_dependents:
        row_count = _table_row_count(conn, table_name)
        if row_count:
            raise RuntimeError(
                f"Refusing to rebuild non-empty {table_name} while retiring "
                "after_sales_support_tickets"
            )

    schemas: dict[str, str] = {}
    for table_name in existing_dependents:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        if row is None or not row[0]:
            raise RuntimeError(f"Cannot find schema for {table_name}")
        schemas[table_name] = _replace_after_sales_ticket_reference(str(row[0]))

    for table_name in existing_dependents:
        conn.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    for table_name in reversed(existing_dependents):
        conn.execute(schemas[table_name])
    return list(reversed(existing_dependents))


def _table_columns(conn: sqlite3.Connection, table_name: str) -> list[str]:
    return [row[1] for row in conn.execute(f'PRAGMA table_info("{table_name}")')]


def _table_column_set(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return set(_table_columns(conn, table_name))


def _json_default(value: Any) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _create_manifest_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retired_table_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            row_count INTEGER NOT NULL,
            source_db TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            source_schema_sql TEXT NOT NULL,
            UNIQUE(table_name, archived_at)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS retired_view_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            view_name TEXT NOT NULL,
            source_db TEXT NOT NULL,
            archived_at TEXT NOT NULL,
            source_sql TEXT NOT NULL,
            UNIQUE(view_name, archived_at)
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sales_target_v2_merge_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            source_metric TEXT,
            target_table TEXT,
            target_id INTEGER,
            target_type TEXT,
            merge_action TEXT NOT NULL,
            reason TEXT,
            archived_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS legacy_permission_merge_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_permission_id INTEGER,
            source_permission_code TEXT,
            source_role_permission_id INTEGER,
            role_id INTEGER,
            api_permission_id INTEGER,
            role_api_permission_id INTEGER,
            merge_action TEXT NOT NULL,
            reason TEXT,
            archived_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS presale_solution_template_merge_manifest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_table TEXT NOT NULL,
            source_id INTEGER NOT NULL,
            source_code TEXT,
            target_table TEXT,
            target_id INTEGER,
            merge_action TEXT NOT NULL,
            reason TEXT,
            archived_at TEXT NOT NULL
        )
        """
    )


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _merge_report_presale_ai_templates() -> dict[str, int]:
    return dict(PRESALE_AI_TEMPLATE_MERGE_REPORT)


def _json_or_raw(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


def _compact_json_payload(payload: dict[str, Any]) -> str | None:
    payload_copy = dict(payload)
    source_name = payload_copy.pop("source", None)
    compacted = {
        key: value
        for key, value in payload_copy.items()
        if value is not None and value != "" and value != [] and value != {}
    }
    if not compacted:
        return None
    if source_name:
        compacted = {"source": source_name, **compacted}
    return json.dumps(compacted, ensure_ascii=False, default=_json_default)


def _insert_payload(conn: sqlite3.Connection, table_name: str, payload: dict[str, Any]) -> int:
    target_columns = _table_column_set(conn, table_name)
    ordered_columns = [column for column in payload if column in target_columns]
    if not ordered_columns:
        raise RuntimeError(f"{table_name} has no compatible columns for insert")

    column_sql = ", ".join(f'"{column}"' for column in ordered_columns)
    placeholder_sql = ", ".join("?" for _ in ordered_columns)
    cursor = conn.execute(
        f'INSERT INTO "{table_name}" ({column_sql}) VALUES ({placeholder_sql})',
        tuple(payload[column] for column in ordered_columns),
    )
    return int(cursor.lastrowid)


def _is_blank(value: Any) -> bool:
    return value is None or value == "" or value == "null"


def _record_presale_solution_template_merge(
    archive: sqlite3.Connection,
    *,
    source_id: int,
    source_code: str | None,
    target_id: int | None,
    merge_action: str,
    reason: str | None,
    archived_at: str,
) -> None:
    archive.execute(
        """
        INSERT INTO presale_solution_template_merge_manifest (
            source_table,
            source_id,
            source_code,
            target_table,
            target_id,
            merge_action,
            reason,
            archived_at
        )
        VALUES ('presale_solution_templates', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            source_code,
            "presale_solution_template" if target_id is not None else None,
            target_id,
            merge_action,
            reason,
            archived_at,
        ),
    )


def _content_template_from_presale_ai_template(row: sqlite3.Row) -> str | None:
    return _compact_json_payload(
        {
            "source": "presale_solution_templates",
            "solution_content": _json_or_raw(row["solution_content"]),
            "architecture_diagram": row["architecture_diagram"],
            "technical_specs": _json_or_raw(row["technical_specs"]),
            "equipment_list": _json_or_raw(row["equipment_list"]),
            "complexity_level": row["complexity_level"],
            "tags": _json_or_raw(row["tags"]),
            "keywords": row["keywords"],
        }
    )


def _cost_template_from_presale_ai_template(row: sqlite3.Row) -> str | None:
    return _compact_json_payload(
        {
            "source": "presale_solution_templates",
            "bom_template": _json_or_raw(row["bom_template"]),
            "typical_cost_range_min": row["typical_cost_range_min"],
            "typical_cost_range_max": row["typical_cost_range_max"],
        }
    )


def _description_from_presale_ai_template(row: sqlite3.Row) -> str | None:
    parts = [
        f"复杂度: {row['complexity_level']}" if row["complexity_level"] else None,
        f"关键词: {row['keywords']}" if row["keywords"] else None,
    ]
    return "；".join(part for part in parts if part) or None


def _insert_presale_ai_template_as_canonical(
    source: sqlite3.Connection,
    *,
    target_columns: set[str],
    row: sqlite3.Row,
    template_no: str,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    created_at = row["created_at"] or now
    updated_at = row["updated_at"] or created_at
    payload: dict[str, Any] = {
        "tenant_id": row["tenant_id"],
        "template_no": template_no,
        "name": row["name"],
        "industry": row["industry"],
        "test_type": row["equipment_type"],
        "description": _description_from_presale_ai_template(row),
        "content_template": _content_template_from_presale_ai_template(row),
        "cost_template": _cost_template_from_presale_ai_template(row),
        "attachments": None,
        "use_count": row["usage_count"] or 0,
        "is_active": 1 if row["is_active"] is None else int(bool(row["is_active"])),
        "created_by": row["created_by"],
        "created_at": created_at,
        "updated_at": updated_at,
    }
    ordered_columns = [
        column
        for column in (
            "tenant_id",
            "template_no",
            "name",
            "industry",
            "test_type",
            "description",
            "content_template",
            "cost_template",
            "attachments",
            "use_count",
            "is_active",
            "created_by",
            "created_at",
            "updated_at",
        )
        if column in target_columns
    ]
    column_sql = ", ".join(f'"{column}"' for column in ordered_columns)
    placeholder_sql = ", ".join("?" for _ in ordered_columns)
    cursor = source.execute(
        f'INSERT INTO presale_solution_template ({column_sql}) VALUES ({placeholder_sql})',
        tuple(payload[column] for column in ordered_columns),
    )
    return int(cursor.lastrowid)


def _update_canonical_presale_template_if_blank(
    source: sqlite3.Connection,
    *,
    target_columns: set[str],
    existing: sqlite3.Row,
    row: sqlite3.Row,
) -> bool:
    candidates: dict[str, Any] = {
        "industry": row["industry"],
        "test_type": row["equipment_type"],
        "description": _description_from_presale_ai_template(row),
        "content_template": _content_template_from_presale_ai_template(row),
        "cost_template": _cost_template_from_presale_ai_template(row),
        "created_by": row["created_by"],
        "tenant_id": row["tenant_id"],
    }
    if "use_count" in target_columns and (existing["use_count"] is None or existing["use_count"] == 0):
        candidates["use_count"] = row["usage_count"] or 0
    if "is_active" in target_columns and existing["is_active"] is None and row["is_active"] is not None:
        candidates["is_active"] = int(bool(row["is_active"]))

    updates = {
        column: value
        for column, value in candidates.items()
        if column in target_columns and not _is_blank(value) and _is_blank(existing[column])
    }
    if not updates:
        return False

    if "updated_at" in target_columns:
        updates["updated_at"] = row["updated_at"] or datetime.now(timezone.utc).isoformat()
    set_sql = ", ".join(f'"{column}" = ?' for column in updates)
    source.execute(
        f'UPDATE presale_solution_template SET {set_sql} WHERE id = ?',
        tuple(updates.values()) + (existing["id"],),
    )
    return True


def _merge_presale_solution_templates_to_canonical(
    source: sqlite3.Connection,
    archive: sqlite3.Connection,
    *,
    archived_at: str,
) -> dict[str, int]:
    report = _merge_report_presale_ai_templates()
    if not _table_exists(source, "presale_solution_templates") or not _table_exists(
        source, "presale_solution_template"
    ):
        return report

    missing_source_columns = PRESALE_AI_TEMPLATE_REQUIRED_COLUMNS - _table_column_set(
        source, "presale_solution_templates"
    )
    if missing_source_columns:
        raise RuntimeError(
            "presale_solution_templates is missing required columns for merge: "
            + ", ".join(sorted(missing_source_columns))
        )

    target_columns = _table_column_set(source, "presale_solution_template")
    missing_target_columns = {"template_no", "name"} - target_columns
    if missing_target_columns:
        raise RuntimeError(
            "presale_solution_template is missing required columns for merge: "
            + ", ".join(sorted(missing_target_columns))
        )

    rows = source.execute('SELECT * FROM "presale_solution_templates" ORDER BY id').fetchall()
    report["source_rows"] = len(rows)

    for row in rows:
        source_id = int(row["id"])
        template_no = row["code"] or f"PAI-TEMPLATE-{source_id}"
        if not row["name"] or not template_no:
            report["skipped_templates"] += 1
            _record_presale_solution_template_merge(
                archive,
                source_id=source_id,
                source_code=template_no,
                target_id=None,
                merge_action="skipped",
                reason="missing name or code",
                archived_at=archived_at,
            )
            continue

        existing = source.execute(
            """
            SELECT *
            FROM presale_solution_template
            WHERE template_no = ?
            LIMIT 1
            """,
            (template_no,),
        ).fetchone()
        if existing is None:
            target_id = _insert_presale_ai_template_as_canonical(
                source,
                target_columns=target_columns,
                row=row,
                template_no=template_no,
            )
            report["inserted_templates"] += 1
            _record_presale_solution_template_merge(
                archive,
                source_id=source_id,
                source_code=template_no,
                target_id=target_id,
                merge_action="inserted",
                reason=None,
                archived_at=archived_at,
            )
            continue

        updated = _update_canonical_presale_template_if_blank(
            source,
            target_columns=target_columns,
            existing=existing,
            row=row,
        )
        if updated:
            report["updated_existing_templates"] += 1
            action = "updated_existing"
        else:
            report["duplicate_templates"] += 1
            action = "duplicate_existing"
        _record_presale_solution_template_merge(
            archive,
            source_id=source_id,
            source_code=template_no,
            target_id=int(existing["id"]),
            merge_action=action,
            reason=None,
            archived_at=archived_at,
        )

    return report


def _project_change_approval_report() -> dict[str, int]:
    return {
        "source_rows": 0,
        "inserted_instances": 0,
        "existing_instances": 0,
        "inserted_logs": 0,
        "skipped_rows": 0,
    }


def _project_change_template_flow(source: sqlite3.Connection) -> tuple[int, int] | None:
    if not _table_exists(source, "approval_templates") or not _table_exists(
        source, "approval_flow_definitions"
    ):
        return None

    placeholders = ", ".join("?" for _ in PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES)
    order_case = " ".join(
        f"WHEN t.template_code = ? THEN {index}"
        for index, _code in enumerate(PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES)
    )
    row = source.execute(
        f"""
        SELECT t.id AS template_id, f.id AS flow_id
        FROM approval_templates t
        JOIN approval_flow_definitions f ON f.template_id = t.id
        WHERE t.template_code IN ({placeholders})
          AND COALESCE(t.is_active, 1) = 1
          AND COALESCE(f.is_active, 1) = 1
        ORDER BY
          CASE {order_case} ELSE 99 END,
          COALESCE(f.is_default, 0) DESC,
          f.id
        LIMIT 1
        """,
        tuple(PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES)
        + tuple(PROJECT_CHANGE_APPROVAL_TEMPLATE_CODES),
    ).fetchone()
    if row is None:
        return None
    return int(row["template_id"]), int(row["flow_id"])


def _existing_project_change_instance_id(
    source: sqlite3.Connection, *, change_request_id: int
) -> int | None:
    row = source.execute(
        """
        SELECT id
        FROM approval_instances
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (PROJECT_CHANGE_APPROVAL_ENTITY_TYPE, change_request_id),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def _insert_project_change_instance(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    template_id: int,
    flow_id: int,
    status: str,
    archived_at: str,
) -> int:
    change_request_id = int(row["change_request_id"])
    approval_date = row["approval_date"] or row["record_created_at"] or archived_at
    completed_at = approval_date if status in {"APPROVED", "REJECTED"} else None
    instance_no = f"PCR-MIG-{change_request_id}"
    payload = {
        "tenant_id": row["tenant_id"] if row["tenant_id"] is not None else row["change_tenant_id"],
        "instance_no": instance_no,
        "template_id": template_id,
        "flow_id": flow_id,
        "entity_type": PROJECT_CHANGE_APPROVAL_ENTITY_TYPE,
        "entity_id": change_request_id,
        "initiator_id": row["submitter_id"] or row["approver_id"],
        "initiator_name": row["submitter_name"] or row["approver_name"],
        "form_data": json.dumps(
            {
                "source": "change_approval_records",
                "change_request_id": change_request_id,
                "change_code": row["change_code"],
                "project_id": row["project_id"],
            },
            ensure_ascii=False,
            default=_json_default,
        ),
        "status": status,
        "title": f"项目变更 {row['change_code'] or change_request_id} 审批",
        "summary": row["title"],
        "submitted_at": row["submit_date"] or row["record_created_at"] or archived_at,
        "completed_at": completed_at,
        "final_comment": row["comments"],
        "final_approver_id": row["approver_id"],
        "created_at": row["record_created_at"] or archived_at,
        "updated_at": row["record_updated_at"] or row["record_created_at"] or archived_at,
    }
    return _insert_payload(source, "approval_instances", payload)


def _insert_project_change_action_log(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    instance_id: int,
    action: str,
    status: str,
    archived_at: str,
) -> None:
    approval_date = row["approval_date"] or row["record_created_at"] or archived_at
    payload = {
        "tenant_id": row["tenant_id"] if row["tenant_id"] is not None else row["change_tenant_id"],
        "instance_id": instance_id,
        "operator_id": row["approver_id"],
        "operator_name": row["approver_name"],
        "action": action,
        "action_detail": json.dumps(
            {
                "source": "change_approval_records",
                "source_id": row["id"],
                "change_request_id": row["change_request_id"],
                "decision": row["decision"],
                "approver_role": row["approver_role"],
            },
            ensure_ascii=False,
            default=_json_default,
        ),
        "comment": row["comments"],
        "attachments": row["attachments"],
        "before_status": "PENDING_APPROVAL",
        "after_status": row["change_status"] or status,
        "action_at": approval_date,
        "created_at": row["record_created_at"] or archived_at,
        "updated_at": row["record_updated_at"] or row["record_created_at"] or archived_at,
    }
    _insert_payload(source, "approval_action_logs", payload)


def _migrate_change_approval_records_to_unified_logs(
    source: sqlite3.Connection,
    *,
    archived_at: str,
) -> dict[str, int]:
    report = _project_change_approval_report()
    if not _table_exists(source, "change_approval_records"):
        return report

    missing_source_columns = CHANGE_APPROVAL_RECORD_REQUIRED_COLUMNS - _table_column_set(
        source, "change_approval_records"
    )
    if missing_source_columns:
        raise RuntimeError(
            "change_approval_records is missing required columns for migration: "
            + ", ".join(sorted(missing_source_columns))
        )

    required_tables = {"change_requests", "approval_instances", "approval_action_logs"}
    missing_tables = sorted(table for table in required_tables if not _table_exists(source, table))
    if missing_tables:
        raise RuntimeError(
            "change_approval_records migration requires tables: " + ", ".join(missing_tables)
        )

    template_flow = _project_change_template_flow(source)
    if template_flow is None:
        raise RuntimeError("No active approval template/flow found for project change migration")
    template_id, flow_id = template_flow

    rows = source.execute(
        """
        SELECT
            r.id,
            r.tenant_id,
            r.change_request_id,
            r.approver_id,
            r.approver_name,
            r.approver_role,
            r.approval_date,
            r.decision,
            r.comments,
            r.attachments,
            r.created_at AS record_created_at,
            r.updated_at AS record_updated_at,
            c.tenant_id AS change_tenant_id,
            c.change_code,
            c.title,
            c.project_id,
            c.submitter_id,
            c.submitter_name,
            c.submit_date,
            c.status AS change_status
        FROM change_approval_records r
        LEFT JOIN change_requests c ON c.id = r.change_request_id
        ORDER BY r.id
        """
    ).fetchall()
    report["source_rows"] = len(rows)

    for row in rows:
        decision = str(row["decision"] or "").upper()
        action = PROJECT_CHANGE_APPROVAL_ACTION_BY_DECISION.get(decision)
        status = PROJECT_CHANGE_APPROVAL_STATUS_BY_DECISION.get(decision)
        if action is None:
            action = PROJECT_CHANGE_APPROVAL_ACTION_BY_STATUS.get(
                str(row["change_status"] or "").upper()
            )
            status = PROJECT_CHANGE_APPROVAL_STATUS_BY_ACTION.get(action or "")
        if action is None:
            action = "COMMENT"
            status = row["change_status"] or PROJECT_CHANGE_APPROVAL_STATUS_BY_ACTION[action]
        if action is None or status is None or row["approver_id"] is None:
            report["skipped_rows"] += 1
            continue

        instance_id = _existing_project_change_instance_id(
            source,
            change_request_id=int(row["change_request_id"]),
        )
        if instance_id is None:
            instance_id = _insert_project_change_instance(
                source,
                row=row,
                template_id=template_id,
                flow_id=flow_id,
                status=status,
                archived_at=archived_at,
            )
            report["inserted_instances"] += 1
        else:
            report["existing_instances"] += 1

        _insert_project_change_action_log(
            source,
            row=row,
            instance_id=instance_id,
            action=action,
            status=status,
            archived_at=archived_at,
        )
        report["inserted_logs"] += 1

    return report


def _timesheet_approval_report() -> dict[str, int]:
    return {
        "source_rows": 0,
        "inserted_instances": 0,
        "existing_instances": 0,
        "inserted_logs": 0,
        "skipped_rows": 0,
    }


def _timesheet_template_flow(source: sqlite3.Connection) -> tuple[int, int] | None:
    if not _table_exists(source, "approval_templates") or not _table_exists(
        source, "approval_flow_definitions"
    ):
        return None

    placeholders = ", ".join("?" for _ in TIMESHEET_APPROVAL_TEMPLATE_CODES)
    order_case = " ".join(
        f"WHEN t.template_code = ? THEN {index}"
        for index, _code in enumerate(TIMESHEET_APPROVAL_TEMPLATE_CODES)
    )
    row = source.execute(
        f"""
        SELECT t.id AS template_id, f.id AS flow_id
        FROM approval_templates t
        JOIN approval_flow_definitions f ON f.template_id = t.id
        WHERE t.template_code IN ({placeholders})
          AND COALESCE(t.is_active, 1) = 1
          AND COALESCE(f.is_active, 1) = 1
        ORDER BY
          CASE {order_case} ELSE 99 END,
          COALESCE(f.is_default, 0) DESC,
          f.id
        LIMIT 1
        """,
        tuple(TIMESHEET_APPROVAL_TEMPLATE_CODES) + tuple(TIMESHEET_APPROVAL_TEMPLATE_CODES),
    ).fetchone()
    if row is None:
        return None
    return int(row["template_id"]), int(row["flow_id"])


def _normalise_timesheet_approval_action(raw_action: Any) -> str:
    return TIMESHEET_APPROVAL_ACTION_ALIASES.get(str(raw_action or "").upper(), "COMMENT")


def _timesheet_instance_status(row: sqlite3.Row, *, action: str) -> str:
    status_from_timesheet = TIMESHEET_APPROVAL_STATUS_BY_TIMESHEET_STATUS.get(
        str(row["timesheet_status"] or "").upper()
    )
    if status_from_timesheet is not None:
        return status_from_timesheet
    return TIMESHEET_APPROVAL_STATUS_BY_ACTION[action]


def _existing_timesheet_instance_id(
    source: sqlite3.Connection, *, timesheet_id: int
) -> int | None:
    row = source.execute(
        """
        SELECT id
        FROM approval_instances
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (TIMESHEET_APPROVAL_ENTITY_TYPE, timesheet_id),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def _timesheet_summary(row: sqlite3.Row) -> str | None:
    parts = [
        f"员工: {row['user_name']}" if row["user_name"] else None,
        f"日期: {row['work_date']}" if row["work_date"] else None,
        f"工时: {row['hours']}小时" if row["hours"] is not None else None,
        f"项目: {row['project_name']}" if row["project_name"] else None,
    ]
    return " | ".join(part for part in parts if part) or None


def _insert_timesheet_instance(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    template_id: int,
    flow_id: int,
    status: str,
    archived_at: str,
) -> int:
    timesheet_id = int(row["timesheet_id"])
    action_at = row["approved_at"] or row["log_created_at"] or archived_at
    completed_at = action_at if status in {"APPROVED", "REJECTED", "CANCELLED"} else None
    payload = {
        "tenant_id": row["tenant_id"] if row["tenant_id"] is not None else row["timesheet_tenant_id"],
        "instance_no": f"TS-MIG-{timesheet_id}",
        "template_id": template_id,
        "flow_id": flow_id,
        "entity_type": TIMESHEET_APPROVAL_ENTITY_TYPE,
        "entity_id": timesheet_id,
        "initiator_id": row["user_id"] or row["approver_id"],
        "initiator_name": row["user_name"] or row["approver_name"],
        "form_data": json.dumps(
            {
                "source": "timesheet_approval_log",
                "source_id": row["id"],
                "timesheet_id": timesheet_id,
                "batch_id": row["batch_id"],
                "timesheet_no": row["timesheet_no"],
                "hours": row["hours"],
                "project_id": row["project_id"],
            },
            ensure_ascii=False,
            default=_json_default,
        ),
        "status": status,
        "title": f"工时 {row['timesheet_no'] or timesheet_id} 审批",
        "summary": _timesheet_summary(row),
        "submitted_at": row["submit_time"] or row["log_created_at"] or archived_at,
        "completed_at": completed_at,
        "final_comment": row["comment"] if status in {"APPROVED", "REJECTED"} else None,
        "final_approver_id": row["approver_id"] if status in {"APPROVED", "REJECTED"} else None,
        "created_at": row["log_created_at"] or archived_at,
        "updated_at": row["log_updated_at"] or row["log_created_at"] or archived_at,
    }
    return _insert_payload(source, "approval_instances", payload)


def _insert_timesheet_action_log(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    instance_id: int,
    action: str,
    status: str,
    archived_at: str,
) -> None:
    action_at = row["approved_at"] or row["log_created_at"] or archived_at
    payload = {
        "tenant_id": row["tenant_id"] if row["tenant_id"] is not None else row["timesheet_tenant_id"],
        "instance_id": instance_id,
        "operator_id": row["approver_id"],
        "operator_name": row["approver_name"],
        "action": action,
        "action_detail": json.dumps(
            {
                "source": "timesheet_approval_log",
                "source_id": row["id"],
                "timesheet_id": row["timesheet_id"],
                "batch_id": row["batch_id"],
                "raw_action": row["action"],
            },
            ensure_ascii=False,
            default=_json_default,
        ),
        "comment": row["comment"],
        "attachments": None,
        "before_status": "PENDING",
        "after_status": row["timesheet_status"] or status,
        "action_at": action_at,
        "created_at": row["log_created_at"] or archived_at,
        "updated_at": row["log_updated_at"] or row["log_created_at"] or archived_at,
    }
    _insert_payload(source, "approval_action_logs", payload)


def _migrate_timesheet_approval_log_to_unified_logs(
    source: sqlite3.Connection,
    *,
    archived_at: str,
) -> dict[str, int]:
    report = _timesheet_approval_report()
    if not _table_exists(source, "timesheet_approval_log"):
        return report

    missing_source_columns = TIMESHEET_APPROVAL_LOG_REQUIRED_COLUMNS - _table_column_set(
        source, "timesheet_approval_log"
    )
    if missing_source_columns:
        raise RuntimeError(
            "timesheet_approval_log is missing required columns for migration: "
            + ", ".join(sorted(missing_source_columns))
        )

    required_tables = {"timesheet", "approval_instances", "approval_action_logs"}
    missing_tables = sorted(table for table in required_tables if not _table_exists(source, table))
    if missing_tables:
        raise RuntimeError(
            "timesheet_approval_log migration requires tables: " + ", ".join(missing_tables)
        )

    missing_timesheet_columns = TIMESHEET_REQUIRED_COLUMNS_FOR_APPROVAL_MIGRATION - _table_column_set(
        source, "timesheet"
    )
    if missing_timesheet_columns:
        raise RuntimeError(
            "timesheet is missing required columns for approval log migration: "
            + ", ".join(sorted(missing_timesheet_columns))
        )

    rows = source.execute(
        """
        SELECT
            l.id,
            l.tenant_id,
            l.timesheet_id,
            l.batch_id,
            l.approver_id,
            l.approver_name,
            l.action,
            l.comment,
            l.approved_at,
            l.created_at AS log_created_at,
            l.updated_at AS log_updated_at,
            t.tenant_id AS timesheet_tenant_id,
            t.timesheet_no,
            t.user_id,
            t.user_name,
            t.work_date,
            t.hours,
            t.project_id,
            t.project_name,
            t.submit_time,
            t.approve_time,
            t.status AS timesheet_status
        FROM timesheet_approval_log l
        LEFT JOIN timesheet t ON t.id = l.timesheet_id
        ORDER BY l.id
        """
    ).fetchall()
    report["source_rows"] = len(rows)

    has_migratable_rows = any(
        row["timesheet_id"] is not None
        and row["user_id"] is not None
        and row["approver_id"] is not None
        for row in rows
    )
    if not has_migratable_rows:
        report["skipped_rows"] = len(rows)
        return report

    template_flow = _timesheet_template_flow(source)
    if template_flow is None:
        raise RuntimeError("No active approval template/flow found for timesheet migration")
    template_id, flow_id = template_flow

    for row in rows:
        if row["timesheet_id"] is None or row["user_id"] is None or row["approver_id"] is None:
            report["skipped_rows"] += 1
            continue

        action = _normalise_timesheet_approval_action(row["action"])
        status = _timesheet_instance_status(row, action=action)
        instance_id = _existing_timesheet_instance_id(
            source,
            timesheet_id=int(row["timesheet_id"]),
        )
        if instance_id is None:
            instance_id = _insert_timesheet_instance(
                source,
                row=row,
                template_id=template_id,
                flow_id=flow_id,
                status=status,
                archived_at=archived_at,
            )
            report["inserted_instances"] += 1
        else:
            report["existing_instances"] += 1

        _insert_timesheet_action_log(
            source,
            row=row,
            instance_id=instance_id,
            action=action,
            status=status,
            archived_at=archived_at,
        )
        report["inserted_logs"] += 1

    return report


def _ecn_approval_report() -> dict[str, int]:
    return {
        "source_rows": 0,
        "inserted_instances": 0,
        "existing_instances": 0,
        "inserted_logs": 0,
        "skipped_rows": 0,
    }


def _ecn_template_flow(source: sqlite3.Connection) -> tuple[int, int] | None:
    if not _table_exists(source, "approval_templates") or not _table_exists(
        source, "approval_flow_definitions"
    ):
        return None

    placeholders = ", ".join("?" for _ in ECN_APPROVAL_TEMPLATE_CODES)
    order_case = " ".join(
        f"WHEN t.template_code = ? THEN {index}"
        for index, _code in enumerate(ECN_APPROVAL_TEMPLATE_CODES)
    )
    row = source.execute(
        f"""
        SELECT t.id AS template_id, f.id AS flow_id
        FROM approval_templates t
        JOIN approval_flow_definitions f ON f.template_id = t.id
        WHERE t.template_code IN ({placeholders})
          AND COALESCE(t.is_active, 1) = 1
          AND COALESCE(f.is_active, 1) = 1
        ORDER BY
          CASE {order_case} ELSE 99 END,
          COALESCE(f.is_default, 0) DESC,
          f.id
        LIMIT 1
        """,
        tuple(ECN_APPROVAL_TEMPLATE_CODES) + tuple(ECN_APPROVAL_TEMPLATE_CODES),
    ).fetchone()
    if row is None:
        return None
    return int(row["template_id"]), int(row["flow_id"])


def _normalise_ecn_approval_action(row: sqlite3.Row) -> str | None:
    result = str(row["approval_result"] or "").upper()
    if result in ECN_APPROVAL_ACTION_BY_RESULT:
        return ECN_APPROVAL_ACTION_BY_RESULT[result]
    status = str(row["approval_status"] or "").upper()
    if status in ECN_APPROVAL_ACTION_BY_RESULT:
        return ECN_APPROVAL_ACTION_BY_RESULT[status]
    return None


def _ecn_instance_status(row: sqlite3.Row, *, action: str) -> str:
    status_from_ecn = ECN_APPROVAL_STATUS_BY_ECN_STATUS.get(str(row["ecn_status"] or "").upper())
    if status_from_ecn is not None:
        return status_from_ecn
    return ECN_APPROVAL_STATUS_BY_ACTION[action]


def _existing_ecn_instance_id(source: sqlite3.Connection, *, ecn_id: int) -> int | None:
    row = source.execute(
        """
        SELECT id
        FROM approval_instances
        WHERE entity_type = ? AND entity_id = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (ECN_APPROVAL_ENTITY_TYPE, ecn_id),
    ).fetchone()
    return int(row["id"]) if row is not None else None


def _ecn_summary(row: sqlite3.Row) -> str | None:
    parts = [
        f"类型: {row['ecn_type']}" if row["ecn_type"] else None,
        f"项目ID: {row['project_id']}" if row["project_id"] is not None else None,
        f"层级: {row['approval_level']}" if row["approval_level"] is not None else None,
        f"角色: {row['approval_role']}" if row["approval_role"] else None,
    ]
    return " | ".join(part for part in parts if part) or None


def _insert_ecn_instance(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    template_id: int,
    flow_id: int,
    status: str,
    archived_at: str,
) -> int:
    ecn_id = int(row["ecn_id"])
    action_at = row["approved_at"] or row["approval_created_at"] or archived_at
    completed_at = action_at if status in {"APPROVED", "REJECTED", "CANCELLED"} else None
    payload = {
        "tenant_id": row["tenant_id"] if row["tenant_id"] is not None else row["ecn_tenant_id"],
        "instance_no": f"ECN-MIG-{ecn_id}",
        "template_id": template_id,
        "flow_id": flow_id,
        "entity_type": ECN_APPROVAL_ENTITY_TYPE,
        "entity_id": ecn_id,
        "initiator_id": row["applicant_id"] or row["approver_id"],
        "initiator_name": row["applicant_name"] or row["approver_name"],
        "form_data": json.dumps(
            {
                "source": "ecn_approvals",
                "source_id": row["id"],
                "ecn_id": ecn_id,
                "ecn_no": row["ecn_no"],
                "ecn_type": row["ecn_type"],
                "project_id": row["project_id"],
                "approval_level": row["approval_level"],
                "approval_role": row["approval_role"],
            },
            ensure_ascii=False,
            default=_json_default,
        ),
        "status": status,
        "title": f"ECN审批 - {row['ecn_no'] or ecn_id}",
        "summary": _ecn_summary(row),
        "submitted_at": row["applied_at"] or row["approval_created_at"] or archived_at,
        "completed_at": completed_at,
        "final_comment": row["approval_opinion"] if status in {"APPROVED", "REJECTED"} else None,
        "final_approver_id": row["approver_id"] if status in {"APPROVED", "REJECTED"} else None,
        "created_at": row["approval_created_at"] or archived_at,
        "updated_at": row["approval_updated_at"] or row["approval_created_at"] or archived_at,
    }
    return _insert_payload(source, "approval_instances", payload)


def _insert_ecn_action_log(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
    instance_id: int,
    action: str,
    status: str,
    archived_at: str,
) -> None:
    action_at = row["approved_at"] or row["approval_updated_at"] or row["approval_created_at"] or archived_at
    payload = {
        "tenant_id": row["tenant_id"] if row["tenant_id"] is not None else row["ecn_tenant_id"],
        "instance_id": instance_id,
        "operator_id": row["approver_id"],
        "operator_name": row["approver_name"],
        "action": action,
        "action_detail": json.dumps(
            {
                "source": "ecn_approvals",
                "source_id": row["id"],
                "ecn_id": row["ecn_id"],
                "approval_level": row["approval_level"],
                "approval_role": row["approval_role"],
                "approval_result": row["approval_result"],
                "legacy_status": row["approval_status"],
                "due_date": row["due_date"],
                "is_overdue": row["is_overdue"],
            },
            ensure_ascii=False,
            default=_json_default,
        ),
        "comment": row["approval_opinion"],
        "attachments": None,
        "before_status": "PENDING",
        "after_status": row["ecn_status"] or status,
        "action_at": action_at,
        "created_at": row["approval_created_at"] or archived_at,
        "updated_at": row["approval_updated_at"] or row["approval_created_at"] or archived_at,
    }
    _insert_payload(source, "approval_action_logs", payload)


def _migrate_ecn_approvals_to_unified_logs(
    source: sqlite3.Connection,
    *,
    archived_at: str,
) -> dict[str, int]:
    report = _ecn_approval_report()
    if not _table_exists(source, "ecn_approvals"):
        return report

    missing_source_columns = ECN_APPROVAL_REQUIRED_COLUMNS - _table_column_set(
        source, "ecn_approvals"
    )
    if missing_source_columns:
        raise RuntimeError(
            "ecn_approvals is missing required columns for migration: "
            + ", ".join(sorted(missing_source_columns))
        )

    required_tables = {"ecn", "approval_instances", "approval_action_logs"}
    missing_tables = sorted(table for table in required_tables if not _table_exists(source, table))
    if missing_tables:
        raise RuntimeError("ecn_approvals migration requires tables: " + ", ".join(missing_tables))

    missing_ecn_columns = ECN_REQUIRED_COLUMNS_FOR_APPROVAL_MIGRATION - _table_column_set(
        source, "ecn"
    )
    if missing_ecn_columns:
        raise RuntimeError(
            "ecn is missing required columns for approval migration: "
            + ", ".join(sorted(missing_ecn_columns))
        )

    rows = source.execute(
        """
        SELECT
            a.id,
            a.tenant_id,
            a.ecn_id,
            a.approval_level,
            a.approval_role,
            a.approver_id,
            a.approver_name,
            a.approval_result,
            a.approval_opinion,
            a.status AS approval_status,
            a.approved_at,
            a.due_date,
            a.is_overdue,
            a.created_at AS approval_created_at,
            a.updated_at AS approval_updated_at,
            e.tenant_id AS ecn_tenant_id,
            e.ecn_no,
            e.ecn_title,
            e.ecn_type,
            e.project_id,
            e.applicant_id,
            e.applicant_name,
            e.applied_at,
            e.status AS ecn_status
        FROM ecn_approvals a
        LEFT JOIN ecn e ON e.id = a.ecn_id
        ORDER BY a.id
        """
    ).fetchall()
    report["source_rows"] = len(rows)

    has_migratable_rows = any(
        row["ecn_id"] is not None
        and row["applicant_id"] is not None
        and row["approver_id"] is not None
        and _normalise_ecn_approval_action(row) is not None
        for row in rows
    )
    if not has_migratable_rows:
        report["skipped_rows"] = len(rows)
        return report

    template_flow = _ecn_template_flow(source)
    if template_flow is None:
        raise RuntimeError("No active approval template/flow found for ECN migration")
    template_id, flow_id = template_flow

    for row in rows:
        action = _normalise_ecn_approval_action(row)
        if (
            row["ecn_id"] is None
            or row["applicant_id"] is None
            or row["approver_id"] is None
            or action is None
        ):
            report["skipped_rows"] += 1
            continue

        status = _ecn_instance_status(row, action=action)
        instance_id = _existing_ecn_instance_id(source, ecn_id=int(row["ecn_id"]))
        if instance_id is None:
            instance_id = _insert_ecn_instance(
                source,
                row=row,
                template_id=template_id,
                flow_id=flow_id,
                status=status,
                archived_at=archived_at,
            )
            report["inserted_instances"] += 1
        else:
            report["existing_instances"] += 1

        _insert_ecn_action_log(
            source,
            row=row,
            instance_id=instance_id,
            action=action,
            status=status,
            archived_at=archived_at,
        )
        report["inserted_logs"] += 1

    return report


def _sales_department_id(conn: sqlite3.Connection) -> int | None:
    if not _table_exists(conn, "departments"):
        return None

    row = conn.execute(
        """
        SELECT id
        FROM departments
        WHERE dept_code = 'D01'
           OR dept_name IN ('销售部', '销售中心', '市场销售部')
        ORDER BY
            CASE
                WHEN dept_code = 'D01' THEN 0
                WHEN dept_name = '销售部' THEN 1
                ELSE 2
            END,
            id
        LIMIT 1
        """
    ).fetchone()
    if row is not None:
        return int(row[0])

    row = conn.execute("SELECT MIN(id) FROM departments").fetchone()
    if row is None or row[0] is None:
        return None
    return int(row[0])


def _period_from_sales_target_v2(row: sqlite3.Row) -> tuple[str, str]:
    year = int(row["target_year"])
    month = row["target_month"]
    quarter = row["target_quarter"]

    if month is not None:
        return "MONTHLY", f"{year}-{int(month):02d}"
    if quarter is not None:
        return "QUARTERLY", f"{year}-Q{int(quarter)}"
    return "YEARLY", str(year)


def _scope_from_sales_target_v2(
    row: sqlite3.Row, *, sales_department_id: int | None
) -> tuple[str | None, int | None, int | None, int | None, str | None]:
    source_type = str(row["target_type"] or "").lower()
    if source_type == "personal":
        if row["user_id"] is None:
            return None, None, None, None, "personal target missing user_id"
        return "PERSONAL", int(row["user_id"]), None, None, None
    if source_type == "team":
        if row["team_id"] is None:
            return None, None, None, None, "team target missing team_id"
        return "TEAM", None, None, int(row["team_id"]), None
    if source_type == "company":
        return "DEPARTMENT", None, sales_department_id, None, None
    return None, None, None, None, f"unsupported target_type={row['target_type']}"


def _valid_sales_target_v2_row(row: sqlite3.Row) -> tuple[bool, str | None]:
    try:
        year = int(row["target_year"])
    except (TypeError, ValueError):
        return False, "invalid target_year"

    if year < 2000 or year > 2100:
        return False, f"invalid target_year={year}"

    source_type = str(row["target_type"] or "").lower()
    if source_type not in {"company", "team", "personal"}:
        return False, f"unsupported target_type={row['target_type']}"
    if source_type == "team" and row["team_id"] is None:
        return False, "team target missing team_id"
    if source_type == "personal" and row["user_id"] is None:
        return False, "personal target missing user_id"
    return True, None


def _record_sales_target_v2_merge(
    archive: sqlite3.Connection,
    *,
    source_id: int,
    source_metric: str | None,
    target_id: int | None,
    target_type: str | None,
    merge_action: str,
    reason: str | None,
    archived_at: str,
) -> None:
    archive.execute(
        """
        INSERT INTO sales_target_v2_merge_manifest (
            source_table,
            source_id,
            source_metric,
            target_table,
            target_id,
            target_type,
            merge_action,
            reason,
            archived_at
        )
        VALUES ('sales_targets_v2', ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_id,
            source_metric,
            "sales_targets" if target_id is not None else None,
            target_id,
            target_type,
            merge_action,
            reason,
            archived_at,
        ),
    )


def _insert_sales_target_from_v2(
    source: sqlite3.Connection,
    *,
    sales_target_columns: set[str],
    row: sqlite3.Row,
    target_scope: str,
    user_id: int | None,
    department_id: int | None,
    team_id: int | None,
    target_type: str,
    target_period: str,
    period_value: str,
    target_value: Decimal,
) -> tuple[str, int | None]:
    source_id = int(row["id"])
    marker = f"[merged_from:sales_targets_v2:{source_id}:{target_type}]"
    duplicate = source.execute(
        """
        SELECT id
        FROM sales_targets
        WHERE description LIKE ?
        LIMIT 1
        """,
        (f"%{marker}%",),
    ).fetchone()
    if duplicate is not None:
        return "duplicate", int(duplicate[0])

    base_description = (row["description"] or "").strip()
    description = f"{base_description} {marker}".strip()
    created_at = row["created_at"] or datetime.now(timezone.utc).isoformat()
    updated_at = row["updated_at"] or created_at
    created_by = row["created_by"] or 1

    payload: dict[str, Any] = {
        "tenant_id": row["tenant_id"],
        "target_scope": target_scope,
        "user_id": user_id,
        "department_id": department_id,
        "team_id": team_id,
        "target_type": target_type,
        "target_period": target_period,
        "period_value": period_value,
        "target_value": str(target_value),
        "description": description,
        "status": "ACTIVE",
        "created_by": created_by,
        "created_at": created_at,
        "updated_at": updated_at,
    }
    ordered_columns = [
        column
        for column in (
            "tenant_id",
            "target_scope",
            "user_id",
            "department_id",
            "team_id",
            "target_type",
            "target_period",
            "period_value",
            "target_value",
            "description",
            "status",
            "created_by",
            "created_at",
            "updated_at",
        )
        if column in sales_target_columns
    ]
    column_sql = ", ".join(f'"{column}"' for column in ordered_columns)
    placeholder_sql = ", ".join("?" for _ in ordered_columns)
    cursor = source.execute(
        f'INSERT INTO sales_targets ({column_sql}) VALUES ({placeholder_sql})',
        tuple(payload[column] for column in ordered_columns),
    )
    return "inserted", int(cursor.lastrowid)


def _merge_sales_targets_v2_to_sales_targets(
    source: sqlite3.Connection,
    archive: sqlite3.Connection,
    *,
    archived_at: str,
) -> dict[str, int]:
    report = {
        "source_rows": 0,
        "valid_source_rows": 0,
        "skipped_source_rows": 0,
        "inserted_targets": 0,
        "duplicate_targets": 0,
        "skipped_metrics": 0,
    }

    if not _table_exists(source, "sales_targets_v2") or not _table_exists(source, "sales_targets"):
        return report

    source_columns = _table_column_set(source, "sales_targets_v2")
    missing_columns = SALES_TARGET_V2_REQUIRED_COLUMNS - source_columns
    if missing_columns:
        raise RuntimeError(
            "sales_targets_v2 is missing required columns for merge: "
            + ", ".join(sorted(missing_columns))
        )

    sales_target_columns = _table_column_set(source, "sales_targets")
    required_target_columns = {
        "target_scope",
        "target_type",
        "target_period",
        "period_value",
        "target_value",
        "created_by",
        "created_at",
        "updated_at",
    }
    missing_target_columns = required_target_columns - sales_target_columns
    if missing_target_columns:
        raise RuntimeError(
            "sales_targets is missing required columns for V2 merge: "
            + ", ".join(sorted(missing_target_columns))
        )

    sales_department_id = _sales_department_id(source)
    rows = source.execute('SELECT * FROM "sales_targets_v2" ORDER BY id').fetchall()
    report["source_rows"] = len(rows)

    for row in rows:
        source_id = int(row["id"])
        is_valid, invalid_reason = _valid_sales_target_v2_row(row)
        if not is_valid:
            report["skipped_source_rows"] += 1
            _record_sales_target_v2_merge(
                archive,
                source_id=source_id,
                source_metric=None,
                target_id=None,
                target_type=None,
                merge_action="skipped",
                reason=f"invalid source row: {invalid_reason}",
                archived_at=archived_at,
            )
            continue

        target_scope, user_id, department_id, team_id, scope_reason = _scope_from_sales_target_v2(
            row, sales_department_id=sales_department_id
        )
        if target_scope is None:
            report["skipped_source_rows"] += 1
            _record_sales_target_v2_merge(
                archive,
                source_id=source_id,
                source_metric=None,
                target_id=None,
                target_type=None,
                merge_action="skipped",
                reason=f"invalid target scope: {scope_reason}",
                archived_at=archived_at,
            )
            continue

        report["valid_source_rows"] += 1
        target_period, period_value = _period_from_sales_target_v2(row)
        for metric_column, target_type in SALES_TARGET_V2_METRICS:
            target_value = _to_decimal(row[metric_column])
            if target_value is None or target_value <= 0:
                report["skipped_metrics"] += 1
                _record_sales_target_v2_merge(
                    archive,
                    source_id=source_id,
                    source_metric=metric_column,
                    target_id=None,
                    target_type=target_type,
                    merge_action="skipped",
                    reason="metric is empty or not positive",
                    archived_at=archived_at,
                )
                continue

            action, target_id = _insert_sales_target_from_v2(
                source,
                sales_target_columns=sales_target_columns,
                row=row,
                target_scope=target_scope,
                user_id=user_id,
                department_id=department_id,
                team_id=team_id,
                target_type=target_type,
                target_period=target_period,
                period_value=period_value,
                target_value=target_value,
            )
            if action == "inserted":
                report["inserted_targets"] += 1
            else:
                report["duplicate_targets"] += 1
            _record_sales_target_v2_merge(
                archive,
                source_id=source_id,
                source_metric=metric_column,
                target_id=target_id,
                target_type=target_type,
                merge_action=action,
                reason=None,
                archived_at=archived_at,
            )

    return report


def _legacy_permission_report() -> dict[str, int]:
    return dict(LEGACY_PERMISSION_MERGE_REPORT)


def _record_legacy_permission_merge(
    archive: sqlite3.Connection,
    *,
    source_permission_id: int | None,
    source_permission_code: str | None,
    source_role_permission_id: int | None,
    role_id: int | None,
    api_permission_id: int | None,
    role_api_permission_id: int | None,
    merge_action: str,
    reason: str | None,
    archived_at: str,
) -> None:
    archive.execute(
        """
        INSERT INTO legacy_permission_merge_manifest (
            source_permission_id,
            source_permission_code,
            source_role_permission_id,
            role_id,
            api_permission_id,
            role_api_permission_id,
            merge_action,
            reason,
            archived_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            source_permission_id,
            source_permission_code,
            source_role_permission_id,
            role_id,
            api_permission_id,
            role_api_permission_id,
            merge_action,
            reason,
            archived_at,
        ),
    )


def _find_api_permission_id(source: sqlite3.Connection, perm_code: str) -> int | None:
    row = source.execute(
        """
        SELECT id
        FROM api_permissions
        WHERE perm_code = ?
        ORDER BY
            CASE WHEN tenant_id IS NULL THEN 0 ELSE 1 END,
            id
        LIMIT 1
        """,
        (perm_code,),
    ).fetchone()
    return int(row[0]) if row is not None else None


def _insert_api_permission_from_legacy(
    source: sqlite3.Connection,
    *,
    row: sqlite3.Row,
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    created_at = row["created_at"] or now
    updated_at = row["updated_at"] or created_at
    permission_type = row["permission_type"] or "API"
    perm_name = row["perm_name"] or row["perm_code"]

    cursor = source.execute(
        """
        INSERT INTO api_permissions (
            tenant_id,
            perm_code,
            perm_name,
            module,
            page_code,
            action,
            description,
            permission_type,
            group_id,
            is_active,
            is_system,
            created_at,
            updated_at
        )
        VALUES (NULL, ?, ?, ?, NULL, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (
            row["perm_code"],
            perm_name,
            row["module"],
            row["action"],
            row["description"],
            permission_type,
            row["group_id"],
            1 if row["is_active"] is None else int(bool(row["is_active"])),
            created_at,
            updated_at,
        ),
    )
    return int(cursor.lastrowid)


def _insert_role_api_permission(
    source: sqlite3.Connection,
    *,
    role_id: int,
    api_permission_id: int,
    tenant_id: int | None,
) -> tuple[str, int | None]:
    existing = source.execute(
        """
        SELECT id
        FROM role_api_permissions
        WHERE role_id = ? AND permission_id = ?
        LIMIT 1
        """,
        (role_id, api_permission_id),
    ).fetchone()
    if existing is not None:
        return "duplicate", int(existing[0])

    columns = _table_column_set(source, "role_api_permissions")
    payload: dict[str, Any] = {
        "role_id": role_id,
        "permission_id": api_permission_id,
        "tenant_id": tenant_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    ordered_columns = [
        column
        for column in ("role_id", "permission_id", "created_at", "updated_at", "tenant_id")
        if column in columns
    ]
    column_sql = ", ".join(f'"{column}"' for column in ordered_columns)
    placeholder_sql = ", ".join("?" for _ in ordered_columns)
    cursor = source.execute(
        f'INSERT INTO role_api_permissions ({column_sql}) VALUES ({placeholder_sql})',
        tuple(payload[column] for column in ordered_columns),
    )
    return "inserted", int(cursor.lastrowid)


def _bump_permission_cache_revisions(
    source: sqlite3.Connection,
    *,
    scopes: set[str],
) -> int:
    if not scopes:
        return 0

    source.execute(
        """
        CREATE TABLE IF NOT EXISTS permission_cache_revisions (
            scope VARCHAR(64) PRIMARY KEY,
            revision INTEGER NOT NULL DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    bumped = 0
    for scope in sorted(scopes):
        row = source.execute(
            "SELECT revision FROM permission_cache_revisions WHERE scope = ?",
            (scope,),
        ).fetchone()
        next_revision = int(row[0]) + 1 if row is not None else 1
        if row is None:
            source.execute(
                """
                INSERT INTO permission_cache_revisions (scope, revision, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (scope, next_revision),
            )
        else:
            source.execute(
                """
                UPDATE permission_cache_revisions
                SET revision = ?, updated_at = CURRENT_TIMESTAMP
                WHERE scope = ?
                """,
                (next_revision, scope),
            )
        bumped += 1
    return bumped


def _merge_legacy_permissions_to_api_permissions(
    source: sqlite3.Connection,
    archive: sqlite3.Connection,
    *,
    archived_at: str,
) -> dict[str, int]:
    report = _legacy_permission_report()
    required_tables = (
        "permissions",
        "role_permissions",
        "api_permissions",
        "role_api_permissions",
    )
    if not all(_table_exists(source, table_name) for table_name in required_tables):
        return report

    missing_permission_columns = LEGACY_PERMISSION_REQUIRED_COLUMNS - _table_column_set(
        source, "permissions"
    )
    if missing_permission_columns:
        raise RuntimeError(
            "permissions is missing required columns for merge: "
            + ", ".join(sorted(missing_permission_columns))
        )
    missing_role_permission_columns = (
        LEGACY_ROLE_PERMISSION_REQUIRED_COLUMNS - _table_column_set(source, "role_permissions")
    )
    if missing_role_permission_columns:
        raise RuntimeError(
            "role_permissions is missing required columns for merge: "
            + ", ".join(sorted(missing_role_permission_columns))
        )

    report["source_permissions"] = source.execute(
        'SELECT COUNT(*) FROM "permissions"'
    ).fetchone()[0]
    report["source_role_permissions"] = source.execute(
        'SELECT COUNT(*) FROM "role_permissions"'
    ).fetchone()[0]

    assigned_permission_ids = {
        int(row[0])
        for row in source.execute(
            'SELECT DISTINCT permission_id FROM "role_permissions" WHERE permission_id IS NOT NULL'
        )
    }
    report["assigned_permissions"] = len(assigned_permission_ids)
    report["unassigned_permissions"] = max(
        0,
        report["source_permissions"] - report["assigned_permissions"],
    )

    scopes_to_bump: set[str] = set()
    rows = source.execute(
        """
        SELECT
            rp.id AS role_permission_id,
            rp.role_id AS role_id,
            p.id AS permission_id,
            p.perm_code AS perm_code,
            p.perm_name AS perm_name,
            p.module AS module,
            p.action AS action,
            p.resource AS resource,
            p.description AS description,
            p.is_active AS is_active,
            p.created_at AS created_at,
            p.updated_at AS updated_at,
            p.permission_type AS permission_type,
            p.group_id AS group_id,
            r.tenant_id AS role_tenant_id
        FROM role_permissions rp
        LEFT JOIN permissions p ON p.id = rp.permission_id
        LEFT JOIN roles r ON r.id = rp.role_id
        ORDER BY rp.id
        """
    ).fetchall()

    for row in rows:
        role_permission_id = int(row["role_permission_id"])
        role_id = row["role_id"]
        perm_code = row["perm_code"]
        if role_id is None or not perm_code:
            report["skipped_role_permissions"] += 1
            _record_legacy_permission_merge(
                archive,
                source_permission_id=row["permission_id"],
                source_permission_code=perm_code,
                source_role_permission_id=role_permission_id,
                role_id=role_id,
                api_permission_id=None,
                role_api_permission_id=None,
                merge_action="role_permission_skipped",
                reason="missing role_id or permission",
                archived_at=archived_at,
            )
            continue

        api_permission_id = _find_api_permission_id(source, perm_code)
        if api_permission_id is None:
            api_permission_id = _insert_api_permission_from_legacy(source, row=row)
            report["inserted_api_permissions"] += 1
            _record_legacy_permission_merge(
                archive,
                source_permission_id=int(row["permission_id"]),
                source_permission_code=perm_code,
                source_role_permission_id=None,
                role_id=None,
                api_permission_id=api_permission_id,
                role_api_permission_id=None,
                merge_action="api_permission_inserted",
                reason=None,
                archived_at=archived_at,
            )
        else:
            report["existing_api_permissions"] += 1
            _record_legacy_permission_merge(
                archive,
                source_permission_id=int(row["permission_id"]),
                source_permission_code=perm_code,
                source_role_permission_id=None,
                role_id=None,
                api_permission_id=api_permission_id,
                role_api_permission_id=None,
                merge_action="api_permission_existing",
                reason=None,
                archived_at=archived_at,
            )

        tenant_id = row["role_tenant_id"]
        action, role_api_permission_id = _insert_role_api_permission(
            source,
            role_id=int(role_id),
            api_permission_id=api_permission_id,
            tenant_id=tenant_id,
        )
        if action == "inserted":
            report["inserted_role_api_permissions"] += 1
        else:
            report["duplicate_role_api_permissions"] += 1
        _record_legacy_permission_merge(
            archive,
            source_permission_id=int(row["permission_id"]),
            source_permission_code=perm_code,
            source_role_permission_id=role_permission_id,
            role_id=int(role_id),
            api_permission_id=api_permission_id,
            role_api_permission_id=role_api_permission_id,
            merge_action=f"role_api_permission_{action}",
            reason=None,
            archived_at=archived_at,
        )

        scopes_to_bump.add("system")
        if tenant_id is not None:
            scopes_to_bump.add(f"tenant:{tenant_id}")

    report["cache_revisions_bumped"] = _bump_permission_cache_revisions(
        source,
        scopes=scopes_to_bump,
    )
    return report


def _archive_view(
    source: sqlite3.Connection,
    archive: sqlite3.Connection,
    *,
    view_name: str,
    source_db: Path,
    archived_at: str,
) -> None:
    row = source.execute(
        "SELECT sql FROM sqlite_master WHERE type='view' AND name=?",
        (view_name,),
    ).fetchone()
    if row is None or not row[0]:
        return

    archive.execute(
        """
        INSERT OR REPLACE INTO retired_view_manifest (
            view_name,
            source_db,
            archived_at,
            source_sql
        )
        VALUES (?, ?, ?, ?)
        """,
        (view_name, str(source_db), archived_at, row[0]),
    )


def _archive_table(
    source: sqlite3.Connection,
    archive: sqlite3.Connection,
    *,
    table_name: str,
    source_db: Path,
    archived_at: str,
) -> int:
    row = source.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    if row is None or not row[0]:
        return 0

    columns = _table_columns(source, table_name)
    archive.execute(f'DROP TABLE IF EXISTS "{table_name}"')
    archive.execute(row[0])

    source_rows = source.execute(f'SELECT * FROM "{table_name}" ORDER BY rowid').fetchall()
    if source_rows:
        column_sql = ", ".join(f'"{column}"' for column in columns)
        placeholders = ", ".join("?" for _ in columns)
        archive.executemany(
            f'INSERT INTO "{table_name}" ({column_sql}) VALUES ({placeholders})',
            [tuple(record[column] for column in columns) for record in source_rows],
        )

    archive.execute(
        """
        INSERT OR REPLACE INTO retired_table_manifest (
            table_name,
            row_count,
            source_db,
            archived_at,
            source_schema_sql
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (table_name, len(source_rows), str(source_db), archived_at, row[0]),
    )
    return len(source_rows)


def retire_unused_tables(
    db_path: str | Path,
    *,
    archive_path: str | Path | None = None,
    drop_tables: bool = False,
    create_backup: bool = True,
) -> dict[str, Any]:
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(db_path)

    if archive_path is None:
        archive_path = db_path.with_name(f"retired_unused_tables_archive_{_timestamp()}.db")
    archive_path = Path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    backup_path: Path | None = None
    if drop_tables and create_backup:
        backup_path = db_path.with_name(f"{db_path.stem}.before_unused_tables_drop_{_timestamp()}.db")
        shutil.copy2(db_path, backup_path)

    source = sqlite3.connect(db_path)
    source.row_factory = sqlite3.Row
    archive = sqlite3.connect(archive_path)
    archive.row_factory = sqlite3.Row

    archived_at = datetime.now(timezone.utc).isoformat()
    archived_rows: dict[str, int] = {}
    dropped_tables: list[str] = []
    dropped_views: list[str] = []
    rebuilt_tables: list[str] = []
    merged_sales_target_v2 = {
        "source_rows": 0,
        "valid_source_rows": 0,
        "skipped_source_rows": 0,
        "inserted_targets": 0,
        "duplicate_targets": 0,
        "skipped_metrics": 0,
    }
    merged_legacy_permissions = _legacy_permission_report()
    merged_presale_solution_templates = _merge_report_presale_ai_templates()
    migrated_change_approval_records = _project_change_approval_report()
    migrated_timesheet_approval_log = _timesheet_approval_report()
    migrated_ecn_approvals = _ecn_approval_report()

    try:
        existing_tables = [table for table in RETIRABLE_TABLES if _table_exists(source, table)]
        existing_views = [view for view in RETIRABLE_VIEWS if _view_exists(source, view)]
        unsafe_fks = _unsafe_incoming_fks(source, set(existing_tables))
        if unsafe_fks:
            raise RuntimeError(
                "Refusing to drop tables still referenced by retained tables: "
                + "; ".join(unsafe_fks)
            )

        _create_manifest_table(archive)
        for view_name in existing_views:
            _archive_view(
                source,
                archive,
                view_name=view_name,
                source_db=db_path,
                archived_at=archived_at,
            )
        for table_name in existing_tables:
            archived_rows[table_name] = _archive_table(
                source,
                archive,
                table_name=table_name,
                source_db=db_path,
                archived_at=archived_at,
            )
        archive.commit()

        if drop_tables:
            original_foreign_keys = source.execute("PRAGMA foreign_keys").fetchone()[0]
            try:
                merged_sales_target_v2 = _merge_sales_targets_v2_to_sales_targets(
                    source,
                    archive,
                    archived_at=archived_at,
                )
                merged_legacy_permissions = _merge_legacy_permissions_to_api_permissions(
                    source,
                    archive,
                    archived_at=archived_at,
                )
                merged_presale_solution_templates = _merge_presale_solution_templates_to_canonical(
                    source,
                    archive,
                    archived_at=archived_at,
                )
                migrated_change_approval_records = (
                    _migrate_change_approval_records_to_unified_logs(
                        source,
                        archived_at=archived_at,
                    )
                )
                migrated_timesheet_approval_log = (
                    _migrate_timesheet_approval_log_to_unified_logs(
                        source,
                        archived_at=archived_at,
                    )
                )
                migrated_ecn_approvals = _migrate_ecn_approvals_to_unified_logs(
                    source,
                    archived_at=archived_at,
                )
                source.execute("PRAGMA foreign_keys = OFF")
                if "after_sales_support_tickets" in existing_tables:
                    rebuilt_tables = _rebuild_after_sales_ticket_dependents(source)
                for view_name in existing_views:
                    source.execute(f'DROP VIEW IF EXISTS "{view_name}"')
                    dropped_views.append(view_name)
                for table_name in existing_tables:
                    source.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                    dropped_tables.append(table_name)
                source.commit()
                archive.commit()
            except Exception:
                source.rollback()
                archive.rollback()
                raise
            finally:
                source.execute(f"PRAGMA foreign_keys = {int(bool(original_foreign_keys))}")

        return {
            "db_path": str(db_path),
            "archive_path": str(archive_path),
            "backup_path": str(backup_path) if backup_path else None,
            "existing_tables": existing_tables,
            "existing_views": existing_views,
            "archived_rows": archived_rows,
            "rebuilt_tables": rebuilt_tables,
            "dropped_views": dropped_views,
            "dropped_tables": dropped_tables,
            "merged_sales_target_v2": merged_sales_target_v2,
            "merged_legacy_permissions": merged_legacy_permissions,
            "merged_presale_solution_templates": merged_presale_solution_templates,
            "migrated_change_approval_records": migrated_change_approval_records,
            "migrated_timesheet_approval_log": migrated_timesheet_approval_log,
            "migrated_ecn_approvals": migrated_ecn_approvals,
        }
    finally:
        archive.close()
        source.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("db_path", nargs="?", default="data/app.db")
    parser.add_argument("--archive-path")
    parser.add_argument("--drop-tables", action="store_true")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    report = retire_unused_tables(
        args.db_path,
        archive_path=args.archive_path,
        drop_tables=args.drop_tables,
        create_backup=not args.no_backup,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
