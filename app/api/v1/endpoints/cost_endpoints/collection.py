# -*- coding: utf-8 -*-
"""
成本自动归集 API
- 从采购订单自动归集材料成本到项目
- 从工单自动归集人工/加工成本到项目
- 归集日志和状态追踪
- 支持手动触发和自动归集
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api import deps
from app.models.material import BomHeader
from app.models.production.work_order import WorkOrder
from app.models.project import Project, ProjectCost
from app.models.purchase import PurchaseOrder
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.cost.cost_basis import (
    actual_cost_basis_expr,
    actual_project_cost_filter,
)
from app.services.cost.cost_collection_service import CostCollectionService

router = APIRouter()


AUTO_SOURCE_TYPES = ("PURCHASE_ORDER", "BOM_COST", "WORK_ORDER", "LABOR_COST")


def _source_type_expr():
    return func.upper(ProjectCost.source_type)


def _collected_count(db: Session, source_type: str, source_ids: list[int]) -> int:
    if not source_ids:
        return 0
    return (
        db.query(ProjectCost)
        .filter(
            _source_type_expr() == source_type, ProjectCost.source_id.in_(source_ids)
        )
        .count()
    )


@router.post("/collect", summary="执行成本归集")
def run_cost_collection(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
    project_id: Optional[int] = Query(None, description="指定项目ID（空=全部）"),
) -> Any:
    """
    手动触发成本归集：
    1. 扫描所有有project_id的采购订单→归集为material成本
    2. 扫描已发布BOM→归集为material成本
    3. 扫描所有有project_id的工单→归集为labor/outsource成本
    4. 扫描已审批工时→归集为labor成本
    5. 已归集来源做更新，不重复插入
    """
    result = CostCollectionService.collect_project_costs(
        db, project_id=project_id, created_by=current_user.id
    )
    db.commit()
    return result


@router.get("/status", summary="归集状态概览")
def get_collection_status(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """查看各来源的归集状态。"""
    po_ids = [
        row[0]
        for row in db.query(PurchaseOrder.id)
        .filter(
            PurchaseOrder.project_id.isnot(None),
            PurchaseOrder.status.in_(
                CostCollectionService.PURCHASE_COLLECTIBLE_STATUSES
            ),
            PurchaseOrder.total_amount > 0,
        )
        .all()
    ]
    bom_ids = [
        row[0]
        for row in db.query(BomHeader.id)
        .filter(BomHeader.project_id.isnot(None), BomHeader.status == "RELEASED")
        .all()
    ]
    work_order_ids = [
        row[0]
        for row in db.query(WorkOrder.id)
        .filter(
            WorkOrder.project_id.isnot(None),
            WorkOrder.status.in_(CostCollectionService.WORK_ORDER_COLLECTIBLE_STATUSES),
        )
        .all()
    ]

    timesheet_groups = {
        (project_id, user_id)
        for project_id, user_id in db.query(Timesheet.project_id, Timesheet.user_id)
        .filter(
            Timesheet.project_id.isnot(None),
            Timesheet.status.in_(CostCollectionService.TIMESHEET_COLLECTIBLE_STATUSES),
        )
        .distinct()
        .all()
    }
    timesheet_collected_groups = {
        (project_id, user_id)
        for project_id, user_id in db.query(
            ProjectCost.project_id, ProjectCost.source_id
        )
        .filter(_source_type_expr() == "LABOR_COST")
        .all()
    }

    recent_rows = (
        db.query(ProjectCost, Project.project_name)
        .join(Project, ProjectCost.project_id == Project.id)
        .filter(_source_type_expr().in_(AUTO_SOURCE_TYPES))
        .order_by(ProjectCost.created_at.desc())
        .limit(10)
        .all()
    )

    recent = [
        {
            "source_type": cost.source_type,
            "source_no": cost.source_no,
            "amount": float(cost.amount or 0),
            "cost_type": cost.cost_type,
            "project_name": project_name,
            "collected_at": cost.created_at,
        }
        for cost, project_name in recent_rows
    ]

    po_collected = _collected_count(db, "PURCHASE_ORDER", po_ids)
    bom_collected = _collected_count(db, "BOM_COST", bom_ids)
    wo_collected = _collected_count(db, "WORK_ORDER", work_order_ids)
    ts_collected = len(timesheet_groups & timesheet_collected_groups)

    return {
        "purchase_orders": {
            "total": len(po_ids),
            "collected": po_collected,
            "pending": max(0, len(po_ids) - po_collected),
        },
        "bom_headers": {
            "total": len(bom_ids),
            "collected": bom_collected,
            "pending": max(0, len(bom_ids) - bom_collected),
        },
        "work_orders": {
            "total": len(work_order_ids),
            "collected": wo_collected,
            "pending": max(0, len(work_order_ids) - wo_collected),
        },
        "timesheets": {
            "total": len(timesheet_groups),
            "collected": ts_collected,
            "pending": max(0, len(timesheet_groups) - ts_collected),
        },
        "recent_collections": recent,
    }


@router.get("/by-project", summary="按项目查看归集明细")
def get_collection_by_project(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    """按项目汇总已归集的成本和来源。"""
    source_type = _source_type_expr()
    cost_basis = actual_cost_basis_expr()
    actual_total_cost = func.coalesce(
        func.sum(case((actual_project_cost_filter(), ProjectCost.amount), else_=0)), 0
    )
    manual_condition = ProjectCost.source_type.is_(None) | (
        ~source_type.in_(AUTO_SOURCE_TYPES)
    )
    rows = (
        db.query(
            Project.id,
            Project.project_name,
            Project.project_code,
            Project.contract_amount,
            func.count(ProjectCost.id).label("cost_records"),
            actual_total_cost.label("total_cost"),
            func.coalesce(
                func.sum(
                    case(
                        (
                            cost_basis == CostCollectionService.COST_BASIS_PLAN,
                            ProjectCost.amount,
                        ),
                        else_=0,
                    )
                ),
                0,
            ).label("plan_cost"),
            func.coalesce(
                func.sum(
                    case((source_type == "PURCHASE_ORDER", ProjectCost.amount), else_=0)
                ),
                0,
            ).label("po_cost"),
            func.coalesce(
                func.sum(
                    case((source_type == "BOM_COST", ProjectCost.amount), else_=0)
                ),
                0,
            ).label("bom_cost"),
            func.coalesce(
                func.sum(
                    case((source_type == "WORK_ORDER", ProjectCost.amount), else_=0)
                ),
                0,
            ).label("wo_cost"),
            func.coalesce(
                func.sum(
                    case((source_type == "LABOR_COST", ProjectCost.amount), else_=0)
                ),
                0,
            ).label("timesheet_cost"),
            func.coalesce(
                func.sum(case((manual_condition, ProjectCost.amount), else_=0)),
                0,
            ).label("manual_cost"),
        )
        .join(ProjectCost, ProjectCost.project_id == Project.id)
        .filter(Project.is_active.is_(True))
        .group_by(Project.id)
        .having(func.count(ProjectCost.id) > 0)
        .order_by(actual_total_cost.desc())
        .all()
    )

    return {
        "projects": [
            {
                "project_id": r.id,
                "project_name": r.project_name,
                "project_code": r.project_code,
                "contract_amount": float(r.contract_amount or 0),
                "total_cost": float(r.total_cost or 0),
                "actual_cost": float(r.total_cost or 0),
                "plan_cost": float(r.plan_cost or 0),
                "po_cost": float(r.po_cost or 0),
                "bom_cost": float(r.bom_cost or 0),
                "wo_cost": float(r.wo_cost or 0),
                "timesheet_cost": float(r.timesheet_cost or 0),
                "labor_cost": float((r.wo_cost or 0) + (r.timesheet_cost or 0)),
                "manual_cost": float(r.manual_cost or 0),
                "cost_records": r.cost_records,
                "margin": (
                    round(
                        (float(r.contract_amount or 0) - float(r.total_cost or 0))
                        / float(r.contract_amount)
                        * 100,
                        2,
                    )
                    if r.contract_amount
                    else 0
                ),
            }
            for r in rows
        ]
    }
