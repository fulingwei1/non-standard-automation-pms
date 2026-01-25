# -*- coding: utf-8 -*-
"""
缺料管理 Dashboard 适配器
"""

from datetime import datetime
from typing import List

from sqlalchemy import desc

from app.models.material import MaterialShortage
from app.models.project import Project
from app.models.shortage import (
    MaterialArrival,
    MaterialSubstitution,
    MaterialTransfer,
    ShortageReport,
)
from app.schemas.dashboard import (
    DashboardListItem,
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class ShortageDashboardAdapter(DashboardAdapter):
    """缺料管理工作台适配器"""

    @property
    def module_id(self) -> str:
        return "shortage"

    @property
    def module_name(self) -> str:
        return "缺料管理"

    @property
    def supported_roles(self) -> List[str]:
        return ["procurement", "production", "pmo", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        # 缺料上报统计
        report_query = self.db.query(ShortageReport)
        total_reports = report_query.count()
        reported = (
            report_query.filter(ShortageReport.status == "REPORTED").count()
        )
        confirmed = (
            report_query.filter(ShortageReport.status == "CONFIRMED").count()
        )
        handling = (
            report_query.filter(ShortageReport.status == "HANDLING").count()
        )
        resolved = (
            report_query.filter(ShortageReport.status == "RESOLVED").count()
        )

        # 紧急缺料
        urgent_reports = (
            report_query.filter(
                ShortageReport.urgent_level.in_(["URGENT", "CRITICAL"]),
                ShortageReport.status != "RESOLVED",
            ).count()
        )

        # 系统检测的缺料预警
        alert_query = self.db.query(MaterialShortage)
        total_alerts = alert_query.count()
        unresolved_alerts = (
            alert_query.filter(MaterialShortage.status != "RESOLVED").count()
        )
        critical_alerts = (
            alert_query.filter(
                MaterialShortage.alert_level == "CRITICAL",
                MaterialShortage.status != "RESOLVED",
            ).count()
        )

        # 到货跟踪统计
        arrival_query = self.db.query(MaterialArrival)
        total_arrivals = arrival_query.count()
        pending_arrivals = (
            arrival_query.filter(MaterialArrival.status == "PENDING").count()
        )
        delayed_arrivals = (
            arrival_query.filter(MaterialArrival.is_delayed == True).count()
        )

        return [
            DashboardStatCard(
                key="total_reports",
                label="缺料上报",
                value=total_reports,
                unit="项",
                icon="report",
                color="blue",
            ),
            DashboardStatCard(
                key="urgent_reports",
                label="紧急缺料",
                value=urgent_reports,
                unit="项",
                icon="urgent",
                color="red",
            ),
            DashboardStatCard(
                key="unresolved_alerts",
                label="未解决预警",
                value=unresolved_alerts,
                unit="项",
                icon="alert",
                color="orange",
            ),
            DashboardStatCard(
                key="pending_arrivals",
                label="待到货",
                value=pending_arrivals,
                unit="项",
                icon="delivery",
                color="cyan",
            ),
            DashboardStatCard(
                key="delayed_arrivals",
                label="逾期到货",
                value=delayed_arrivals,
                unit="项",
                icon="delay",
                color="purple",
            ),
            DashboardStatCard(
                key="resolved_reports",
                label="已解决",
                value=resolved,
                unit="项",
                icon="success",
                color="green",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        # 最近缺料上报
        recent_reports = (
            self.db.query(ShortageReport)
            .order_by(desc(ShortageReport.created_at))
            .limit(10)
            .all()
        )

        recent_reports_list = []
        for report in recent_reports:
            project = (
                self.db.query(Project).filter(Project.id == report.project_id).first()
            )
            recent_reports_list.append(
                DashboardListItem(
                    id=report.id,
                    title=report.material_name or "未知物料",
                    subtitle=project.project_name if project else None,
                    status=report.status,
                    priority=report.urgent_level,
                    event_date=report.report_time,
                    extra={
                        "report_no": report.report_no,
                        "shortage_qty": float(report.shortage_qty),
                    },
                )
            )

        # 物料替代统计
        sub_query = self.db.query(MaterialSubstitution)
        total_substitutions = sub_query.count()
        pending_substitutions = sub_query.filter(
            MaterialSubstitution.status.in_(["DRAFT", "TECH_PENDING", "PROD_PENDING"])
        ).count()

        # 物料调拨统计
        transfer_query = self.db.query(MaterialTransfer)
        total_transfers = transfer_query.count()
        pending_transfers = transfer_query.filter(
            MaterialTransfer.status.in_(["DRAFT", "PENDING"])
        ).count()

        operation_stats = {
            "substitutions": {
                "total": total_substitutions,
                "pending": pending_substitutions,
            },
            "transfers": {"total": total_transfers, "pending": pending_transfers},
        }

        return [
            DashboardWidget(
                widget_id="recent_reports",
                widget_type="list",
                title="最近缺料上报",
                data=recent_reports_list,
                order=1,
                span=16,
            ),
            DashboardWidget(
                widget_id="operation_stats",
                widget_type="stats",
                title="处理操作统计",
                data=operation_stats,
                order=2,
                span=8,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        # 按状态统计
        by_status = {}
        for status in ["REPORTED", "CONFIRMED", "HANDLING", "RESOLVED"]:
            count = (
                self.db.query(ShortageReport)
                .filter(ShortageReport.status == status)
                .count()
            )
            by_status[status] = count

        # 按紧急程度统计
        by_urgent = {}
        for level in ["LOW", "MEDIUM", "HIGH", "URGENT", "CRITICAL"]:
            count = (
                self.db.query(ShortageReport)
                .filter(ShortageReport.urgent_level == level)
                .count()
            )
            by_urgent[level] = count

        details = {"by_status": by_status, "by_urgent": by_urgent}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )
