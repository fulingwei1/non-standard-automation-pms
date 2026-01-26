# -*- coding: utf-8 -*-
"""
ApprovalEngine 数据模型
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovalFlowType(str, Enum):
    """审批流程类型"""

    SINGLE_LEVEL = "SINGLE_LEVEL"  # 单级审批
    MULTI_LEVEL = "MULTI_LEVEL"  # 多级审批
    CONDITIONAL_ROUTE = "CONDITIONAL_ROUTE"  # 条件路由
    AMOUNT_BASED = "AMOUNT_BASED"  # 金额判断
    PARALLEL = "PARALLEL"  # 并行审批


class ApprovalNodeRole(str, Enum):
    """审批节点角色类型"""

    USER = "USER"  # 具体用户
    ROLE = "ROLE"  # 角色
    DEPARTMENT = "DEPARTMENT"  # 部门
    SUPERVISOR = "SUPERVISOR"  # 上级


class ApprovalStatus(str, Enum):
    """审批状态"""

    PENDING = "PENDING"  # 待审批
    IN_PROGRESS = "IN_PROGRESS"  # 审批中
    APPROVED = "APPROVED"  # 已通过
    REJECTED = "REJECTED"  # 已驳回
    CANCELLED = "CANCELLED"  # 已取消
    EXPIRED = "EXPIRED"  # 已超时


class ApprovalDecision(str, Enum):
    """审批决策"""

    APPROVED = "APPROVED"  # 通过
    REJECTED = "REJECTED"  # 驳回
    RETURNED = "RETURNED"  # 退回上一级
    COMMENT_ONLY = "COMMENT_ONLY"  # 仅评论


class LegacyApprovalFlow(Base, TimestampMixin):
    """审批流程定义"""

    __tablename__ = "legacy_approval_flows"

    id = Column(Integer, primary_key=True, index=True)
    flow_code = Column(
        String(50), unique=True, nullable=False, comment="流程编码，如ECN_TECHNICAL"
    )
    flow_name = Column(String(100), nullable=False, comment="流程名称")
    flow_type = Column(String(50), nullable=False, comment="流程类型")
    module_name = Column(String(50), nullable=False, comment="所属模块，如ECN、SALES")
    is_active = Column(Boolean, default=True, nullable=False, comment="是否启用")
    config_json = Column(Text, comment="流程配置JSON")
    version = Column(Integer, default=1, comment="版本号")

    # 关系
    nodes = relationship(
        "LegacyApprovalNode", back_populates="flow", cascade="all, delete-orphan"
    )


class LegacyApprovalNode(Base, TimestampMixin):
    """审批节点定义"""

    __tablename__ = "legacy_approval_nodes"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer,
        ForeignKey("legacy_approval_flows.id"),
        nullable=False,
        comment="流程ID",
    )
    node_code = Column(String(50), nullable=False, comment="节点编码")
    node_name = Column(String(100), nullable=False, comment="节点名称")
    sequence = Column(Integer, default=0, nullable=False, comment="节点顺序")
    role_type = Column(String(50), nullable=False, comment="角色类型")
    role_value = Column(String(100), comment="角色值（用户ID或角色代码或部门ID）")
    is_required = Column(Boolean, default=True, nullable=False, comment="是否必审")
    timeout_hours = Column(Integer, default=48, comment="超时时间（小时）")
    condition_expression = Column(Text, comment="条件表达式（JSON）")

    # 关系
    flow = relationship("LegacyApprovalFlow", back_populates="nodes")


class LegacyApprovalInstance(Base, TimestampMixin):
    """审批实例"""

    __tablename__ = "legacy_approval_instances"

    id = Column(Integer, primary_key=True, index=True)
    flow_id = Column(
        Integer,
        ForeignKey("legacy_approval_flows.id"),
        nullable=False,
        comment="流程ID",
    )
    flow_code = Column(String(50), nullable=False, comment="流程编码")
    business_type = Column(String(50), comment="业务类型，如ECN、QUOTE")
    business_id = Column(Integer, nullable=False, index=True, comment="业务ID")
    business_title = Column(String(200), comment="业务标题")

    # 提交人信息
    submitted_by = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="提交人ID"
    )
    submitted_at = Column(DateTime, default=datetime.now, comment="提交时间")

    # 当前状态
    current_status = Column(
        String(50), default=ApprovalStatus.PENDING.value, comment="当前状态"
    )
    current_node_id = Column(
        Integer, ForeignKey("legacy_approval_nodes.id"), comment="当前节点ID"
    )

    # 统计信息
    total_nodes = Column(Integer, comment="总节点数")
    completed_nodes = Column(Integer, default=0, comment="已完成节点数")

    # 到期时间
    due_date = Column(DateTime, comment="到期时间")

    # 关系
    flow = relationship("LegacyApprovalFlow")
    current_node = relationship("LegacyApprovalNode", foreign_keys=[current_node_id])
    records = relationship(
        "LegacyApprovalRecord", back_populates="instance", cascade="all, delete-orphan"
    )


class LegacyApprovalRecord(Base, TimestampMixin):
    """审批记录"""

    __tablename__ = "legacy_approval_records"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(
        Integer,
        ForeignKey("legacy_approval_instances.id"),
        nullable=False,
        index=True,
        comment="审批实例ID",
    )
    node_id = Column(
        Integer,
        ForeignKey("legacy_approval_nodes.id"),
        nullable=False,
        index=True,
        comment="节点ID",
    )

    # 审批人信息
    approver_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="审批人ID"
    )
    approver_name = Column(String(100), comment="审批人姓名")
    approver_role = Column(String(100), comment="审批人角色")

    # 审批决策
    decision = Column(String(50), comment="决策（APPROVED/REJECTED/RETURNED）")
    comment = Column(Text, comment="审批意见")

    # 审批时间
    approved_at = Column(DateTime, comment="审批时间")

    # 关系
    instance = relationship("LegacyApprovalInstance", back_populates="records")
    node = relationship("LegacyApprovalNode")
