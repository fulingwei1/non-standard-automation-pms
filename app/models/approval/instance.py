# -*- coding: utf-8 -*-
"""
审批实例模型

记录每次发起的审批流程实例
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovalInstance(Base, TimestampMixin):
    """审批实例 - 每次发起的审批"""

    __tablename__ = "approval_instances"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    instance_no = Column(String(50), unique=True, nullable=False, comment="审批单号（如AP202601200001）")

    # 关联模板和流程
    template_id = Column(Integer, ForeignKey("approval_templates.id"), nullable=False, comment="模板ID")
    flow_id = Column(Integer, ForeignKey("approval_flow_definitions.id"), nullable=False, comment="流程ID")

    # 关联业务实体
    entity_type = Column(String(50), comment="业务实体类型（如QUOTE/CONTRACT/ECN）")
    entity_id = Column(Integer, comment="业务实体ID")

    # 发起人信息
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发起人ID")
    initiator_dept_id = Column(Integer, ForeignKey("departments.id"), comment="发起人部门ID")

    # 表单数据
    form_data = Column(JSON, comment="""
        表单数据，示例：
        {
            "title": "XX项目报价审批",
            "leave_type": "年假",
            "leave_days": 5,
            "reason": "家庭事务"
        }
    """)

    # 审批状态
    status = Column(String(20), nullable=False, default="PENDING", comment="""
        审批状态：
        DRAFT: 草稿（未提交）
        PENDING: 审批中
        APPROVED: 已通过
        REJECTED: 已驳回
        CANCELLED: 已撤销（发起人撤销）
        TERMINATED: 已终止（管理员终止）
    """)

    # 当前节点
    current_node_id = Column(Integer, ForeignKey("approval_node_definitions.id"), comment="当前节点ID")
    current_node_order = Column(Integer, comment="当前节点顺序")

    # 紧急程度
    urgency = Column(String(10), default="NORMAL", comment="""
        紧急程度：
        NORMAL: 普通
        URGENT: 紧急
        CRITICAL: 特急
    """)

    # 标题和摘要
    title = Column(String(200), comment="审批标题")
    summary = Column(Text, comment="审批摘要（用于列表展示）")

    # 时间记录
    submitted_at = Column(DateTime, comment="提交时间")
    completed_at = Column(DateTime, comment="完成时间")

    # 最终处理结果
    final_comment = Column(Text, comment="最终审批意见")
    final_approver_id = Column(Integer, ForeignKey("users.id"), comment="最终审批人ID")

    # 关系
    template = relationship("ApprovalTemplate", back_populates="instances")
    flow = relationship("ApprovalFlowDefinition", back_populates="instances")
    initiator = relationship("User", foreign_keys=[initiator_id])
    initiator_dept = relationship("Department", foreign_keys=[initiator_dept_id])
    current_node = relationship("ApprovalNodeDefinition", foreign_keys=[current_node_id])
    final_approver = relationship("User", foreign_keys=[final_approver_id])
    tasks = relationship("ApprovalTask", back_populates="instance", cascade="all, delete-orphan")
    cc_records = relationship("ApprovalCarbonCopy", back_populates="instance", cascade="all, delete-orphan")
    action_logs = relationship("ApprovalActionLog", back_populates="instance", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_approval_instance_no", "instance_no"),
        Index("idx_approval_instance_template", "template_id"),
        Index("idx_approval_instance_entity", "entity_type", "entity_id"),
        Index("idx_approval_instance_initiator", "initiator_id"),
        Index("idx_approval_instance_status", "status"),
        Index("idx_approval_instance_urgency", "urgency"),
        Index("idx_approval_instance_submitted", "submitted_at"),
        Index("idx_approval_instance_current_node", "current_node_id"),
    )

    def __repr__(self):
        return f"<ApprovalInstance {self.instance_no} ({self.status})>"

    @staticmethod
    def generate_instance_no() -> str:
        """生成审批单号"""
        now = datetime.now()
        # 格式：AP + 年月日 + 4位序号
        prefix = f"AP{now.strftime('%Y%m%d')}"
        # 注意：实际使用时需要查询数据库获取当天序号
        return prefix
