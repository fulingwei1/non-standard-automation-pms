# -*- coding: utf-8 -*-
"""
工时提醒模块 ORM 模型
包含：提醒规则配置、提醒记录、提醒类型
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


# ==================== 枚举定义 ====================


class ReminderTypeEnum(str, Enum):
    """提醒类型"""
    MISSING_TIMESHEET = 'MISSING_TIMESHEET'  # 未填报工时
    APPROVAL_TIMEOUT = 'APPROVAL_TIMEOUT'    # 审批超时
    ANOMALY_TIMESHEET = 'ANOMALY_TIMESHEET'  # 异常工时
    WEEKEND_WORK = 'WEEKEND_WORK'            # 周末工时
    HOLIDAY_WORK = 'HOLIDAY_WORK'            # 节假日工时
    SYNC_FAILURE = 'SYNC_FAILURE'            # 同步失败


class ReminderStatusEnum(str, Enum):
    """提醒状态"""
    PENDING = 'PENDING'      # 待处理
    SENT = 'SENT'            # 已发送
    READ = 'READ'            # 已读
    DISMISSED = 'DISMISSED'  # 已忽略
    RESOLVED = 'RESOLVED'    # 已解决


class AnomalyTypeEnum(str, Enum):
    """异常工时类型"""
    DAILY_OVER_12 = 'DAILY_OVER_12'              # 单日>12小时
    DAILY_INVALID = 'DAILY_INVALID'              # 单日<0或>24
    WEEKLY_OVER_60 = 'WEEKLY_OVER_60'            # 周工时>60小时
    NO_REST_7DAYS = 'NO_REST_7DAYS'              # 连续7天无休息
    PROGRESS_MISMATCH = 'PROGRESS_MISMATCH'      # 工时与进度不匹配


class NotificationChannelEnum(str, Enum):
    """通知渠道"""
    EMAIL = 'EMAIL'              # 邮件
    WECHAT = 'WECHAT'            # 企业微信
    SYSTEM = 'SYSTEM'            # 系统通知
    SMS = 'SMS'                  # 短信


# ==================== 提醒规则配置 ====================


class TimesheetReminderConfig(Base, TimestampMixin):
    """工时提醒规则配置"""
    __tablename__ = 'timesheet_reminder_config'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 规则基本信息
    rule_code = Column(String(50), unique=True, nullable=False, comment='规则编码')
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    reminder_type = Column(
        SQLEnum(ReminderTypeEnum),
        nullable=False,
        comment='提醒类型'
    )
    
    # 适用范围
    apply_to_departments = Column(JSON, comment='适用部门ID列表')
    apply_to_roles = Column(JSON, comment='适用角色ID列表')
    apply_to_users = Column(JSON, comment='适用用户ID列表')
    
    # 规则参数（JSON格式存储不同类型的规则参数）
    rule_parameters = Column(JSON, comment='规则参数')
    # 示例参数：
    # - MISSING_TIMESHEET: {"check_days_ago": 1, "remind_time": "09:00"}
    # - APPROVAL_TIMEOUT: {"timeout_days": 3}
    # - ANOMALY_TIMESHEET: {"max_daily_hours": 12, "max_weekly_hours": 60}
    
    # 通知配置
    notification_channels = Column(
        JSON,
        default=["SYSTEM"],
        comment='通知渠道列表'
    )
    notification_template = Column(Text, comment='通知模板')
    
    # 提醒频率控制
    remind_frequency = Column(
        String(20),
        default='ONCE_DAILY',
        comment='提醒频率: ONCE_DAILY/TWICE_DAILY/HOURLY'
    )
    max_reminders_per_day = Column(Integer, default=1, comment='每日最大提醒次数')
    
    # 优先级
    priority = Column(
        String(20),
        default='NORMAL',
        comment='优先级: LOW/NORMAL/HIGH/URGENT'
    )
    
    # 启用状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_reminder_config_type', 'reminder_type'),
        Index('idx_reminder_config_active', 'is_active'),
        {'comment': '工时提醒规则配置表'}
    )


# ==================== 提醒记录 ====================


class TimesheetReminderRecord(Base, TimestampMixin):
    """工时提醒记录"""
    __tablename__ = 'timesheet_reminder_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 提醒基本信息
    reminder_no = Column(String(50), unique=True, nullable=False, comment='提醒编号')
    reminder_type = Column(
        SQLEnum(ReminderTypeEnum),
        nullable=False,
        comment='提醒类型'
    )
    
    # 关联规则
    config_id = Column(
        Integer,
        ForeignKey('timesheet_reminder_config.id'),
        comment='关联配置ID'
    )
    
    # 接收人
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    
    # 提醒内容
    title = Column(String(200), nullable=False, comment='提醒标题')
    content = Column(Text, nullable=False, comment='提醒内容')
    
    # 关联数据
    source_type = Column(
        String(50),
        comment='来源类型: timesheet/timesheet_batch/overtime'
    )
    source_id = Column(Integer, comment='来源ID')
    extra_data = Column(JSON, comment='额外数据')
    # 示例数据：
    # - MISSING_TIMESHEET: {"target_date": "2024-02-01", "missing_days": 3}
    # - APPROVAL_TIMEOUT: {"timesheet_id": 123, "days_pending": 5}
    # - ANOMALY_TIMESHEET: {"anomaly_type": "DAILY_OVER_12", "hours": 14.5}
    
    # 状态
    status = Column(
        SQLEnum(ReminderStatusEnum),
        default=ReminderStatusEnum.PENDING,
        comment='提醒状态'
    )
    
    # 通知渠道
    notification_channels = Column(JSON, comment='已发送通知渠道')
    
    # 发送时间
    sent_at = Column(DateTime, comment='发送时间')
    
    # 处理信息
    read_at = Column(DateTime, comment='已读时间')
    dismissed_at = Column(DateTime, comment='忽略时间')
    dismissed_by = Column(Integer, ForeignKey('users.id'), comment='忽略人ID')
    dismissed_reason = Column(Text, comment='忽略原因')
    resolved_at = Column(DateTime, comment='解决时间')
    
    # 优先级
    priority = Column(
        String(20),
        default='NORMAL',
        comment='优先级: LOW/NORMAL/HIGH/URGENT'
    )

    # 关系
    config = relationship('TimesheetReminderConfig', foreign_keys=[config_id])
    user = relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_reminder_record_user', 'user_id'),
        Index('idx_reminder_record_type', 'reminder_type'),
        Index('idx_reminder_record_status', 'status'),
        Index('idx_reminder_record_sent', 'sent_at'),
        Index('idx_reminder_record_source', 'source_type', 'source_id'),
        {'comment': '工时提醒记录表'}
    )


# ==================== 异常工时检测记录 ====================


class TimesheetAnomalyRecord(Base, TimestampMixin):
    """异常工时检测记录"""
    __tablename__ = 'timesheet_anomaly_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联工时记录
    timesheet_id = Column(
        Integer,
        ForeignKey('timesheet.id'),
        nullable=False,
        comment='工时记录ID'
    )
    
    # 用户信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    
    # 异常类型
    anomaly_type = Column(
        SQLEnum(AnomalyTypeEnum),
        nullable=False,
        comment='异常类型'
    )
    
    # 异常详情
    description = Column(Text, nullable=False, comment='异常描述')
    anomaly_data = Column(JSON, comment='异常数据')
    # 示例数据：
    # - DAILY_OVER_12: {"hours": 14.5, "threshold": 12}
    # - WEEKLY_OVER_60: {"weekly_hours": 68, "threshold": 60, "week_start": "2024-02-05"}
    
    # 严重程度
    severity = Column(
        String(20),
        default='WARNING',
        comment='严重程度: INFO/WARNING/ERROR/CRITICAL'
    )
    
    # 检测时间
    detected_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False,
        comment='检测时间'
    )
    
    # 处理状态
    is_resolved = Column(Boolean, default=False, comment='是否已解决')
    resolved_at = Column(DateTime, comment='解决时间')
    resolved_by = Column(Integer, ForeignKey('users.id'), comment='解决人ID')
    resolution_note = Column(Text, comment='解决说明')
    
    # 关联提醒
    reminder_id = Column(
        Integer,
        ForeignKey('timesheet_reminder_record.id'),
        comment='关联提醒记录ID'
    )

    # 关系
    timesheet = relationship('Timesheet', foreign_keys=[timesheet_id])
    user = relationship('User', foreign_keys=[user_id])
    reminder = relationship('TimesheetReminderRecord', foreign_keys=[reminder_id])

    __table_args__ = (
        Index('idx_anomaly_timesheet', 'timesheet_id'),
        Index('idx_anomaly_user', 'user_id'),
        Index('idx_anomaly_type', 'anomaly_type'),
        Index('idx_anomaly_resolved', 'is_resolved'),
        Index('idx_anomaly_detected', 'detected_at'),
        {'comment': '异常工时检测记录表'}
    )
