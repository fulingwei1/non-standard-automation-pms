# -*- coding: utf-8 -*-
"""
通知中心模块 ORM 模型
包含：系统通知、通知设置
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime,
    ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Notification(Base, TimestampMixin):
    """系统通知表"""
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='接收用户ID')
    
    # 通知类型
    notification_type = Column(String(30), nullable=False, comment='通知类型')
    # 类型包括：TASK_ASSIGNED, TASK_COMPLETED, APPROVAL_PENDING, APPROVAL_RESULT,
    # ALERT, ISSUE_ASSIGNED, ISSUE_RESOLVED, PROJECT_UPDATE, MILESTONE_REACHED等
    
    # 通知来源
    source_type = Column(String(30), comment='来源类型：project/task/issue/alert/approval等')
    source_id = Column(Integer, comment='来源ID')
    
    # 通知内容
    title = Column(String(200), nullable=False, comment='通知标题')
    content = Column(Text, comment='通知内容')
    
    # 跳转链接
    link_url = Column(String(500), comment='跳转链接')
    link_params = Column(JSON, comment='链接参数')
    
    # 状态
    is_read = Column(Boolean, default=False, comment='是否已读')
    read_at = Column(DateTime, comment='阅读时间')
    
    # 优先级
    priority = Column(String(10), default='NORMAL', comment='优先级：LOW/NORMAL/HIGH/URGENT')
    
    # 额外数据
    extra_data = Column(JSON, comment='额外数据（JSON格式）')
    
    # 关系
    user = relationship('User', foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_notification_user', 'user_id'),
        Index('idx_notification_type', 'notification_type'),
        Index('idx_notification_read', 'is_read'),
        Index('idx_notification_created', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Notification {self.id} to user {self.user_id}>'


class NotificationSettings(Base, TimestampMixin):
    """用户通知设置表"""
    __tablename__ = 'notification_settings'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), unique=True, nullable=False, comment='用户ID')
    
    # 通知渠道偏好
    email_enabled = Column(Boolean, default=True, comment='邮件通知')
    sms_enabled = Column(Boolean, default=False, comment='短信通知')
    wechat_enabled = Column(Boolean, default=True, comment='微信通知')
    system_enabled = Column(Boolean, default=True, comment='系统通知')
    
    # 通知类型偏好
    task_notifications = Column(Boolean, default=True, comment='任务通知')
    approval_notifications = Column(Boolean, default=True, comment='审批通知')
    alert_notifications = Column(Boolean, default=True, comment='预警通知')
    issue_notifications = Column(Boolean, default=True, comment='问题通知')
    project_notifications = Column(Boolean, default=True, comment='项目通知')
    
    # 免打扰时间
    quiet_hours_start = Column(String(5), comment='免打扰开始时间（HH:mm）')
    quiet_hours_end = Column(String(5), comment='免打扰结束时间（HH:mm）')
    
    # 关系
    user = relationship('User', foreign_keys=[user_id])
    
    __table_args__ = (
        Index('idx_notification_settings_user', 'user_id'),
    )
    
    def __repr__(self):
        return f'<NotificationSettings user {self.user_id}>'



