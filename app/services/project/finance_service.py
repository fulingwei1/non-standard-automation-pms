# -*- coding: utf-8 -*-
"""
项目财务聚合服务

聚合项目成本、预算及费用分布，供分析端点复用。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost
from app.models.user import User
from app.services.data_scope import DataScopeService
from app.services.project.core_service import ProjectCoreService


class ProjectFinanceService:
    """提供跨项目成本/预算统计能力。"""

    def __init__(self, db: Session, core_service: Optional[ProjectCoreService] = None):
        self.db = db
        self.core_service = core_service or ProjectCoreService(db)

    def get_cost_summary(
        self,
        current_user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = "cost_type",
    ) -> Dict[str, Any]:
        project_ids = self._get_accessible_project_ids(current_user)
        if not project_ids:
            return {
                "projects": 0,
                "total_cost": 0.0,
                "breakdown": {},
                "top_projects": [],
                "budget": {"total_budget": 0.0, "variance": 0.0},
            }

        cost_query = self.db.query(ProjectCost).filter(ProjectCost.project_id.in_(project_ids))
        if start_date:
            cost_query = cost_query.filter(ProjectCost.cost_date >= start_date)
        if end_date:
            cost_query = cost_query.filter(ProjectCost.cost_date <= end_date)

        total_cost = float(
            cost_query.with_entities(func.coalesce(func.sum(ProjectCost.amount), 0)).scalar() or 0
        )

        group_attr = getattr(ProjectCost, group_by, None)
        if group_attr is None:
            group_attr = ProjectCost.cost_type

        grouped_rows = (
            cost_query.with_entities(
                group_attr.label("label"),
                func.coalesce(func.sum(ProjectCost.amount), 0).label("total"),
            )
            .group_by(group_attr)
            .all()
        )
        breakdown = {
            (label or "未分类"): float(total or 0) for label, total in grouped_rows
        }

        top_rows = (
            cost_query.with_entities(
                ProjectCost.project_id,
                func.coalesce(func.sum(ProjectCost.amount), 0).label("total"),
            )
            .group_by(ProjectCost.project_id)
            .order_by(func.coalesce(func.sum(ProjectCost.amount), 0).desc())
            .limit(5)
            .all()
        )
        project_map = {
            project.id: project
            for project in self.db.query(Project).filter(Project.id.in_([pid for pid, _ in top_rows])).all()
        }
        top_projects = [
            {
                "project_id": pid,
                "project_code": project_map.get(pid).project_code if project_map.get(pid) else None,
                "project_name": project_map.get(pid).project_name if project_map.get(pid) else None,
                "amount": float(total or 0),
            }
            for pid, total in top_rows
        ]

        budgets = self.db.query(Project).filter(Project.id.in_(project_ids)).all()
        total_budget = float(sum(p.budget_amount or 0 for p in budgets))
        variance = round(total_budget - total_cost, 2)

        return {
            "projects": len(project_ids),
            "total_cost": round(total_cost, 2),
            "breakdown": breakdown,
            "top_projects": top_projects,
            "budget": {
                "total_budget": round(total_budget, 2),
                "variance": variance,
            },
        }

    def _get_accessible_project_ids(self, current_user: User) -> List[int]:
        scoped_query = DataScopeService.filter_projects_by_scope(
            self.db, self.db.query(Project.id), current_user
        )
        return [project_id for (project_id,) in scoped_query.all()]
