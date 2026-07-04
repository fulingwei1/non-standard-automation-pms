# -*- coding: utf-8 -*-
"""Project lifecycle status normalization.

The canonical project lifecycle is represented by stage S1-S9 plus STxx status
codes. Older data and endpoints used coarse values such as EXECUTING,
COMPLETED, active, and archived in projects.status. Keep reads compatible while
new writes stop adding those legacy values.
"""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy import and_, func, not_, or_

PROJECT_STAGE_STATUS_MAP: Dict[str, str] = {
    "S1": "ST01",
    "S2": "ST03",
    "S3": "ST05",
    "S4": "ST07",
    "S5": "ST10",
    "S6": "ST15",
    "S7": "ST20",
    "S8": "ST25",
    "S9": "ST30",
}

DELIVERY_STAGES = ("S2", "S3", "S4", "S5", "S6", "S7", "S8")
CANONICAL_PROJECT_STATUSES = tuple(f"ST{i:02d}" for i in range(1, 31))
LEGACY_COMPLETED_STATUSES = {"COMPLETED", "CLOSED", "DONE", "FINISHED"}
LEGACY_EXECUTING_STATUSES = {"EXECUTING", "IN_PROGRESS", "ACTIVE"}
LEGACY_ARCHIVED_STATUSES = {"ARCHIVED"}
PROJECT_CANCELLED_STATUSES = {"CANCELLED", "ST99"}


def _normalized_status_value(status: Any) -> str:
    return str(status or "").strip().upper()


def status_for_stage(stage: Any, fallback: str = "ST01") -> str:
    return PROJECT_STAGE_STATUS_MAP.get(str(stage or "").strip().upper(), fallback)


def normalize_legacy_project_state(
    status: Any,
    stage: Any,
    is_archived: bool | None = False,
) -> Dict[str, Any]:
    """Return canonical stage/status/is_archived for a legacy project row."""
    normalized_status = _normalized_status_value(status)
    normalized_stage = str(stage or "S1").strip().upper()
    archived = bool(is_archived) or normalized_status in LEGACY_ARCHIVED_STATUSES

    if normalized_status in PROJECT_CANCELLED_STATUSES:
        return {"status": normalized_status, "stage": normalized_stage, "is_archived": archived}

    if normalized_status in LEGACY_COMPLETED_STATUSES:
        return {"status": "ST30", "stage": "S9", "is_archived": archived}

    if normalized_status in LEGACY_ARCHIVED_STATUSES:
        return {
            "status": status_for_stage(normalized_stage),
            "stage": normalized_stage,
            "is_archived": True,
        }

    if normalized_status in LEGACY_EXECUTING_STATUSES:
        return {
            "status": status_for_stage(normalized_stage),
            "stage": normalized_stage,
            "is_archived": archived,
        }

    if normalized_status in CANONICAL_PROJECT_STATUSES:
        return {
            "status": normalized_status,
            "stage": normalized_stage,
            "is_archived": archived,
        }

    return {
        "status": status_for_stage(normalized_stage),
        "stage": normalized_stage,
        "is_archived": archived,
    }


def project_status_bucket(status: Any, stage: Any, is_archived: bool | None = False) -> str:
    """Return a display/statistics bucket without legacy lifecycle status values."""
    normalized_status = _normalized_status_value(status)
    if bool(is_archived) or normalized_status in LEGACY_ARCHIVED_STATUSES:
        return "ARCHIVED"
    state = normalize_legacy_project_state(status, stage, is_archived)
    return str(state["status"] or "UNKNOWN")


def _status_upper_expr(model):
    return func.upper(func.coalesce(model.status, ""))


def is_project_archived_expr(model):
    return or_(
        model.is_archived.is_(True),
        _status_upper_expr(model).in_(LEGACY_ARCHIVED_STATUSES),
    )


def is_project_completed_expr(model):
    return or_(
        model.stage == "S9",
        model.status == "ST30",
        _status_upper_expr(model).in_(LEGACY_COMPLETED_STATUSES),
    )


def is_project_cancelled_expr(model):
    return _status_upper_expr(model).in_(PROJECT_CANCELLED_STATUSES)


def is_project_not_cancelled_expr(model):
    return not_(is_project_cancelled_expr(model))


def is_project_not_archived_expr(model):
    return and_(
        or_(model.is_archived.is_(False), model.is_archived.is_(None)),
        not_(_status_upper_expr(model).in_(LEGACY_ARCHIVED_STATUSES)),
    )


def is_project_open_expr(model):
    return and_(
        model.is_active.is_(True),
        is_project_not_archived_expr(model),
        is_project_not_cancelled_expr(model),
        not_(is_project_completed_expr(model)),
    )


def project_delivery_scope_expr(model):
    return and_(
        model.is_active.is_(True),
        is_project_not_archived_expr(model),
        is_project_not_cancelled_expr(model),
        model.stage.in_(DELIVERY_STAGES),
        not_(_status_upper_expr(model).in_(LEGACY_COMPLETED_STATUSES)),
        or_(model.status.is_(None), model.status != "ST30"),
    )


def apply_project_status_filter(query, status: Any, model):
    normalized = _normalized_status_value(status)
    if not normalized:
        return query
    if normalized in LEGACY_EXECUTING_STATUSES:
        return query.filter(project_delivery_scope_expr(model))
    if normalized in LEGACY_COMPLETED_STATUSES or normalized == "ST30":
        return query.filter(is_project_completed_expr(model))
    if normalized in LEGACY_ARCHIVED_STATUSES:
        return query.filter(is_project_archived_expr(model))
    if normalized in PROJECT_CANCELLED_STATUSES:
        return query.filter(is_project_cancelled_expr(model))
    if normalized in CANONICAL_PROJECT_STATUSES:
        return query.filter(model.status == normalized)
    return query.filter(_status_upper_expr(model) == normalized)
