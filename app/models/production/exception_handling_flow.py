# -*- coding: utf-8 -*-
"""
异常处理流程模型
"""
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import Base, TimestampMixin


class FlowStatus(str, enum.Enum):
    """流程状态枚举"""
    PENDING = "PENDING"  # 待处理
    PROCESSING = "PROCESSING"  # 处理中
    RESOLVED = "RESOLVED"  # 已解决
    VERIFIED = "VERIFIED"  # 已验证
    CLOSED = "CLOSED"  # 已关闭


class EscalationLevel(str, enum.Enum):
    """升级级别枚举"""
    NONE = "NONE"  # 未升级
    LEVEL_1 = "LEVEL_1"  # 一级升级（班组长）
    LEVEL_2 = "LEVEL_2"  # 二级升级（车间主任）
    LEVEL_3 = "LEVEL_3"  # 三级升级（生产经理）


class ExceptionHandlingFlow(Base, TimestampMixin):
    """异常处理流程表"""
    __tablename__ = 'exception_handling_flow'
    __table_args__ = (
        Index('idx_ehf_exception_id', 'exception_id'),
        Index('idx_ehf_status', 'status'),
        Index('idx_ehf_escalation_level', 'escalation_level'),
        {'extend_existing': True, 'comment': '异常处理流程表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联异常
    exception_id = Column(
        Integer,
        ForeignKey('production_exception.id'),
        nullable=False,
        comment='异常ID'
    )
    
    # 流程状态
    status = Column(
        Enum(FlowStatus),
        nullable=False,
        default=FlowStatus.PENDING,
        comment='流程状态'
    )
    
    # 升级信息
    escalation_level = Column(
        Enum(EscalationLevel),
        nullable=False,
        default=EscalationLevel.NONE,
        comment='升级级别'
    )
    escalation_reason = Column(Text, nullable=True, comment='升级原因')
    escalated_at = Column(DateTime, nullable=True, comment='升级时间')
    escalated_to_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='升级至处理人ID'
    )
    
    # 处理时长统计
    pending_duration_minutes = Column(Integer, nullable=True, comment='待处理时长(分钟)')
    processing_duration_minutes = Column(Integer, nullable=True, comment='处理中时长(分钟)')
    total_duration_minutes = Column(Integer, nullable=True, comment='总处理时长(分钟)')
    
    # 状态变更时间
    pending_at = Column(DateTime, nullable=True, comment='进入待处理时间')
    processing_at = Column(DateTime, nullable=True, comment='进入处理中时间')
    resolved_at = Column(DateTime, nullable=True, comment='进入已解决时间')
    verified_at = Column(DateTime, nullable=True, comment='进入已验证时间')
    closed_at = Column(DateTime, nullable=True, comment='进入已关闭时间')
    
    # 验证信息
    verifier_id = Column(
        Integer,
        ForeignKey('users.id'),
        nullable=True,
        comment='验证人ID'
    )
    verify_result = Column(String(20), nullable=True, comment='验证结果：PASS/FAIL')
    verify_comment = Column(Text, nullable=True, comment='验证意见')
    
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    exception = relationship('ProductionException', backref='handling_flows')
    escalated_to = relationship('User', foreign_keys=[escalated_to_id], backref='escalated_exceptions')
    verifier = relationship('User', foreign_keys=[verifier_id], backref='verified_exceptions')
