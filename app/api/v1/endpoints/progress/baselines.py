# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 计划基线管理
包含：基线CRUD、基线对比分析、偏差分析、关键路径计算
"""

from collections import deque
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.progress import BaselineTask, ScheduleBaseline, Task, TaskDependency
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.progress import (
    BaselineCreate,
    BaselineListResponse,
    BaselineResponse,
)

router = APIRouter()


# ==================== 计划基线管理 ====================

@router.get("/projects/{project_id}/baselines", response_model=BaselineListResponse, status_code=status.HTTP_200_OK)
def read_project_baselines(
    project_id: int,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目计划基线列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(ScheduleBaseline).filter(ScheduleBaseline.project_id == project_id)

    total = query.count()
    offset = (page - 1) * page_size
    baselines = query.order_by(ScheduleBaseline.created_at.desc()).offset(offset).limit(page_size).all()

    # 补充任务数量
    items = []
    for baseline in baselines:
        task_count = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline.id).count()
        baseline_dict = {
            "id": baseline.id,
            "project_id": baseline.project_id,
            "baseline_no": baseline.baseline_no,
            "created_by": baseline.created_by,
            "task_count": task_count,
            "created_at": baseline.created_at,
            "updated_at": baseline.updated_at
        }
        items.append(baseline_dict)

    return BaselineListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/projects/{project_id}/baselines", response_model=BaselineResponse, status_code=status.HTTP_201_CREATED)
def create_project_baseline(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    baseline_in: BaselineCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建项目计划基线
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 生成基线编号（如果未提供）
    baseline_no = baseline_in.baseline_no
    if not baseline_no:
        # 查找已有基线数量，生成下一个编号
        existing_count = db.query(ScheduleBaseline).filter(ScheduleBaseline.project_id == project_id).count()
        baseline_no = f"V{existing_count + 1}"

    # 创建基线
    baseline = ScheduleBaseline(
        project_id=project_id,
        baseline_no=baseline_no,
        created_by=current_user.id
    )
    db.add(baseline)
    db.flush()  # 获取baseline.id

    # 获取项目所有任务，创建基线快照
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    for task in tasks:
        baseline_task = BaselineTask(
            baseline_id=baseline.id,
            task_id=task.id,
            plan_start=task.plan_start,
            plan_end=task.plan_end,
            weight=task.weight
        )
        db.add(baseline_task)

    db.commit()
    db.refresh(baseline)

    # 补充任务数量
    task_count = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline.id).count()

    return {
        "id": baseline.id,
        "project_id": baseline.project_id,
        "baseline_no": baseline.baseline_no,
        "created_by": baseline.created_by,
        "task_count": task_count,
        "created_at": baseline.created_at,
        "updated_at": baseline.updated_at
    }


@router.get("/baselines/{baseline_id}", response_model=BaselineResponse, status_code=status.HTTP_200_OK)
def read_baseline(
    baseline_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取计划基线详情
    """
    baseline = db.query(ScheduleBaseline).filter(ScheduleBaseline.id == baseline_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="计划基线不存在")

    task_count = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline_id).count()

    return {
        "id": baseline.id,
        "project_id": baseline.project_id,
        "baseline_no": baseline.baseline_no,
        "created_by": baseline.created_by,
        "task_count": task_count,
        "created_at": baseline.created_at,
        "updated_at": baseline.updated_at
    }


