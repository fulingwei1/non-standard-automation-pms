# -*- coding: utf-8 -*-
"""
成本分解模型

提供项目成本的详细分类和汇总，支持非标自动化测试设备行业的成本管理
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class CostCategoryEnum(str, Enum):
    """成本类别枚举"""

    MECHANICAL = "MECHANICAL"  # 机械结构（机架、工装、气缸等）
    ELECTRICAL = "ELECTRICAL"  # 电气元件（PLC、传感器、线缆等）
    SOFTWARE = "SOFTWARE"  # 软件开发（测试程序、上位机等）
    OUTSOURCE = "OUTSOURCE"  # 外协加工（钣金、机加工等）
    LABOR = "LABOR"  # 人工成本


class CostSourceEnum(str, Enum):
    """成本来源枚举"""

    BOM = "BOM"  # 来自 BOM 明细
    OUTSOURCE = "OUTSOURCE"  # 外协订单
    LABOR = "LABOR"  # 人工录入
    PURCHASE = "PURCHASE"  # 采购订单
    ESTIMATE = "ESTIMATE"  # 估算
    OTHER = "OTHER"  # 其他


class CostBreakdown(Base, TimestampMixin):
    """
    项目成本分解明细

    用于记录项目的各类成本明细，支持：
    1. 按成本类别（机械、电气、软件、外协、人工）分类
    2. 关联 BOM 明细、采购订单、外协订单等来源
    3. 支持预估成本与实际成本对比
    """

    __tablename__ = "cost_breakdowns"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="机台ID")
    bom_item_id = Column(Integer, ForeignKey("bom_items.id"), comment="BOM明细ID")

    # 成本分类
    cost_category = Column(String(50), nullable=False, comment="成本类别")
    cost_subcategory = Column(String(100), comment="成本子类别")

    # 成本来源
    source_type = Column(String(50), default="BOM", comment="成本来源类型")
    source_id = Column(Integer, comment="来源记录ID（BOM ID/采购订单ID等）")
    source_ref = Column(String(100), comment="来源单据编号")

    # 成本项信息
    item_name = Column(String(200), nullable=False, comment="成本项名称")
    item_code = Column(String(100), comment="成本项编码")
    specification = Column(String(500), comment="规格型号")
    unit = Column(String(20), default="件", comment="单位")

    # 数量和金额
    quantity = Column(Numeric(10, 4), default=1, comment="数量")
    unit_price = Column(Numeric(12, 4), default=0, comment="单价")
    estimated_amount = Column(Numeric(14, 2), default=0, comment="预估金额")
    actual_amount = Column(Numeric(14, 2), default=0, comment="实际金额")
    variance_amount = Column(Numeric(14, 2), default=0, comment="差异金额")

    # 供应商信息
    supplier_id = Column(Integer, ForeignKey("vendors.id"), comment="供应商ID")
    supplier_name = Column(String(200), comment="供应商名称")

    # 状态
    is_confirmed = Column(Boolean, default=False, comment="是否已确认")
    confirmed_by = Column(Integer, ForeignKey("users.id"), comment="确认人ID")
    confirmed_at = Column(DateTime, comment="确认时间")

    # 备注
    remark = Column(Text, comment="备注")

    # 审计
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    machine = relationship("Machine", foreign_keys=[machine_id])
    bom_item = relationship("BomItem", foreign_keys=[bom_item_id])

    __table_args__ = (
        Index("idx_cost_breakdown_project", "project_id"),
        Index("idx_cost_breakdown_machine", "machine_id"),
        Index("idx_cost_breakdown_category", "cost_category"),
        Index("idx_cost_breakdown_source", "source_type", "source_id"),
        {"comment": "项目成本分解明细表"},
    )

    def __repr__(self):
        return f"<CostBreakdown {self.project_id}: {self.item_name}>"


class ProjectCostSummary(Base, TimestampMixin):
    """
    项目成本汇总

    按成本类别汇总项目的预估成本、实际成本和差异
    """

    __tablename__ = "project_cost_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 关联信息
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")

    # 成本类别
    cost_category = Column(String(50), nullable=False, comment="成本类别")

    # 金额汇总
    estimated_amount = Column(Numeric(14, 2), default=0, comment="预估金额")
    actual_amount = Column(Numeric(14, 2), default=0, comment="实际金额")
    variance_amount = Column(Numeric(14, 2), default=0, comment="差异金额")
    variance_ratio = Column(Numeric(5, 2), default=0, comment="差异率(%)")

    # 占比
    estimated_ratio = Column(Numeric(5, 2), default=0, comment="预估占比(%)")
    actual_ratio = Column(Numeric(5, 2), default=0, comment="实际占比(%)")

    # 明细统计
    item_count = Column(Integer, default=0, comment="成本项数量")
    confirmed_count = Column(Integer, default=0, comment="已确认数量")

    # 最后计算时间
    calculated_at = Column(DateTime, default=datetime.now, comment="计算时间")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])

    __table_args__ = (
        Index("idx_cost_summary_project", "project_id"),
        Index("idx_cost_summary_category", "cost_category"),
        Index("idx_cost_summary_unique", "project_id", "cost_category", unique=True),
        {"comment": "项目成本汇总表"},
    )

    def __repr__(self):
        return f"<ProjectCostSummary {self.project_id}: {self.cost_category}>"
