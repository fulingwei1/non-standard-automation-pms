# -*- coding: utf-8 -*-
"""
PMO Dashboard 适配器
"""

from datetime import datetime
from typing import List

from app.models.project import Project
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class PmoDashboardAdapter(DashboardAdapter):
    """PMO工作台适配器"""

    @property
    def module_id(self) -> str:
        return "pmo"

    @property
    def module_name(self) -> str:
        return "项目管理办公室"

    @property
    def supported_roles(self) -> List[str]:
        return ["pmo", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        # 应用数据权限过滤
        from app.services.data_scope_service import DataScopeService

        query = self.db.query(Project).filter(Project.is_active)
        query = DataScopeService.apply_data_scope(
            query,
            self.db,
            self.current_user,
            resource_type="project",
            pm_field="pm_id",
        )

        projects = query.all()

        # 统计项目数据
        total = len(projects)

        # 按健康度统计
        on_track = sum(1 for p in projects if p.health == "H1")
        at_risk = sum(1 for p in projects if p.health == "H2")
        delayed = sum(1 for p in projects if p.health == "H3")
        completed = sum(1 for p in projects if p.health == "H4")

        return [
            DashboardStatCard(
                key="active_projects",
                label="活跃项目",
                value=total,
                unit="个",
                icon="project",
                color="blue",
            ),
            DashboardStatCard(
                key="on_track",
                label="正常进度",
                value=on_track,
                unit="个",
                icon="check",
                color="green",
            ),
            DashboardStatCard(
                key="at_risk",
                label="有风险",
                value=at_risk,
                unit="个",
                icon="warning",
                color="orange",
            ),
            DashboardStatCard(
                key="delayed",
                label="延期项目",
                value=delayed,
                unit="个",
                icon="alert",
                color="red",
            ),
            DashboardStatCard(
                key="completed",
                label="已完成",
                value=completed,
                unit="个",
                icon="success",
                color="gray",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        # 获取风险项目列表
        from app.services.data_scope_service import DataScopeService

        query = self.db.query(Project).filter(
            Project.is_active, Project.health.in_(["H2", "H3"])
        )
        query = DataScopeService.apply_data_scope(
            query,
            self.db,
            self.current_user,
            resource_type="project",
            pm_field="pm_id",
        )
        risk_projects = query.limit(10).all()

        risk_project_list = [
            {
                "id": p.id,
                "project_code": p.project_code,
                "project_name": p.project_name,
                "health": p.health,
                "current_stage": p.current_stage,
            }
            for p in risk_projects
        ]

        return [
            DashboardWidget(
                widget_id="risk_projects",
                widget_type="list",
                title="风险项目",
                data=risk_project_list,
                order=1,
                span=24,
            )
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        # 汇总数据
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        # 按阶段统计
        from app.services.data_scope_service import DataScopeService

        query = self.db.query(Project).filter(Project.is_active)
        query = DataScopeService.apply_data_scope(
            query,
            self.db,
            self.current_user,
            resource_type="project",
            pm_field="pm_id",
        )
        projects = query.all()

        by_stage = {}
        for project in projects:
            stage = project.current_stage or "未知"
            by_stage[stage] = by_stage.get(stage, 0) + 1

        details = {
            "by_stage": [{"stage": k, "count": v} for k, v in by_stage.items()]
        }

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )
