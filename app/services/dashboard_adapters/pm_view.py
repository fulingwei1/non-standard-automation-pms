# -*- coding: utf-8 -*-
"""
PM (项目经理) 个性化视图 Dashboard 适配器

关注：
- 负责项目的整体健康度
- 待处理的审批/决策
- 近期里程碑提醒
- 资源冲突告警
"""

from datetime import date, timedelta
from typing import List

from sqlalchemy import func

from app.models.project import Project
from app.models.project.financial import ProjectMilestone
from app.models.project.team import ProjectMember
from app.models.project_risk import ProjectRisk
from app.models.progress import Task
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class PmViewDashboardAdapter(DashboardAdapter):
    """项目经理个性化视图适配器"""

    @property
    def module_id(self) -> str:
        return "pm_view"

    @property
    def module_name(self) -> str:
        return "项目经理视图"

    @property
    def supported_roles(self) -> List[str]:
        return ["PM", "pm", "PMC", "pmc"]

    def _get_my_projects(self):
        """获取当前用户负责的项目"""
        return (
            self.db.query(Project)
            .filter(
                Project.is_active == True,  # noqa: E712
                Project.pm_id == self.current_user.id,
            )
            .all()
        )

    def get_stats(self) -> List[DashboardStatCard]:
        projects = self._get_my_projects()
        total = len(projects)
        healthy = sum(1 for p in projects if p.health == "H1")
        at_risk = sum(1 for p in projects if p.health == "H2")
        critical = sum(1 for p in projects if p.health in ("H3", "H4"))

        # 待处理审批数
        pending_approvals = (
            self.db.query(func.count(Project.id))
            .filter(
                Project.pm_id == self.current_user.id,
                Project.approval_status == "PENDING",
            )
            .scalar()
            or 0
        )

        # 近期里程碑（未来14天）
        today = date.today()
        upcoming_deadline = today + timedelta(days=14)
        upcoming_milestones = (
            self.db.query(func.count(ProjectMilestone.id))
            .join(Project, ProjectMilestone.project_id == Project.id)
            .filter(
                Project.pm_id == self.current_user.id,
                Project.is_active == True,  # noqa: E712
                ProjectMilestone.status == "PENDING",
                ProjectMilestone.planned_date >= today,
                ProjectMilestone.planned_date <= upcoming_deadline,
            )
            .scalar()
            or 0
        )

        # 活跃风险数
        active_risks = (
            self.db.query(func.count(ProjectRisk.id))
            .join(Project, ProjectRisk.project_id == Project.id)
            .filter(
                Project.pm_id == self.current_user.id,
                Project.is_active == True,  # noqa: E712
                ProjectRisk.status.in_(["IDENTIFIED", "ANALYZING", "PLANNING", "MONITORING"]),
            )
            .scalar()
            or 0
        )

        return [
            DashboardStatCard(
                key="my_projects",
                title="我的项目",
                value=total,
                unit="个",
            ),
            DashboardStatCard(
                key="healthy_projects",
                title="健康项目",
                value=healthy,
                unit="个",
                trend="stable" if healthy == total else "down",
            ),
            DashboardStatCard(
                key="risk_projects",
                title="风险/严重",
                value=f"{at_risk}/{critical}",
                trend="up" if (at_risk + critical) > 0 else "stable",
            ),
            DashboardStatCard(
                key="pending_approvals",
                title="待审批",
                value=pending_approvals,
                unit="项",
            ),
            DashboardStatCard(
                key="upcoming_milestones",
                title="近期里程碑",
                value=upcoming_milestones,
                unit="个",
            ),
            DashboardStatCard(
                key="active_risks",
                title="活跃风险",
                value=active_risks,
                unit="个",
                trend="up" if active_risks > 3 else "stable",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        today = date.today()

        # 1. 项目健康度概览
        projects = self._get_my_projects()
        health_data = []
        for p in projects[:20]:
            health_data.append({
                "id": p.id,
                "project_code": p.project_code,
                "project_name": p.project_name,
                "health": p.health,
                "progress_pct": float(p.progress_pct or 0),
                "current_stage": p.stage,
                "planned_end_date": str(p.planned_end_date) if p.planned_end_date else None,
            })

        # 2. 近期里程碑列表
        upcoming_deadline = today + timedelta(days=30)
        milestones = (
            self.db.query(ProjectMilestone, Project.project_name, Project.project_code)
            .join(Project, ProjectMilestone.project_id == Project.id)
            .filter(
                Project.pm_id == self.current_user.id,
                Project.is_active == True,  # noqa: E712
                ProjectMilestone.status == "PENDING",
                ProjectMilestone.planned_date >= today,
                ProjectMilestone.planned_date <= upcoming_deadline,
            )
            .order_by(ProjectMilestone.planned_date)
            .limit(10)
            .all()
        )
        milestone_list = [
            {
                "id": ms.id,
                "milestone_name": ms.milestone_name,
                "planned_date": str(ms.planned_date),
                "project_name": proj_name,
                "project_code": proj_code,
                "is_key": ms.is_key,
                "days_remaining": (ms.planned_date - today).days,
            }
            for ms, proj_name, proj_code in milestones
        ]

        # 3. 资源冲突（同一人在多个项目分配超100%）
        resource_conflicts = (
            self.db.query(
                ProjectMember.user_id,
                func.sum(ProjectMember.allocation_pct).label("total_alloc"),
                func.count(ProjectMember.project_id).label("project_count"),
            )
            .join(Project, ProjectMember.project_id == Project.id)
            .filter(
                Project.pm_id == self.current_user.id,
                Project.is_active == True,  # noqa: E712
            )
            .group_by(ProjectMember.user_id)
            .having(func.sum(ProjectMember.allocation_pct) > 100)
            .limit(10)
            .all()
        )
        conflict_list = [
            {
                "user_id": r.user_id,
                "total_allocation": float(r.total_alloc),
                "project_count": r.project_count,
            }
            for r in resource_conflicts
        ]

        # 4. 活跃风险 TOP 列表
        risks = (
            self.db.query(ProjectRisk, Project.project_name)
            .join(Project, ProjectRisk.project_id == Project.id)
            .filter(
                Project.pm_id == self.current_user.id,
                Project.is_active == True,  # noqa: E712
                ProjectRisk.status.in_(["IDENTIFIED", "ANALYZING", "MONITORING", "OCCURRED"]),
            )
            .order_by(ProjectRisk.risk_score.desc())
            .limit(10)
            .all()
        )
        risk_list = [
            {
                "id": r.id,
                "risk_name": r.risk_name,
                "risk_level": r.risk_level,
                "risk_score": r.risk_score,
                "project_name": proj_name,
                "status": r.status,
            }
            for r, proj_name in risks
        ]

        widgets = [
            DashboardWidget(
                widget_id="pm_project_health",
                widget_type="table",
                title="项目健康度一览",
                data={"items": health_data},
                config={"sortable": True, "columns": ["project_code", "project_name", "health", "progress_pct", "current_stage"]},
            ),
            DashboardWidget(
                widget_id="pm_milestone_reminder",
                widget_type="list",
                title="近期里程碑提醒",
                data={"items": milestone_list},
                config={"highlight_key": True},
            ),
            DashboardWidget(
                widget_id="pm_risk_overview",
                widget_type="list",
                title="活跃风险 TOP",
                data={"items": risk_list},
            ),
            DashboardWidget(
                widget_id="pm_resource_conflict",
                widget_type="list",
                title="资源冲突告警",
                data={"items": conflict_list},
                config={"alert_threshold": 100},
            ),
        ]
        return widgets