@router.get("/baselines/{baseline_id}/compare", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def compare_baseline(
    baseline_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度基线对比分析
    对比基线计划与实际进度
    """
    baseline = db.query(ScheduleBaseline).filter(ScheduleBaseline.id == baseline_id).first()
    if not baseline:
        raise HTTPException(status_code=404, detail="计划基线不存在")

    # 获取基线任务
    baseline_tasks = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline_id).all()

    # 获取当前实际任务
    current_tasks = db.query(Task).filter(Task.project_id == baseline.project_id).all()

    # 构建任务映射
    task_map = {t.task_id: t for t in baseline_tasks}

    # 对比分析
    comparison_items = []
    total_deviation_days = 0
    delayed_tasks = 0
    ahead_tasks = 0
    on_schedule_tasks = 0

    for current_task in current_tasks:
        baseline_task = task_map.get(current_task.id)
        if not baseline_task:
            continue

        # 计算偏差
        if current_task.plan_end and baseline_task.plan_end:
            deviation_days = (current_task.plan_end - baseline_task.plan_end).days
            total_deviation_days += deviation_days

            if deviation_days > 0:
                delayed_tasks += 1
            elif deviation_days < 0:
                ahead_tasks += 1
            else:
                on_schedule_tasks += 1

        comparison_items.append({
            "task_id": current_task.id,
            "task_name": current_task.task_name,
            "baseline_start": baseline_task.plan_start.isoformat() if baseline_task.plan_start else None,
            "baseline_end": baseline_task.plan_end.isoformat() if baseline_task.plan_end else None,
            "actual_start": current_task.actual_start.isoformat() if current_task.actual_start else None,
            "actual_end": current_task.actual_end.isoformat() if current_task.actual_end else None,
            "plan_start": current_task.plan_start.isoformat() if current_task.plan_start else None,
            "plan_end": current_task.plan_end.isoformat() if current_task.plan_end else None,
            "deviation_days": (current_task.plan_end - baseline_task.plan_end).days if (current_task.plan_end and baseline_task.plan_end) else None,
            "progress": float(current_task.progress) if current_task.progress else 0.0
        })

    avg_deviation = total_deviation_days / len(comparison_items) if comparison_items else 0.0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "baseline_id": baseline_id,
            "baseline_no": baseline.baseline_no,
            "project_id": baseline.project_id,
            "summary": {
                "total_tasks": len(comparison_items),
                "delayed_tasks": delayed_tasks,
                "ahead_tasks": ahead_tasks,
                "on_schedule_tasks": on_schedule_tasks,
                "avg_deviation_days": round(avg_deviation, 2),
                "total_deviation_days": total_deviation_days
            },
            "comparison": comparison_items
        }
    )


@router.get("/projects/{project_id}/deviation-analysis", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def analyze_progress_deviation(
    project_id: int,
    db: Session = Depends(deps.get_db),
    baseline_id: Optional[int] = Query(None, description="基线ID（不提供则使用最新基线）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    进度偏差分析
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取基线
    if baseline_id:
        baseline = db.query(ScheduleBaseline).filter(ScheduleBaseline.id == baseline_id).first()
    else:
        baseline = db.query(ScheduleBaseline).filter(
            ScheduleBaseline.project_id == project_id
        ).order_by(ScheduleBaseline.created_at.desc()).first()

    if not baseline:
        raise HTTPException(status_code=404, detail="未找到计划基线")

    # 获取任务数据
    baseline_tasks = db.query(BaselineTask).filter(BaselineTask.baseline_id == baseline.id).all()
    current_tasks = db.query(Task).filter(Task.project_id == project_id).all()

    task_map = {t.task_id: t for t in baseline_tasks}

    # 偏差统计
    deviations = []
    for task in current_tasks:
        baseline_task = task_map.get(task.id)
        if not baseline_task or not task.plan_end or not baseline_task.plan_end:
            continue

        deviation = (task.plan_end - baseline_task.plan_end).days
        deviations.append({
            "task_id": task.id,
            "task_name": task.task_name,
            "deviation_days": deviation,
            "baseline_end": baseline_task.plan_end.isoformat(),
            "actual_end": task.plan_end.isoformat()
        })

    # 按偏差天数分组统计
    deviation_ranges = {
        "严重延期 (>7天)": len([d for d in deviations if d["deviation_days"] > 7]),
        "延期 (1-7天)": len([d for d in deviations if 1 <= d["deviation_days"] <= 7]),
        "按时完成": len([d for d in deviations if d["deviation_days"] == 0]),
        "提前完成 (1-7天)": len([d for d in deviations if -7 <= d["deviation_days"] < 0]),
        "大幅提前 (>7天)": len([d for d in deviations if d["deviation_days"] < -7])
    }

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "baseline_id": baseline.id,
            "baseline_no": baseline.baseline_no,
            "deviation_ranges": deviation_ranges,
            "total_tasks": len(deviations),
            "avg_deviation": round(sum(d["deviation_days"] for d in deviations) / len(deviations), 2) if deviations else 0.0,
            "details": deviations
        }
    )


@router.get("/projects/{project_id}/critical-path", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def calculate_critical_path(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    关键路径计算
    使用拓扑排序和最长路径算法计算关键路径
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取所有任务及其依赖
    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    dependencies = db.query(TaskDependency).join(Task).filter(Task.project_id == project_id).all()

    # 构建任务图
    task_dict = {task.id: task for task in tasks}
    in_degree = {task.id: 0 for task in tasks}
    graph = {task.id: [] for task in tasks}

    for dep in dependencies:
        if dep.depends_on_task_id in graph:
            graph[dep.depends_on_task_id].append(dep.task_id)
            in_degree[dep.task_id] = in_degree.get(dep.task_id, 0) + 1

    # 拓扑排序 + 最长路径计算
    queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
    earliest_start = {task_id: 0 for task_id in task_dict.keys()}

    # 计算最早开始时间
    while queue:
        task_id = queue.popleft()
        task = task_dict[task_id]
        duration = 0
        if task.plan_start and task.plan_end:
            duration = (task.plan_end - task.plan_start).days

        for next_task_id in graph[task_id]:
            in_degree[next_task_id] -= 1
            if in_degree[next_task_id] == 0:
                queue.append(next_task_id)

            # 更新最早开始时间
            earliest_start[next_task_id] = max(
                earliest_start.get(next_task_id, 0),
                earliest_start[task_id] + duration
            )

    # 计算最晚开始时间（反向）
    max_duration = max(earliest_start.values()) if earliest_start else 0
    latest_start = {task_id: max_duration for task_id in task_dict.keys()}

    # 找出关键路径（最早开始时间 = 最晚开始时间的任务）
    critical_path = []
    for task_id in task_dict.keys():
        task = task_dict[task_id]
        duration = 0
        if task.plan_start and task.plan_end:
            duration = (task.plan_end - task.plan_start).days

        es = earliest_start.get(task_id, 0)
        ls = latest_start.get(task_id, max_duration)

        if es == ls or (es + duration) == max_duration:
            critical_path.append({
                "task_id": task_id,
                "task_name": task.task_name,
                "earliest_start": es,
                "latest_start": ls,
                "duration": duration,
                "slack": ls - es
            })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "total_duration": max_duration,
            "critical_path": sorted(critical_path, key=lambda x: x["earliest_start"]),
            "critical_path_length": len(critical_path)
        }
    )
