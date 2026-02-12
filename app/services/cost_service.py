# -*- coding: utf-8 -*-
"""
成本统一服务（Facade）

聚合成本分析、成本统计与利润分析等常用逻辑，减少各处重复计算。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost


class CostService:
    """成本服务统一入口"""

    def __init__(self, db: Session):
        self.db = db

    def get_project(self, project_id: int) -> Optional[Project]:
        return self.db.query(Project).filter(Project.id == project_id).first()

    def get_cost_breakdown(self, project_id: int) -> Dict[str, Any]:
        """获取项目成本汇总与分布"""
        total_cost_result = (
            self.db.query(func.sum(ProjectCost.amount).label("total"))
            .filter(ProjectCost.project_id == project_id)
            .first()
        )
        total_cost = float(total_cost_result.total or 0)

        cost_by_type_result = (
            self.db.query(ProjectCost.cost_type, func.sum(ProjectCost.amount).label("amount"))
            .filter(ProjectCost.project_id == project_id)
            .group_by(ProjectCost.cost_type)
            .all()
        )
        cost_by_type = {ct or "其他": float(amount or 0) for ct, amount in cost_by_type_result}

        cost_by_category_result = (
            self.db.query(ProjectCost.cost_category, func.sum(ProjectCost.amount).label("amount"))
            .filter(ProjectCost.project_id == project_id)
            .group_by(ProjectCost.cost_category)
            .all()
        )
        cost_by_category = {cc or "其他": float(amount or 0) for cc, amount in cost_by_category_result}

        return {
            "total_cost": total_cost,
            "cost_by_type": cost_by_type,
            "cost_by_category": cost_by_category,
        }

    @staticmethod
    def calculate_variance(budget_amount: float, actual_cost: float) -> Dict[str, float]:
        """计算预算偏差与偏差率"""
        budget_variance = actual_cost - budget_amount if budget_amount > 0 else 0
        budget_variance_pct = (budget_variance / budget_amount * 100) if budget_amount > 0 else 0
        return {
            "budget_variance": budget_variance,
            "budget_variance_pct": budget_variance_pct,
        }

    def get_project_cost_analysis(
        self,
        project_id: int,
        compare_project_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """成本对比分析"""
        project = self.get_project(project_id)
        if not project:
            return {"error": "项目不存在"}

        breakdown = self.get_cost_breakdown(project_id)
        total_cost = breakdown["total_cost"]
        budget_amount = float(project.budget_amount or 0)
        contract_amount = float(project.contract_amount or 0)
        actual_cost = float(project.actual_cost or 0)

        variance = self.calculate_variance(budget_amount, actual_cost)
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
            "budget_variance": round(variance["budget_variance"], 2),
            "budget_variance_pct": round(variance["budget_variance_pct"], 2),
            "contract_variance": round(contract_variance, 2),
            "contract_variance_pct": round(contract_variance_pct, 2),
            "cost_by_type": [
                {"type": k, "amount": round(v, 2)} for k, v in breakdown["cost_by_type"].items()
            ],
            "cost_by_category": [
                {"category": k, "amount": round(v, 2)} for k, v in breakdown["cost_by_category"].items()
            ],
        }

        if compare_project_id:
            compare_project = self.get_project(compare_project_id)
            if compare_project:
                compare_breakdown = self.get_cost_breakdown(compare_project_id)
                compare_budget = float(compare_project.budget_amount or 0)
                compare_actual = float(compare_project.actual_cost or 0)

                result["comparison"] = {
                    "compare_project_id": compare_project_id,
                    "compare_project_name": compare_project.project_name,
                    "compare_budget_amount": compare_budget,
                    "compare_actual_cost": compare_actual,
                    "compare_total_cost": round(compare_breakdown["total_cost"], 2),
                    "budget_diff": round(budget_amount - compare_budget, 2),
                    "actual_diff": round(actual_cost - compare_actual, 2),
                }

        return result

    def get_project_revenue_detail(self, project_id: int) -> Dict[str, Any]:
        """获取项目收入详情（封装 RevenueService）"""
        from app.services.revenue_service import RevenueService

        revenue_detail = RevenueService.get_project_revenue_detail(self.db, project_id)
        return {
            "project_id": revenue_detail["project_id"],
            "project_code": revenue_detail.get("project_code"),
            "project_name": revenue_detail.get("project_name"),
            "contract_amount": float(revenue_detail["contract_amount"]),
            "received_amount": float(revenue_detail["received_amount"]),
            "invoiced_amount": float(revenue_detail["invoiced_amount"]),
            "paid_invoice_amount": float(revenue_detail["paid_invoice_amount"]),
            "pending_amount": float(revenue_detail["pending_amount"]),
            "receive_rate": float(revenue_detail["receive_rate"]),
        }

    def get_project_profit_analysis(self, project_id: int) -> Dict[str, Any]:
        """项目利润分析"""
        project = self.get_project(project_id)
        if not project:
            return {"error": "项目不存在"}

        revenue_detail = self.get_project_revenue_detail(project_id)
        contract_amount = revenue_detail["contract_amount"]
        received_amount = revenue_detail["received_amount"]
        invoiced_amount = revenue_detail["invoiced_amount"]

        actual_cost = float(project.actual_cost or 0)

        gross_profit = contract_amount - actual_cost
        profit_margin = (gross_profit / contract_amount * 100) if contract_amount > 0 else 0

        breakdown = self.get_cost_breakdown(project_id)
        cost_breakdown = []
        for cost_type, amount in breakdown["cost_by_type"].items():
            pct = (amount / actual_cost * 100) if actual_cost > 0 else 0
            cost_breakdown.append({
                "cost_type": cost_type,
                "amount": round(amount, 2),
                "percentage": round(pct, 2),
            })

        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "contract_amount": contract_amount,
            "received_amount": received_amount,
            "invoiced_amount": invoiced_amount,
            "actual_cost": actual_cost,
            "gross_profit": round(gross_profit, 2),
            "profit_margin": round(profit_margin, 2),
            "cost_breakdown": cost_breakdown,
        }

    def calculate_cost_stats(self, project_id: int, budget_amount: float) -> Dict[str, Any]:
        """项目成本统计（用于仪表盘等）"""
        breakdown = self.get_cost_breakdown(project_id)
        total_cost = breakdown["total_cost"]
        variance = self.calculate_variance(budget_amount, total_cost)
        variance_rate = variance["budget_variance_pct"] if budget_amount > 0 else 0

        return {
            "total_cost": total_cost,
            "budget_amount": budget_amount,
            "cost_variance": variance["budget_variance"],
            "cost_variance_rate": variance_rate,
            "cost_by_type": breakdown["cost_by_type"],
            "cost_by_category": breakdown["cost_by_category"],
            "is_over_budget": total_cost > budget_amount if budget_amount > 0 else False,
        }


__all__ = ["CostService"]
