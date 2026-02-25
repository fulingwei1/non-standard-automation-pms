# -*- coding: utf-8 -*-
"""
管理节律 Dashboard 适配器
"""

from datetime import date, datetime
from typing import List

from sqlalchemy import desc

from app.models.enums import ActionItemStatus
from app.models.management_rhythm import (
    MeetingActionItem,
    RhythmDashboardSnapshot,
    StrategicMeeting,
)
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class ManagementRhythmDashboardAdapter(DashboardAdapter):
    """管理节律工作台适配器"""

    @property
    def module_id(self) -> str:
        return "management_rhythm"

    @property
    def module_name(self) -> str:
        return "管理节律"

    @property
    def supported_roles(self) -> List[str]:
        return ["admin", "pmo", "management"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        # 获取各层级的最新快照
        strategic_snapshot = (
            self.db.query(RhythmDashboardSnapshot)
            .filter(
                RhythmDashboardSnapshot.rhythm_level == "STRATEGIC"
            )
            .order_by(desc(RhythmDashboardSnapshot.snapshot_date))
            .first()
        )

        (
            self.db.query(RhythmDashboardSnapshot)
            .filter(
                RhythmDashboardSnapshot.rhythm_level == "OPERATIONAL"
            )
            .order_by(desc(RhythmDashboardSnapshot.snapshot_date))
            .first()
        )

        # 汇总统计
        total_meetings = (
            self.db.query(StrategicMeeting)
            .filter(StrategicMeeting.status.in_(["SCHEDULED", "ONGOING", "COMPLETED"]))
            .count()
        )

        total_action_items = self.db.query(MeetingActionItem).count()
        completed_action_items = (
            self.db.query(MeetingActionItem)
            .filter(MeetingActionItem.status == ActionItemStatus.DONE.value)
            .count()
        )
        overdue_action_items = (
            self.db.query(MeetingActionItem)
            .filter(MeetingActionItem.status == ActionItemStatus.OVERDUE.value)
            .count()
        )

        completion_rate = (
            (completed_action_items / total_action_items * 100)
            if total_action_items > 0
            else 0
        )

        return [
            DashboardStatCard(
                key="total_meetings",
                title="会议总数",
                value=total_meetings,
                unit="个",
            ),
            DashboardStatCard(
                key="total_action_items",
                title="行动项总数",
                value=total_action_items,
                unit="项",
            ),
            DashboardStatCard(
                key="completed_action_items",
                title="已完成",
                value=completed_action_items,
                unit="项",
            ),
            DashboardStatCard(
                key="overdue_action_items",
                title="逾期",
                value=overdue_action_items,
                unit="项",
            ),
            DashboardStatCard(
                key="completion_rate",
                title="完成率",
                value=completion_rate,
                unit="%",
            ),
            DashboardStatCard(
                key="strategic_health",
                title="战略会议健康度",
                value=(
                    strategic_snapshot.health_status if strategic_snapshot else "N/A"
                ),
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        today = date.today()

        # 即将召开的会议
        upcoming_meetings = (
            self.db.query(StrategicMeeting)
            .filter(
                StrategicMeeting.status.in_(["SCHEDULED", "ONGOING"]),
                StrategicMeeting.meeting_date >= today,
            )
            .order_by(StrategicMeeting.meeting_date)
            .limit(5)
            .all()
        )

        upcoming_meetings_data = [
            {
                "id": m.id,
                "title": m.title,
                "rhythm_level": m.rhythm_level,
                "meeting_date": m.meeting_date,
                "status": m.status,
            }
            for m in upcoming_meetings
        ]

        # 我的待办行动项
        my_action_items = (
            self.db.query(MeetingActionItem)
            .filter(
                MeetingActionItem.owner_id == self.current_user.id,
                MeetingActionItem.status.in_(
                    [ActionItemStatus.TODO.value, ActionItemStatus.IN_PROGRESS.value]
                ),
            )
            .order_by(MeetingActionItem.due_date)
            .limit(10)
            .all()
        )

        my_action_items_data = [
            {
                "id": item.id,
                "title": item.title,
                "due_date": item.due_date,
                "status": item.status,
                "priority": item.priority,
            }
            for item in my_action_items
        ]

        return [
            DashboardWidget(
                widget_id="upcoming_meetings",
                widget_type="list",
                title="即将召开的会议",
                data=upcoming_meetings_data,
                order=1,
                span=12,
            ),
            DashboardWidget(
                widget_id="my_action_items",
                widget_type="list",
                title="我的待办行动项",
                data=my_action_items_data,
                order=2,
                span=12,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        # 按层级统计
        levels = [
            "STRATEGIC",
            "OPERATIONAL",
            "OPERATION",
            "TASK",
        ]

        level_stats = []
        for level in levels:
            meetings_count = (
                self.db.query(StrategicMeeting)
                .filter(StrategicMeeting.rhythm_level == level)
                .count()
            )

            completed_meetings = (
                self.db.query(StrategicMeeting)
                .filter(
                    StrategicMeeting.rhythm_level == level,
                    StrategicMeeting.status == "COMPLETED",
                )
                .count()
            )

            level_stats.append(
                {
                    "level": level,
                    "meetings_count": meetings_count,
                    "completed_meetings": completed_meetings,
                }
            )

        details = {"level_stats": level_stats}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details=details,
            generated_at=datetime.now(),
        )
