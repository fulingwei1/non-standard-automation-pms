# -*- coding: utf-8 -*-
"""
项目成本分析模块

提供项目成本分析、利润分析、收入详情等功能。
路由: /projects/{project_id}/costs/analysis
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.cost_service import CostService

router = APIRouter()


@router.get("/cost-analysis", response_model=ResponseModel)
def get_project_cost_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    compare_project_id: Optional[int] = Query(None, description="对比项目ID（可选）"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    成本对比分析
    对比项目预算、实际成本、合同金额等，支持与另一个项目对比
    """
    service = CostService(db)
    result = service.get_project_cost_analysis(project_id, compare_project_id)
    if result.get("error"):
        raise HTTPException(status_code=404, detail=result["error"])

    return ResponseModel(
        code=200,
        message="success",
        data=result
    )


@router.get("/revenue-detail", response_model=ResponseModel)
def get_project_revenue_detail(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目收入详情
    包含合同金额、已收款金额、已开票金额等
    """
    service = CostService(db)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    result = service.get_project_revenue_detail(project_id)

    return ResponseModel(
        code=200,
        message="success",
        data=result
    )


@router.get("/profit-analysis", response_model=ResponseModel)
def get_project_profit_analysis(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    项目利润分析
    分析项目的收入、成本、利润等财务指标
    """
    service = CostService(db)
    project = service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    profit_result = service.get_project_profit_analysis(project_id)
    if profit_result.get("error"):
        raise HTTPException(status_code=404, detail=profit_result["error"])

    revenue_detail = service.get_project_revenue_detail(project_id)

    contract_amount = profit_result["contract_amount"]
    received_amount = profit_result["received_amount"]
    invoiced_amount = profit_result["invoiced_amount"]
    actual_cost = profit_result["actual_cost"]
    gross_profit = profit_result["gross_profit"]
    profit_margin = profit_result["profit_margin"]
    cost_breakdown = profit_result["cost_breakdown"]

    # 按机台分析
    machines = db.query(Machine).filter(Machine.project_id == project_id).all()
    machine_profit = []
    for machine in machines:
        machine_costs = db.query(ProjectCost).filter(
            ProjectCost.project_id == project_id,
            ProjectCost.machine_id == machine.id
        ).all()
        machine_total_cost = sum([float(c.amount or 0) for c in machine_costs])
        # 假设按机台数量平均分配合同金额
        machine_revenue = contract_amount / len(machines) if machines else 0
        machine_profit_amount = machine_revenue - machine_total_cost
        machine_profit_margin = (machine_profit_amount / machine_revenue * 100) if machine_revenue > 0 else 0

        machine_profit.append({
            "machine_id": machine.id,
            "machine_code": machine.machine_code,
            "machine_name": machine.machine_name,
            "revenue": round(machine_revenue, 2),
            "cost": round(machine_total_cost, 2),
            "profit": round(machine_profit_amount, 2),
            "profit_margin": round(machine_profit_margin, 2)
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "project_id": project_id,
            "project_name": project.project_name,
            "project_code": project.project_code,
            "revenue": {
                "contract_amount": contract_amount,
                "received_amount": round(received_amount, 2),
                "invoiced_amount": round(invoiced_amount, 2),
                "pending_amount": round(revenue_detail["pending_amount"], 2),
                "receive_rate": round(float(revenue_detail["receive_rate"]), 2),
            },
            "cost": {
                "total_cost": round(actual_cost, 2),
                "budget_amount": round(float(project.budget_amount or 0), 2),
                "cost_overrun": round(actual_cost - float(project.budget_amount or 0), 2),
            },
            "profit": {
                "gross_profit": round(gross_profit, 2),
                "profit_margin": round(profit_margin, 2),
                "profit_status": "盈利" if gross_profit > 0 else "亏损",
            },
            "cost_breakdown": cost_breakdown,
            "machine_profit": machine_profit,
        }
    )
