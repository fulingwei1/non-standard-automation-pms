# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 自动化处理 API endpoints
包含：进度预测应用、依赖修复、完整自动处理流程
"""

from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.services.progress_auto_service import ProgressAutoService

router = APIRouter()


# ==================== 自动化处理流程 API ====================

@router.post(
    "/projects/{project_id}/auto-apply-forecast",
    response_model=None,
    summary="自动应用进度预测到任务"
)
def auto_apply_forecast(
    project_id: int,
    auto_block: bool = Query(False, description="是否自动阻塞延迟任务"),
    delay_threshold: int = Query(7, ge=1, description="延迟阈值（天）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
) -> Any:
    """
    自动将进度预测结果应用到任务

    功能：
    1. 自动阻塞严重延迟的任务（超过阈值的任务）
    2. 为高风险任务添加进度日志标记
    3. 记录预测信息到进度日志

    Args:
        project_id: 项目ID
        auto_block: 是否自动阻塞延迟任务
        delay_threshold: 延迟阈值（天），超过此天数会被标记为高风险

    Returns:
        处理结果统计
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 导入预测函数
    from sqlalchemy.orm import joinedload

    from app.api.v1.endpoints.progress.utils import _build_project_forecast
    from app.models.progress import Task

    # 获取所有任务
    tasks = (
        db.query(Task)
        .options(joinedload(Task.progress_logs))
        .filter(Task.project_id == project_id)
        .all()
    )

    if not tasks:
        return {
            "success": False,
            "message": "项目没有任务",
            "data": None
        }

    # 计算进度预测
    forecast = _build_project_forecast(project, tasks)

    # 应用预测
    service = ProgressAutoService(db)
    stats = service.apply_forecast_to_tasks(
        project_id=project_id,
        forecast_items=forecast.tasks,
        auto_block=auto_block,
        delay_threshold=delay_threshold
    )

    return {
        "success": True,
        "message": f"进度预测已应用到 {stats['total']} 个任务",
        "data": {
            "forecast": forecast.model_dump(),
            "application_stats": stats
        }
    }


