# -*- coding: utf-8 -*-
"""甘特图依赖关系与关键路径 API"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

router = APIRouter()

CREATE_TABLE_SQL = text(
    """
CREATE TABLE IF NOT EXISTS task_dependencies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    task_id INTEGER NOT NULL,
    depends_on_task_id INTEGER NOT NULL,
    dependency_type VARCHAR(10) DEFAULT "FS",
    lag_days INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""
)

_table_created = False
VALID_DEPENDENCY_TYPES = {"FS", "SS", "FF", "SF"}


class DependencyCreate(BaseModel):
    task_id: int = Field(..., description="任务ID")
    depends_on_task_id: int = Field(..., description="前置任务ID")
    dependency_type: str = Field(default="FS", description="依赖类型：FS/SS/FF/SF")
    lag_days: int = Field(default=0, description="滞后天数")


def _ensure_table(db: Session) -> None:
    global _table_created
    if _table_created:
        return

    try:
        db.execute(CREATE_TABLE_SQL)
        db.commit()
    except Exception:
        db.rollback()
        raise

    _table_created = True


def _parse_to_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue
    return None


def _task_duration_days(task: Dict[str, Any]) -> float:
    start_date = _parse_to_date(task.get("plan_start"))
    end_date = _parse_to_date(task.get("plan_end"))
    if not start_date or not end_date:
        return 1.0
    if end_date < start_date:
        return 1.0
    return float((end_date - start_date).days + 1)


def _has_path(adjacency: Dict[int, Set[int]], start: int, target: int) -> bool:
    stack = [start]
    visited = set()
    while stack:
        node = stack.pop()
        if node == target:
            return True
        if node in visited:
            continue
        visited.add(node)
        stack.extend(adjacency.get(node, set()))
    return False


@router.get("/{project_id}", summary="获取项目甘特图依赖数据")
def get_gantt_data(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: int,
) -> Any:
    _ensure_table(db)

    task_sql = text(
        """
        SELECT id, task_name, plan_start, plan_end, progress_percent, status, stage
        FROM tasks
        WHERE project_id = :project_id
        ORDER BY COALESCE(plan_start, plan_end), id
    """
    )
    dep_sql = text(
        """
        SELECT id, project_id, task_id, depends_on_task_id, dependency_type, lag_days, created_at
        FROM task_dependencies
        WHERE project_id = :project_id
        ORDER BY id
    """
    )

    task_rows = db.execute(task_sql, {"project_id": project_id}).fetchall()
    dep_rows = db.execute(dep_sql, {"project_id": project_id}).fetchall()

    tasks = [
        {
            "id": row.id,
            "task_name": row.task_name,
            "plan_start": row.plan_start,
            "plan_end": row.plan_end,
            "progress_percent": int(row.progress_percent or 0),
            "status": row.status,
            "stage": row.stage,
        }
        for row in task_rows
    ]
    dependencies = [
        {
            "id": row.id,
            "project_id": row.project_id,
            "task_id": row.task_id,
            "depends_on_task_id": row.depends_on_task_id,
            "dependency_type": row.dependency_type or "FS",
            "lag_days": int(row.lag_days or 0),
            "created_at": row.created_at,
        }
        for row in dep_rows
    ]

    return {
        "project_id": project_id,
        "tasks": tasks,
        "dependencies": dependencies,
        "task_count": len(tasks),
        "dependency_count": len(dependencies),
    }


@router.post("/{project_id}/dependency", summary="新增任务依赖关系")
def add_dependency(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: int,
    payload: DependencyCreate,
) -> Any:
    _ensure_table(db)

    dependency_type = (payload.dependency_type or "FS").upper()
    if dependency_type not in VALID_DEPENDENCY_TYPES:
        raise HTTPException(status_code=400, detail="dependency_type 仅支持 FS/SS/FF/SF")
    if payload.task_id == payload.depends_on_task_id:
        raise HTTPException(status_code=400, detail="任务不能依赖自身")

    task_check_sql = text(
        """
        SELECT id FROM tasks
        WHERE project_id = :project_id
          AND id IN (:task_id, :depends_on_task_id)
    """
    )
    valid_task_ids = {
        row.id
        for row in db.execute(
            task_check_sql,
            {
                "project_id": project_id,
                "task_id": payload.task_id,
                "depends_on_task_id": payload.depends_on_task_id,
            },
        ).fetchall()
    }
    if payload.task_id not in valid_task_ids or payload.depends_on_task_id not in valid_task_ids:
        raise HTTPException(status_code=404, detail="任务不存在或不属于该项目")

    dup_sql = text(
        """
        SELECT id FROM task_dependencies
        WHERE project_id = :project_id
          AND task_id = :task_id
          AND depends_on_task_id = :depends_on_task_id
        LIMIT 1
    """
    )
    existing = db.execute(
        dup_sql,
        {
            "project_id": project_id,
            "task_id": payload.task_id,
            "depends_on_task_id": payload.depends_on_task_id,
        },
    ).fetchone()
    if existing:
        raise HTTPException(status_code=400, detail="该依赖关系已存在")

    graph_sql = text(
        """
        SELECT task_id, depends_on_task_id
        FROM task_dependencies
        WHERE project_id = :project_id
    """
    )
    graph_rows = db.execute(graph_sql, {"project_id": project_id}).fetchall()
    adjacency: Dict[int, Set[int]] = {}
    for row in graph_rows:
        adjacency.setdefault(row.depends_on_task_id, set()).add(row.task_id)

    if _has_path(adjacency, payload.task_id, payload.depends_on_task_id):
        raise HTTPException(status_code=400, detail="新增依赖会形成循环依赖")

    insert_sql = text(
        """
        INSERT INTO task_dependencies (
            project_id, task_id, depends_on_task_id, dependency_type, lag_days
        ) VALUES (
            :project_id, :task_id, :depends_on_task_id, :dependency_type, :lag_days
        )
    """
    )
    row_sql = text(
        """
        SELECT id, project_id, task_id, depends_on_task_id, dependency_type, lag_days, created_at
        FROM task_dependencies
        WHERE id = :id
    """
    )

    try:
        result = db.execute(
            insert_sql,
            {
                "project_id": project_id,
                "task_id": payload.task_id,
                "depends_on_task_id": payload.depends_on_task_id,
                "dependency_type": dependency_type,
                "lag_days": payload.lag_days or 0,
            },
        )
        dependency_id = int(result.lastrowid)
        db.commit()
    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"新增依赖失败: {exc}") from exc

    row = db.execute(row_sql, {"id": dependency_id}).fetchone()
    return {
        "message": "依赖关系创建成功",
        "dependency": {
            "id": row.id,
            "project_id": row.project_id,
            "task_id": row.task_id,
            "depends_on_task_id": row.depends_on_task_id,
            "dependency_type": row.dependency_type,
            "lag_days": int(row.lag_days or 0),
            "created_at": row.created_at,
        },
    }


