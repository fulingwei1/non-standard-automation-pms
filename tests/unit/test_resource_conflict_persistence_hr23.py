# -*- coding: utf-8 -*-
"""HR-23: resource conflict detection must persist conflicts for mediation."""

from datetime import date
from decimal import Decimal
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_cross_project_overlap(db_session):
    from app.models.project import Project, ProjectStageResourcePlan
    from app.models.user import User

    employee = User(
        username=_code("hr23-employee").lower(),
        password_hash="not-used",
        real_name="HR23冲突员工",
        department_id=23,
        department="资源调度部",
        is_active=True,
    )
    db_session.add(employee)
    db_session.flush()

    project_a = Project(
        project_code=_code("HR23A"),
        project_name="HR23项目A",
        status="ST01",
        stage="S1",
        health="H1",
        is_active=True,
    )
    project_b = Project(
        project_code=_code("HR23B"),
        project_name="HR23项目B",
        status="ST01",
        stage="S1",
        health="H1",
        is_active=True,
    )
    db_session.add_all([project_a, project_b])
    db_session.flush()

    plan_a = ProjectStageResourcePlan(
        project_id=project_a.id,
        stage_code="S2",
        role_code="ME",
        role_name="机械工程师",
        headcount=1,
        allocation_pct=Decimal("70"),
        assigned_employee_id=employee.id,
        assignment_status="ASSIGNED",
        planned_start=date(2026, 7, 1),
        planned_end=date(2026, 7, 20),
    )
    plan_b = ProjectStageResourcePlan(
        project_id=project_b.id,
        stage_code="S3",
        role_code="ME",
        role_name="机械工程师",
        headcount=1,
        allocation_pct=Decimal("60"),
        assigned_employee_id=employee.id,
        assignment_status="ASSIGNED",
        planned_start=date(2026, 7, 10),
        planned_end=date(2026, 7, 30),
    )
    db_session.add_all([plan_a, plan_b])
    db_session.commit()
    return employee, project_a, project_b, plan_a, plan_b


def test_project_conflict_check_persists_cross_project_conflict(db_session):
    from app.api.v1.endpoints.analytics.resource_conflicts import check_project_conflicts
    from app.models.project import ResourceConflict

    employee, project_a, project_b, plan_a, plan_b = _seed_cross_project_overlap(db_session)

    response = check_project_conflicts(
        project_id=project_a.id,
        db=db_session,
        current_user=employee,
    )

    conflict = db_session.query(ResourceConflict).one()

    assert response.data["has_conflicts"] is True
    assert response.data["conflict_count"] == 1
    assert response.data["new_conflicts"][0]["plan_a_id"] == plan_a.id
    assert response.data["new_conflicts"][0]["plan_b_id"] == plan_b.id
    assert response.data["new_conflicts"][0]["plan_b_project_id"] == project_b.id
    assert conflict.employee_id == employee.id
    assert conflict.plan_a_id == plan_a.id
    assert conflict.plan_b_id == plan_b.id
    assert conflict.overlap_start == date(2026, 7, 10)
    assert conflict.overlap_end == date(2026, 7, 20)
    assert conflict.total_allocation == Decimal("130.00")
    assert conflict.over_allocation == Decimal("30.00")
    assert conflict.severity == "MEDIUM"
    assert conflict.is_resolved == 0

    check_project_conflicts(project_id=project_a.id, db=db_session, current_user=employee)

    assert db_session.query(ResourceConflict).count() == 1

