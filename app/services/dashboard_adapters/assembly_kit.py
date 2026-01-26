# -*- coding: utf-8 -*-
"""
装配齐套 Dashboard 适配器
"""

from datetime import datetime
from decimal import Decimal
from typing import List

from sqlalchemy import and_, func

from app.models import (
    AssemblyStage,
    MaterialReadiness,
    SchedulingSuggestion,
    ShortageDetail,
)
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class AssemblyKitDashboardAdapter(DashboardAdapter):
    """装配齐套工作台适配器"""

    @property
    def module_id(self) -> str:
        return "assembly_kit"

    @property
    def module_name(self) -> str:
        return "装配齐套分析"

    @property
    def supported_roles(self) -> List[str]:
        return ["production", "procurement", "pmo", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        # 获取最近的齐套分析记录(每个项目取最新一条)
        subquery = (
            self.db.query(
                MaterialReadiness.project_id,
                func.max(MaterialReadiness.id).label("max_id"),
            )
            .group_by(MaterialReadiness.project_id)
            .subquery()
        )

        recent_analyses = (
            self.db.query(MaterialReadiness)
            .join(
                subquery,
                and_(
                    MaterialReadiness.project_id == subquery.c.project_id,
                    MaterialReadiness.id == subquery.c.max_id,
                ),
            )
            .all()
        )

        total = len(recent_analyses)
        can_start = sum(1 for r in recent_analyses if r.can_start)
        not_ready = sum(1 for r in recent_analyses if r.blocking_kit_rate < 50)
        partial = total - can_start - not_ready

        avg_kit = (
            sum(r.overall_kit_rate for r in recent_analyses) / total
            if total > 0
            else Decimal(0)
        )
        avg_blocking = (
            sum(r.blocking_kit_rate for r in recent_analyses) / total
            if total > 0
            else Decimal(0)
        )

        # 预警汇总
        alert_counts = {
            "L1": self.db.query(ShortageDetail)
            .filter(ShortageDetail.alert_level == "L1", ShortageDetail.shortage_qty > 0)
            .count(),
            "L2": self.db.query(ShortageDetail)
            .filter(ShortageDetail.alert_level == "L2", ShortageDetail.shortage_qty > 0)
            .count(),
            "L3": self.db.query(ShortageDetail)
            .filter(ShortageDetail.alert_level == "L3", ShortageDetail.shortage_qty > 0)
            .count(),
            "L4": self.db.query(ShortageDetail)
            .filter(ShortageDetail.alert_level == "L4", ShortageDetail.shortage_qty > 0)
            .count(),
        }
        total_alerts = sum(alert_counts.values())

        return [
            DashboardStatCard(
                key="total_projects",
                label="齐套分析项目",
                value=total,
                unit="个",
                icon="project",
                color="blue",
            ),
            DashboardStatCard(
                key="can_start",
                label="可以开工",
                value=can_start,
                unit="个",
                icon="start",
                color="green",
            ),
            DashboardStatCard(
                key="partial_ready",
                label="部分齐套",
                value=partial,
                unit="个",
                icon="partial",
                color="orange",
            ),
            DashboardStatCard(
                key="not_ready",
                label="未齐套",
                value=not_ready,
                unit="个",
                icon="warning",
                color="red",
            ),
            DashboardStatCard(
                key="avg_kit_rate",
                label="平均齐套率",
                value=f"{float(avg_kit):.1f}%",
                icon="rate",
                color="cyan",
            ),
            DashboardStatCard(
                key="total_alerts",
                label="缺料预警",
                value=total_alerts,
                unit="项",
                icon="alert",
                color="purple",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        # 待处理建议
        pending_suggestions = (
            self.db.query(SchedulingSuggestion)
            .filter(SchedulingSuggestion.status == "pending")
            .order_by(SchedulingSuggestion.priority_score.desc())
            .limit(5)
            .all()
        )

        suggestion_list = []
        for s in pending_suggestions:
            from app.models import Machine, Project

            project = (
                self.db.query(Project).filter(Project.id == s.project_id).first()
            )
            machine = (
                self.db.query(Machine).filter(Machine.id == s.machine_id).first()
                if s.machine_id
                else None
            )

            suggestion_list.append(
                {
                    "id": s.id,
                    "project_name": project.project_name if project else None,
                    "machine_no": machine.machine_code if machine else None,
                    "suggestion_type": s.suggestion_type,
                    "priority_score": float(s.priority_score),
                    "reason": s.reason,
                }
            )

        # 分阶段统计
        stages = (
            self.db.query(AssemblyStage)
            .filter(AssemblyStage.is_active == True)
            .order_by(AssemblyStage.stage_order)
            .all()
        )

        stage_stats = []
        for stage in stages:
            stage_stats.append(
                {
                    "stage_code": stage.stage_code,
                    "stage_name": stage.stage_name,
                    "stage_order": stage.stage_order,
                }
            )

        return [
            DashboardWidget(
                widget_id="pending_suggestions",
                widget_type="list",
                title="待处理排产建议",
                data=suggestion_list,
                order=1,
                span=12,
            ),
            DashboardWidget(
                widget_id="stage_stats",
                widget_type="table",
                title="分阶段统计",
                data=stage_stats,
                order=2,
                span=12,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        # 获取最近分析列表
        subquery = (
            self.db.query(
                MaterialReadiness.project_id,
                func.max(MaterialReadiness.id).label("max_id"),
            )
            .group_by(MaterialReadiness.project_id)
            .subquery()
        )

        recent_analyses = (
            self.db.query(MaterialReadiness)
            .join(
                subquery,
                and_(
                    MaterialReadiness.project_id == subquery.c.project_id,
                    MaterialReadiness.id == subquery.c.max_id,
                ),
            )
            .limit(10)
            .all()
        )

        from app.models import BomHeader, Machine, Project

        recent_list = []
        for r in recent_analyses:
            project = self.db.query(Project).filter(Project.id == r.project_id).first()
            bom = self.db.query(BomHeader).filter(BomHeader.id == r.bom_id).first()
            machine = (
                self.db.query(Machine).filter(Machine.id == r.machine_id).first()
                if r.machine_id
                else None
            )

            recent_list.append(
                {
                    "id": r.id,
                    "readiness_no": r.readiness_no,
                    "project_name": project.project_name if project else None,
                    "machine_no": machine.machine_code if machine else None,
                    "overall_kit_rate": float(r.overall_kit_rate),
                    "blocking_kit_rate": float(r.blocking_kit_rate),
                    "can_start": r.can_start,
                    "analysis_time": r.analysis_time,
                }
            )

        details = {"recent_analyses": recent_list}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )
