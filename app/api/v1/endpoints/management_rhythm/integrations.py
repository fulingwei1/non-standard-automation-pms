# -*- coding: utf-8 -*-
"""
数据集成 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/integrations",
    tags=["integrations"]
)

# 共 3 个路由

# ==================== 数据集成 ====================

@router.get("/rhythm-integration/financial-metrics")
def get_financial_metrics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取财务指标（用于经营分析会）
    """
    from sqlalchemy import func

    from app.models.budget import ProjectBudget
    from app.models.project.financial import ProjectCost, ProjectPaymentPlan

    # 构建日期过滤条件
    cost_query = db.query(func.coalesce(func.sum(ProjectCost.amount), 0))
    if start_date:
        cost_query = cost_query.filter(ProjectCost.cost_date >= start_date)
    if end_date:
        cost_query = cost_query.filter(ProjectCost.cost_date <= end_date)

    # 查询成本总额
    total_cost = float(cost_query.scalar() or 0)

    # 查询收入（已收款金额）
    revenue_query = db.query(func.coalesce(func.sum(ProjectPaymentPlan.actual_amount), 0)).filter(
        ProjectPaymentPlan.status.in_(['PARTIAL', 'COMPLETED'])
    )
    if start_date:
        revenue_query = revenue_query.filter(ProjectPaymentPlan.actual_date >= start_date)
    if end_date:
        revenue_query = revenue_query.filter(ProjectPaymentPlan.actual_date <= end_date)
    total_revenue = float(revenue_query.scalar() or 0)

    # 计算利润
    profit = total_revenue - total_cost

    # 查询预算总额（已批准的预算）
    budget_total = db.query(func.coalesce(func.sum(ProjectBudget.total_amount), 0)).filter(
        ProjectBudget.status == 'APPROVED',
        ProjectBudget.is_active
    ).scalar() or 0

    # 计算毛利率和净利润率
    gross_margin_rate = (profit / total_revenue * 100) if total_revenue > 0 else 0.0
    net_profit_rate = gross_margin_rate  # 简化处理，实际需考虑其他费用

    # 现金流（收入 - 成本）
    cash_flow = profit

    metrics = {
        "revenue": total_revenue,
        "cost": total_cost,
        "profit": profit,
        "cash_flow": cash_flow,
        "gross_margin_rate": round(gross_margin_rate, 2),
        "net_profit_rate": round(net_profit_rate, 2),
        "budget_total": float(budget_total),
        "budget_usage_rate": round((total_cost / float(budget_total) * 100) if budget_total else 0, 2),
    }

    return metrics


@router.get("/rhythm-integration/project-metrics")
def get_project_metrics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目指标（用于运营例会）
    """
    from app.models.project import Project

    # 获取项目统计数据
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.health.in_(['H1', 'H2', 'H3'])).count()
    at_risk_projects = db.query(Project).filter(Project.health.in_(['H2', 'H3'])).count()

    metrics = {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "at_risk_projects": at_risk_projects,
        "project_health_distribution": {},
    }

    # 统计健康度分布
    health_counts = db.query(Project.health, func.count(Project.id)).group_by(Project.health).all()
    for health, count in health_counts:
        metrics["project_health_distribution"][health] = count

    return metrics


@router.get("/rhythm-integration/task-metrics")
def get_task_metrics(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取任务指标（用于日清会）
    """
    from app.models.task_center import TaskUnified as Task

    # 获取任务统计数据
    query = db.query(Task)

    if start_date:
        query = query.filter(Task.created_at >= start_date)
    if end_date:
        query = query.filter(Task.created_at <= end_date)

    total_tasks = query.count()
    completed_tasks = query.filter(Task.status == 'COMPLETED').count()
    overdue_tasks = query.filter(
        and_(
            Task.due_date < date.today(),
            Task.status != 'COMPLETED'
        )
    ).count()

    metrics = {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "overdue_tasks": overdue_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0,
    }

    return metrics



