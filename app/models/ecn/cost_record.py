# -*- coding: utf-8 -*-
"""
ECN成本记录模型 - 跟踪ECN导致的实际成本
"""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class EcnCostRecord(Base, TimestampMixin):
    """
    ECN成本记录表

    记录ECN导致的每笔实际成本，支持：
    - 物料报废成本
    - 返工成本（人工+设备）
    - 新物料采购成本
    - 供应商退货/索赔成本
    - 项目延期成本
    - 管理成本
    """

    __tablename__ = "ecn_cost_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey("ecn.id"), nullable=False, comment="ECN ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")

    # 成本分类
    cost_type = Column(
        String(30),
        nullable=False,
        comment="成本类型: SCRAP/REWORK/NEW_PURCHASE/CLAIM/DELAY/ADMIN",
    )
    cost_category = Column(String(50), comment="成本子分类")

    # 金额
    estimated_amount = Column(Numeric(14, 2), default=0, comment="预估金额")
    actual_amount = Column(Numeric(14, 2), default=0, comment="实际金额")
    currency = Column(String(10), default="CNY", comment="币种")

    # 发生日期
    cost_date = Column(Date, comment="成本发生日期")

    # 关联物料（报废/新购类型）
    material_id = Column(Integer, ForeignKey("materials.id"), comment="物料ID")
    material_code = Column(String(50), comment="物料编码")
    material_name = Column(String(200), comment="物料名称")
    quantity = Column(Numeric(10, 4), comment="数量")
    unit_price = Column(Numeric(12, 4), comment="单价")

    # 返工相关
    rework_hours = Column(Numeric(10, 2), comment="返工工时")
    hourly_rate = Column(Numeric(10, 2), comment="工时费率")

    # 凭证
    voucher_type = Column(String(30), comment="凭证类型: INVOICE/RECEIPT/CLAIM_NOTE/OTHER")
    voucher_no = Column(String(100), comment="凭证号")
    voucher_attachment_id = Column(Integer, comment="凭证附件ID")

    # 供应商（索赔类型）
    vendor_id = Column(Integer, ForeignKey("vendors.id"), comment="供应商ID")

    # 描述
    description = Column(Text, comment="成本说明")

    # 审批
    approval_status = Column(
        String(20),
        default="PENDING",
        comment="审批状态: PENDING/APPROVED/REJECTED",
    )
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人")
    approved_at = Column(DateTime, comment="审批时间")
    approval_note = Column(Text, comment="审批意见")

    # 记录人
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="记录人")

    # 关系
    ecn = relationship("Ecn", back_populates="cost_records")
    project = relationship("Project", foreign_keys=[project_id])
    machine = relationship("Machine", foreign_keys=[machine_id])
    recorder = relationship("User", foreign_keys=[recorded_by])
    approver = relationship("User", foreign_keys=[approved_by])

    __table_args__ = (
        Index("idx_ecn_cost_ecn", "ecn_id"),
        Index("idx_ecn_cost_project", "project_id"),
        Index("idx_ecn_cost_type", "cost_type"),
        Index("idx_ecn_cost_date", "cost_date"),
        Index("idx_ecn_cost_approval", "approval_status"),
        {"comment": "ECN成本记录表"},
    )

    def __repr__(self):
        return f"<EcnCostRecord ecn={self.ecn_id} type={self.cost_type} amount={self.actual_amount}>"
