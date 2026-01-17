# -*- coding: utf-8 -*-
"""
进度跟踪模块 - 统计报表
包含：任务完成率统计、里程碑达成率统计、延期原因统计
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.organization import Department
from app.models.progress import Task
from app.models.project import Project, ProjectMilestone
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.progress import (
    DelayReasonItem,
    DelayReasonsResponse,
    MilestoneRateResponse,
)

router = APIRouter()


# ==================== 任务完成率统计 ====================

@router.get("/reports/task-completion-rate", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_task_completion_rate(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务完成率统计（按部门/人员）
    """
    query = db.query(Task)

    # 筛选条件
    if project_id:
        query = query.filter(Task.project_id == project_id)

    if owner_id:
        query = query.filter(Task.owner_id == owner_id)
    elif department_id:
        # 通过负责人关联部门
        query = query.join(User).filter(User.department_id == department_id)

    if start_date:
        query = query.filter(Task.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.filter(Task.created_at <= datetime.combine(end_date, datetime.max.time()))

    tasks = query.all()

    if not tasks:
        return ResponseModel(
            code=200,
            message="success",
            data={
                "total_tasks": 0,
                "completed_tasks": 0,
                "completion_rate": 0.0,
                "by_department": [],
                "by_owner": []
            }
        )

    total_tasks = len(tasks)
    completed_tasks = len([t for t in tasks if t.status == "DONE"])
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0

    # 按部门统计
    dept_stats = {}
    for task in tasks:
        if task.owner_id:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            if owner and owner.department_id:
                dept = db.query(Department).filter(Department.id == owner.department_id).first()
                dept_name = dept.dept_name if dept else "未分配部门"
                dept_id = owner.department_id

                if dept_id not in dept_stats:
                    dept_stats[dept_id] = {
                        "department_id": dept_id,
                        "department_name": dept_name,
                        "total_tasks": 0,
                        "completed_tasks": 0
                    }

                dept_stats[dept_id]["total_tasks"] += 1
                if task.status == "DONE":
                    dept_stats[dept_id]["completed_tasks"] += 1

    # 计算部门完成率
    by_department = []
    for dept_stat in dept_stats.values():
        dept_completion_rate = (dept_stat["completed_tasks"] / dept_stat["total_tasks"] * 100) if dept_stat["total_tasks"] > 0 else 0.0
        by_department.append({
            **dept_stat,
            "completion_rate": round(dept_completion_rate, 2)
        })

    # 按负责人统计
    owner_stats = {}
    for task in tasks:
        if task.owner_id:
            owner = db.query(User).filter(User.id == task.owner_id).first()
            owner_name = owner.real_name or owner.username if owner else "未知"

            if task.owner_id not in owner_stats:
                owner_stats[task.owner_id] = {
                    "owner_id": task.owner_id,
                    "owner_name": owner_name,
                    "total_tasks": 0,
                    "completed_tasks": 0
                }

            owner_stats[task.owner_id]["total_tasks"] += 1
            if task.status == "DONE":
                owner_stats[task.owner_id]["completed_tasks"] += 1

    # 计算负责人完成率
    by_owner = []
    for owner_stat in owner_stats.values():
        owner_completion_rate = (owner_stat["completed_tasks"] / owner_stat["total_tasks"] * 100) if owner_stat["total_tasks"] > 0 else 0.0
        by_owner.append({
            **owner_stat,
            "completion_rate": round(owner_completion_rate, 2)
        })

    # 按完成率排序
    by_department.sort(key=lambda x: x["completion_rate"], reverse=True)
    by_owner.sort(key=lambda x: x["completion_rate"], reverse=True)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_rate": round(completion_rate, 2),
            "by_department": by_department,
            "by_owner": by_owner[:20]  # 只返回前20名
        }
    )


# ==================== 里程碑达成率统计 ====================

@router.get("/reports/milestone-rate", response_model=MilestoneRateResponse, status_code=status.HTTP_200_OK)
def get_milestone_rate(
    project_id: Optional[int] = Query(None, description="项目ID（可选，不填则统计所有项目）"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取里程碑达成率统计
    """
    if project_id:
        # 单个项目统计
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        milestones = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).all()

        total_milestones = len(milestones)
        completed_milestones = len([m for m in milestones if m.status == "COMPLETED"])
        completion_rate = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0.0

        today = date.today()
        overdue_milestones = len([m for m in milestones if m.planned_date < today and m.status != "COMPLETED"])
        pending_milestones = len([m for m in milestones if m.status == "PENDING"])

        # 构建里程碑详情列表
        milestone_list = []
        for m in milestones:
            milestone_list.append({
                "id": m.id,
                "milestone_code": m.milestone_code,
                "milestone_name": m.milestone_name,
                "planned_date": m.planned_date.isoformat() if m.planned_date else None,
                "actual_date": m.actual_date.isoformat() if m.actual_date else None,
                "status": m.status,
                "is_key": m.is_key
            })

        return MilestoneRateResponse(
            project_id=project_id,
            project_name=project.project_name,
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            completion_rate=round(completion_rate, 2),
            overdue_milestones=overdue_milestones,
            pending_milestones=pending_milestones,
            milestones=milestone_list
        )
    else:
        # 全局统计（所有项目）
        all_milestones = db.query(ProjectMilestone).all()

        total_milestones = len(all_milestones)
        completed_milestones = len([m for m in all_milestones if m.status == "COMPLETED"])
        completion_rate = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0.0

        today = date.today()
        overdue_milestones = len([m for m in all_milestones if m.planned_date < today and m.status != "COMPLETED"])
        pending_milestones = len([m for m in all_milestones if m.status == "PENDING"])

        return MilestoneRateResponse(
            project_id=0,  # 0表示全局
            project_name="全局统计",
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            completion_rate=round(completion_rate, 2),
            overdue_milestones=overdue_milestones,
            pending_milestones=pending_milestones,
            milestones=[]
        )


# ==================== 延期原因统计 ====================

@router.get("/reports/delay-reasons", response_model=DelayReasonsResponse, status_code=status.HTTP_200_OK)
def get_delay_reasons(
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    top_n: int = Query(10, ge=1, le=50, description="返回Top N原因"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取延期原因统计（Top N）
    """
    today = date.today()

    # 查询逾期任务
    query = db.query(Task).filter(
        Task.plan_end < today,
        Task.status != "DONE"
    )

    if project_id:
        query = query.filter(Task.project_id == project_id)
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

    delayed_tasks = query.all()
    total_delayed = len(delayed_tasks)

    # 统计延期原因（从block_reason字段）
    reason_count = {}
    for task in delayed_tasks:
        reason = task.block_reason or "未填写原因"
        reason_count[reason] = reason_count.get(reason, 0) + 1

    # 按数量排序，取Top N
    sorted_reasons = sorted(reason_count.items(), key=lambda x: x[1], reverse=True)[:top_n]

    # 构建响应
    reasons = []
    for reason, count in sorted_reasons:
        percentage = (count / total_delayed * 100) if total_delayed > 0 else 0.0
        reasons.append(DelayReasonItem(
            reason=reason,
            count=count,
            percentage=round(percentage, 2)
        ))

    return DelayReasonsResponse(
        project_id=project_id,
        total_delayed_tasks=total_delayed,
        reasons=reasons
    )
