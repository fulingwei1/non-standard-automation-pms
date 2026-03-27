# -*- coding: utf-8 -*-
"""
ECN模型 - 物料影响跟踪（处置决策、执行进度、相关人员）
"""
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class EcnMaterialDisposition(Base, TimestampMixin):
    """ECN物料处置决策表

    记录每个受影响物料的处置方案（继续使用/返工/报废/退货）
    """

    __tablename__ = "ecn_material_dispositions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey("ecn.id"), nullable=False, comment="ECN ID")
    affected_material_id = Column(
        Integer, ForeignKey("ecn_affected_materials.id"), comment="受影响物料记录ID"
    )
    material_id = Column(Integer, ForeignKey("materials.id"), comment="物料ID")

    # 物料基本信息（冗余，方便查询）
    material_code = Column(String(50), nullable=False, comment="物料编码")
    material_name = Column(String(200), nullable=False, comment="物料名称")
    specification = Column(String(500), comment="规格型号")

    # 物料当前状态
    material_status = Column(
        String(20),
        nullable=False,
        comment="物料当前状态: NOT_PURCHASED/ORDERED/IN_TRANSIT/IN_STOCK",
    )

    # 关联采购信息
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), comment="采购订单ID")
    purchase_order_no = Column(String(50), comment="采购订单号")
    supplier_id = Column(Integer, ForeignKey("vendors.id"), comment="供应商ID")
    supplier_name = Column(String(200), comment="供应商名称")

    # 数量与金额
    affected_quantity = Column(Numeric(10, 4), default=0, comment="受影响数量")
    unit_price = Column(Numeric(12, 4), default=0, comment="单价")
    potential_loss = Column(Numeric(14, 2), default=0, comment="潜在损失金额")

    # 处置决策
    disposition = Column(
        String(20),
        comment="处置方式: CONTINUE_USE/REWORK/SCRAP/RETURN/PENDING",
    )
    disposition_reason = Column(Text, comment="处置原因")
    disposition_cost = Column(Numeric(14, 2), default=0, comment="处置成本（返工/报废等）")
    actual_loss = Column(Numeric(14, 2), default=0, comment="实际损失金额")

    # 决策信息
    decided_by = Column(Integer, ForeignKey("users.id"), comment="决策人")
    decided_at = Column(DateTime, comment="决策时间")

    # 处理状态
    status = Column(
        String(20), default="PENDING",
        comment="处理状态: PENDING/DECIDED/IN_PROGRESS/COMPLETED",
    )
    completed_at = Column(DateTime, comment="处理完成时间")

    remark = Column(Text, comment="备注")

    # 关系
    ecn = relationship("Ecn")
    affected_material = relationship("EcnAffectedMaterial")
    material = relationship("Material")
    purchase_order = relationship("PurchaseOrder")
    decider = relationship("User", foreign_keys=[decided_by])

    __table_args__ = (
        Index("idx_mat_disp_ecn", "ecn_id"),
        Index("idx_mat_disp_material", "material_id"),
        Index("idx_mat_disp_status", "status"),
        Index("idx_mat_disp_po", "purchase_order_id"),
    )


class EcnExecutionProgress(Base, TimestampMixin):
    """ECN执行进度表

    跟踪ECN执行各阶段的进度
    """

    __tablename__ = "ecn_execution_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey("ecn.id"), nullable=False, comment="ECN ID")

    # 阶段信息
    phase = Column(
        String(30),
        nullable=False,
        comment="执行阶段: NOTIFY_SUPPLIER/PURCHASE_CHANGE/MATERIAL_DISPOSITION/VERIFICATION/CLOSE",
    )
    phase_name = Column(String(100), comment="阶段名称")
    phase_order = Column(Integer, default=0, comment="阶段顺序")

    # 进度
    status = Column(
        String(20), default="PENDING",
        comment="状态: PENDING/IN_PROGRESS/COMPLETED/BLOCKED/SKIPPED",
    )
    progress_pct = Column(Integer, default=0, comment="进度百分比(0-100)")

    # 时间
    planned_start = Column(Date, comment="计划开始")
    planned_end = Column(Date, comment="计划结束")
    actual_start = Column(DateTime, comment="实际开始")
    actual_end = Column(DateTime, comment="实际完成")
    estimated_completion = Column(Date, comment="预计完成日期")

    # 负责人
    assignee_id = Column(Integer, ForeignKey("users.id"), comment="负责人")

    # 阻塞问题
    is_blocked = Column(Boolean, default=False, comment="是否阻塞")
    block_reason = Column(Text, comment="阻塞原因")
    block_resolved_at = Column(DateTime, comment="阻塞解除时间")

    # 详情
    summary = Column(Text, comment="阶段摘要")
    details = Column(JSON, comment="详细信息(JSON)")

    remark = Column(Text, comment="备注")

    # 关系
    ecn = relationship("Ecn")
    assignee = relationship("User", foreign_keys=[assignee_id])

    __table_args__ = (
        Index("idx_exec_prog_ecn", "ecn_id"),
        Index("idx_exec_prog_phase", "phase"),
        Index("idx_exec_prog_status", "status"),
    )


class EcnStakeholder(Base, TimestampMixin):
    """ECN相关人员表

    记录ECN相关的所有干系人及其角色
    """

    __tablename__ = "ecn_stakeholders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey("ecn.id"), nullable=False, comment="ECN ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")

    # 角色
    role = Column(
        String(30),
        nullable=False,
        comment="角色: PROJECT_MANAGER/PURCHASER/SUPPLIER_CONTACT/DESIGNER/APPROVER/OBSERVER",
    )
    role_name = Column(String(100), comment="角色名称")

    # 关联来源
    source = Column(
        String(30), default="AUTO",
        comment="添加来源: AUTO/MANUAL",
    )
    source_reason = Column(String(200), comment="添加原因（自动识别时记录识别逻辑）")

    # 通知订阅
    is_subscribed = Column(Boolean, default=True, comment="是否订阅通知")
    subscription_types = Column(
        JSON, comment="订阅的通知类型列表(JSON), 如 ['STATUS_CHANGE','DISPOSITION','PROGRESS']"
    )

    # 查看权限
    can_view_detail = Column(Boolean, default=True, comment="可查看ECN详情")
    can_view_progress = Column(Boolean, default=True, comment="可查看执行进度")

    remark = Column(Text, comment="备注")

    # 关系
    ecn = relationship("Ecn")
    user = relationship("User")

    __table_args__ = (
        Index("idx_stakeholder_ecn", "ecn_id"),
        Index("idx_stakeholder_user", "user_id"),
        Index("idx_stakeholder_role", "role"),
    )
