# -*- coding: utf-8 -*-
"""
项目执行聚合服务

负责提供跨项目进度、里程碑和任务的统计结果，供 /analytics 或
其他聚合端点复用。
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.services.project.core_service import ProjectCoreService
from app.services.project_dashboard_service import (
    calculate_milestone_stats,
    calculate_progress_stats,
    calculate_task_stats,
)


class ProjectExecutionService:
    """面向执行层（阶段、进度、里程碑）的聚合服务。"""

    def __init__(self, db: Session, core_service: Optional[ProjectCoreService] = None):
        self.db = db
        self.core_service = core_service or ProjectCoreService(db)

    def get_progress_overview(
        self,
        current_user: User,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        获取跨项目进度概览，默认返回最近更新的 N 个项目及统计指标。
        """
        query = (
            self.core_service.get_scoped_query(current_user)
            .order_by(Project.updated_at.desc().nullslast(), Project.id.desc())
        )
        total_projects = query.count()
        projects: List[Project] = query.limit(limit).all()

        today = date.today()
        entries: List[Dict[str, Any]] = []
        progress_values: List[float] = []
        delayed_projects = 0

        for project in projects:
            progress = calculate_progress_stats(project, today)
            milestones = calculate_milestone_stats(self.db, project.id, today)
            tasks = calculate_task_stats(self.db, project.id)

            if progress.get("is_delayed"):
                delayed_projects += 1
            progress_values.append(float(progress.get("actual_progress", 0)))

            entries.append(
                {
                    "project_id": project.id,
                    "project_code": project.project_code,
                    "project_name": project.project_name,
                    "stage": project.stage or "S1",
                    "status": project.status or "ST01",
                    "pm_name": project.pm_name,
                    "progress": progress,
                    "milestones": milestones,
                    "tasks": tasks,
                }
            )

        average_progress = (
            round(sum(progress_values) / len(progress_values), 2) if progress_values else 0.0
        )

        slowest = sorted(entries, key=lambda item: item["progress"]["actual_progress"])[:5]
        top_performers = sorted(
            entries, key=lambda item: item["progress"]["actual_progress"], reverse=True
        )[:5]

        return {
            "total_projects": total_projects,
            "sampled_projects": len(entries),
            "average_progress": average_progress,
            "delayed_projects": delayed_projects,
            "projects": entries,
            "slowest_projects": slowest,
            "top_projects": top_performers,
        }
