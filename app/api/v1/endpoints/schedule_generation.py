# -*- coding: utf-8 -*-
"""
AI 智能排程 API
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.schedule_generation_service import ScheduleGenerationService

router = APIRouter()


@router.post("/projects/{project_id}/generate-schedule", summary="AI 生成项目计划")
def generate_schedule(
    project_id: int = Path(..., description="项目 ID"),
    mode: str = Query("NORMAL", description="计划模式 NORMAL/INTENSIVE"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    AI 生成项目进度计划
    
    模式：
    - NORMAL: 正常强度（标准工期）
    - INTENSIVE: 高强度（工期缩短 30%）
    
    考虑因素：
    1. 历史类似项目数据
    2. 团队效率系数（AI 能力/多项目能力）
    3. 任务依赖关系
    """
    service = ScheduleGenerationService(db)
    schedule = service.generate_schedule(project_id, mode)
    
    if 'error' in schedule:
        raise HTTPException(status_code=404, detail=schedule['error'])
    
    return schedule


@router.post("/projects/{project_id}/generate-both-modes", summary="生成两种模式计划")
def generate_both_modes(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    同时生成正常强度和高强度两种计划
    
    供项目经理对比选择
    """
    service = ScheduleGenerationService(db)
    
    normal_schedule = service.generate_schedule(project_id, 'NORMAL')
    intensive_schedule = service.generate_schedule(project_id, 'INTENSIVE')
    
    if 'error' in normal_schedule:
        raise HTTPException(status_code=404, detail=normal_schedule['error'])
    
    return {
        'project_id': project_id,
        'normal_mode': normal_schedule,
        'intensive_mode': intensive_schedule,
        'comparison': {
            'time_saved': normal_schedule['total_days'] - intensive_schedule['total_days'],
            'time_saved_percentage': round(
                (normal_schedule['total_days'] - intensive_schedule['total_days']) 
                / normal_schedule['total_days'] * 100, 1
            ),
        },
    }


@router.post("/projects/{project_id}/save-schedule", summary="保存项目计划")
def save_schedule(
    project_id: int = Path(..., description="项目 ID"),
    schedule_data: dict = Body(..., description="计划数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """保存项目计划"""
    service = ScheduleGenerationService(db)
    
    schedule_data['project_id'] = project_id
    plan = service.save_schedule_plan(schedule_data, current_user.id)
    
    return {
        'plan_id': plan.id,
        'plan_no': plan.plan_no,
        'status': plan.status,
        'total_days': plan.total_days,
    }


@router.get("/schedule-plans/{plan_id}", summary="获取计划详情")
def get_schedule_plan(
    plan_id: int = Path(..., description="计划 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取计划详情"""
    from app.models.project_schedule import ProjectSchedulePlan, ScheduleTask
    import json
    
    plan = db.query(ProjectSchedulePlan).filter(
        ProjectSchedulePlan.id == plan_id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    
    tasks = db.query(ScheduleTask).filter(
        ScheduleTask.schedule_plan_id == plan_id
    ).order_by(ScheduleTask.planned_start_date).all()
    
    return {
        'plan': plan,
        'tasks': [
            {
                'id': t.id,
                'task_no': t.task_no,
                'task_name': t.task_name,
                'phase': t.phase,
                'planned_start_date': t.planned_start_date.isoformat() if t.planned_start_date else None,
                'planned_end_date': t.planned_end_date.isoformat() if t.planned_end_date else None,
                'duration_days': t.duration_days,
                'assigned_engineer': t.assigned_engineer_name,
                'status': t.status,
                'progress': t.progress_percentage,
            }
            for t in tasks
        ],
    }


@router.put("/schedule-tasks/{task_id}", summary="调整任务")
def update_task(
    task_id: int = Path(..., description="任务 ID"),
    task_data: dict = Body(..., description="任务数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """调整任务（工期/负责人/时间）"""
    from app.models.project_schedule import ScheduleTask
    from datetime import date
    
    task = db.query(ScheduleTask).filter(ScheduleTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    # 更新字段
    if 'duration_days' in task_data:
        task.duration_days = task_data['duration_days']
    if 'planned_start_date' in task_data:
        task.planned_start_date = date.fromisoformat(task_data['planned_start_date'])
    if 'planned_end_date' in task_data:
        task.planned_end_date = date.fromisoformat(task_data['planned_end_date'])
    if 'assigned_engineer_id' in task_data:
        task.assigned_engineer_id = task_data['assigned_engineer_id']
    if 'assigned_engineer_name' in task_data:
        task.assigned_engineer_name = task_data['assigned_engineer_name']
    
    db.commit()
    
    return {'message': '任务已更新', 'task_id': task_id}
