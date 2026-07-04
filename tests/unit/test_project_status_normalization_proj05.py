from datetime import date
from types import SimpleNamespace

from app.models import Project, ProjectStatusLog


def _make_project(db, code, *, status, stage, is_archived=False, **overrides):
    project = Project(
        project_code=code,
        project_name=f"{code} 项目",
        customer_name="测试客户",
        status=status,
        stage=stage,
        health=overrides.pop("health", "H1"),
        is_active=overrides.pop("is_active", True),
        is_archived=is_archived,
        planned_end_date=overrides.pop("planned_end_date", date(2026, 8, 1)),
        actual_end_date=overrides.pop("actual_end_date", None),
        **overrides,
    )
    db.add(project)
    db.flush()
    return project


def test_legacy_project_state_normalization_rules():
    from app.services.project_status_normalization import (
        normalize_legacy_project_state,
        project_status_bucket,
    )

    assert normalize_legacy_project_state("COMPLETED", "S3") == {
        "status": "ST30",
        "stage": "S9",
        "is_archived": False,
    }
    assert normalize_legacy_project_state("EXECUTING", "S5") == {
        "status": "ST10",
        "stage": "S5",
        "is_archived": False,
    }
    assert normalize_legacy_project_state("archived", "S4") == {
        "status": "ST07",
        "stage": "S4",
        "is_archived": True,
    }
    assert project_status_bucket("COMPLETED", "S3") == "ST30"
    assert project_status_bucket("EXECUTING", "S5") == "ST10"
    assert project_status_bucket("archived", "S4") == "ARCHIVED"


def test_project_open_and_delivery_scope_predicates(db_session):
    from app.services.project_status_normalization import (
        is_project_open_expr,
        project_delivery_scope_expr,
    )

    open_legacy = _make_project(db_session, "PROJ05-OPEN-LEGACY", status="EXECUTING", stage="S4")
    open_st = _make_project(db_session, "PROJ05-OPEN-ST", status="ST10", stage="S5")
    _make_project(
        db_session,
        "PROJ05-COMPLETED-LEGACY",
        status="COMPLETED",
        stage="S3",
        actual_end_date=date(2026, 7, 1),
    )
    _make_project(db_session, "PROJ05-COMPLETED-ST", status="ST30", stage="S9")
    archived = _make_project(db_session, "PROJ05-ARCHIVED", status="ST03", stage="S2", is_archived=True)
    cancelled = _make_project(db_session, "PROJ05-CANCELLED", status="ST99", stage="S5")
    db_session.commit()

    open_ids = {
        project.id
        for project in db_session.query(Project).filter(is_project_open_expr(Project)).all()
    }
    delivery_ids = {
        project.id
        for project in db_session.query(Project).filter(project_delivery_scope_expr(Project)).all()
    }

    assert open_legacy.id in open_ids
    assert open_st.id in open_ids
    assert open_legacy.id in delivery_ids
    assert open_st.id in delivery_ids
    assert archived.id not in open_ids
    assert archived.id not in delivery_ids
    assert cancelled.id not in open_ids
    assert cancelled.id not in delivery_ids
    assert len(open_ids & delivery_ids) >= 2


def test_apply_project_status_filter_understands_legacy_lifecycle_statuses(db_session):
    from app.services.project_status_normalization import apply_project_status_filter

    executing_legacy = _make_project(db_session, "PROJ05-FILTER-EXEC", status="EXECUTING", stage="S4")
    executing_st = _make_project(db_session, "PROJ05-FILTER-ST", status="ST15", stage="S6")
    completed_legacy = _make_project(
        db_session,
        "PROJ05-FILTER-COMPLETE",
        status="COMPLETED",
        stage="S2",
        actual_end_date=date(2026, 7, 2),
    )
    completed_st = _make_project(db_session, "PROJ05-FILTER-ST30", status="ST30", stage="S9")
    archived = _make_project(
        db_session, "PROJ05-FILTER-ARCHIVED", status="ST03", stage="S2", is_archived=True
    )
    db_session.commit()

    executing_ids = {
        project.id
        for project in apply_project_status_filter(
            db_session.query(Project), "EXECUTING", Project
        ).all()
    }
    completed_ids = {
        project.id
        for project in apply_project_status_filter(
            db_session.query(Project), "COMPLETED", Project
        ).all()
    }

    assert {executing_legacy.id, executing_st.id}.issubset(executing_ids)
    assert completed_legacy.id not in executing_ids
    assert {completed_legacy.id, completed_st.id}.issubset(completed_ids)
    assert archived.id not in completed_ids


def test_archive_preserves_project_status_and_logs_real_old_status(db_session, monkeypatch):
    from app.api.v1.endpoints.projects.archive import archive_project

    project = _make_project(db_session, "PROJ05-ARCHIVE-WRITE", status="ST03", stage="S2")
    db_session.commit()

    monkeypatch.setattr(
        "app.utils.permission_helpers.check_project_access_or_raise",
        lambda db, current_user, project_id: project,
    )

    archive_project(
        db=db_session,
        project_id=project.id,
        reason="资料封存",
        current_user=SimpleNamespace(id=7, is_superuser=True),
    )
    db_session.refresh(project)

    log = (
        db_session.query(ProjectStatusLog)
        .filter(ProjectStatusLog.project_id == project.id, ProjectStatusLog.change_type == "ARCHIVE")
        .one()
    )

    assert project.is_archived is True
    assert project.status == "ST03"
    assert log.old_status == "ST03"
    assert log.new_status == "ST03"
