# -*- coding: utf-8 -*-
"""
项目成本聚合服务
用于批量获取多个项目的成本数据，避免N+1查询问题
"""

from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost
from app.models.project.financial import FinancialProjectCost
from app.schemas.project import ProjectCostBreakdown, ProjectCostSummary


class ProjectCostAggregationService:
    """项目成本聚合服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_projects_cost_summary(
        self, project_ids: List[int], include_breakdown: bool = True
    ) -> Dict[int, ProjectCostSummary]:
        """
        批量获取项目成本摘要
        
        Args:
            project_ids: 项目ID列表
            include_breakdown: 是否包含成本明细
            
        Returns:
            dict: {project_id: ProjectCostSummary}
        """
        if not project_ids:
            return {}

        # 1. 获取项目基础数据（预算、实际成本）
        projects_data = (
            self.db.query(
                Project.id,
                Project.budget_amount,
                Project.actual_cost,
            )
            .filter(Project.id.in_(project_ids))
            .all()
        )

        projects_dict = {
            p.id: {
                "budget": Decimal(str(p.budget_amount or 0)),
                "actual_cost": Decimal(str(p.actual_cost or 0)),
            }
            for p in projects_data
        }

        # 2. 如果需要成本明细，批量查询成本数据
        cost_breakdown_dict = {}
        if include_breakdown:
            cost_breakdown_dict = self._get_cost_breakdown_batch(project_ids)

        # 3. 组装成本摘要
        result = {}
        for project_id in project_ids:
            project_info = projects_dict.get(project_id)
            if not project_info:
                continue

            budget = project_info["budget"]
            actual_cost = project_info["actual_cost"]
            
            # 计算差异
            variance = actual_cost - budget
            variance_pct = (
                (variance / budget * 100) if budget > 0 else Decimal("0")
            )
            
            # 计算使用率
            budget_used_pct = (
                (actual_cost / budget * 100) if budget > 0 else Decimal("0")
            )
            
            # 判断是否超支
            overrun = actual_cost > budget and budget > 0

            # 成本明细
            cost_breakdown = None
            if include_breakdown and project_id in cost_breakdown_dict:
                cost_breakdown = cost_breakdown_dict[project_id]

            result[project_id] = ProjectCostSummary(
                total_cost=round(actual_cost, 2),
                budget=round(budget, 2),
                budget_used_pct=round(budget_used_pct, 2),
                overrun=overrun,
                variance=round(variance, 2),
                variance_pct=round(variance_pct, 2),
                cost_breakdown=cost_breakdown,
            )

        return result

    def _get_cost_breakdown_batch(
        self, project_ids: List[int]
    ) -> Dict[int, ProjectCostBreakdown]:
        """
        批量获取成本明细（按类型分类）
        
        Args:
            project_ids: 项目ID列表
            
        Returns:
            dict: {project_id: ProjectCostBreakdown}
        """
        # 查询ProjectCost表
        project_cost_data = (
            self.db.query(
                ProjectCost.project_id,
                ProjectCost.cost_type,
                func.sum(ProjectCost.amount).label("amount"),
            )
            .filter(ProjectCost.project_id.in_(project_ids))
            .group_by(ProjectCost.project_id, ProjectCost.cost_type)
            .all()
        )

        # 查询FinancialProjectCost表
        financial_cost_data = (
            self.db.query(
                FinancialProjectCost.project_id,
                FinancialProjectCost.cost_type,
                func.sum(FinancialProjectCost.amount).label("amount"),
            )
            .filter(FinancialProjectCost.project_id.in_(project_ids))
            .group_by(FinancialProjectCost.project_id, FinancialProjectCost.cost_type)
            .all()
        )

        # 合并数据
        breakdown_data: Dict[int, Dict[str, Decimal]] = {}
        for project_id, cost_type, amount in project_cost_data:
            if project_id not in breakdown_data:
                breakdown_data[project_id] = {}
            cost_type_key = self._map_cost_type(cost_type)
            breakdown_data[project_id][cost_type_key] = (
                breakdown_data[project_id].get(cost_type_key, Decimal("0"))
                + Decimal(str(amount or 0))
            )

        for project_id, cost_type, amount in financial_cost_data:
            if project_id not in breakdown_data:
                breakdown_data[project_id] = {}
            cost_type_key = self._map_cost_type(cost_type)
            breakdown_data[project_id][cost_type_key] = (
                breakdown_data[project_id].get(cost_type_key, Decimal("0"))
                + Decimal(str(amount or 0))
            )

        # 转换为ProjectCostBreakdown对象
        result = {}
        for project_id, breakdown in breakdown_data.items():
            result[project_id] = ProjectCostBreakdown(
                labor=round(breakdown.get("labor", Decimal("0")), 2),
                material=round(breakdown.get("material", Decimal("0")), 2),
                equipment=round(breakdown.get("equipment", Decimal("0")), 2),
                travel=round(breakdown.get("travel", Decimal("0")), 2),
                other=round(breakdown.get("other", Decimal("0")), 2),
            )

        return result

    def _map_cost_type(self, cost_type: Optional[str]) -> str:
        """
        将成本类型映射到标准类别
        
        Args:
            cost_type: 原始成本类型
            
        Returns:
            str: 标准成本类别 (labor/material/equipment/travel/other)
        """
        if not cost_type:
            return "other"

        cost_type_upper = cost_type.upper()
        
        # 人工成本
        if cost_type_upper in ["LABOR", "LABOUR", "人工", "工资", "薪资"]:
            return "labor"
        
        # 材料成本
        if cost_type_upper in ["MATERIAL", "MATERIALS", "材料", "物料", "原材料"]:
            return "material"
        
        # 设备成本
        if cost_type_upper in ["EQUIPMENT", "MACHINE", "设备", "机械", "工具"]:
            return "equipment"
        
        # 差旅成本
        if cost_type_upper in ["TRAVEL", "差旅", "出差", "交通"]:
            return "travel"
        
        # 其他成本
        return "other"

    def get_cost_summary_for_project(
        self, project_id: int, include_breakdown: bool = True
    ) -> Optional[ProjectCostSummary]:
        """
        获取单个项目的成本摘要（方便单独调用）
        
        Args:
            project_id: 项目ID
            include_breakdown: 是否包含成本明细
            
        Returns:
            ProjectCostSummary or None
        """
        summaries = self.get_projects_cost_summary([project_id], include_breakdown)
        return summaries.get(project_id)
