# -*- coding: utf-8 -*-
"""
成本仪表盘服务
提供成本看板所需的数据聚合和分析功能
"""

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, extract, func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost, ProjectPaymentPlan
from app.models.project.financial import FinancialProjectCost


class CostDashboardService:
    """成本仪表盘服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_cost_overview(self) -> Dict[str, Any]:
        """
        获取成本总览数据
        
        Returns:
            dict: 成本总览数据
        """
        # 统计所有项目
        total_projects = self.db.query(Project).filter(
            Project.stage.notin_(["S0", "S9"])  # 排除未启动和已关闭
        ).count()
        
        # 统计预算和成本
        budget_cost_stats = self.db.query(
            func.sum(Project.budget_amount).label("total_budget"),
            func.sum(Project.actual_cost).label("total_actual_cost"),
            func.sum(Project.contract_amount).label("total_contract_amount"),
        ).filter(
            Project.stage.notin_(["S0", "S9"])
        ).first()
        
        total_budget = float(budget_cost_stats.total_budget or 0)
        total_actual_cost = float(budget_cost_stats.total_actual_cost or 0)
        total_contract_amount = float(budget_cost_stats.total_contract_amount or 0)
        
        # 预算执行率
        budget_execution_rate = (
            (total_actual_cost / total_budget * 100) if total_budget > 0 else 0
        )
        
        # 统计超支项目
        cost_overrun_count = self.db.query(Project).filter(
            and_(
                Project.stage.notin_(["S0", "S9"]),
                Project.actual_cost > Project.budget_amount,
                Project.budget_amount > 0
            )
        ).count()
        
        # 统计正常项目（成本 <= 90% 预算）
        cost_normal_count = self.db.query(Project).filter(
            and_(
                Project.stage.notin_(["S0", "S9"]),
                Project.actual_cost <= Project.budget_amount * 0.9,
                Project.budget_amount > 0
            )
        ).count()
        
        # 统计预警项目（90% < 成本 <= 100% 预算）
        cost_alert_count = self.db.query(Project).filter(
            and_(
                Project.stage.notin_(["S0", "S9"]),
                Project.actual_cost > Project.budget_amount * 0.9,
                Project.actual_cost <= Project.budget_amount,
                Project.budget_amount > 0
            )
        ).count()
        
        # 本月成本趋势
        today = date.today()
        month_start = today.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # 本月成本（从ProjectCost和FinancialProjectCost聚合）
        month_cost_project = self.db.query(
            func.sum(ProjectCost.amount).label("total")
        ).filter(
            and_(
                ProjectCost.cost_date >= month_start,
                ProjectCost.cost_date <= month_end
            )
        ).first()
        
        month_cost_financial = self.db.query(
            func.sum(FinancialProjectCost.amount).label("total")
        ).filter(
            and_(
                FinancialProjectCost.cost_date >= month_start,
                FinancialProjectCost.cost_date <= month_end
            )
        ).first()
        
        month_actual_cost = (
            float(month_cost_project.total or 0) +
            float(month_cost_financial.total or 0)
        )
        
        # 本月预算（简化估算：总预算 / 12）
        month_budget = total_budget / 12 if total_budget > 0 else 0
        
        month_variance = month_actual_cost - month_budget
        month_variance_pct = (
            (month_variance / month_budget * 100) if month_budget > 0 else 0
        )
        
        return {
            "total_projects": total_projects,
            "total_budget": round(total_budget, 2),
            "total_actual_cost": round(total_actual_cost, 2),
            "total_contract_amount": round(total_contract_amount, 2),
            "budget_execution_rate": round(budget_execution_rate, 2),
            "cost_overrun_count": cost_overrun_count,
            "cost_normal_count": cost_normal_count,
            "cost_alert_count": cost_alert_count,
            "month_budget": round(month_budget, 2),
            "month_actual_cost": round(month_actual_cost, 2),
            "month_variance": round(month_variance, 2),
            "month_variance_pct": round(month_variance_pct, 2),
        }

    def get_top_projects(self, limit: int = 10) -> Dict[str, Any]:
        """
        获取TOP项目统计
        
        Args:
            limit: 返回数量，默认10
            
        Returns:
            dict: TOP项目数据
        """
        # 查询所有活跃项目
        projects = self.db.query(Project).filter(
            and_(
                Project.stage.notin_(["S0", "S9"]),
                Project.budget_amount > 0
            )
        ).all()
        
        project_list = []
        for project in projects:
            budget_amount = float(project.budget_amount or 0)
            actual_cost = float(project.actual_cost or 0)
            contract_amount = float(project.contract_amount or 0)
            
            cost_variance = actual_cost - budget_amount
            cost_variance_pct = (
                (cost_variance / budget_amount * 100) if budget_amount > 0 else 0
            )
            
            profit = contract_amount - actual_cost
            profit_margin = (
                (profit / contract_amount * 100) if contract_amount > 0 else 0
            )
            
            project_list.append({
                "project_id": project.id,
                "project_code": project.project_code,
                "project_name": project.project_name,
                "customer_name": project.customer_name,
                "pm_name": project.pm_name,
                "budget_amount": round(budget_amount, 2),
                "actual_cost": round(actual_cost, 2),
                "contract_amount": round(contract_amount, 2),
                "cost_variance": round(cost_variance, 2),
                "cost_variance_pct": round(cost_variance_pct, 2),
                "profit": round(profit, 2),
                "profit_margin": round(profit_margin, 2),
                "stage": project.stage,
                "status": project.status,
                "health": project.health,
            })
        
        # TOP 成本最高的项目
        top_cost_projects = sorted(
            project_list, key=lambda x: x["actual_cost"], reverse=True
        )[:limit]
        
        # TOP 超支最严重的项目
        top_overrun_projects = sorted(
            [p for p in project_list if p["cost_variance"] > 0],
            key=lambda x: x["cost_variance_pct"], reverse=True
        )[:limit]
        
        # TOP 利润率最高的项目
        top_profit_margin_projects = sorted(
            project_list, key=lambda x: x["profit_margin"], reverse=True
        )[:limit]
        
        # TOP 利润率最低的项目
        bottom_profit_margin_projects = sorted(
            project_list, key=lambda x: x["profit_margin"]
        )[:limit]
        
        return {
            "top_cost_projects": top_cost_projects,
            "top_overrun_projects": top_overrun_projects,
            "top_profit_margin_projects": top_profit_margin_projects,
            "bottom_profit_margin_projects": bottom_profit_margin_projects,
        }

    def get_cost_alerts(self) -> Dict[str, Any]:
        """
        获取成本预警列表
        
        Returns:
            dict: 成本预警数据
        """
        alerts = []
        
        # 查询所有活跃项目
        projects = self.db.query(Project).filter(
            and_(
                Project.stage.notin_(["S0", "S9"]),
                Project.budget_amount > 0
            )
        ).all()
        
        for project in projects:
            budget_amount = float(project.budget_amount or 0)
            actual_cost = float(project.actual_cost or 0)
            variance = actual_cost - budget_amount
            variance_pct = (variance / budget_amount * 100) if budget_amount > 0 else 0
            
            alert_type = None
            alert_level = None
            message = None
            
            # 1. 超支预警
            if actual_cost > budget_amount:
                alert_type = "overrun"
                if variance_pct > 20:
                    alert_level = "high"
                    message = f"项目成本严重超支 {variance_pct:.1f}%"
                elif variance_pct > 10:
                    alert_level = "medium"
                    message = f"项目成本超支 {variance_pct:.1f}%"
                else:
                    alert_level = "low"
                    message = f"项目成本轻微超支 {variance_pct:.1f}%"
                    
            # 2. 预算告急（90%-100%）
            elif actual_cost > budget_amount * 0.9:
                alert_type = "budget_critical"
                usage_pct = (actual_cost / budget_amount * 100)
                if usage_pct > 95:
                    alert_level = "high"
                    message = f"预算即将用尽，已使用 {usage_pct:.1f}%"
                else:
                    alert_level = "medium"
                    message = f"预算告急，已使用 {usage_pct:.1f}%"
                    
            # 3. 成本异常波动（近期成本突增）
            # 简化版：检查本月成本是否异常高
            today = date.today()
            month_start = today.replace(day=1)
            
            month_cost = self.db.query(
                func.sum(ProjectCost.amount).label("total")
            ).filter(
                and_(
                    ProjectCost.project_id == project.id,
                    ProjectCost.cost_date >= month_start
                )
            ).first()
            
            month_cost_value = float(month_cost.total or 0)
            avg_monthly_cost = actual_cost / 12 if actual_cost > 0 else 0
            
            if month_cost_value > avg_monthly_cost * 2 and avg_monthly_cost > 0:
                # 本月成本是平均月成本的2倍以上
                alert_type = "abnormal"
                alert_level = "high"
                message = f"本月成本异常增长，为平均月成本的 {month_cost_value / avg_monthly_cost:.1f} 倍"
            
            # 添加预警
            if alert_type:
                alerts.append({
                    "project_id": project.id,
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "alert_type": alert_type,
                    "alert_level": alert_level,
                    "budget_amount": round(budget_amount, 2),
                    "actual_cost": round(actual_cost, 2),
                    "variance": round(variance, 2),
                    "variance_pct": round(variance_pct, 2),
                    "message": message,
                    "created_at": datetime.now().date(),
                })
        
        # 统计预警级别
        high_alerts = len([a for a in alerts if a["alert_level"] == "high"])
        medium_alerts = len([a for a in alerts if a["alert_level"] == "medium"])
        low_alerts = len([a for a in alerts if a["alert_level"] == "low"])
        
        # 按预警级别和偏差率排序
        alerts.sort(
            key=lambda x: (
                {"high": 0, "medium": 1, "low": 2}[x["alert_level"]],
                -abs(x["variance_pct"])
            )
        )
        
        return {
            "total_alerts": len(alerts),
            "high_alerts": high_alerts,
            "medium_alerts": medium_alerts,
            "low_alerts": low_alerts,
            "alerts": alerts,
        }

    def get_project_cost_dashboard(self, project_id: int) -> Dict[str, Any]:
        """
        获取单项目成本仪表盘
        
        Args:
            project_id: 项目ID
            
        Returns:
            dict: 项目成本仪表盘数据
        """
        project = self.db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"项目 {project_id} 不存在")
        
        budget_amount = float(project.budget_amount or 0)
        actual_cost = float(project.actual_cost or 0)
        contract_amount = float(project.contract_amount or 0)
        variance = actual_cost - budget_amount
        variance_pct = (variance / budget_amount * 100) if budget_amount > 0 else 0
        
        # 成本结构（按cost_type分类）
        cost_breakdown_data = self.db.query(
            ProjectCost.cost_type,
            func.sum(ProjectCost.amount).label("amount")
        ).filter(
            ProjectCost.project_id == project_id
        ).group_by(
            ProjectCost.cost_type
        ).all()
        
        # 加入财务成本
        financial_breakdown_data = self.db.query(
            FinancialProjectCost.cost_type,
            func.sum(FinancialProjectCost.amount).label("amount")
        ).filter(
            FinancialProjectCost.project_id == project_id
        ).group_by(
            FinancialProjectCost.cost_type
        ).all()
        
        # 合并成本数据
        breakdown_dict = {}
        for cost_type, amount in cost_breakdown_data:
            key = cost_type or "其他"
            breakdown_dict[key] = breakdown_dict.get(key, 0) + float(amount or 0)
        
        for cost_type, amount in financial_breakdown_data:
            key = cost_type or "其他"
            breakdown_dict[key] = breakdown_dict.get(key, 0) + float(amount or 0)
        
        total_breakdown = sum(breakdown_dict.values())
        cost_breakdown = [
            {
                "category": category,
                "amount": round(amount, 2),
                "percentage": round((amount / total_breakdown * 100) if total_breakdown > 0 else 0, 2)
            }
            for category, amount in breakdown_dict.items()
        ]
        
        # 月度成本数据（近12个月）
        monthly_costs = []
        today = date.today()
        
        for i in range(11, -1, -1):
            month_date = today - timedelta(days=30 * i)
            month_start = month_date.replace(day=1)
            if month_date.month == 12:
                month_end = month_date.replace(day=31)
            else:
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            month_str = month_date.strftime("%Y-%m")
            
            # 查询该月成本
            month_cost_project = self.db.query(
                func.sum(ProjectCost.amount).label("total")
            ).filter(
                and_(
                    ProjectCost.project_id == project_id,
                    ProjectCost.cost_date >= month_start,
                    ProjectCost.cost_date <= month_end
                )
            ).first()
            
            month_cost_financial = self.db.query(
                func.sum(FinancialProjectCost.amount).label("total")
            ).filter(
                and_(
                    FinancialProjectCost.project_id == project_id,
                    FinancialProjectCost.cost_date >= month_start,
                    FinancialProjectCost.cost_date <= month_end
                )
            ).first()
            
            month_actual = (
                float(month_cost_project.total or 0) +
                float(month_cost_financial.total or 0)
            )
            
            # 月度预算（简化：总预算 / 12）
            month_budget = budget_amount / 12 if budget_amount > 0 else 0
            month_variance = month_actual - month_budget
            month_variance_pct = (
                (month_variance / month_budget * 100) if month_budget > 0 else 0
            )
            
            monthly_costs.append({
                "month": month_str,
                "budget": round(month_budget, 2),
                "actual_cost": round(month_actual, 2),
                "variance": round(month_variance, 2),
                "variance_pct": round(month_variance_pct, 2),
            })
        
        # 成本趋势（累计成本）
        cost_trend = []
        cumulative_cost = 0
        for monthly_data in monthly_costs:
            cumulative_cost += monthly_data["actual_cost"]
            cost_trend.append({
                "month": monthly_data["month"],
                "cumulative_cost": round(cumulative_cost, 2),
                "budget_line": round(budget_amount * (len(cost_trend) + 1) / 12, 2),
            })
        
        # 收入与利润
        # 已收款
        received_amount_data = self.db.query(
            func.sum(ProjectPaymentPlan.actual_amount).label("total")
        ).filter(
            and_(
                ProjectPaymentPlan.project_id == project_id,
                ProjectPaymentPlan.status == "COMPLETED"
            )
        ).first()
        received_amount = float(received_amount_data.total or 0)
        
        # 已开票
        invoiced_amount_data = self.db.query(
            func.sum(ProjectPaymentPlan.invoice_amount).label("total")
        ).filter(
            ProjectPaymentPlan.project_id == project_id
        ).first()
        invoiced_amount = float(invoiced_amount_data.total or 0)
        
        # 毛利润和利润率
        gross_profit = contract_amount - actual_cost
        profit_margin = (gross_profit / contract_amount * 100) if contract_amount > 0 else 0
        
        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "budget_amount": round(budget_amount, 2),
            "actual_cost": round(actual_cost, 2),
            "contract_amount": round(contract_amount, 2),
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
            "cost_breakdown": cost_breakdown,
            "monthly_costs": monthly_costs,
            "cost_trend": cost_trend,
            "received_amount": round(received_amount, 2),
            "invoiced_amount": round(invoiced_amount, 2),
            "gross_profit": round(gross_profit, 2),
            "profit_margin": round(profit_margin, 2),
        }
