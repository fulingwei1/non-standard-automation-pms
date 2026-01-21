# -*- coding: utf-8 -*-
"""
审批工作流和销售目标模型
"""
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ApprovalWorkflow(Base, TimestampMixin):
    """审批工作流配置表"""
    __tablename__ = "approval_workflows"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    workflow_type = Column(String(20), nullable=False, comment="工作流类型：QUOTE/CONTRACT/INVOICE")
    workflow_name = Column(String(100), nullable=False, comment="工作流名称")
    description = Column(Text, comment="工作流描述")
    routing_rules = Column(JSON, comment="审批路由规则（JSON）")
    is_active = Column(Boolean, default=True, comment="是否启用")

    steps = relationship("ApprovalWorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="ApprovalWorkflowStep.step_order")
    records = relationship("ApprovalRecord", back_populates="workflow")

    __table_args__ = (
        Index("idx_approval_workflow_type", "workflow_type"),
        Index("idx_approval_workflow_active", "is_active"),
    )

    def __repr__(self):
        return f"<ApprovalWorkflow {self.workflow_name}>"


class ApprovalWorkflowStep(Base, TimestampMixin):
    """审批工作流步骤表"""
    __tablename__ = "approval_workflow_steps"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False, comment="工作流ID")
    step_order = Column(Integer, nullable=False, comment="步骤顺序")
    step_name = Column(String(100), nullable=False, comment="步骤名称")
    approver_role = Column(String(50), comment="审批角色（如：SALES_MANAGER）")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="指定审批人ID（可选）")
    is_required = Column(Boolean, default=True, comment="是否必需")
    can_delegate = Column(Boolean, default=True, comment="是否允许委托")
    can_withdraw = Column(Boolean, default=True, comment="是否允许撤回（在下一级审批前）")
    due_hours = Column(Integer, comment="审批期限（小时）")

    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_approval_workflow_step_workflow", "workflow_id"),
        Index("idx_approval_workflow_step_order", "workflow_id", "step_order"),
    )

    def __repr__(self):
        return f"<ApprovalWorkflowStep {self.workflow_id}-{self.step_order}>"


class ApprovalRecord(Base, TimestampMixin):
    """审批记录表（每个实体的审批实例）"""
    __tablename__ = "approval_records"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    entity_type = Column(String(20), nullable=False, comment="实体类型：QUOTE/CONTRACT/INVOICE")
    entity_id = Column(Integer, nullable=False, comment="实体ID")
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False, comment="工作流ID")
    current_step = Column(Integer, default=1, comment="当前审批步骤（从1开始）")
    status = Column(String(20), default="PENDING", comment="审批状态：PENDING/APPROVED/REJECTED/CANCELLED")
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发起人ID")

    workflow = relationship("ApprovalWorkflow", back_populates="records")
    initiator = relationship("User", foreign_keys=[initiator_id])
    history = relationship("ApprovalHistory", back_populates="record", cascade="all, delete-orphan", order_by="ApprovalHistory.step_order")

    __table_args__ = (
        Index("idx_approval_record_entity", "entity_type", "entity_id"),
        Index("idx_approval_record_workflow", "workflow_id"),
        Index("idx_approval_record_status", "status"),
        Index("idx_approval_record_initiator", "initiator_id"),
    )

    def __repr__(self):
        return f"<ApprovalRecord {self.entity_type}-{self.entity_id}>"


class ApprovalHistory(Base, TimestampMixin):
    """审批历史表（记录每个审批步骤的历史）"""
    __tablename__ = "approval_history"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    approval_record_id = Column(Integer, ForeignKey("approval_records.id"), nullable=False, comment="审批记录ID")
    step_order = Column(Integer, nullable=False, comment="步骤顺序")
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="审批人ID")
    action = Column(String(20), nullable=False, comment="审批操作：APPROVE/REJECT/DELEGATE/WITHDRAW")
    comment = Column(Text, comment="审批意见")
    delegate_to_id = Column(Integer, ForeignKey("users.id"), comment="委托给的用户ID")
    action_at = Column(DateTime, nullable=False, default=datetime.now, comment="操作时间")

    record = relationship("ApprovalRecord", back_populates="history")
    approver = relationship("User", foreign_keys=[approver_id])
    delegate_to = relationship("User", foreign_keys=[delegate_to_id])

    __table_args__ = (
        Index("idx_approval_history_record", "approval_record_id"),
        Index("idx_approval_history_step", "approval_record_id", "step_order"),
        Index("idx_approval_history_approver", "approver_id"),
    )

    def __repr__(self):
        return f"<ApprovalHistory {self.approval_record_id}-{self.step_order}>"


class SalesTarget(Base, TimestampMixin):
    """销售目标表"""
    __tablename__ = "sales_targets"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    target_scope = Column(String(20), nullable=False, comment="目标范围：PERSONAL/TEAM/DEPARTMENT")
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID（个人目标）")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="部门ID（部门目标）")
    team_id = Column(Integer, ForeignKey("sales_teams.id"), comment="团队ID（团队目标）")
    target_type = Column(String(20), nullable=False, comment="目标类型：LEAD_COUNT/OPPORTUNITY_COUNT/CONTRACT_AMOUNT/COLLECTION_AMOUNT")
    target_period = Column(String(20), nullable=False, comment="目标周期：MONTHLY/QUARTERLY/YEARLY")
    period_value = Column(String(20), nullable=False, comment="周期标识：2025-01/2025-Q1/2025")
    target_value = Column(Numeric(14, 2), nullable=False, comment="目标值")
    description = Column(Text, comment="目标描述")
    status = Column(String(20), default="ACTIVE", comment="状态：ACTIVE/COMPLETED/CANCELLED")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")

    user = relationship("User", foreign_keys=[user_id])
    department = relationship("Department", foreign_keys=[department_id])
    team = relationship("SalesTeam", foreign_keys=[team_id])
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_sales_target_scope", "target_scope", "user_id", "department_id"),
        Index("idx_sales_target_type_period", "target_type", "target_period", "period_value"),
        Index("idx_sales_target_status", "status"),
        Index("idx_sales_target_user", "user_id"),
        Index("idx_sales_target_department", "department_id"),
        Index("idx_sales_target_team", "team_id"),
    )

    def __repr__(self):
        return f"<SalesTarget {self.target_type}-{self.period_value}>"


class SalesRankingConfig(Base, TimestampMixin):
    """销售排名权重配置"""
    __tablename__ = "sales_ranking_configs"
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    metrics = Column(JSON, nullable=False, comment="指标配置(JSON数组)")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    updated_by = Column(Integer, ForeignKey("users.id"), comment="最后更新人ID")

    __table_args__ = (
        Index("idx_sales_ranking_config_updated_at", "updated_at"),
        {"comment": "销售排名权重配置表"},
    )

    def __repr__(self):
        return f"<SalesRankingConfig {self.id}>"
