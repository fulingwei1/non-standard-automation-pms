# -*- coding: utf-8 -*-
"""
资源利用率分析 API

提供部门和全局工作负载分布、瓶颈分析
"""

from datetime import date, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.models.organization import Department
from app.models.project import ProjectStageResourcePlan
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


# ==================== Department Workload ====================

@router.get("/departments/{dept_id}/workload/summary", response_model=ResponseModel)
def get_department_workload_summary(
    dept_id: int,
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    部门工作量汇总
    """
    # 默认当月
    if not start_date:
        today = date.today()
        start_date = today.replace(day=1)
    if not end_date:
        # 下月1号减1天
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)

    # 获取部门成员
    members = db.query(User).filter(
        User.department_id == dept_id,
        User.is_active == True,
    ).all()

    member_ids = [m.id for m in members]

    if not member_ids:
        return ResponseModel(data={
            "department_id": dept_id,
            "period": f"{start_date} ~ {end_date}",
            "members": [],
            "summary": {
                "total_members": 0,
                "avg_allocation": 0,
                "overloaded_count": 0,
                "underutilized_count": 0,
            },
        })

    # 获取该期间的资源分配
    allocations = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.assigned_employee_id.in_(member_ids),
        ProjectStageResourcePlan.planned_start <= end_date,
        ProjectStageResourcePlan.planned_end >= start_date,
    ).all()

    # 按员工汇总
    member_workload = {m.id: {"user": m, "total_allocation": 0, "projects": []} for m in members}

    for alloc in allocations:
        emp_id = alloc.assigned_employee_id
        if emp_id in member_workload:
            pct = float(alloc.allocation_pct) if alloc.allocation_pct else 100.0
            member_workload[emp_id]["total_allocation"] += pct
            member_workload[emp_id]["projects"].append({
                "project_id": alloc.project_id,
                "stage_code": alloc.stage_code,
                "allocation_pct": pct,
            })

    # 构建响应
    members_data = []
    overloaded = 0
    underutilized = 0
    total_alloc = 0

    for emp_id, data in member_workload.items():
        alloc = data["total_allocation"]
        total_alloc += alloc

        status = "normal"
        if alloc > 100:
            status = "overloaded"
            overloaded += 1
        elif alloc < 50:
            status = "underutilized"
            underutilized += 1

        members_data.append({
            "id": emp_id,
            "name": data["user"].username,
            "total_allocation": round(alloc, 1),
            "status": status,
            "project_count": len(data["projects"]),
        })

    # 按分配率排序
    members_data.sort(key=lambda x: x["total_allocation"], reverse=True)

    return ResponseModel(data={
        "department_id": dept_id,
        "period": f"{start_date} ~ {end_date}",
        "members": members_data,
        "summary": {
            "total_members": len(members),
            "avg_allocation": round(total_alloc / len(members), 1) if members else 0,
            "overloaded_count": overloaded,
            "underutilized_count": underutilized,
        },
    })


@router.get("/departments/{dept_id}/workload/distribution", response_model=ResponseModel)
def get_department_workload_distribution(
    dept_id: int,
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    部门工作负载分布（用于可视化）
    """
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)

    members = db.query(User).filter(
        User.department_id == dept_id,
        User.is_active == True,
    ).all()

    member_ids = [m.id for m in members]

    allocations = db.query(ProjectStageResourcePlan).filter(
        ProjectStageResourcePlan.assigned_employee_id.in_(member_ids),
        ProjectStageResourcePlan.planned_start <= end_date,
        ProjectStageResourcePlan.planned_end >= start_date,
    ).all()

    # 计算分配
    member_alloc = {}
    for m in members:
        member_alloc[m.id] = 0

    for alloc in allocations:
        if alloc.assigned_employee_id in member_alloc:
            member_alloc[alloc.assigned_employee_id] += float(alloc.allocation_pct or 100)

    # 分布区间
    distribution = {
        "overloaded_high": [],    # >150%
        "overloaded": [],         # 100-150%
        "optimal": [],            # 80-100%
        "available": [],          # 50-80%
        "underutilized": [],      # <50%
    }

    for m in members:
        alloc = member_alloc.get(m.id, 0)
        item = {"id": m.id, "name": m.username, "allocation": round(alloc, 1)}

        if alloc > 150:
            distribution["overloaded_high"].append(item)
        elif alloc > 100:
            distribution["overloaded"].append(item)
        elif alloc >= 80:
            distribution["optimal"].append(item)
        elif alloc >= 50:
            distribution["available"].append(item)
        else:
            distribution["underutilized"].append(item)

    return ResponseModel(data={
        "department_id": dept_id,
        "period": f"{start_date} ~ {end_date}",
        "distribution": distribution,
        "counts": {k: len(v) for k, v in distribution.items()},
    })