@router.delete("/dependency/{id}", summary="删除任务依赖关系")
def delete_dependency(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    id: int,
) -> Any:
    _ensure_table(db)

    existing_sql = text("SELECT id FROM task_dependencies WHERE id = :id")
    delete_sql = text("DELETE FROM task_dependencies WHERE id = :id")

    existing = db.execute(existing_sql, {"id": id}).fetchone()
    if not existing:
        raise HTTPException(status_code=404, detail="依赖关系不存在")

    try:
        db.execute(delete_sql, {"id": id})
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除依赖失败: {exc}") from exc

    return {"message": "依赖关系删除成功", "id": id}


@router.get("/{project_id}/critical-path", summary="计算项目关键路径")
def get_critical_path(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: int,
) -> Any:
    _ensure_table(db)

    task_sql = text(
        """
        SELECT id, task_name, plan_start, plan_end, progress_percent, status, stage
        FROM tasks
        WHERE project_id = :project_id
        ORDER BY id
    """
    )
    dep_sql = text(
        """
        SELECT task_id, depends_on_task_id, dependency_type, lag_days
        FROM task_dependencies
        WHERE project_id = :project_id
    """
    )

    task_rows = db.execute(task_sql, {"project_id": project_id}).fetchall()
    if not task_rows:
        return {
            "project_id": project_id,
            "critical_path_task_ids": [],
            "critical_path": [],
            "total_duration_days": 0.0,
            "dependency_chain_length": 0,
        }

    tasks: Dict[int, Dict[str, Any]] = {
        row.id: {
            "id": row.id,
            "task_name": row.task_name,
            "plan_start": row.plan_start,
            "plan_end": row.plan_end,
            "progress_percent": int(row.progress_percent or 0),
            "status": row.status,
            "stage": row.stage,
        }
        for row in task_rows
    }
    durations = {task_id: _task_duration_days(task) for task_id, task in tasks.items()}

    dependency_rows = db.execute(dep_sql, {"project_id": project_id}).fetchall()
    predecessors: Dict[int, List[Dict[str, Any]]] = {}
    for row in dependency_rows:
        if row.task_id not in tasks or row.depends_on_task_id not in tasks:
            continue
        predecessors.setdefault(row.task_id, []).append(
            {
                "task_id": row.depends_on_task_id,
                "lag_days": float(row.lag_days or 0),
                "dependency_type": row.dependency_type or "FS",
            }
        )

    memo: Dict[int, float] = {}
    previous: Dict[int, Optional[int]] = {}
    visit_state: Dict[int, int] = {}

    def longest_path_to(task_id: int) -> float:
        state = visit_state.get(task_id, 0)
        if state == 2:
            return memo[task_id]
        if state == 1:
            return durations[task_id]

        visit_state[task_id] = 1
        best_predecessor = None
        best_value = 0.0

        for pred in predecessors.get(task_id, []):
            predecessor_id = pred["task_id"]
            lag_days = float(pred["lag_days"] or 0)
            candidate = longest_path_to(predecessor_id) + lag_days
            if candidate > best_value:
                best_value = candidate
                best_predecessor = predecessor_id

        total = durations[task_id] + best_value
        memo[task_id] = total
        previous[task_id] = best_predecessor
        visit_state[task_id] = 2
        return total

    for task_id in tasks:
        longest_path_to(task_id)

    end_task_id = max(tasks.keys(), key=lambda task_id: memo.get(task_id, 0.0))
    total_duration = round(memo.get(end_task_id, 0.0), 2)

    chain_ids: List[int] = []
    current = end_task_id
    seen = set()
    while current is not None and current not in seen:
        chain_ids.append(current)
        seen.add(current)
        current = previous.get(current)
    chain_ids.reverse()

    chain = [
        {
            "id": task_id,
            "task_name": tasks[task_id]["task_name"],
            "plan_start": tasks[task_id]["plan_start"],
            "plan_end": tasks[task_id]["plan_end"],
            "status": tasks[task_id]["status"],
            "stage": tasks[task_id]["stage"],
            "duration_days": durations[task_id],
        }
        for task_id in chain_ids
    ]

    return {
        "project_id": project_id,
        "critical_path_task_ids": chain_ids,
        "critical_path": chain,
        "total_duration_days": total_duration,
        "dependency_chain_length": max(len(chain_ids) - 1, 0),
    }
