# -*- coding: utf-8 -*-
"""
项目预算执行分析模块

提供项目预算执行情况分析和趋势分析。
路由: /projects/{project_id}/costs/budget
"""

from datetime import date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Project, ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


class LegacyBudgetUpdateRequest(BaseModel):
    """兼容旧版预算更新请求体"""

    total_budget: Optional[float] = None
    labor_cost_budget: Optional[float] = None
    material_cost_budget: Optional[float] = None
    other_cost_budget: Optional[float] = None


class LegacyBudgetApprovalRequest(BaseModel):
    """兼容旧版预算审批请求体"""

    budget_change: float
    reason: Optional[str] = None
    approver_id: Optional[int] = None


class LegacyCostEntryCreateRequest(BaseModel):
    """兼容旧版成本录入请求体"""

    cost_category: str
    amount: float
    description: Optional[str] = None
    cost_date: date
    vendor: Optional[str] = None


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


def _sum_project_cost(db: Session, project_id: int) -> float:
    total = (
        db.query(func.coalesce(func.sum(ProjectCost.amount), 0))
        .filter(ProjectCost.project_id == project_id)
        .scalar()
    )
    return float(total or 0)


@router.get("/budget", response_model=ResponseModel)
def get_project_budget_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：获取项目预算"""
    project = _get_project_or_404(db, project_id)
    actual_cost = _sum_project_cost(db, project_id)
    budget_amount = float(project.budget_amount or 0)
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project.id,
            "total_budget": budget_amount,
            "actual_cost": actual_cost,
            "variance": round(budget_amount - actual_cost, 2),
        },
    )


@router.put("/budget", response_model=ResponseModel)
def update_project_budget_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    payload: LegacyBudgetUpdateRequest,
    current_user: User = Depends(security.require_permission("cost:update")),
) -> Any:
    """兼容旧版：更新项目预算"""
    project = _get_project_or_404(db, project_id)
    total_budget = payload.total_budget
    if total_budget is None:
        total_budget = (
            (payload.labor_cost_budget or 0)
            + (payload.material_cost_budget or 0)
            + (payload.other_cost_budget or 0)
        )
    project.budget_amount = total_budget
    db.commit()
    db.refresh(project)
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project.id,
            "total_budget": float(project.budget_amount or 0),
        },
    )


@router.post("/budget/approval", response_model=ResponseModel, status_code=201)
def create_budget_approval_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    payload: LegacyBudgetApprovalRequest,
    current_user: User = Depends(security.require_permission("cost:update")),
) -> Any:
    """兼容旧版：提交预算审批（轻量实现）"""
    _get_project_or_404(db, project_id)
    return ResponseModel(
        code=201,
        message="审批申请已提交",
        data={
            "project_id": project_id,
            "budget_change": payload.budget_change,
            "reason": payload.reason,
            "approver_id": payload.approver_id,
            "status": "PENDING",
        },
    )


@router.get("/actual", response_model=ResponseModel)
def get_project_actual_cost_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：获取项目实际成本"""
    _get_project_or_404(db, project_id)
    actual_cost = _sum_project_cost(db, project_id)
    return ResponseModel(
        code=200,
        message="success",
        data={"project_id": project_id, "actual_cost": actual_cost},
    )


@router.get("/breakdown", response_model=ResponseModel)
def get_project_cost_breakdown_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：按类别分解成本"""
    _get_project_or_404(db, project_id)
    rows = (
        db.query(
            ProjectCost.cost_category,
            func.coalesce(func.sum(ProjectCost.amount), 0).label("total_amount"),
        )
        .filter(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_category)
        .all()
    )
    items = [
        {
            "category": row.cost_category or "uncategorized",
            "amount": float(row.total_amount or 0),
        }
        for row in rows
    ]
    return ResponseModel(
        code=200,
        message="success",
        data={"project_id": project_id, "items": items},
    )


@router.get("/variance", response_model=ResponseModel)
def get_project_cost_variance_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：成本偏差分析"""
    project = _get_project_or_404(db, project_id)
    actual_cost = _sum_project_cost(db, project_id)
    budget_amount = float(project.budget_amount or 0)
    variance = round(budget_amount - actual_cost, 2)
    variance_pct = round((variance / budget_amount * 100), 2) if budget_amount else 0
    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "budget_amount": budget_amount,
            "actual_cost": actual_cost,
            "variance": variance,
            "variance_pct": variance_pct,
        },
    )