# ==================== Global Workload Analytics ====================

@router.get("/analytics/workload/overview", response_model=ResponseModel)
def get_global_workload_overview(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    全局工作量概览
    """
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)

    # 按部门统计
    departments = db.query(Department).filter(Department.is_active == True).all()

    dept_stats = []
    for dept in departments:
        members = db.query(User).filter(
            User.department_id == dept.id,
            User.is_active == True,
        ).all()

        if not members:
            continue

        member_ids = [m.id for m in members]

        # 统计分配
        total_alloc = db.query(func.sum(ProjectStageResourcePlan.allocation_pct)).filter(
            ProjectStageResourcePlan.assigned_employee_id.in_(member_ids),
            ProjectStageResourcePlan.planned_start <= end_date,
            ProjectStageResourcePlan.planned_end >= start_date,
        ).scalar() or 0

        avg_alloc = float(total_alloc) / len(members) if members else 0

        dept_stats.append({
            "department_id": dept.id,
            "department_name": dept.name,
            "member_count": len(members),
            "avg_allocation": round(avg_alloc, 1),
            "status": "overloaded" if avg_alloc > 100 else ("optimal" if avg_alloc >= 70 else "available"),
        })

    # 排序
    dept_stats.sort(key=lambda x: x["avg_allocation"], reverse=True)

    return ResponseModel(data={
        "period": f"{start_date} ~ {end_date}",
        "departments": dept_stats,
        "summary": {
            "total_departments": len(dept_stats),
            "overloaded_count": len([d for d in dept_stats if d["status"] == "overloaded"]),
            "avg_global_allocation": round(sum(d["avg_allocation"] for d in dept_stats) / len(dept_stats), 1) if dept_stats else 0,
        },
    })


@router.get("/analytics/workload/bottlenecks", response_model=ResponseModel)
def get_workload_bottlenecks(
    db: Session = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    资源瓶颈分析
    """
    if not start_date:
        start_date = date.today().replace(day=1)
    if not end_date:
        next_month = start_date.replace(day=28) + timedelta(days=4)
        end_date = next_month.replace(day=1) - timedelta(days=1)

    bottlenecks = []

    # 1. 检测严重超载的员工
    overloaded_employees = db.query(
        ProjectStageResourcePlan.assigned_employee_id,
        func.sum(ProjectStageResourcePlan.allocation_pct).label("total_alloc"),
    ).filter(
        ProjectStageResourcePlan.assigned_employee_id.isnot(None),
        ProjectStageResourcePlan.planned_start <= end_date,
        ProjectStageResourcePlan.planned_end >= start_date,
    ).group_by(
        ProjectStageResourcePlan.assigned_employee_id
    ).having(
        func.sum(ProjectStageResourcePlan.allocation_pct) > 150
    ).all()

    for emp_id, total in overloaded_employees:
        emp = db.query(User).filter(User.id == emp_id).first()
        bottlenecks.append({
            "type": "EMPLOYEE_OVERLOAD",
            "severity": "HIGH",
            "employee": {"id": emp_id, "name": emp.username if emp else None},
            "detail": f"总分配 {float(total):.0f}%，严重超载",
            "recommendation": "考虑重新分配部分任务或增加人手",
        })

    # 2. 检测超载部门
    departments = db.query(Department).filter(Department.is_active == True).all()
    for dept in departments:
        members = db.query(User).filter(User.department_id == dept.id, User.is_active == True).all()
        if not members:
            continue

        member_ids = [m.id for m in members]
        total_alloc = db.query(func.sum(ProjectStageResourcePlan.allocation_pct)).filter(
            ProjectStageResourcePlan.assigned_employee_id.in_(member_ids),
            ProjectStageResourcePlan.planned_start <= end_date,
            ProjectStageResourcePlan.planned_end >= start_date,
        ).scalar() or 0

        avg = float(total_alloc) / len(members)
        if avg > 120:
            bottlenecks.append({
                "type": "DEPARTMENT_OVERLOAD",
                "severity": "MEDIUM" if avg < 150 else "HIGH",
                "department": {"id": dept.id, "name": dept.name},
                "detail": f"部门平均负载 {avg:.0f}%",
                "recommendation": "考虑跨部门借调或外协",
            })

    return ResponseModel(data={
        "period": f"{start_date} ~ {end_date}",
        "bottlenecks": bottlenecks,
        "total_count": len(bottlenecks),
        "high_severity_count": len([b for b in bottlenecks if b["severity"] == "HIGH"]),
    })
