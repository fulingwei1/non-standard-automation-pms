"""
成本分析和统计

提供成本汇总、趋势分析、利润分析、收入详情等功能。
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.project import Machine, Project, ProjectCost
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/projects/{project_id}/costs/summary", response_model=dict)
def get_project_cost_summary(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    获取项目成本汇总统计
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

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
            "amount": float(stat.amount) if stat.amount else 0,
            "count": stat.count or 0
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
            "amount": float(stat.amount) if stat.amount else 0,
            "count": stat.count or 0
        }
        for stat in category_stats
    ]

    # 按机台统计
    machine_stats = db.query(
        ProjectCost.machine_id,
        func.sum(ProjectCost.amount).label('amount'),
        func.count(ProjectCost.id).label('count')
    ).filter(
        ProjectCost.project_id == project_id,
        ProjectCost.machine_id.isnot(None)
    ).group_by(ProjectCost.machine_id).all()

    machine_summary = []
    for stat in machine_stats:
        machine = db.query(Machine).filter(Machine.id == stat.machine_id).first()
        machine_summary.append({
            "machine_id": stat.machine_id,
            "machine_code": machine.machine_code if machine else None,
            "machine_name": machine.machine_name if machine else None,
            "amount": float(stat.amount) if stat.amount else 0,
            "count": stat.count or 0
        })

    return {
        "project_id": project_id,
        "project_code": project.project_code,
        "project_name": project.project_name,
        "contract_amount": float(project.contract_amount) if project.contract_amount else 0,
        "budget_amount": float(project.budget_amount) if project.budget_amount else 0,
        "actual_cost": float(project.actual_cost) if project.actual_cost else 0,
        "summary": {
            "total_amount": total_amount,
            "total_tax": total_tax,
            "total_with_tax": total_amount + total_tax,
            "total_count": total_count
        },
        "by_type": type_summary,
        "by_category": category_summary,
        "by_machine": machine_summary
    }


@router.get("/projects/{project_id}/cost-analysis", response_model=ResponseModel)
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


@router.get("/projects/{project_id}/revenue-detail", response_model=ResponseModel)
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


@router.get("/projects/{project_id}/profit-analysis", response_model=ResponseModel)
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


@router.get("/cost-trends", response_model=ResponseModel)
def get_cost_trends(
    *,
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选（可选，不提供则查询所有项目）"),
    start_date: Optional[date] = Query(None, description="开始日期（默认30天前）"),
    end_date: Optional[date] = Query(None, description="结束日期（默认今天）"),
    group_by: str = Query("day", description="分组方式：day/week/month"),
    cost_type: Optional[str] = Query(None, description="成本类型筛选"),
    current_user: User = Depends(security.require_permission("cost:read")),
) -> Any:
    """
    成本趋势分析
    按时间分组统计成本变化趋势，支持按项目、成本类型筛选
    """
    # 设置默认日期范围
    if not end_date:
        end_date = date.today()
    if not start_date:
        start_date = end_date - timedelta(days=30)

    if group_by not in ["day", "week", "month"]:
        raise HTTPException(status_code=400, detail="group_by 必须是 day、week 或 month")

    # 构建查询
    query = db.query(ProjectCost).filter(
        ProjectCost.cost_date >= start_date,
        ProjectCost.cost_date <= end_date
    )

    if project_id:
        query = query.filter(ProjectCost.project_id == project_id)
    if cost_type:
        query = query.filter(ProjectCost.cost_type == cost_type)

    costs = query.all()

    # 按时间分组统计
    trend_data = {}

    for cost in costs:
        cost_date = cost.cost_date
        if not cost_date:
            continue

        # 根据分组方式确定时间键
        if group_by == "day":
            time_key = cost_date.isoformat()
        elif group_by == "week":
            # 计算周的开始日期（周一）
            days_since_monday = cost_date.weekday()
            week_start = cost_date - timedelta(days=days_since_monday)
            time_key = week_start.isoformat()
        else:  # month
            time_key = cost_date.strftime("%Y-%m")

        if time_key not in trend_data:
            trend_data[time_key] = {
                "period": time_key,
                "total_amount": Decimal("0"),
                "count": 0,
                "by_type": {},
                "by_category": {}
            }

        trend_data[time_key]["total_amount"] += cost.amount or Decimal("0")
        trend_data[time_key]["count"] += 1

        # 按类型统计
        cost_type_key = cost.cost_type or "其他"
        if cost_type_key not in trend_data[time_key]["by_type"]:
            trend_data[time_key]["by_type"][cost_type_key] = Decimal("0")
        trend_data[time_key]["by_type"][cost_type_key] += cost.amount or Decimal("0")

        # 按分类统计
        cost_category_key = cost.cost_category or "其他"
        if cost_category_key not in trend_data[time_key]["by_category"]:
            trend_data[time_key]["by_category"][cost_category_key] = Decimal("0")
        trend_data[time_key]["by_category"][cost_category_key] += cost.amount or Decimal("0")

    # 转换为列表并排序
    trend_list = []
    for time_key in sorted(trend_data.keys()):
        data = trend_data[time_key]
        trend_list.append({
            "period": data["period"],
            "total_amount": round(float(data["total_amount"]), 2),
            "count": data["count"],
            "by_type": {
                k: round(float(v), 2) for k, v in data["by_type"].items()
            },
            "by_category": {
                k: round(float(v), 2) for k, v in data["by_category"].items()
            }
        })

    # 计算趋势指标
    trend_analysis = {}
    if len(trend_list) >= 2:
        first_amount = trend_list[0]["total_amount"]
        last_amount = trend_list[-1]["total_amount"]
        trend_change = last_amount - first_amount
        trend_change_pct = (trend_change / first_amount * 100) if first_amount > 0 else 0

        # 计算平均成本
        avg_amount = sum([t["total_amount"] for t in trend_list]) / len(trend_list) if trend_list else 0

        # 找出最高和最低
        max_period = max(trend_list, key=lambda x: x["total_amount"])
        min_period = min(trend_list, key=lambda x: x["total_amount"])

        trend_analysis = {
            "trend_direction": "up" if trend_change > 0 else ("down" if trend_change < 0 else "stable"),
            "trend_change": round(trend_change, 2),
            "trend_change_pct": round(trend_change_pct, 2),
            "avg_amount": round(avg_amount, 2),
            "max_period": max_period["period"],
            "max_amount": max_period["total_amount"],
            "min_period": min_period["period"],
            "min_amount": min_period["total_amount"]
        }

    return ResponseModel(
        code=200,
        message="success",
        data={
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "group_by": group_by
            },
            "filters": {
                "project_id": project_id,
                "cost_type": cost_type
            },
            "trend_data": trend_list,
            "trend_analysis": trend_analysis,
            "total_periods": len(trend_list)
        }
    )
