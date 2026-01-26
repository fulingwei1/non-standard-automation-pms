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
from app.models.project import Machine, Project, ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel

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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 获取当前项目的成本统计
    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()

    total_cost = sum([float(c.amount or 0) for c in costs])
    budget_amount = float(project.budget_amount or 0)
    contract_amount = float(project.contract_amount or 0)
    actual_cost = float(project.actual_cost or 0)

    # 按成本类型统计
    cost_by_type = {}
    for cost in costs:
        cost_type = cost.cost_type or "其他"
        if cost_type not in cost_by_type:
            cost_by_type[cost_type] = 0
        cost_by_type[cost_type] += float(cost.amount or 0)

    # 按成本分类统计
    cost_by_category = {}
    for cost in costs:
        category = cost.cost_category or "其他"
        if category not in cost_by_category:
            cost_by_category[category] = 0
        cost_by_category[category] += float(cost.amount or 0)

    # 计算偏差
    budget_variance = actual_cost - budget_amount if budget_amount > 0 else 0
    budget_variance_pct = (budget_variance / budget_amount * 100) if budget_amount > 0 else 0

    contract_variance = contract_amount - actual_cost if contract_amount > 0 else 0
    contract_variance_pct = (contract_variance / contract_amount * 100) if contract_amount > 0 else 0

    result = {
        "project_id": project_id,
        "project_name": project.project_name,
        "project_code": project.project_code,
        "budget_amount": budget_amount,
        "contract_amount": contract_amount,
        "actual_cost": actual_cost,
        "total_cost": total_cost,
        "budget_variance": round(budget_variance, 2),
        "budget_variance_pct": round(budget_variance_pct, 2),
        "contract_variance": round(contract_variance, 2),
        "contract_variance_pct": round(contract_variance_pct, 2),
        "cost_by_type": [{"type": k, "amount": round(v, 2)} for k, v in cost_by_type.items()],
        "cost_by_category": [{"category": k, "amount": round(v, 2)} for k, v in cost_by_category.items()]
    }

    # 如果指定了对比项目，添加对比数据
    if compare_project_id:
        compare_project = db.query(Project).filter(Project.id == compare_project_id).first()
        if compare_project:
            compare_costs = db.query(ProjectCost).filter(ProjectCost.project_id == compare_project_id).all()
            compare_total_cost = sum([float(c.amount or 0) for c in compare_costs])
            compare_budget = float(compare_project.budget_amount or 0)
            compare_actual = float(compare_project.actual_cost or 0)

            result["comparison"] = {
                "compare_project_id": compare_project_id,
                "compare_project_name": compare_project.project_name,
                "compare_budget_amount": compare_budget,
                "compare_actual_cost": compare_actual,
                "compare_total_cost": round(compare_total_cost, 2),
                "budget_diff": round(budget_amount - compare_budget, 2),
                "actual_diff": round(actual_cost - compare_actual, 2)
            }

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
    from app.services.revenue_service import RevenueService

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    revenue_detail = RevenueService.get_project_revenue_detail(db, project_id)

    # 转换Decimal为float以便JSON序列化
    result = {
        "project_id": revenue_detail["project_id"],
        "project_code": revenue_detail.get("project_code"),
        "project_name": revenue_detail.get("project_name"),
        "contract_amount": float(revenue_detail["contract_amount"]),
        "received_amount": float(revenue_detail["received_amount"]),
        "invoiced_amount": float(revenue_detail["invoiced_amount"]),
        "paid_invoice_amount": float(revenue_detail["paid_invoice_amount"]),
        "pending_amount": float(revenue_detail["pending_amount"]),
        "receive_rate": float(revenue_detail["receive_rate"])
    }

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
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 使用营业收入服务获取收入数据
    from app.services.revenue_service import RevenueService

    revenue_detail = RevenueService.get_project_revenue_detail(db, project_id)
    contract_amount = float(revenue_detail["contract_amount"])
    received_amount = float(revenue_detail["received_amount"])
    invoiced_amount = float(revenue_detail["invoiced_amount"])

    # 获取实际成本
    actual_cost = float(project.actual_cost or 0)

    # 计算利润
    gross_profit = contract_amount - actual_cost
    profit_margin = (gross_profit / contract_amount * 100) if contract_amount > 0 else 0

    # 按成本类型分析
    costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
    cost_by_type = {}
    for cost in costs:
        cost_type = cost.cost_type or "其他"
        if cost_type not in cost_by_type:
            cost_by_type[cost_type] = 0
        cost_by_type[cost_type] += float(cost.amount or 0)

    # 成本占比
    cost_breakdown = []
    for cost_type, amount in cost_by_type.items():
        pct = (amount / actual_cost * 100) if actual_cost > 0 else 0
        cost_breakdown.append({
            "cost_type": cost_type,
            "amount": round(amount, 2),
            "percentage": round(pct, 2)
        })

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
                "receive_rate": round(float(revenue_detail["receive_rate"]), 2)
            },
            "cost": {
                "total_cost": round(actual_cost, 2),
                "budget_amount": round(float(project.budget_amount or 0), 2),
                "cost_overrun": round(actual_cost - float(project.budget_amount or 0), 2)
            },
            "profit": {
                "gross_profit": round(gross_profit, 2),
                "profit_margin": round(profit_margin, 2),
                "profit_status": "盈利" if gross_profit > 0 else "亏损"
            },
            "cost_breakdown": cost_breakdown,
            "machine_profit": machine_profit
        }
    )
