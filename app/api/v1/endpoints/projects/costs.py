# -*- coding: utf-8 -*-
"""
项目成本管理端点

包含项目成本汇总、成本明细等端点
"""

from typing import Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import Project, Machine, ProjectMilestone, ProjectMember
from app.models.pmo import PmoProjectRisk
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


# ==================== 项目概览数据 ====================

@router.get("/{project_id}/summary", response_model=ResponseModel)
def get_project_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目概览数据
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.models.progress import Task
    from app.models.alert import Alert
    from app.models.issue import Issue
    from app.models.project import ProjectDocument, ProjectCost

    project = check_project_access_or_raise(db, current_user, project_id)

    machine_count = db.query(Machine).filter(Machine.project_id == project_id).count()
    milestone_count = db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id).count()
    completed_milestone_count = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()

    task_count = db.query(Task).filter(Task.project_id == project_id).count()
    completed_task_count = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).count()

    alert_count = db.query(Alert).filter(
        Alert.project_id == project_id,
        Alert.status != "RESOLVED"
    ).count()

    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status != "CLOSED"
    ).count()

    document_count = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id).count()

    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    total_cost = float(sum(cost.cost_amount or 0 for cost in costs))

    return ResponseModel(
        code=200,
        message="获取项目概览成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "customer_name": project.customer_name,
            "pm_name": project.pm_name,
            "stage": project.stage or "S1",
            "status": project.status or "ST01",
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "contract_amount": float(project.contract_amount or 0),
            "machine_count": machine_count,
            "milestone_count": milestone_count,
            "completed_milestone_count": completed_milestone_count,
            "task_count": task_count,
            "completed_task_count": completed_task_count,
            "member_count": member_count,
            "alert_count": alert_count,
            "issue_count": issue_count,
            "document_count": document_count,
            "total_cost": total_cost,
        }
    )