@router.post(
    "/projects/{project_id}/auto-fix-dependencies",
    response_model=None,
    summary="自动修复依赖问题"
)
def auto_fix_dependencies(
    project_id: int,
    auto_fix_timing: bool = Query(False, description="是否自动修复时序冲突"),
    auto_fix_missing: bool = Query(True, description="是否自动移除缺失依赖"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
) -> Any:
    """
    自动修复依赖问题

    功能：
    1. 自动调整任务计划时间以修复时序冲突
    2. 自动移除指向不存在任务的依赖
    3. 记录修复操作到进度日志

    Args:
        project_id: 项目ID
        auto_fix_timing: 是否自动修复时序冲突
        auto_fix_missing: 是否自动移除缺失依赖

    Returns:
        修复结果统计
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取依赖分析结果
    from app.api.v1.endpoints.progress.utils import _analyze_dependency_graph
    from app.models.progress import Task

    tasks = db.query(Task).filter(Task.project_id == project_id).all()
    task_map = {task.id: task for task in tasks}

    if task_map:
        from app.models.progress import TaskDependency
        dependencies = (
            db.query(TaskDependency)
            .filter(TaskDependency.task_id.in_(task_map.keys()))
            .all()
        )
    else:
        dependencies = []

    # 分析依赖关系
    cycle_paths, issues = _analyze_dependency_graph(task_map, dependencies)

    # 自动修复
    service = ProgressAutoService(db)
    stats = service.auto_fix_dependency_issues(
        project_id=project_id,
        issues=issues,
        auto_fix_timing=auto_fix_timing,
        auto_fix_missing=auto_fix_missing
    )

    return {
        "success": True,
        "message": f"依赖问题修复完成",
        "data": {
            "dependency_check": {
                "has_cycle": bool(cycle_paths),
                "cycle_count": len(cycle_paths),
                "cycle_paths": cycle_paths,
                "issue_count": len(issues),
                "issues": [issue.model_dump() for issue in issues]
            },
            "fix_stats": stats
        }
    }


@router.post(
    "/projects/{project_id}/auto-process-complete",
    response_model=None,
    summary="执行完整的自动处理流程"
)
def run_complete_auto_processing(
    project_id: int,
    options: Dict[str, Any] = Body({
        "auto_block": False,
        "delay_threshold": 7,
        "auto_fix_timing": False,
        "auto_fix_missing": True,
        "send_notifications": True
    }, description="处理选项"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
) -> Any:
    """
    执行完整的自动处理流程（预测应用 + 依赖修复 + 通知）

    处理流程：
    1. 计算进度预测
    2. 应用预测到任务（阻塞、标记）
    3. 分析依赖关系
    4. 自动修复依赖问题
    5. 发送风险通知

    处理选项：
    - auto_block: 是否自动阻塞延迟任务
    - delay_threshold: 延迟阈值（天）
    - auto_fix_timing: 是否自动修复时序冲突
    - auto_fix_missing: 是否自动移除缺失依赖
    - send_notifications: 是否发送通知

    Returns:
        完整的处理结果
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    service = ProgressAutoService(db)

    # 执行自动处理
    result = service.run_auto_processing(
        project_id=project_id,
        options=options
    )

    if result.get("success"):
        return {
            "success": True,
            "message": "自动处理流程执行成功",
            "data": result
        }
    else:
        error_msg = result.get("error", "未知错误")
        raise HTTPException(
            status_code=500,
            detail=f"自动处理失败: {error_msg}"
        )


@router.get(
    "/projects/{project_id}/auto-preview",
    status_code=200,
    summary="预览自动处理结果（不实际执行）"
)
def preview_auto_processing(
    project_id: int,
    auto_block: bool = Query(False, description="是否自动阻塞延迟任务"),
    delay_threshold: int = Query(7, ge=1, description="延迟阈值"),
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    预览自动处理结果（不实际执行修改）

    功能：
    1. 计算进度预测
    2. 分析依赖问题
    3. 返回预览结果，供用户确认

    Returns:
        预览结果
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 计算预测
    from sqlalchemy.orm import joinedload

    from app.api.v1.endpoints.progress.utils import (
        _analyze_dependency_graph,
        _build_project_forecast,
    )
    from app.models.progress import Task

    tasks = (
        db.query(Task)
        .options(joinedload(Task.progress_logs))
        .filter(Task.project_id == project_id)
        .all()
    )

    if not tasks:
        return {
            "success": False,
            "message": "项目没有任务",
            "data": None
        }

    # 进度预测
    forecast = _build_project_forecast(project, tasks)

    # 依赖分析
    task_map = {task.id: task for task in tasks}
    if task_map:
        from app.models.progress import TaskDependency
        dependencies = (
            db.query(TaskDependency)
            .filter(TaskDependency.task_id.in_(task_map.keys()))
            .all()
        )
    else:
        dependencies = []

    cycle_paths, issues = _analyze_dependency_graph(task_map, dependencies)

    # 预览处理结果
    preview = {
        "forecast": forecast.model_dump(),
        "dependency_check": {
            "has_cycle": bool(cycle_paths),
            "cycle_count": len(cycle_paths),
            "cycle_paths": cycle_paths,
            "issue_count": len(issues),
            "issues": [issue.model_dump() for issue in issues]
        },
        "preview_actions": {
            "will_block": [
                {
                    "task_id": item.task_id,
                    "task_name": item.task_name,
                    "delay_days": item.delay_days,
                    "reason": f"延迟 {item.delay_days} 天，超过阈值 {delay_threshold} 天"
                }
                for item in forecast.tasks
                if item.delay_days and item.delay_days > delay_threshold
            ],
            "will_fix_timing": len([
                issue for issue in issues
                if issue.issue_type == "TIMING_CONFLICT"
            ]),
            "will_remove_missing": len([
                issue for issue in issues
                if issue.issue_type == "MISSING_PREDECESSOR"
            ]),
            "will_send_notifications": (
                len([item for item in forecast.tasks if item.critical]) > 0 or
                len(cycle_paths) > 0 or
                len([i for i in issues if (i.severity or "").upper() in ["HIGH", "URGENT"]]) > 0
            )
        }
    }

    return {
        "success": True,
        "message": "自动处理预览完成",
        "data": preview
    }


@router.post(
    "/projects/batch/auto-process",
    response_model=None,
    summary="批量执行自动处理"
)
def batch_auto_process(
    project_ids: list[int] = Body(..., description="项目ID列表"),
    options: Dict[str, Any] = Body({
        "auto_block": False,
        "delay_threshold": 7,
        "auto_fix_timing": False,
        "auto_fix_missing": True,
        "send_notifications": True
    }, description="处理选项"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user)
) -> Any:
    """
    批量执行自动处理流程

    Args:
        project_ids: 项目ID列表（最多20个项目）
        options: 处理选项

    Returns:
        批量处理结果
    """
    if len(project_ids) > 20:
        raise HTTPException(status_code=400, detail="单次最多处理20个项目")

    if not project_ids:
        raise HTTPException(status_code=400, detail="项目ID列表不能为空")

    service = ProgressAutoService(db)

    results = []
    success_count = 0
    failed_count = 0
    errors = []

    for project_id in project_ids:
        try:
            result = service.run_auto_processing(
                project_id=project_id,
                options=options
            )

            if result.get("success"):
                success_count += 1
            else:
                failed_count += 1
                errors.append({
                    "project_id": project_id,
                    "error": result.get("error", "未知错误")
                })

            results.append({
                "project_id": project_id,
                "success": result.get("success", False),
                "data": result
            })

        except Exception as e:
            failed_count += 1
            errors.append({
                "project_id": project_id,
                "error": str(e)
            })
            results.append({
                "project_id": project_id,
                "success": False,
                "error": str(e)
            })

    return {
        "success": True,
        "message": f"批量处理完成：成功 {success_count}，失败 {failed_count}",
        "data": {
            "total": len(project_ids),
            "success_count": success_count,
            "failed_count": failed_count,
            "results": results,
            "errors": errors
        }
    }
