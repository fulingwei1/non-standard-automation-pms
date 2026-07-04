from datetime import date
from types import SimpleNamespace

from app.api.v1.endpoints import gantt_dependency
from app.api.v1.endpoints.gantt_dependency import (
    DependencyCreate,
    add_dependency,
    get_critical_path,
)
from app.models import Project
from app.models.task_center import TaskUnified


def _create_project(db_session, code="PJ-PROJ09"):
    project = Project(
        project_code=code,
        project_name="甘特依赖级联测试",
        customer_name="测试客户",
        stage="S4",
        status="ST07",
        health="H1",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def _create_task(
    db_session,
    *,
    project_id,
    code,
    title,
    start,
    end,
):
    task = TaskUnified(
        task_code=code,
        title=title,
        task_type="PROJECT",
        project_id=project_id,
        assignee_id=1,
        status="IN_PROGRESS",
        progress=0,
        plan_start_date=start,
        plan_end_date=end,
        is_active=True,
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)
    return task


def test_add_fs_dependency_cascades_successor_schedule(db_session, monkeypatch):
    monkeypatch.setattr(gantt_dependency, "_table_created", False)
    project = _create_project(db_session, "PJ-PROJ09-FS")
    user = SimpleNamespace(id=1)

    task_a = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-A",
        title="前置任务 A",
        start=date(2026, 7, 1),
        end=date(2026, 7, 3),
    )
    task_b = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-B",
        title="后继任务 B",
        start=date(2026, 7, 2),
        end=date(2026, 7, 3),
    )
    task_c = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-C",
        title="后继任务 C",
        start=date(2026, 7, 3),
        end=date(2026, 7, 4),
    )

    add_dependency(
        db=db_session,
        current_user=user,
        project_id=project.id,
        payload=DependencyCreate(
            task_id=task_c.id,
            depends_on_task_id=task_b.id,
            dependency_type="FS",
            lag_days=0,
        ),
    )

    response = add_dependency(
        db=db_session,
        current_user=user,
        project_id=project.id,
        payload=DependencyCreate(
            task_id=task_b.id,
            depends_on_task_id=task_a.id,
            dependency_type="FS",
            lag_days=0,
        ),
    )

    db_session.refresh(task_b)
    db_session.refresh(task_c)

    assert task_b.plan_start_date == date(2026, 7, 4)
    assert task_b.plan_end_date == date(2026, 7, 5)
    assert task_c.plan_start_date == date(2026, 7, 6)
    assert task_c.plan_end_date == date(2026, 7, 7)
    assert response["schedule_adjustments"] == [
        {
            "task_id": task_b.id,
            "old_plan_start": "2026-07-02",
            "old_plan_end": "2026-07-03",
            "new_plan_start": "2026-07-04",
            "new_plan_end": "2026-07-05",
        },
        {
            "task_id": task_c.id,
            "old_plan_start": "2026-07-04",
            "old_plan_end": "2026-07-05",
            "new_plan_start": "2026-07-06",
            "new_plan_end": "2026-07-07",
        },
    ]


def test_add_ss_dependency_uses_dependency_type_semantics(db_session, monkeypatch):
    monkeypatch.setattr(gantt_dependency, "_table_created", False)
    project = _create_project(db_session, "PJ-PROJ09-SS")

    predecessor = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-SS-A",
        title="SS 前置任务",
        start=date(2026, 7, 1),
        end=date(2026, 7, 5),
    )
    successor = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-SS-B",
        title="SS 后继任务",
        start=date(2026, 7, 1),
        end=date(2026, 7, 2),
    )

    add_dependency(
        db=db_session,
        current_user=SimpleNamespace(id=1),
        project_id=project.id,
        payload=DependencyCreate(
            task_id=successor.id,
            depends_on_task_id=predecessor.id,
            dependency_type="SS",
            lag_days=2,
        ),
    )

    db_session.refresh(successor)

    assert successor.plan_start_date == date(2026, 7, 3)
    assert successor.plan_end_date == date(2026, 7, 4)


def test_critical_path_uses_dependency_type_semantics(db_session, monkeypatch):
    monkeypatch.setattr(gantt_dependency, "_table_created", False)
    project = _create_project(db_session, "PJ-PROJ09-CP")

    predecessor = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-CP-A",
        title="关键路径长任务",
        start=date(2026, 7, 1),
        end=date(2026, 7, 5),
    )
    successor = _create_task(
        db_session,
        project_id=project.id,
        code="TSK-PROJ09-CP-B",
        title="SS 并行短任务",
        start=date(2026, 7, 1),
        end=date(2026, 7, 2),
    )

    add_dependency(
        db=db_session,
        current_user=SimpleNamespace(id=1),
        project_id=project.id,
        payload=DependencyCreate(
            task_id=successor.id,
            depends_on_task_id=predecessor.id,
            dependency_type="SS",
            lag_days=2,
        ),
    )

    result = get_critical_path(
        db=db_session,
        current_user=SimpleNamespace(id=1),
        project_id=project.id,
    )

    assert result["total_duration_days"] == 5.0
    assert result["critical_path_task_ids"] == [predecessor.id]
