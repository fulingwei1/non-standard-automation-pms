# -*- coding: utf-8 -*-
"""
项目变更管理模块 ORM 模型
包含：变更请求、审批记录、通知记录
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    ChangeTypeEnum,
    ChangeSourceEnum,
    ChangeStatusEnum,
    ImpactLevelEnum,
    ApprovalDecisionEnum,
)


# ==================== 变更请求表 ====================

class ChangeRequest(Base, TimestampMixin):
    """项目变更请求表"""
    __tablename__ = 'change_requests'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    change_code = Column(String(50), unique=True, nullable=False, comment='变更编号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 变更基本信息
    title = Column(String(200), nullable=False, comment='变更标题')
    description = Column(Text, comment='变更描述')
    change_type = Column(
        Enum(ChangeTypeEnum),
        nullable=False,
        comment='变更类型'
    )
    change_source = Column(
        Enum(ChangeSourceEnum),
        nullable=False,
        comment='变更来源'
    )
    
    # 提出人信息
    submitter_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='提交人ID')
    submitter_name = Column(String(50), comment='提交人姓名')
    submit_date = Column(DateTime, default=datetime.utcnow, comment='提交日期')

    # 影响评估
    cost_impact = Column(Numeric(15, 2), comment='成本影响（元）')
    cost_impact_level = Column(
        Enum(ImpactLevelEnum),
        comment='成本影响程度'
    )
    time_impact = Column(Integer, comment='时间影响（天）')
    time_impact_level = Column(
        Enum(ImpactLevelEnum),
        comment='时间影响程度'
    )
    scope_impact = Column(Text, comment='范围影响描述')
    scope_impact_level = Column(
        Enum(ImpactLevelEnum),
        comment='范围影响程度'
    )
    risk_assessment = Column(Text, comment='风险评估')
    
    # 影响评估详情（JSON格式）
    impact_details = Column(JSON, comment='影响评估详情')
    # 示例结构：
    # {
    #   "cost": {
    #     "labor": 10000,
    #     "material": 5000,
    #     "total": 15000,
    #     "description": "需增加2名开发人员"
    #   },
    #   "schedule": {
    #     "delay_days": 15,
    #     "affected_milestones": ["MS-001", "MS-002"],
    #     "description": "影响交付里程碑"
    #   },
    #   "scope": {
    #     "added_features": ["F1", "F2"],
    #     "removed_features": [],
    #     "modified_features": ["F3"]
    #   },
    #   "resources": {
    #     "additional_staff": 2,
    #     "additional_equipment": ["设备A"]
    #   }
    # }

    # 工作流状态
    status = Column(
        Enum(ChangeStatusEnum),
        default=ChangeStatusEnum.SUBMITTED,
        nullable=False,
        comment='变更状态'
    )
    
    # 审批信息
    approver_id = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approver_name = Column(String(50), comment='审批人姓名')
    approval_date = Column(DateTime, comment='审批日期')
    approval_decision = Column(
        Enum(ApprovalDecisionEnum),
        default=ApprovalDecisionEnum.PENDING,
        comment='审批决策'
    )
    approval_comments = Column(Text, comment='审批意见')
    
    # 实施信息
    implementation_plan = Column(Text, comment='实施计划')
    implementation_start_date = Column(DateTime, comment='实施开始日期')
    implementation_end_date = Column(DateTime, comment='实施结束日期')
    implementation_status = Column(String(50), comment='实施状态')
    implementation_notes = Column(Text, comment='实施备注')
    
    # 验证信息
    verification_notes = Column(Text, comment='验证说明')
    verification_date = Column(DateTime, comment='验证日期')
    verified_by_id = Column(Integer, ForeignKey('users.id'), comment='验证人ID')
    verified_by_name = Column(String(50), comment='验证人姓名')
    
    # 关闭信息
    close_date = Column(DateTime, comment='关闭日期')
    close_notes = Column(Text, comment='关闭说明')
    
    # 附件信息（JSON数组）
    attachments = Column(JSON, comment='附件列表')
    # 示例结构：
    # [
    #   {
    #     "name": "需求文档.pdf",
    #     "url": "/uploads/xxx.pdf",
    #     "size": 1024000,
    #     "uploaded_at": "2024-01-01T10:00:00"
    #   }
    # ]
    
    # 是否需要通知
    notify_customer = Column(Boolean, default=False, comment='是否通知客户')
    notify_team = Column(Boolean, default=True, comment='是否通知团队')
    
    # 关系
    project = relationship('Project', back_populates='change_requests')
    submitter = relationship('User', foreign_keys=[submitter_id])
    approver = relationship('User', foreign_keys=[approver_id])
    verified_by = relationship('User', foreign_keys=[verified_by_id])
    approval_records = relationship(
        'ChangeApprovalRecord',
        back_populates='change_request',
        cascade='all, delete-orphan'
    )
    notifications = relationship(
        'ChangeNotification',
        back_populates='change_request',
        cascade='all, delete-orphan'
    )
    impact_analyses = relationship(
        'ChangeImpactAnalysis',
        back_populates='change_request',
        cascade='all, delete-orphan'
    )
    response_suggestions = relationship(
        'ChangeResponseSuggestion',
        back_populates='change_request',
        cascade='all, delete-orphan'
    )

    __table_args__ = (
        Index('idx_change_code', 'change_code'),
        Index('idx_change_project', 'project_id'),
        Index('idx_change_status', 'status'),
        Index('idx_change_type', 'change_type'),
        Index('idx_change_submit_date', 'submit_date'),
        {'comment': '项目变更请求表'}
    )

    def __repr__(self):
        return f"<ChangeRequest {self.change_code}>"


# ==================== 变更审批记录表 ====================

class ChangeApprovalRecord(Base, TimestampMixin):
    """变更审批记录表"""
    __tablename__ = 'change_approval_records'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    change_request_id = Column(
        Integer,
        ForeignKey('change_requests.id'),
        nullable=False,
        comment='变更请求ID'
    )
    
    # 审批人信息
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='审批人ID')
    approver_name = Column(String(50), comment='审批人姓名')
    approver_role = Column(String(50), comment='审批人角色')
    
    # 审批信息
    approval_date = Column(DateTime, default=datetime.utcnow, comment='审批日期')
    decision = Column(
        Enum(ApprovalDecisionEnum),
        nullable=False,
        comment='审批决策'
    )
    comments = Column(Text, comment='审批意见')
    
    # 审批附件
    attachments = Column(JSON, comment='审批附件')
    
    # 关系
    change_request = relationship('ChangeRequest', back_populates='approval_records')
    approver = relationship('User')

    __table_args__ = (
        Index('idx_approval_change', 'change_request_id'),
        Index('idx_approval_approver', 'approver_id'),
        Index('idx_approval_date', 'approval_date'),
        {'comment': '变更审批记录表'}
    )

    def __repr__(self):
        return f"<ChangeApprovalRecord {self.id}>"


# ==================== 变更通知记录表 ====================

class ChangeNotification(Base, TimestampMixin):
    """变更通知记录表
    
    【状态】未启用 - 变更通知"""
    __tablename__ = 'change_notifications'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    change_request_id = Column(
        Integer,
        ForeignKey('change_requests.id'),
        nullable=False,
        comment='变更请求ID'
    )
    
    # 通知信息
    notification_type = Column(String(50), nullable=False, comment='通知类型')
    # 类型：SUBMITTED（已提交）、APPROVED（已批准）、REJECTED（已拒绝）、
    #       IMPLEMENTING（实施中）、COMPLETED（已完成）
    
    recipient_id = Column(Integer, ForeignKey('users.id'), comment='接收人ID')
    recipient_name = Column(String(50), comment='接收人姓名')
    recipient_email = Column(String(100), comment='接收人邮箱')
    
    notification_channel = Column(String(20), comment='通知渠道')
    # EMAIL、SMS、SYSTEM（系统消息）
    
    notification_title = Column(String(200), comment='通知标题')
    notification_content = Column(Text, comment='通知内容')
    
    sent_at = Column(DateTime, comment='发送时间')
    is_sent = Column(Boolean, default=False, comment='是否已发送')
    is_read = Column(Boolean, default=False, comment='是否已读')
    read_at = Column(DateTime, comment='阅读时间')
    
    # 关系
    change_request = relationship('ChangeRequest', back_populates='notifications')
    recipient = relationship('User')

    __table_args__ = (
        Index('idx_notification_change', 'change_request_id'),
        Index('idx_notification_recipient', 'recipient_id'),
        Index('idx_notification_sent', 'is_sent'),
        {'comment': '变更通知记录表'}
    )

    def __repr__(self):
        return f"<ChangeNotification {self.id}>"