@router.get("/in-production/summary", response_model=ResponseModel)
def get_in_production_projects_summary(
    db: Session = Depends(deps.get_db),
    stage: Optional[str] = Query(None, description="阶段筛选：S4-S8"),
    health: Optional[str] = Query(None, description="健康度筛选：H1-H3"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    在产项目进度汇总（专门给生产总监/经理看）
    """
    query = db.query(Project).filter(
        Project.stage.in_(["S4", "S5", "S6", "S7", "S8"]),
        Project.is_active == True
    )

    from app.services.data_scope_service import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    if stage:
        query = query.filter(Project.stage == stage)
    if health:
        query = query.filter(Project.health == health)

    projects = query.all()

    result = []
    for project in projects:
        milestones = db.query(ProjectMilestone).filter(
            ProjectMilestone.project_id == project.id,
            ProjectMilestone.status != "COMPLETED"
        ).order_by(ProjectMilestone.planned_date).limit(5).all()

        today = date.today()
        overdue_milestones = [
            m for m in milestones
            if m.planned_date and m.planned_date < today and m.status != "COMPLETED"
        ]

        next_milestone = milestones[0].milestone_name if milestones else None
        next_milestone_date = milestones[0].planned_date if milestones else None

        result.append({
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage or "S4",
            "health": project.health,
            "progress": float(project.progress_pct or 0),
            "planned_end_date": project.planned_end_date.isoformat() if project.planned_end_date else None,
            "overdue_milestones_count": len(overdue_milestones),
            "next_milestone": next_milestone,
            "next_milestone_date": next_milestone_date.isoformat() if next_milestone_date else None,
        })

    return ResponseModel(
        code=200,
        message="获取在产项目汇总成功",
        data={"total": len(result), "projects": result}
    )


@router.get("/{project_id}/project-dashboard", response_model=ResponseModel)
def get_single_project_dashboard(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取单个项目仪表盘数据
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    from app.models.progress import Task
    from app.models.issue import Issue

    project = check_project_access_or_raise(db, current_user, project_id)

    # 任务统计
    total_tasks = db.query(Task).filter(Task.project_id == project_id).count()
    completed_tasks = db.query(Task).filter(
        Task.project_id == project_id,
        Task.status == "COMPLETED"
    ).count()

    # 里程碑统计
    total_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).count()
    completed_milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).count()

    # 风险统计
    risk_count = db.query(PmoProjectRisk).filter(
        PmoProjectRisk.project_id == project_id,
        PmoProjectRisk.status != "CLOSED"
    ).count()

    # 问题统计
    issue_count = db.query(Issue).filter(
        Issue.project_id == project_id,
        Issue.status.notin_(["RESOLVED", "CLOSED"])
    ).count()

    return ResponseModel(
        code=200,
        message="获取项目仪表盘成功",
        data={
            "project_id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "stage": project.stage,
            "health": project.health,
            "progress_pct": float(project.progress_pct or 0),
            "task_stats": {
                "total": total_tasks,
                "completed": completed_tasks,
                "completion_rate": round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
            },
            "milestone_stats": {
                "total": total_milestones,
                "completed": completed_milestones,
            },
            "risk_count": risk_count,
            "issue_count": issue_count,
        }
    )


# ==================== 项目成本管理 ====================

@router.get("/projects/{project_id}/cost-summary", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_project_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    项目成本汇总
    获取项目的成本汇总统计信息
    """
    from app.models.project import ProjectCost
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    # 总成本统计
    total_result = db.query(
        func.sum(ProjectCost.amount).label('total_amount'),
        func.sum(ProjectCost.tax_amount).label('total_tax'),
        func.count(ProjectCost.id).label('total_count')
    ).filter(ProjectCost.project_id == project_id).first()

    total_amount = float(total_result.total_amount) if total_result.total_amount else 0
    total_tax = float(total_result.total_tax) if total_result.total_tax else 0
    total_count = total_result.total_count or 0

    # 按成本类型统计
    type_stats = db.query(
        ProjectCost.cost_type,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_type).all()

    type_summary = [
        {
            "cost_type": stat.cost_type,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in type_stats
    ]

    # 按成本分类统计
    category_stats = db.query(
        ProjectCost.cost_category,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id
    ).group_by(ProjectCost.cost_category).all()

    category_summary = [
        {
            "cost_category": stat.cost_category,
            "amount": round(float(stat.amount) if stat.amount else 0, 2),
            "count": stat.count or 0,
            "percentage": round((float(stat.amount) / total_amount * 100) if total_amount > 0 else 0, 2)
        }
        for stat in category_stats
    ]

    # 预算对比
    budget_amount = float(project.budget_amount or 0)
    actual_cost = float(project.actual_cost or 0)
    cost_variance = actual_cost - budget_amount
    cost_variance_pct = (cost_variance / budget_amount * 100) if budget_amount > 0 else 0

    # 合同对比
    contract_amount = float(project.contract_amount or 0)
    profit = contract_amount - actual_cost
    profit_margin = (profit / contract_amount * 100) if contract_amount > 0 else 0

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "budget_info": {
                "budget_amount": round(budget_amount, 2),
                "actual_cost": round(actual_cost, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_variance_pct": round(cost_variance_pct, 2),
                "is_over_budget": cost_variance > 0
            },
            "contract_info": {
                "contract_amount": round(contract_amount, 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2)
            },
            "cost_summary": {
                "total_amount": round(total_amount, 2),
                "total_tax": round(total_tax, 2),
                "total_with_tax": round(total_amount + total_tax, 2),
                "total_count": total_count
            },
            "by_type": type_summary,
            "by_category": category_summary,
        }
    )


@router.get("/projects/{project_id}/cost-details", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_project_cost_details(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    cost_category: Optional[str] = Query(None, description="成本分类筛选"),
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    成本明细列表
    获取项目的成本明细记录列表，支持分页和筛选
    """
    from app.models.project import ProjectCost
    from app.utils.permission_helpers import check_project_access_or_raise

    project = check_project_access_or_raise(db, current_user, project_id)

    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)

    if machine_id:
        query = query.filter(ProjectCost.machine_id == machine_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)
    if cost_category:
        query = query.filter(ProjectCost.cost_category == cost_category)
    if start_date:
        query = query.filter(ProjectCost.cost_date >= start_date)
    if end_date:
        query = query.filter(ProjectCost.cost_date <= end_date)

    total = query.count()
    offset = (page - 1) * page_size
    costs = query.order_by(desc(ProjectCost.cost_date), desc(ProjectCost.created_at)).offset(offset).limit(page_size).all()

    cost_details = []
    for cost in costs:
        machine = None
        if cost.machine_id:
            machine = db.query(Machine).filter(Machine.id == cost.machine_id).first()

        cost_details.append({
            "id": cost.id,
            "cost_no": cost.cost_no,
            "cost_date": cost.cost_date.isoformat() if cost.cost_date else None,
            "cost_type": cost.cost_type,
            "cost_category": cost.cost_category,
            "amount": float(cost.amount) if cost.amount else 0,
            "tax_amount": float(cost.tax_amount) if cost.tax_amount else 0,
            "total_amount": float(cost.amount or 0) + float(cost.tax_amount or 0),
            "machine_id": cost.machine_id,
            "machine_code": machine.machine_code if machine else None,
            "machine_name": machine.machine_name if machine else None,
            "description": cost.description,
            "remark": cost.remark,
        })

    return PaginatedResponse(
        items=cost_details,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )
