# -*- coding: utf-8 -*-
"""售前技术评估状态字典收敛工具。"""

from __future__ import annotations

from typing import Any

from app.models.enums import AssessmentStatusEnum


CANONICAL_ASSESSMENT_STATUSES = {
    AssessmentStatusEnum.PENDING.value,
    AssessmentStatusEnum.IN_PROGRESS.value,
    AssessmentStatusEnum.COMPLETED.value,
    AssessmentStatusEnum.CANCELLED.value,
}

LEGACY_ASSESSMENT_STATUS_ALIASES = {
    "REQUESTED": AssessmentStatusEnum.PENDING.value,
    "ASSESSMENT_IN_PROGRESS": AssessmentStatusEnum.IN_PROGRESS.value,
    "ASSESSMENT_COMPLETED": AssessmentStatusEnum.COMPLETED.value,
}

OPEN_ASSESSMENT_STATUSES = {
    AssessmentStatusEnum.PENDING.value,
    AssessmentStatusEnum.IN_PROGRESS.value,
    "REQUESTED",
    "ASSESSMENT_IN_PROGRESS",
}

COMPLETED_ASSESSMENT_STATUSES = {
    AssessmentStatusEnum.COMPLETED.value,
    "ASSESSMENT_COMPLETED",
}


def canonical_assessment_status(value: Any) -> str | None:
    """Return the canonical assessment status, preserving unknown values for visibility."""
    if hasattr(value, "value"):
        value = value.value
    status = str(value or "").strip().upper()
    if not status:
        return None
    return LEGACY_ASSESSMENT_STATUS_ALIASES.get(status, status)


def is_open_assessment_status(value: Any) -> bool:
    status = canonical_assessment_status(value)
    return status in {
        AssessmentStatusEnum.PENDING.value,
        AssessmentStatusEnum.IN_PROGRESS.value,
    }


def is_completed_assessment_status(value: Any) -> bool:
    return canonical_assessment_status(value) == AssessmentStatusEnum.COMPLETED.value


def unfinished_assessment_sql(column_sql: str) -> str:
    """SQL predicate for missing/open assessment statuses.

    `column_sql` is an internal hard-coded SQL fragment, not user input.
    """
    values = ", ".join(f"'{status}'" for status in sorted(OPEN_ASSESSMENT_STATUSES))
    return (
        f"({column_sql} IS NULL OR TRIM({column_sql}) = '' "
        f"OR UPPER(TRIM({column_sql})) IN ({values}))"
    )


def completed_assessment_sql(column_sql: str) -> str:
    """SQL predicate for completed assessment statuses, including legacy aliases."""
    values = ", ".join(f"'{status}'" for status in sorted(COMPLETED_ASSESSMENT_STATUSES))
    return f"(UPPER(TRIM({column_sql})) IN ({values}))"
