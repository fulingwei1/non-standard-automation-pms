# -*- coding: utf-8 -*-
"""
工时提醒管理服务
负责提醒规则配置、提醒记录管理
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

from app.models.timesheet_reminder import (
    AnomalyTypeEnum,
    NotificationChannelEnum,
    ReminderStatusEnum,
    ReminderTypeEnum,
    TimesheetAnomalyRecord,
    TimesheetReminderConfig,
    TimesheetReminderRecord,
)

logger = logging.getLogger(__name__)


class TimesheetReminderManager:
    """工时提醒管理器"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 规则配置管理 ====================

    def create_reminder_config(
        self,
        rule_code: str,
        rule_name: str,
        reminder_type: ReminderTypeEnum,
        rule_parameters: Dict,
        apply_to_departments: Optional[List[int]] = None,
        apply_to_roles: Optional[List[int]] = None,
        apply_to_users: Optional[List[int]] = None,
        notification_channels: Optional[List[str]] = None,
        notification_template: Optional[str] = None,
        remind_frequency: str = 'ONCE_DAILY',
        max_reminders_per_day: int = 1,
        priority: str = 'NORMAL',
        created_by: Optional[int] = None,
    ) -> TimesheetReminderConfig:
        """创建提醒规则配置"""
        config = TimesheetReminderConfig(
            rule_code=rule_code,
            rule_name=rule_name,
            reminder_type=reminder_type,
            rule_parameters=rule_parameters,
            apply_to_departments=apply_to_departments or [],
            apply_to_roles=apply_to_roles or [],
            apply_to_users=apply_to_users or [],
            notification_channels=notification_channels or ['SYSTEM'],
            notification_template=notification_template,
            remind_frequency=remind_frequency,
            max_reminders_per_day=max_reminders_per_day,
            priority=priority,
            is_active=True,
            created_by=created_by,
        )

        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)

        logger.info(f"创建提醒规则配置: {rule_code} - {rule_name}")
        return config

    def update_reminder_config(
        self,
        config_id: int,
        **kwargs
    ) -> Optional[TimesheetReminderConfig]:
        """更新提醒规则配置"""
        config = self.db.query(TimesheetReminderConfig).filter(
            TimesheetReminderConfig.id == config_id
        ).first()

        if not config:
            return None

        for key, value in kwargs.items():
            if hasattr(config, key) and value is not None:
                setattr(config, key, value)

        self.db.commit()
        self.db.refresh(config)

        logger.info(f"更新提醒规则配置: {config.rule_code}")
        return config

    def get_reminder_config(self, config_id: int) -> Optional[TimesheetReminderConfig]:
        """获取提醒规则配置"""
        return self.db.query(TimesheetReminderConfig).filter(
            TimesheetReminderConfig.id == config_id
        ).first()

    def get_active_configs_by_type(
        self,
        reminder_type: ReminderTypeEnum
    ) -> List[TimesheetReminderConfig]:
        """获取指定类型的活跃配置"""
        return self.db.query(TimesheetReminderConfig).filter(
            TimesheetReminderConfig.reminder_type == reminder_type,
            TimesheetReminderConfig.is_active == True
        ).all()

    def check_user_applicable(
        self,
        config: TimesheetReminderConfig,
        user_id: int,
        department_id: Optional[int] = None,
        role_ids: Optional[List[int]] = None
    ) -> bool:
        """检查用户是否适用该规则"""
        # 如果没有指定适用范围，则适用所有用户
        if (not config.apply_to_users and 
            not config.apply_to_departments and 
            not config.apply_to_roles):
            return True

        # 检查用户列表
        if config.apply_to_users and user_id in config.apply_to_users:
            return True

        # 检查部门列表
        if config.apply_to_departments and department_id:
            if department_id in config.apply_to_departments:
                return True

        # 检查角色列表
        if config.apply_to_roles and role_ids:
            if any(role_id in config.apply_to_roles for role_id in role_ids):
                return True

        return False

    # ==================== 提醒记录管理 ====================

    def create_reminder_record(
        self,
        reminder_type: ReminderTypeEnum,
        user_id: int,
        title: str,
        content: str,
        user_name: Optional[str] = None,
        config_id: Optional[int] = None,
        source_type: Optional[str] = None,
        source_id: Optional[int] = None,
        extra_data: Optional[Dict] = None,
        priority: str = 'NORMAL',
        notification_channels: Optional[List[str]] = None,
    ) -> TimesheetReminderRecord:
        """创建提醒记录"""
        # 生成提醒编号
        reminder_no = self._generate_reminder_no(reminder_type)

        record = TimesheetReminderRecord(
            reminder_no=reminder_no,
            reminder_type=reminder_type,
            config_id=config_id,
            user_id=user_id,
            user_name=user_name,
            title=title,
            content=content,
            source_type=source_type,
            source_id=source_id,
            extra_data=extra_data or {},
            status=ReminderStatusEnum.PENDING,
            priority=priority,
            notification_channels=notification_channels or ['SYSTEM'],
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(f"创建提醒记录: {reminder_no} - {title}")
        return record

    def mark_reminder_sent(
        self,
        reminder_id: int,
        channels: List[str]
    ) -> Optional[TimesheetReminderRecord]:
        """标记提醒已发送"""
        record = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.id == reminder_id
        ).first()

        if not record:
            return None

        record.status = ReminderStatusEnum.SENT
        record.sent_at = datetime.now()
        record.notification_channels = channels

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"标记提醒已发送: {record.reminder_no}")
        return record

    def mark_reminder_read(self, reminder_id: int) -> Optional[TimesheetReminderRecord]:
        """标记提醒已读"""
        record = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.id == reminder_id
        ).first()

        if not record:
            return None

        record.status = ReminderStatusEnum.READ
        record.read_at = datetime.now()

        self.db.commit()
        self.db.refresh(record)

        return record

    def dismiss_reminder(
        self,
        reminder_id: int,
        dismissed_by: int,
        reason: Optional[str] = None
    ) -> Optional[TimesheetReminderRecord]:
        """忽略提醒"""
        record = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.id == reminder_id
        ).first()

        if not record:
            return None

        record.status = ReminderStatusEnum.DISMISSED
        record.dismissed_at = datetime.now()
        record.dismissed_by = dismissed_by
        record.dismissed_reason = reason

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"忽略提醒: {record.reminder_no}")
        return record

    def mark_reminder_resolved(
        self,
        reminder_id: int
    ) -> Optional[TimesheetReminderRecord]:
        """标记提醒已解决"""
        record = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.id == reminder_id
        ).first()

        if not record:
            return None

        record.status = ReminderStatusEnum.RESOLVED
        record.resolved_at = datetime.now()

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"标记提醒已解决: {record.reminder_no}")
        return record

    def get_pending_reminders(
        self,
        user_id: Optional[int] = None,
        reminder_type: Optional[ReminderTypeEnum] = None,
        limit: int = 100
    ) -> List[TimesheetReminderRecord]:
        """获取待处理提醒列表"""
        query = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.status.in_([
                ReminderStatusEnum.PENDING,
                ReminderStatusEnum.SENT
            ])
        )

        if user_id:
            query = query.filter(TimesheetReminderRecord.user_id == user_id)

        if reminder_type:
            query = query.filter(TimesheetReminderRecord.reminder_type == reminder_type)

        return query.order_by(
            desc(TimesheetReminderRecord.priority),
            desc(TimesheetReminderRecord.created_at)
        ).limit(limit).all()

    def get_reminder_history(
        self,
        user_id: Optional[int] = None,
        reminder_type: Optional[ReminderTypeEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> tuple[List[TimesheetReminderRecord], int]:
        """获取提醒历史"""
        query = self.db.query(TimesheetReminderRecord)

        if user_id:
            query = query.filter(TimesheetReminderRecord.user_id == user_id)

        if reminder_type:
            query = query.filter(TimesheetReminderRecord.reminder_type == reminder_type)

        if start_date:
            query = query.filter(TimesheetReminderRecord.created_at >= start_date)

        if end_date:
            query = query.filter(TimesheetReminderRecord.created_at <= end_date)

        total = query.count()
        records = query.order_by(
            desc(TimesheetReminderRecord.created_at)
        ).limit(limit).offset(offset).all()

        return records, total

    def check_reminder_limit(
        self,
        user_id: int,
        reminder_type: ReminderTypeEnum,
        max_per_day: int
    ) -> bool:
        """检查提醒次数限制"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        count = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.user_id == user_id,
            TimesheetReminderRecord.reminder_type == reminder_type,
            TimesheetReminderRecord.created_at >= today_start
        ).count()

        return count < max_per_day

    # ==================== 异常记录管理 ====================

    def create_anomaly_record(
        self,
        timesheet_id: int,
        user_id: int,
        anomaly_type: AnomalyTypeEnum,
        description: str,
        user_name: Optional[str] = None,
        anomaly_data: Optional[Dict] = None,
        severity: str = 'WARNING',
        reminder_id: Optional[int] = None,
    ) -> TimesheetAnomalyRecord:
        """创建异常记录"""
        record = TimesheetAnomalyRecord(
            timesheet_id=timesheet_id,
            user_id=user_id,
            user_name=user_name,
            anomaly_type=anomaly_type,
            description=description,
            anomaly_data=anomaly_data or {},
            severity=severity,
            detected_at=datetime.now(),
            is_resolved=False,
            reminder_id=reminder_id,
        )

        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)

        logger.info(f"创建异常记录: {anomaly_type.value} - {description}")
        return record

    def resolve_anomaly(
        self,
        anomaly_id: int,
        resolved_by: int,
        resolution_note: Optional[str] = None
    ) -> Optional[TimesheetAnomalyRecord]:
        """解决异常"""
        record = self.db.query(TimesheetAnomalyRecord).filter(
            TimesheetAnomalyRecord.id == anomaly_id
        ).first()

        if not record:
            return None

        record.is_resolved = True
        record.resolved_at = datetime.now()
        record.resolved_by = resolved_by
        record.resolution_note = resolution_note

        self.db.commit()
        self.db.refresh(record)

        logger.info(f"解决异常记录: ID={anomaly_id}")
        return record

    def get_unresolved_anomalies(
        self,
        user_id: Optional[int] = None,
        anomaly_type: Optional[AnomalyTypeEnum] = None,
        limit: int = 100
    ) -> List[TimesheetAnomalyRecord]:
        """获取未解决的异常列表"""
        query = self.db.query(TimesheetAnomalyRecord).filter(
            TimesheetAnomalyRecord.is_resolved == False
        )

        if user_id:
            query = query.filter(TimesheetAnomalyRecord.user_id == user_id)

        if anomaly_type:
            query = query.filter(TimesheetAnomalyRecord.anomaly_type == anomaly_type)

        return query.order_by(
            desc(TimesheetAnomalyRecord.detected_at)
        ).limit(limit).all()

    # ==================== 工具方法 ====================

    def _generate_reminder_no(self, reminder_type: ReminderTypeEnum) -> str:
        """生成提醒编号"""
        prefix_map = {
            ReminderTypeEnum.MISSING_TIMESHEET: 'RM',
            ReminderTypeEnum.APPROVAL_TIMEOUT: 'RA',
            ReminderTypeEnum.ANOMALY_TIMESHEET: 'RN',
            ReminderTypeEnum.WEEKEND_WORK: 'RW',
            ReminderTypeEnum.HOLIDAY_WORK: 'RH',
            ReminderTypeEnum.SYNC_FAILURE: 'RS',
        }
        
        prefix = prefix_map.get(reminder_type, 'RX')
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # 查询今天该类型已有的记录数
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        count = self.db.query(TimesheetReminderRecord).filter(
            TimesheetReminderRecord.reminder_type == reminder_type,
            TimesheetReminderRecord.created_at >= today_start
        ).count()

        seq = str(count + 1).zfill(4)
        return f"{prefix}{timestamp}{seq}"
