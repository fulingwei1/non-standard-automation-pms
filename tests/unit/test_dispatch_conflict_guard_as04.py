# -*- coding: utf-8 -*-
"""AS-04: installation dispatch assignment must respect engineer conflicts."""

from datetime import date

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.installation_dispatch.workflow import _ensure_no_dispatch_conflict
from app.models.engineer_capacity import EngineerTaskAssignment
from app.models.installation_dispatch import InstallationDispatchOrder


def test_dispatch_assignment_blocks_overlapping_engineer_task(db_session):
    existing = EngineerTaskAssignment(
        assignment_no="AS04-EXISTING",
        engineer_id=1,
        project_id=1001,
        task_type="现场调试",
        task_description="既有现场任务",
        estimated_hours=8,
        planned_start_date=date(2026, 7, 1),
        planned_end_date=date(2026, 7, 10),
        status="PENDING",
        priority=50,
    )
    db_session.add(existing)
    db_session.flush()

    order = InstallationDispatchOrder(
        id=9001,
        order_no="AS04-DISPATCH",
        project_id=1002,
        customer_id=1,
        task_type="DEBUGGING",
        task_title="冲突派工",
        scheduled_date=date(2026, 7, 5),
        estimated_hours=8,
        status="PENDING",
        priority="NORMAL",
    )

    with pytest.raises(HTTPException) as exc_info:
        _ensure_no_dispatch_conflict(db_session, order, assigned_to_id=1)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["conflict_count"] == 1
    assert exc_info.value.detail["conflicts"][0]["conflict_project_id"] == 1001