@router.get("/entries", response_model=ResponseModel)
def list_project_cost_entries_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    category: Optional[str] = Query(None, description="成本分类"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：获取成本记录列表"""
    _get_project_or_404(db, project_id)
    query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)
    if start_date:
        query = query.filter(ProjectCost.cost_date >= start_date)
    if end_date:
        query = query.filter(ProjectCost.cost_date <= end_date)
    if category:
        query = query.filter(ProjectCost.cost_category == category)

    items = []
    for item in query.order_by(ProjectCost.cost_date.desc(), ProjectCost.id.desc()).all():
        items.append(
            {
                "id": item.id,
                "cost_category": item.cost_category,
                "amount": float(item.amount or 0),
                "description": item.description,
                "cost_date": item.cost_date.isoformat() if item.cost_date else None,
                "vendor": item.source_no,
            }
        )

    return ResponseModel(
        code=200,
        message="success",
        data={"items": items, "total": len(items)},
    )


@router.post("/entries", response_model=ResponseModel, status_code=201)
def create_project_cost_entry_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    payload: LegacyCostEntryCreateRequest,
    current_user: User = Depends(security.require_permission("cost:create")),
) -> Any:
    """兼容旧版：新增成本记录"""
    _get_project_or_404(db, project_id)
    cost = ProjectCost(
        project_id=project_id,
        cost_type=(payload.cost_category or "OTHER").upper(),
        cost_category=payload.cost_category,
        amount=payload.amount,
        description=payload.description,
        cost_date=payload.cost_date,
        source_no=payload.vendor,
    )
    db.add(cost)
    db.commit()
    db.refresh(cost)
    return ResponseModel(
        code=201,
        message="created",
        data={"id": cost.id},
    )


@router.get("/export", response_model=ResponseModel)
def export_project_cost_entries_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：成本导出（占位实现）"""
    _get_project_or_404(db, project_id)
    return ResponseModel(
        code=200,
        message="success",
        data={"project_id": project_id, "export_url": None},
    )


@router.get("/analysis/charts", response_model=ResponseModel)
def get_project_cost_analysis_charts_legacy(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """兼容旧版：成本分析图表数据"""
    _get_project_or_404(db, project_id)
    breakdown = (
        db.query(
            ProjectCost.cost_category,
            func.coalesce(func.sum(ProjectCost.amount), 0).label("total_amount"),
        )
        .filter(ProjectCost.project_id == project_id)
        .group_by(ProjectCost.cost_category)
        .all()
    )
    categories = [row.cost_category or "uncategorized" for row in breakdown]
    values = [float(row.total_amount or 0) for row in breakdown]
    return ResponseModel(
        code=200,
        message="success",
        data={"categories": categories, "values": values},
    )


@router.get("/execution", response_model=ResponseModel)
def get_budget_execution_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目预算执行情况分析
    """
    from app.services.budget_analysis_service import BudgetAnalysisService

    try:
        result = BudgetAnalysisService.get_budget_execution_analysis(db, project_id)
        return ResponseModel(code=200, message="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算执行分析失败：{str(e)}")


@router.get("/budget-trend", response_model=ResponseModel)
def get_budget_trend_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    start_date: Optional[str] = Query(None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYY-MM-DD）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目预算执行趋势分析（按时间维度）
    """
    from app.services.budget_analysis_service import BudgetAnalysisService

    try:
        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        result = BudgetAnalysisService.get_budget_trend_analysis(
            db, project_id, start_date=start, end_date=end
        )
        return ResponseModel(code=200, message="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取预算趋势分析失败：{str(e)}")
