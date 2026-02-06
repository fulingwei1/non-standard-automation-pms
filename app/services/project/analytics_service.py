# -*- coding: utf-8 -*-
"""
项目分析聚合服务

整合核心、执行、资源、财务服务能力，面向 `/analytics` 顶层路由使用。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.services.project.core_service import ProjectCoreService
from app.services.project.execution_service import ProjectExecutionService
from app.services.project.finance_service import ProjectFinanceService
from app.services.project.resource_service import ProjectResourceService


class ProjectAnalyticsService:
    """聚合项目健康、进度、资源、财务的分析数据。"""

    def __init__(self, db: Session):
        self.db = db
        self.core_service = ProjectCoreService(db)
        self.execution_service = ProjectExecutionService(db, self.core_service)
        self.resource_service = ProjectResourceService(db, self.core_service)
        self.finance_service = ProjectFinanceService(db, self.core_service)

    def get_projects_health_summary(self, current_user: User) -> Dict[str, Any]:
        query = self.core_service.get_scoped_query(current_user)
        projects = query.all()

        by_health: Dict[str, int] = {}
        by_stage: Dict[str, int] = {}
        risk_projects = []
        today = date.today()

        for project in projects:
            health = project.health or "H1"
            stage = project.stage or "S1"
            by_health[health] = by_health.get(health, 0) + 1
            by_stage[stage] = by_stage.get(stage, 0) + 1

            if health in {"H3", "H4"} or self._is_delayed(project, today):
                risk_projects.append(
                    {
                        "project_id": project.id,
                        "project_code": project.project_code,
                        "project_name": project.project_name,
                        "health": health,
                        "stage": stage,
                        "pm_name": project.pm_name,
                        "progress_pct": float(project.progress_pct or 0),
                    }
                )

        risk_projects = sorted(risk_projects, key=lambda item: item["progress_pct"])[:10]

        return {
            "total_projects": len(projects),
            "by_health": by_health,
            "by_stage": by_stage,
            "risk_projects": risk_projects,
        }

    def get_projects_progress_summary(
        self,
        current_user: User,
        limit: int = 50,
    ) -> Dict[str, Any]:
        return self.execution_service.get_progress_overview(current_user, limit)

    def get_workload_overview(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        return self.resource_service.get_workload_overview(start_date, end_date)

    def get_costs_summary(
        self,
        current_user: User,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        group_by: str = "cost_type",
    ) -> Dict[str, Any]:
        return self.finance_service.get_cost_summary(current_user, start_date, end_date, group_by)

    @staticmethod
    def _is_delayed(project: Project, today: date) -> bool:
        if not project.planned_end_date:
            return False
        if project.actual_end_date:
            return project.actual_end_date > project.planned_end_date
        return today > project.planned_end_date and (project.stage or "") not in {"S9", "CLOSED"}
