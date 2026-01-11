# -*- coding: utf-8 -*-
"""
预算与实际对比分析服务
"""

from decimal import Decimal
from datetime import date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.project import Project, ProjectCost
from app.models.budget import ProjectBudget, ProjectBudgetItem


class BudgetAnalysisService:
    """预算分析服务"""
    
    @staticmethod
    def get_budget_execution_analysis(
        db: Session,
        project_id: int
    ) -> Dict:
        """
        获取项目预算执行情况分析
        
        Returns:
            包含预算执行情况的字典
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")
        
        # 获取项目的最新生效预算
        budget = (
            db.query(ProjectBudget)
            .filter(
                ProjectBudget.project_id == project_id,
                ProjectBudget.is_active == True,
                ProjectBudget.status == "APPROVED"
            )
            .order_by(ProjectBudget.version.desc())
            .first()
        )
        
        # 获取实际成本
        costs = db.query(ProjectCost).filter(ProjectCost.project_id == project_id).all()
        total_actual_cost = sum([float(c.amount or 0) for c in costs])
        
        # 如果项目有actual_cost字段，优先使用
        if project.actual_cost:
            total_actual_cost = float(project.actual_cost)
        
        # 预算金额
        budget_amount = float(budget.total_amount) if budget else float(project.budget_amount or 0)
        
        # 计算偏差
        variance = total_actual_cost - budget_amount
        variance_pct = (variance / budget_amount * 100) if budget_amount > 0 else 0
        
        # 预算执行率
        execution_rate = (total_actual_cost / budget_amount * 100) if budget_amount > 0 else 0
        
        # 剩余预算
        remaining_budget = budget_amount - total_actual_cost
        
        # 按成本类别对比（如果有预算明细）
        category_comparison = []
        if budget and budget.items:
            # 按成本类别汇总预算
            budget_by_category = {}
            for item in budget.items:
                category = item.cost_category
                if category not in budget_by_category:
                    budget_by_category[category] = 0
                budget_by_category[category] += float(item.budget_amount)
            
            # 按成本类别汇总实际成本
            actual_by_category = {}
            for cost in costs:
                category = cost.cost_category or "其他"
                if category not in actual_by_category:
                    actual_by_category[category] = 0
                actual_by_category[category] += float(cost.amount or 0)
            
            # 合并对比
            all_categories = set(list(budget_by_category.keys()) + list(actual_by_category.keys()))
            for category in all_categories:
                budget_amt = budget_by_category.get(category, 0)
                actual_amt = actual_by_category.get(category, 0)
                cat_variance = actual_amt - budget_amt
                cat_variance_pct = (cat_variance / budget_amt * 100) if budget_amt > 0 else 0
                cat_execution_rate = (actual_amt / budget_amt * 100) if budget_amt > 0 else 0
                
                category_comparison.append({
                    "category": category,
                    "budget_amount": round(budget_amt, 2),
                    "actual_amount": round(actual_amt, 2),
                    "variance": round(cat_variance, 2),
                    "variance_pct": round(cat_variance_pct, 2),
                    "execution_rate": round(cat_execution_rate, 2),
                    "status": "正常" if abs(cat_variance_pct) <= 5 else "警告" if abs(cat_variance_pct) <= 10 else "超支"
                })
        
        # 预警状态
        if execution_rate > 100:
            warning_status = "超支"
        elif execution_rate > 90:
            warning_status = "警告"
        elif execution_rate > 80:
            warning_status = "注意"
        else:
            warning_status = "正常"
        
        return {
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "budget_amount": round(budget_amount, 2),
            "actual_cost": round(total_actual_cost, 2),
            "variance": round(variance, 2),
            "variance_pct": round(variance_pct, 2),
            "execution_rate": round(execution_rate, 2),
            "remaining_budget": round(remaining_budget, 2),
            "warning_status": warning_status,
            "budget_version": budget.version if budget else None,
            "budget_no": budget.budget_no if budget else None,
            "category_comparison": category_comparison
        }
    
    @staticmethod
    def get_budget_trend_analysis(
        db: Session,
        project_id: int,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """
        获取预算执行趋势分析（按时间维度）
        
        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        
        Returns:
            包含趋势数据的字典
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError("项目不存在")
        
        # 获取预算金额
        budget = (
            db.query(ProjectBudget)
            .filter(
                ProjectBudget.project_id == project_id,
                ProjectBudget.is_active == True,
                ProjectBudget.status == "APPROVED"
            )
            .order_by(ProjectBudget.version.desc())
            .first()
        )
        budget_amount = float(budget.total_amount) if budget else float(project.budget_amount or 0)
        
        # 查询成本记录（按日期）
        query = db.query(ProjectCost).filter(ProjectCost.project_id == project_id)
        if start_date:
            query = query.filter(ProjectCost.cost_date >= start_date)
        if end_date:
            query = query.filter(ProjectCost.cost_date <= end_date)
        
        costs = query.order_by(ProjectCost.cost_date).all()
        
        # 按月份汇总
        monthly_data = {}
        cumulative_cost = 0
        
        for cost in costs:
            cost_date = cost.cost_date
            if cost_date:
                month_key = cost_date.strftime("%Y-%m")
                if month_key not in monthly_data:
                    monthly_data[month_key] = {
                        "month": month_key,
                        "monthly_cost": 0,
                        "cumulative_cost": 0,
                        "budget_amount": budget_amount,
                        "execution_rate": 0
                    }
                
                monthly_data[month_key]["monthly_cost"] += float(cost.amount or 0)
        
        # 计算累计成本和执行率
        monthly_list = []
        for month_key in sorted(monthly_data.keys()):
            data = monthly_data[month_key]
            cumulative_cost += data["monthly_cost"]
            data["cumulative_cost"] = round(cumulative_cost, 2)
            data["execution_rate"] = round((cumulative_cost / budget_amount * 100) if budget_amount > 0 else 0, 2)
            data["monthly_cost"] = round(data["monthly_cost"], 2)
            monthly_list.append(data)
        
        return {
            "project_id": project_id,
            "budget_amount": round(budget_amount, 2),
            "total_actual_cost": round(cumulative_cost, 2),
            "monthly_trend": monthly_list
        }






