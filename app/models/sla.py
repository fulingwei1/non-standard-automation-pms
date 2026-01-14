# -*- coding: utf-8 -*-
"""
SLA管理模块 ORM 模型
包含：SLA策略、SLA监控记录
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date,
    Numeric, ForeignKey, Index, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from enum import Enum


# ==================== 枚举定义 ====================

class SLAStatusEnum(str, Enum):
    """SLA状态"""
    ON_TIME = 'ON_TIME'        # 按时
    OVERDUE = 'OVERDUE'        # 超时
    WARNING = 'WARNING'        # 预警（接近超时）
    NOT_APPLICABLE = 'NOT_APPLICABLE'  # 不适用


# ==================== SLA策略 ====================

class SLAPolicy(Base, TimestampMixin):
    """SLA策略表"""
    __tablename__ = 'sla_policies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_name = Column(String(100), nullable=False, comment='策略名称')
    policy_code = Column(String(50), unique=True, nullable=False, comment='策略编码')
    
    # 适用条件
    problem_type = Column(String(20), comment='问题类型（可选，为空表示适用所有类型）')
    urgency = Column(String(20), comment='紧急程度（可选，为空表示适用所有紧急程度）')
    
    # SLA标准
    response_time_hours = Column(Integer, nullable=False, comment='响应时间（小时）')
    resolve_time_hours = Column(Integer, nullable=False, comment='解决时间（小时）')
    
    # 预警设置
    warning_threshold_percent = Column(Numeric(5, 2), default=80, comment='预警阈值（百分比，达到此比例时预警）')
    
    # 优先级（用于匹配策略时的优先级，数字越小优先级越高）
    priority = Column(Integer, default=100, comment='优先级')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 描述
    description = Column(Text, comment='策略描述')
    remark = Column(Text, comment='备注')
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    created_by_name = Column(String(50), comment='创建人姓名')
    
    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    monitors = relationship('SLAMonitor', back_populates='policy')
    
    __table_args__ = (
        Index('idx_sla_policy_code', 'policy_code'),
        Index('idx_sla_policy_type_urgency', 'problem_type', 'urgency'),
        Index('idx_sla_policy_active', 'is_active'),
        {'comment': 'SLA策略表'},
    )
    
    def __repr__(self):
        return f'<SLAPolicy {self.policy_code}: {self.policy_name}>'


# ==================== SLA监控记录 ====================

class SLAMonitor(Base, TimestampMixin):
    """SLA监控记录表"""
    __tablename__ = 'sla_monitors'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 关联信息
    ticket_id = Column(Integer, ForeignKey('service_tickets.id'), nullable=False, comment='工单ID')
    policy_id = Column(Integer, ForeignKey('sla_policies.id'), nullable=False, comment='SLA策略ID')
    
    # 截止时间
    response_deadline = Column(DateTime, nullable=False, comment='响应截止时间')
    resolve_deadline = Column(DateTime, nullable=False, comment='解决截止时间')
    
    # 实际时间
    actual_response_time = Column(DateTime, comment='实际响应时间')
    actual_resolve_time = Column(DateTime, comment='实际解决时间')
    
    # SLA状态
    response_status = Column(String(20), default='ON_TIME', nullable=False, comment='响应状态：ON_TIME/OVERDUE/WARNING')
    resolve_status = Column(String(20), default='ON_TIME', nullable=False, comment='解决状态：ON_TIME/OVERDUE/WARNING')
    
    # 时间差（小时）
    response_time_diff_hours = Column(Numeric(10, 2), comment='响应时间差（小时，正数表示超时，负数表示提前）')
    resolve_time_diff_hours = Column(Numeric(10, 2), comment='解决时间差（小时，正数表示超时，负数表示提前）')
    
    # 预警记录
    response_warning_sent = Column(Boolean, default=False, comment='是否已发送响应预警')
    resolve_warning_sent = Column(Boolean, default=False, comment='是否已发送解决预警')
    response_warning_sent_at = Column(DateTime, comment='响应预警发送时间')
    resolve_warning_sent_at = Column(DateTime, comment='解决预警发送时间')
    
    # 备注
    remark = Column(Text, comment='备注')
    
    # 关系
    ticket = relationship('ServiceTicket', foreign_keys=[ticket_id])
    policy = relationship('SLAPolicy', back_populates='monitors')
    
    __table_args__ = (
        Index('idx_sla_monitor_ticket', 'ticket_id'),
        Index('idx_sla_monitor_policy', 'policy_id'),
        Index('idx_sla_monitor_response_status', 'response_status'),
        Index('idx_sla_monitor_resolve_status', 'resolve_status'),
        Index('idx_sla_monitor_response_deadline', 'response_deadline'),
        Index('idx_sla_monitor_resolve_deadline', 'resolve_deadline'),
        {'comment': 'SLA监控记录表'},
    )
    
    def __repr__(self):
        return f'<SLAMonitor {self.id}: Ticket {self.ticket_id}>'
