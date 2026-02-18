# -*- coding: utf-8 -*-
"""
人员匹配和齐套率 Dashboard 适配器 + 其他综合仪表盘适配器
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func

from app.models.staff_matching import HrAIMatchingLog, MesProjectStaffingNeed
from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


class OthersDashboardAdapter:
    """其他综合仪表盘适配器 —— 提供快速统计、活动、健康、任务、通知等"""

    def __init__(self, db):
        self.db = db

    def get_quick_stats(self) -> dict:
        """获取快速统计数据"""
        try:
            from app.models.project import Project
            from app.models.user import User
            from app.models.alert import AlertRecord

            project_count = self.db.query(Project).count()
            user_count = self.db.query(User).count()
            alert_count = self.db.query(AlertRecord).filter(
                AlertRecord.status == "ACTIVE"
            ).count()
        except Exception:
            project_count = 0
            user_count = 0
            alert_count = 0

        return {
            "project_count": project_count,
            "user_count": user_count,
            "alert_count": alert_count,
        }

    def get_recent_activities(
        self, limit: int = 10, user_id: Optional[int] = None
    ) -> list:
        """获取最近活动"""
        try:
            from app.models.approval import ApprovalRecord

            query = self.db.query(ApprovalRecord)
            if user_id is not None:
                query = query.filter(ApprovalRecord.user_id == user_id)
            query = query.order_by(ApprovalRecord.created_at.desc())
            query = query.limit(limit)
            return query.all()
        except Exception:
            return []

    def get_system_health(self) -> dict:
        """获取系统健康状态"""
        result = {
            "database": "unknown",
            "cache": "unknown",
            "status": "healthy",
        }
        try:
            from sqlalchemy import text
            self.db.execute(text("SELECT 1"))
            result["database"] = "healthy"
        except Exception:
            result["database"] = "unhealthy"
            result["status"] = "degraded"

        try:
            from app.utils.redis_client import redis_client
            if redis_client:
                result["cache"] = "healthy"
            else:
                result["cache"] = "not_configured"
        except Exception:
            result["cache"] = "unavailable"

        return result

    def get_user_tasks(
        self,
        user_id: int,
        status: Optional[str] = None,
        include_approvals: bool = False,
    ) -> list:
        """获取用户任务"""
        try:
            from app.models.task_center import TaskItem

            query = self.db.query(TaskItem)
            query = query.filter(TaskItem.assignee_id == user_id)
            if status:
                query = query.filter(TaskItem.status == status)
            query = query.order_by(TaskItem.created_at.desc())
            query = query.limit(20)
            tasks = query.all()
        except Exception:
            tasks = []

        if include_approvals:
            try:
                from app.models.approval import ApprovalTask

                approval_query = self.db.query(ApprovalTask)
                approval_query = approval_query.filter(
                    ApprovalTask.assignee_id == user_id,
                    ApprovalTask.status == "PENDING",
                )
                approval_query = approval_query.limit(10)
                approval_tasks = approval_query.all()
                tasks.extend(approval_tasks)
            except Exception:
                pass

        return tasks

    def get_notifications(
        self, user_id: int, unread_only: bool = False
    ) -> list:
        """获取用户通知"""
        try:
            from app.models.notification import Notification

            query = self.db.query(Notification)
            query = query.filter(Notification.user_id == user_id)
            if unread_only:
                query = query.filter(Notification.is_read == False)
            query = query.order_by(Notification.created_at.desc())
            query = query.limit(20)
            return query.all()
        except Exception:
            return []


@register_dashboard
class StaffMatchingDashboardAdapter(DashboardAdapter):
    """人员匹配工作台适配器"""

    @property
    def module_id(self) -> str:
        return "staff_matching"

    @property
    def module_name(self) -> str:
        return "人员匹配"

    @property
    def supported_roles(self) -> List[str]:
        return ["hr", "pmo", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        # 需求统计
        open_needs = (
            self.db.query(func.count(MesProjectStaffingNeed.id))
            .filter(MesProjectStaffingNeed.status == "OPEN")
            .scalar()
            or 0
        )

        matching_needs = (
            self.db.query(func.count(MesProjectStaffingNeed.id))
            .filter(MesProjectStaffingNeed.status == "MATCHING")
            .scalar()
            or 0
        )

        filled_needs = (
            self.db.query(func.count(MesProjectStaffingNeed.id))
            .filter(MesProjectStaffingNeed.status == "FILLED")
            .scalar()
            or 0
        )

        # 匹配统计
        (
            self.db.query(func.count(func.distinct(HrAIMatchingLog.request_id))).scalar()
            or 0
        )
        total_matched = self.db.query(func.count(HrAIMatchingLog.id)).scalar() or 0
        accepted = (
            self.db.query(func.count(HrAIMatchingLog.id))
            .filter(HrAIMatchingLog.is_accepted)
            .scalar()
            or 0
        )
        (
            self.db.query(func.count(HrAIMatchingLog.id))
            .filter(HrAIMatchingLog.is_accepted == False)
            .scalar()
            or 0
        )

        (
            self.db.query(func.avg(HrAIMatchingLog.total_score))
            .filter(HrAIMatchingLog.is_accepted)
            .scalar()
        )

        success_rate = (accepted / total_matched * 100) if total_matched > 0 else 0

        # 统计总人数需求
        total_headcount_needed = (
            self.db.query(func.sum(MesProjectStaffingNeed.headcount))
            .filter(MesProjectStaffingNeed.status.in_(["OPEN", "MATCHING", "FILLED"]))
            .scalar()
            or 0
        )

        # 统计已填充人数
        total_headcount_filled = (
            self.db.query(func.sum(MesProjectStaffingNeed.filled_headcount))
            .filter(MesProjectStaffingNeed.status.in_(["OPEN", "MATCHING", "FILLED"]))
            .scalar()
            or 0
        )

        return [
            DashboardStatCard(
                key="open_needs",
                title="待匹配需求",
                value=open_needs,
                unit="个",
                icon="need",
                color="blue",
            ),
            DashboardStatCard(
                key="matching_needs",
                title="匹配中",
                value=matching_needs,
                unit="个",
                icon="matching",
                color="orange",
            ),
            DashboardStatCard(
                key="filled_needs",
                title="已填充",
                value=filled_needs,
                unit="个",
                icon="filled",
                color="green",
            ),
            DashboardStatCard(
                key="total_headcount",
                title="总需求人数",
                value=int(total_headcount_needed),
                unit="人",
                icon="people",
                color="cyan",
            ),
            DashboardStatCard(
                key="filled_headcount",
                title="已填充人数",
                value=int(total_headcount_filled),
                unit="人",
                icon="filled-people",
                color="purple",
            ),
            DashboardStatCard(
                key="success_rate",
                title="匹配成功率",
                value=round(float(success_rate), 1),
                icon="success",
                color="green",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        # 最近匹配
        recent_logs = (
            self.db.query(HrAIMatchingLog)
            .order_by(HrAIMatchingLog.matching_time.desc())
            .limit(10)
            .all()
        )

        recent_matches = []
        for log in recent_logs:
            recent_matches.append(
                {
                    "id": log.id,
                    "request_id": log.request_id,
                    "project_id": log.project_id,
                    "total_score": log.total_score,
                    "is_accepted": log.is_accepted,
                    "matching_time": log.matching_time,
                    "project_name": log.project.name if log.project else None,
                    "employee_name": log.candidate.name if log.candidate else None,
                }
            )

        # 按优先级统计
        priority_counts = (
            self.db.query(
                MesProjectStaffingNeed.priority,
                func.count(MesProjectStaffingNeed.id),
            )
            .filter(MesProjectStaffingNeed.status.in_(["OPEN", "MATCHING"]))
            .group_by(MesProjectStaffingNeed.priority)
            .all()
        )

        needs_by_priority = {p: c for p, c in priority_counts}

        return [
            DashboardWidget(
                widget_id="recent_matches",
                widget_type="list",
                title="最近匹配记录",
                data={'items': recent_matches},
                order=1,
                span=16,
            ),
            DashboardWidget(
                widget_id="priority_distribution",
                widget_type="chart",
                title="需求优先级分布",
                data=needs_by_priority,
                order=2,
                span=8,
            ),
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        # 按状态详细统计
        by_status = {}
        for status in ["OPEN", "MATCHING", "FILLED", "CANCELLED"]:
            count = (
                self.db.query(MesProjectStaffingNeed)
                .filter(MesProjectStaffingNeed.status == status)
                .count()
            )
            by_status[status] = count

        details = {"by_status": by_status}

        return DetailedDashboardResponse(
            module_id=self.module_id,
            module_name=self.module_name,
            data={'summary': summary, 'details': details},
        )


@register_dashboard
class KitRateDashboardAdapter(DashboardAdapter):
    """齐套率工作台适配器"""

    @property
    def module_id(self) -> str:
        return "kit_rate"

    @property
    def module_name(self) -> str:
        return "齐套率"

    @property
    def supported_roles(self) -> List[str]:
        return ["procurement", "production", "pmo", "admin"]

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片"""
        from app.services.kit_rate import KitRateService

        service = KitRateService(self.db)
        dashboard_data = service.get_dashboard(None)

        # 从service返回的数据中提取统计信息
        data = dashboard_data.get("data", {})
        overall_stats = data.get("overall_stats", {})

        return [
            DashboardStatCard(
                key="total_projects",
                title="项目总数",
                value=overall_stats.get("total_projects", 0),
                unit="个",
                icon="project",
                color="blue",
            ),
            DashboardStatCard(
                key="avg_kit_rate",
                title="平均齐套率",
                value=round(float(overall_stats.get('avg_kit_rate', 0)), 1),
                icon="rate",
                color="green",
            ),
            DashboardStatCard(
                key="can_start_count",
                title="可开工项目",
                value=overall_stats.get("can_start_count", 0),
                unit="个",
                icon="start",
                color="cyan",
            ),
            DashboardStatCard(
                key="shortage_count",
                title="缺料项目",
                value=overall_stats.get("shortage_count", 0),
                unit="个",
                icon="shortage",
                color="red",
            ),
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表"""
        from app.services.kit_rate import KitRateService

        service = KitRateService(self.db)
        dashboard_data = service.get_dashboard(None)

        data = dashboard_data.get("data", {})
        project_list = data.get("project_list", [])

        return [
            DashboardWidget(
                widget_id="project_list",
                widget_type="table",
                title="项目齐套情况",
                data={'items': project_list[:10]},  # 只显示前10个
                order=1,
                span=24,
            )
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据"""
        from app.services.kit_rate import KitRateService

        service = KitRateService(self.db)
        dashboard_data = service.get_dashboard(None)

        data = dashboard_data.get("data", {})
        overall_stats = data.get("overall_stats", {})
        project_list = data.get("project_list", [])

        summary = overall_stats
        details = {"project_list": project_list}

        return DetailedDashboardResponse(
            module_id=self.module_id,
            module_name=self.module_name,
            data={'summary': summary, 'details': details},
        )
