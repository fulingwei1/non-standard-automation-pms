# -*- coding: utf-8 -*-
"""
齐套率优化模块 - 数据模型
催货记录、替代料关系
"""
from datetime import datetime

from sqlalchemy import (
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

from app.models.base import Base, TimestampMixin


class ExpediteRecord(Base, TimestampMixin):
    """催货记录表"""

    __tablename__ = "expedite_records"
    __table_args__ = (
        Index("idx_expedite_material", "material_id"),
        Index("idx_expedite_supplier", "supplier_id"),
        Index("idx_expedite_po", "purchase_order_id"),
        Index("idx_expedite_status", "status"),
        Index("idx_expedite_shortage", "shortage_id"),
        {"extend_existing": True, "comment": "催货记录表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 关联信息
    shortage_id = Column(Integer, ForeignKey("material_shortages.id"), comment="缺料预警ID")
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False, comment="物料ID")
    supplier_id = Column(Integer, ForeignKey("vendors.id"), comment="供应商ID")
    purchase_order_id = Column(Integer, ForeignKey("purchase_orders.id"), comment="采购订单ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")

    # 物料冗余
    material_code = Column(String(50), nullable=False, comment="物料编码")
    material_name = Column(String(200), nullable=False, comment="物料名称")

    # 催货信息
    expedite_type = Column(
        String(20), default="MANUAL",
        comment="催货类型: AUTO-自动, MANUAL-手动",
    )
    urgency_level = Column(
        String(20), default="NORMAL",
        comment="紧急程度: CRITICAL-紧急, HIGH-高, NORMAL-普通, LOW-低",
    )
    shortage_qty = Column(Numeric(10, 4), comment="缺料数量")
    required_date = Column(Date, comment="需求日期")
    original_promised_date = Column(Date, comment="原承诺交期")
    new_promised_date = Column(Date, comment="催货后新承诺交期")

    # 通知方式
    notify_method = Column(
        String(50), default="SYSTEM",
        comment="通知方式: EMAIL-邮件, SMS-短信, WECHAT-微信, SYSTEM-系统消息, MULTI-多渠道",
    )
    notify_content = Column(Text, comment="通知内容")
    notify_sent_at = Column(DateTime, comment="通知发送时间")
    notify_status = Column(
        String(20), default="PENDING",
        comment="通知状态: PENDING-待发送, SENT-已发送, FAILED-发送失败",
    )

    # 催货结果
    status = Column(
        String(20), default="PENDING",
        comment="催货状态: PENDING-待处理, IN_PROGRESS-跟进中, RESOLVED-已解决, CLOSED-已关闭",
    )
    supplier_response = Column(Text, comment="供应商回复")
    response_at = Column(DateTime, comment="回复时间")
    actual_delivery_date = Column(Date, comment="实际到货日期")
    is_on_time = Column(Boolean, comment="催后是否准时到货")

    # 操作人
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    remark = Column(Text, comment="备注")

    # 关系
    material = relationship("Material")
    vendor = relationship("Vendor")
    purchase_order = relationship("PurchaseOrder")
    project = relationship("Project")
    shortage = relationship("MaterialShortage")


class MaterialAlternative(Base, TimestampMixin):
    """替代料关系表"""

    __tablename__ = "material_alternatives"
    __table_args__ = (
        Index("idx_alt_original", "original_material_id"),
        Index("idx_alt_alternative", "alternative_material_id"),
        {"extend_existing": True, "comment": "替代料关系表"},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)

    original_material_id = Column(
        Integer, ForeignKey("materials.id"), nullable=False, comment="原物料ID"
    )
    alternative_material_id = Column(
        Integer, ForeignKey("materials.id"), nullable=False, comment="替代物料ID"
    )

    # 替代信息
    match_score = Column(Numeric(5, 2), default=0, comment="匹配度评分(0-100)")
    match_reason = Column(Text, comment="匹配原因说明")
    is_verified = Column(Boolean, default=False, comment="是否经过验证")
    verified_by = Column(Integer, ForeignKey("users.id"), comment="验证人")
    verified_at = Column(DateTime, comment="验证时间")

    # 价格对比
    price_diff_pct = Column(Numeric(5, 2), comment="价格差异百分比")

    # ECN关联
    ecn_no = Column(String(50), comment="关联ECN编号")
    ecn_status = Column(String(20), comment="ECN状态")

    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    remark = Column(Text, comment="备注")

    # 关系
    original_material = relationship("Material", foreign_keys=[original_material_id])
    alternative_material = relationship("Material", foreign_keys=[alternative_material_id])
