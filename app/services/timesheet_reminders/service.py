# -*- coding: utf-8 -*-
"""
工时提醒服务层
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.models.timesheet_reminder import (
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
    TimesheetAnomalyRecord,
)
from app.services.timesheet_reminder.reminder_manager import TimesheetReminderManager

logger = logging.getLogger(__name__)


class TimesheetReminderService:
    """工时提醒服务"""

    def __init__(self, db: Session):
        self.db = db
        self.manager = TimesheetReminderManager(db)

    # ==================== 提醒规则配置 ====================

    def create_reminder_config(
        self,
        rule_code: str,
        rule_name: str,
        reminder_type: str,
        created_by: int,
        rule_parameters: Optional[Dict[str, Any]] = None,
        apply_to_departments: Optional[List[int]] = None,
        apply_to_roles: Optional[List[int]] = None,
        apply_to_users: Optional[List[int]] = None,
        notification_channels: Optional[List[str]] = None,
        notification_template: Optional[str] = None,
        remind_frequency: Optional[str] = None,
        max_reminders_per_day: Optional[int] = None,
        priority: Optional[str] = None,
    ) -> TimesheetReminderConfig:
        """创建提醒规则配置"""
        # 检查规则编码是否已存在
        existing = self.db.query(TimesheetReminderConfig).filter(
            TimesheetReminderConfig.rule_code == rule_code
        ).first()

        if existing:
            raise ValueError(f"规则编码已存在: {rule_code}")

        # 创建规则配置
        config = self.manager.create_reminder_config(
            rule_code=rule_code,
            rule_name=rule_name,
            reminder_type=ReminderTypeEnum(reminder_type),
            rule_parameters=rule_parameters,
            apply_to_departments=apply_to_departments,
            apply_to_roles=apply_to_roles,
            apply_to_users=apply_to_users,
            notification_channels=notification_channels,
            notification_template=notification_template,
            remind_frequency=remind_frequency,
            max_reminders_per_day=max_reminders_per_day,
            priority=priority,
            created_by=created_by,
        )

        return config

    def update_reminder_config(
        self, config_id: int, **kwargs
    ) -> Optional[TimesheetReminderConfig]:
        """更新提醒规则配置"""
        config = self.manager.update_reminder_config(config_id=config_id, **kwargs)
        return config

    def list_reminder_configs(
        self,
        reminder_type: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[TimesheetReminderConfig], int]:
        """获取提醒规则配置列表"""
        query = self.db.query(TimesheetReminderConfig)

        if reminder_type:
            query = query.filter(TimesheetReminderConfig.reminder_type == reminder_type)

        if is_active is not None:
            query = query.filter(TimesheetReminderConfig.is_active == is_active)

        total = query.count()
        configs = (
            query.order_by(desc(TimesheetReminderConfig.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return configs, total

    # ==================== 待处理提醒 ====================

    def list_pending_reminders(
        self,
        user_id: int,
        reminder_type: Optional[str] = None,
        priority: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[TimesheetReminderRecord], int]:
        """获取待处理提醒列表"""
        query = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.user_id == user_id,
            TimesheetReminderRecord.status.in_(
                [ReminderStatusEnum.PENDING, ReminderStatusEnum.SENT]
            ),
        )

        if reminder_type:
            query = query.filter(TimesheetReminderRecord.reminder_type == reminder_type)

        if priority:
            query = query.filter(TimesheetReminderRecord.priority == priority)

        total = query.count()
        reminders = (
            query.order_by(
                desc(TimesheetReminderRecord.priority),
                desc(TimesheetReminderRecord.created_at),
            )
            .limit(limit)
            .offset(offset)
            .all()
        )

        return reminders, total

    # ==================== 提醒历史 ====================

    def list_reminder_history(
        self,
        user_id: int,
        reminder_type: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[TimesheetReminderRecord], int]:
        """获取提醒历史记录"""
        query = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.user_id == user_id
        )

        if reminder_type:
            query = query.filter(TimesheetReminderRecord.reminder_type == reminder_type)

        if status:
            query = query.filter(TimesheetReminderRecord.status == status)

        if start_date:
            query = query.filter(TimesheetReminderRecord.created_at >= start_date)

        if end_date:
            query = query.filter(TimesheetReminderRecord.created_at <= end_date)

        total = query.count()
        reminders = (
            query.order_by(desc(TimesheetReminderRecord.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return reminders, total

    # ==================== 提醒操作 ====================

    def dismiss_reminder(
        self, reminder_id: int, user_id: int, dismissed_by: int, reason: Optional[str] = None
    ) -> Optional[TimesheetReminderRecord]:
        """忽略提醒"""
        # 检查提醒是否属于当前用户
        reminder = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.id == reminder_id,
                TimesheetReminderRecord.user_id == user_id,
            )
            .first()
        )

        if not reminder:
            return None

        updated_reminder = self.manager.dismiss_reminder(
            reminder_id=reminder_id, dismissed_by=dismissed_by, reason=reason
        )

        return updated_reminder

    def mark_reminder_read(
        self, reminder_id: int, user_id: int
    ) -> Optional[TimesheetReminderRecord]:
        """标记提醒已读"""
        # 检查提醒是否属于当前用户
        reminder = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.id == reminder_id,
                TimesheetReminderRecord.user_id == user_id,
            )
            .first()
        )

        if not reminder:
            return None

        updated_reminder = self.manager.mark_reminder_read(reminder_id)

        return updated_reminder

    # ==================== 异常记录 ====================

    def list_anomalies(
        self,
        user_id: int,
        anomaly_type: Optional[str] = None,
        is_resolved: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[TimesheetAnomalyRecord], int]:
        """获取异常记录列表"""
        query = self.db.query(TimesheetAnomalyRecord).filter(
            TimesheetAnomalyRecord.user_id == user_id
        )

        if anomaly_type:
            query = query.filter(TimesheetAnomalyRecord.anomaly_type == anomaly_type)

        if is_resolved is not None:
            query = query.filter(TimesheetAnomalyRecord.is_resolved == is_resolved)

        total = query.count()
        anomalies = (
            query.order_by(desc(TimesheetAnomalyRecord.detected_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

        return anomalies, total

    def resolve_anomaly(
        self, anomaly_id: int, user_id: int, resolved_by: int, resolution_note: Optional[str] = None
    ) -> Optional[TimesheetAnomalyRecord]:
        """解决异常记录"""
        # 检查异常是否属于当前用户
        anomaly = (
            self.db.query(TimesheetAnomalyRecord)
            .filter(
                TimesheetAnomalyRecord.id == anomaly_id,
                TimesheetAnomalyRecord.user_id == user_id,
            )
            .first()
        )

        if not anomaly:
            return None

        resolved_anomaly = self.manager.resolve_anomaly(
            anomaly_id=anomaly_id, resolved_by=resolved_by, resolution_note=resolution_note
        )

        return resolved_anomaly

    # ==================== 统计和Dashboard ====================

    def get_reminder_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取提醒统计信息"""
        # 基础统计
        total = (
            self.db.query(TimesheetReminderRecord)
            .filter(TimesheetReminderRecord.user_id == user_id)
            .count()
        )

        pending = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.user_id == user_id,
                TimesheetReminderRecord.status.in_(
                    [ReminderStatusEnum.PENDING, ReminderStatusEnum.SENT]
                ),
            )
            .count()
        )

        sent = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.user_id == user_id,
                TimesheetReminderRecord.status == ReminderStatusEnum.SENT,
            )
            .count()
        )

        dismissed = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.user_id == user_id,
                TimesheetReminderRecord.status == ReminderStatusEnum.DISMISSED,
            )
            .count()
        )

        resolved = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.user_id == user_id,
                TimesheetReminderRecord.status == ReminderStatusEnum.RESOLVED,
            )
            .count()
        )

        # 按类型统计
        by_type_query = (
            self.db.query(
                TimesheetReminderRecord.reminder_type,
                func.count(TimesheetReminderRecord.id),
            )
            .filter(TimesheetReminderRecord.user_id == user_id)
            .group_by(TimesheetReminderRecord.reminder_type)
            .all()
        )

        by_type = {str(rt): count for rt, count in by_type_query}

        # 按优先级统计
        by_priority_query = (
            self.db.query(
                TimesheetReminderRecord.priority, func.count(TimesheetReminderRecord.id)
            )
            .filter(TimesheetReminderRecord.user_id == user_id)
            .group_by(TimesheetReminderRecord.priority)
            .all()
        )

        by_priority = {p: count for p, count in by_priority_query}

        # 最近提醒
        recent_reminders = (
            self.db.query(TimesheetReminderRecord)
            .filter(TimesheetReminderRecord.user_id == user_id)
            .order_by(desc(TimesheetReminderRecord.created_at))
            .limit(10)
            .all()
        )

        return {
            "total_reminders": total,
            "pending_reminders": pending,
            "sent_reminders": sent,
            "dismissed_reminders": dismissed,
            "resolved_reminders": resolved,
            "by_type": by_type,
            "by_priority": by_priority,
            "recent_reminders": recent_reminders,
        }

    def get_anomaly_statistics(self, user_id: int) -> Dict[str, Any]:
        """获取异常统计信息"""
        total_anomalies = (
            self.db.query(TimesheetAnomalyRecord)
            .filter(TimesheetAnomalyRecord.user_id == user_id)
            .count()
        )

        unresolved_anomalies = (
            self.db.query(TimesheetAnomalyRecord)
            .filter(
                TimesheetAnomalyRecord.user_id == user_id,
                TimesheetAnomalyRecord.is_resolved == False,
            )
            .count()
        )

        resolved_anomalies = (
            self.db.query(TimesheetAnomalyRecord)
            .filter(
                TimesheetAnomalyRecord.user_id == user_id,
                TimesheetAnomalyRecord.is_resolved == True,
            )
            .count()
        )

        by_anomaly_type_query = (
            self.db.query(
                TimesheetAnomalyRecord.anomaly_type, func.count(TimesheetAnomalyRecord.id)
            )
            .filter(TimesheetAnomalyRecord.user_id == user_id)
            .group_by(TimesheetAnomalyRecord.anomaly_type)
            .all()
        )

        by_anomaly_type = {str(at): count for at, count in by_anomaly_type_query}

        by_severity_query = (
            self.db.query(
                TimesheetAnomalyRecord.severity, func.count(TimesheetAnomalyRecord.id)
            )
            .filter(TimesheetAnomalyRecord.user_id == user_id)
            .group_by(TimesheetAnomalyRecord.severity)
            .all()
        )

        by_severity = {s: count for s, count in by_severity_query}

        recent_anomalies = (
            self.db.query(TimesheetAnomalyRecord)
            .filter(TimesheetAnomalyRecord.user_id == user_id)
            .order_by(desc(TimesheetAnomalyRecord.detected_at))
            .limit(10)
            .all()
        )

        return {
            "total_anomalies": total_anomalies,
            "unresolved_anomalies": unresolved_anomalies,
            "resolved_anomalies": resolved_anomalies,
            "by_type": by_anomaly_type,
            "by_severity": by_severity,
            "recent_anomalies": recent_anomalies,
        }

    def get_dashboard(self, user_id: int) -> Dict[str, Any]:
        """获取提醒Dashboard（包含提醒和异常统计）"""
        # 提醒统计
        reminder_stats = self.get_reminder_statistics(user_id)

        # 异常统计
        anomaly_stats = self.get_anomaly_statistics(user_id)

        # 活跃规则配置
        active_configs = (
            self.db.query(TimesheetReminderConfig)
            .filter(TimesheetReminderConfig.is_active == True)
            .limit(20)
            .all()
        )

        # 紧急事项
        urgent_items = (
            self.db.query(TimesheetReminderRecord)
            .filter(
                TimesheetReminderRecord.user_id == user_id,
                TimesheetReminderRecord.status.in_(
                    [ReminderStatusEnum.PENDING, ReminderStatusEnum.SENT]
                ),
                TimesheetReminderRecord.priority.in_(["HIGH", "URGENT"]),
            )
            .order_by(desc(TimesheetReminderRecord.created_at))
            .limit(10)
            .all()
        )

        return {
            "reminder_stats": reminder_stats,
            "anomaly_stats": anomaly_stats,
            "active_configs": active_configs,
            "urgent_items": urgent_items,
        }
