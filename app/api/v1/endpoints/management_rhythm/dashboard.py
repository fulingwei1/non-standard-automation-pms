# -*- coding: utf-8 -*-
"""
节律仪表盘 - 自动生成
从 management_rhythm.py 拆分
"""

from datetime import date
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard.base import BaseDashboardEndpoint
from app.models.enums import (
    ActionItemStatus,
    MeetingCycleType,
    MeetingRhythmLevel,
    RhythmHealthStatus,
)
from app.models.management_rhythm import (
    MeetingActionItem,
    RhythmDashboardSnapshot,
    StrategicMeeting,
)
from app.models.user import User
from app.schemas.management_rhythm import (
    RhythmDashboardResponse,
    RhythmDashboardSummary,
)


class ManagementRhythmDashboardEndpoint(BaseDashboardEndpoint):
    """管理节律Dashboard端点"""
    
    module_name = "management-rhythm"
    permission_required = None  # 使用默认权限
    
    def __init__(self):
        """初始化路由"""
        # 先创建router，不调用super().__init__()，因为需要自定义路由路径
        self.router = APIRouter(
            prefix="/dashboard",
            tags=["dashboard"]
        )
        self._register_custom_routes()
    
    def _register_custom_routes(self):
        """注册自定义路由"""
        user_dependency = self._get_user_dependency()
        
        async def dashboard_endpoint(
            db: Session = Depends(deps.get_db),
            current_user: User = Depends(user_dependency),
        ):
            return self._get_dashboard_handler(db, current_user)
        
        # 主dashboard端点（保持原有路径）
        self.router.add_api_route(
            "/dashboard",
            dashboard_endpoint,
            methods=["GET"],
            summary="获取节律仪表盘数据",
            response_model=RhythmDashboardSummary
        )
    
    def get_dashboard_data(
        self,
        db: Session,
        current_user: User
    ) -> Dict[str, Any]:
        """
        获取节律仪表盘数据
        """
        # 获取各层级的最新快照
        levels = [MeetingRhythmLevel.STRATEGIC.value, MeetingRhythmLevel.OPERATIONAL.value,
                  MeetingRhythmLevel.OPERATION.value, MeetingRhythmLevel.TASK.value]

        result = {}

        for level in levels:
            # 获取最新快照
            snapshot = db.query(RhythmDashboardSnapshot).filter(
                RhythmDashboardSnapshot.rhythm_level == level
            ).order_by(desc(RhythmDashboardSnapshot.snapshot_date)).first()

            if snapshot:
                result[level.lower()] = RhythmDashboardResponse(
                    rhythm_level=snapshot.rhythm_level,
                    cycle_type=snapshot.cycle_type,
                    current_cycle=snapshot.current_cycle,
                    key_metrics_snapshot=snapshot.key_metrics_snapshot if snapshot.key_metrics_snapshot else {},
                    health_status=snapshot.health_status,
                    last_meeting_date=snapshot.last_meeting_date,
                    next_meeting_date=snapshot.next_meeting_date,
                    meetings_count=snapshot.meetings_count,
                    completed_meetings_count=snapshot.completed_meetings_count,
                    total_action_items=snapshot.total_action_items,
                    completed_action_items=snapshot.completed_action_items,
                    overdue_action_items=snapshot.overdue_action_items,
                    completion_rate=snapshot.completion_rate,
                    snapshot_date=snapshot.snapshot_date,
                )
            else:
                # 如果没有快照，实时计算
                dashboard_data = _calculate_dashboard_data(db, level)
                result[level.lower()] = dashboard_data

        dashboard_summary = RhythmDashboardSummary(
            strategic=result.get("strategic"),
            operational=result.get("operational"),
            operation=result.get("operation"),
            task=result.get("task"),
        )
        
        # 转换为字典并添加统计卡片
        result_dict = dashboard_summary.model_dump()
        
        # 创建统计卡片
        stats = []
        for level_key, level_data in result.items():
            if level_data:
                stats.append(
                    self.create_stat_card(
                        key=f"{level_key}_meetings",
                        label=f"{level_data.rhythm_level}会议数",
                        value=level_data.meetings_count,
                        unit="个",
                        icon="meeting"
                    )
                )
                stats.append(
                    self.create_stat_card(
                        key=f"{level_key}_action_items",
                        label=f"{level_data.rhythm_level}行动项",
                        value=level_data.total_action_items,
                        unit="个",
                        icon="action"
                    )
                )
                stats.append(
                    self.create_stat_card(
                        key=f"{level_key}_completion_rate",
                        label=f"{level_data.rhythm_level}完成率",
                        value=level_data.completion_rate,
                        icon="completion",
                        color="green" if level_data.health_status == RhythmHealthStatus.GREEN.value else 
                              ("yellow" if level_data.health_status == RhythmHealthStatus.YELLOW.value else "red")
                    )
                )
        
        result_dict["stats"] = stats
        return result_dict
    
    def _get_dashboard_handler(self, db: Session, current_user: User) -> RhythmDashboardSummary:
        """重写处理器，返回RhythmDashboardSummary"""
        # 获取各层级的最新快照
        levels = [MeetingRhythmLevel.STRATEGIC.value, MeetingRhythmLevel.OPERATIONAL.value,
                  MeetingRhythmLevel.OPERATION.value, MeetingRhythmLevel.TASK.value]

        result = {}

        for level in levels:
            # 获取最新快照
            snapshot = db.query(RhythmDashboardSnapshot).filter(
                RhythmDashboardSnapshot.rhythm_level == level
            ).order_by(desc(RhythmDashboardSnapshot.snapshot_date)).first()

            if snapshot:
                result[level.lower()] = RhythmDashboardResponse(
                    rhythm_level=snapshot.rhythm_level,
                    cycle_type=snapshot.cycle_type,
                    current_cycle=snapshot.current_cycle,
                    key_metrics_snapshot=snapshot.key_metrics_snapshot if snapshot.key_metrics_snapshot else {},
                    health_status=snapshot.health_status,
                    last_meeting_date=snapshot.last_meeting_date,
                    next_meeting_date=snapshot.next_meeting_date,
                    meetings_count=snapshot.meetings_count,
                    completed_meetings_count=snapshot.completed_meetings_count,
                    total_action_items=snapshot.total_action_items,
                    completed_action_items=snapshot.completed_action_items,
                    overdue_action_items=snapshot.overdue_action_items,
                    completion_rate=snapshot.completion_rate,
                    snapshot_date=snapshot.snapshot_date,
                )
            else:
                # 如果没有快照，实时计算
                dashboard_data = _calculate_dashboard_data(db, level)
                result[level.lower()] = dashboard_data

        return RhythmDashboardSummary(
            strategic=result.get("strategic"),
            operational=result.get("operational"),
            operation=result.get("operation"),
            task=result.get("task"),
        )


# 创建端点实例并获取路由
dashboard_endpoint = ManagementRhythmDashboardEndpoint()
router = dashboard_endpoint.router


def _calculate_dashboard_data(db: Session, rhythm_level: str) -> RhythmDashboardResponse:
    """计算仪表盘数据"""
    # 获取当前周期的会议
    today = date.today()

    # 根据层级确定周期类型
    cycle_type_map = {
        MeetingRhythmLevel.STRATEGIC.value: MeetingCycleType.QUARTERLY.value,
        MeetingRhythmLevel.OPERATIONAL.value: MeetingCycleType.MONTHLY.value,
        MeetingRhythmLevel.OPERATION.value: MeetingCycleType.WEEKLY.value,
        MeetingRhythmLevel.TASK.value: MeetingCycleType.DAILY.value,
    }

    cycle_type = cycle_type_map.get(rhythm_level, MeetingCycleType.MONTHLY.value)

    # 计算当前周期
    if cycle_type == MeetingCycleType.QUARTERLY.value:
        quarter = (today.month - 1) // 3 + 1
        current_cycle = f"{today.year}-Q{quarter}"
    elif cycle_type == MeetingCycleType.MONTHLY.value:
        current_cycle = f"{today.year}-{today.month:02d}"
    elif cycle_type == MeetingCycleType.WEEKLY.value:
        week_num = today.isocalendar()[1]
        current_cycle = f"{today.year}-W{week_num:02d}"
    else:
        current_cycle = today.isoformat()

    # 查询会议
    meetings = db.query(StrategicMeeting).filter(
        StrategicMeeting.rhythm_level == rhythm_level
    ).all()

    meetings_count = len(meetings)
    completed_meetings = [m for m in meetings if m.status == "COMPLETED"]
    completed_meetings_count = len(completed_meetings)

    # 查询行动项
    meeting_ids = [m.id for m in meetings]
    if meeting_ids:
        total_action_items = db.query(MeetingActionItem).filter(
            MeetingActionItem.meeting_id.in_(meeting_ids)
        ).count()

        completed_action_items = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id.in_(meeting_ids),
                MeetingActionItem.status == ActionItemStatus.COMPLETED.value
            )
        ).count()

        overdue_action_items = db.query(MeetingActionItem).filter(
            and_(
                MeetingActionItem.meeting_id.in_(meeting_ids),
                MeetingActionItem.status == ActionItemStatus.OVERDUE.value
            )
        ).count()
    else:
        total_action_items = 0
        completed_action_items = 0
        overdue_action_items = 0

    # 计算完成率
    completion_rate = f"{(completed_action_items / total_action_items * 100):.1f}%" if total_action_items > 0 else "0%"

    # 计算健康状态
    if total_action_items > 0:
        completion_ratio = completed_action_items / total_action_items
        if completion_ratio >= 0.9:
            health_status = RhythmHealthStatus.GREEN.value
        elif completion_ratio >= 0.7:
            health_status = RhythmHealthStatus.YELLOW.value
        else:
            health_status = RhythmHealthStatus.RED.value
    else:
        health_status = RhythmHealthStatus.GREEN.value

    # 获取最近和下次会议
    last_meeting = db.query(StrategicMeeting).filter(
        and_(
            StrategicMeeting.rhythm_level == rhythm_level,
            StrategicMeeting.status == "COMPLETED"
        )
    ).order_by(desc(StrategicMeeting.meeting_date)).first()

    next_meeting = db.query(StrategicMeeting).filter(
        and_(
            StrategicMeeting.rhythm_level == rhythm_level,
            StrategicMeeting.status.in_(["SCHEDULED", "ONGOING"]),
            StrategicMeeting.meeting_date >= today
        )
    ).order_by(StrategicMeeting.meeting_date).first()

    return RhythmDashboardResponse(
        rhythm_level=rhythm_level,
        cycle_type=cycle_type,
        current_cycle=current_cycle,
        key_metrics_snapshot={},
        health_status=health_status,
        last_meeting_date=last_meeting.meeting_date if last_meeting else None,
        next_meeting_date=next_meeting.meeting_date if next_meeting else None,
        meetings_count=meetings_count,
        completed_meetings_count=completed_meetings_count,
        total_action_items=total_action_items,
        completed_action_items=completed_action_items,
        overdue_action_items=overdue_action_items,
        completion_rate=completion_rate,
        snapshot_date=today,
    )



