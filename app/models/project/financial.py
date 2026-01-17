# -*- coding: utf-8 -*-
"""
项目财务模型 - ProjectMilestone, ProjectPaymentPlan, ProjectCost, FinancialProjectCost
"""

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

from ..base import Base, TimestampMixin


class ProjectMilestone(Base, TimestampMixin):
    """项目里程碑表"""

    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID（可选）")
    milestone_code = Column(String(50), nullable=False, comment="里程碑编码")
    milestone_name = Column(String(200), nullable=False, comment="里程碑名称")
    milestone_type = Column(
        String(20), default="CUSTOM", comment="GATE/DELIVERY/PAYMENT/CUSTOM"
    )

    # 时间
    planned_date = Column(Date, nullable=False, comment="计划日期")
    actual_date = Column(Date, comment="实际完成日期")
    reminder_days = Column(Integer, default=7, comment="提前提醒天数")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    is_key = Column(Boolean, default=False, comment="是否关键里程碑")

    # 关联
    stage_code = Column(String(20), comment="关联阶段")
    deliverables = Column(Text, comment="交付物JSON")

    owner_id = Column(Integer, ForeignKey("users.id"), comment="责任人")
    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", back_populates="milestones")

    __table_args__ = (
        Index("idx_project_milestones_project", "project_id"),
        Index("idx_project_milestones_status", "status"),
        Index("idx_project_milestones_date", "planned_date"),
    )

    def __repr__(self):
        return f"<ProjectMilestone {self.milestone_code}>"


class ProjectPaymentPlan(Base, TimestampMixin):
    """项目收款计划表"""

    __tablename__ = "project_payment_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    contract_id = Column(Integer, ForeignKey("contracts.id"), comment="合同ID")

    payment_no = Column(Integer, nullable=False, comment="期次")
    payment_name = Column(String(100), nullable=False, comment="款项名称")
    payment_type = Column(String(20), nullable=False, comment="款项类型：ADVANCE/DELIVERY/ACCEPTANCE/WARRANTY")

    # 金额
    payment_ratio = Column(Numeric(5, 2), comment="比例(%)")
    planned_amount = Column(Numeric(14, 2), nullable=False, comment="计划金额")
    actual_amount = Column(Numeric(14, 2), default=0, comment="实际收款")

    # 时间
    planned_date = Column(Date, comment="计划收款日期")
    actual_date = Column(Date, comment="实际收款日期")

    # 触发条件
    milestone_id = Column(Integer, ForeignKey("project_milestones.id"), comment="关联里程碑ID")
    trigger_milestone = Column(String(50), comment="触发里程碑名称")
    trigger_condition = Column(Text, comment="触发条件描述")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/INVOICED/PARTIAL/COMPLETED")

    # 发票信息
    invoice_id = Column(Integer, ForeignKey("invoices.id"), comment="关联发票ID")
    invoice_no = Column(String(100), comment="发票号")
    invoice_date = Column(Date, comment="开票日期")
    invoice_amount = Column(Numeric(14, 2), comment="开票金额")

    remark = Column(Text, comment="备注")

    # 关系
    project = relationship("Project", foreign_keys=[project_id])
    contract = relationship("Contract", foreign_keys=[contract_id])
    milestone = relationship("ProjectMilestone", foreign_keys=[milestone_id])
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    invoice_requests = relationship("InvoiceRequest", back_populates="payment_plan")

    __table_args__ = (
        Index("idx_payment_plans_project", "project_id"),
        Index("idx_payment_plans_contract", "contract_id"),
        Index("idx_payment_plans_milestone", "milestone_id"),
        Index("idx_payment_plans_status", "status"),
    )

    def __repr__(self):
        return f"<ProjectPaymentPlan {self.project_id}-{self.payment_no}>"


class ProjectCost(Base, TimestampMixin):
    """项目成本表"""

    __tablename__ = "project_costs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(
        Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")
    cost_type = Column(String(50), nullable=False, comment="成本类型")
    cost_category = Column(String(50), nullable=False, comment="成本分类")

    # 来源
    source_module = Column(String(50), comment="来源模块")
    source_type = Column(String(50), comment="来源类型")
    source_id = Column(Integer, comment="来源ID")
    source_no = Column(String(100), comment="来源单号")

    # 金额
    amount = Column(Numeric(14, 2), nullable=False, default=0, comment="金额")
    tax_amount = Column(Numeric(12, 2), default=0, comment="税额")

    # 时间
    cost_date = Column(Date, nullable=False, comment="发生日期")

    description = Column(Text, comment="描述")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")

    # 关系
    project = relationship("Project", back_populates="costs")
    machine = relationship("Machine")

    __table_args__ = (
        Index("idx_project_costs_project", "project_id"),
        Index("idx_project_costs_type", "cost_type"),
        Index("idx_project_costs_date", "cost_date"),
    )


class FinancialProjectCost(Base, TimestampMixin):
    """财务历史项目成本表（财务部维护的非物料成本）"""

    __tablename__ = "financial_project_costs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 项目关联
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, comment="项目ID")
    project_code = Column(String(50), comment="项目编号（冗余字段，便于查询）")
    project_name = Column(String(200), comment="项目名称（冗余字段，便于查询）")
    machine_id = Column(Integer, ForeignKey("machines.id"), comment="设备ID")

    # 成本类型和分类
    cost_type = Column(String(50), nullable=False, comment="成本类型：LABOR/TRAVEL/ENTERTAINMENT/OTHER")
    cost_category = Column(String(50), nullable=False, comment="成本分类：出差费/人工费/招待费/其他")
    cost_item = Column(String(200), comment="成本项名称")

    # 金额信息
    amount = Column(Numeric(14, 2), nullable=False, comment="金额")
    tax_amount = Column(Numeric(12, 2), default=0, comment="税额")
    currency = Column(String(10), default="CNY", comment="币种")

    # 时间信息
    cost_date = Column(Date, nullable=False, comment="发生日期")
    cost_month = Column(String(7), comment="成本月份(YYYY-MM)")

    # 详细信息
    description = Column(Text, comment="费用说明")
    location = Column(String(200), comment="地点（出差费用）")
    participants = Column(String(500), comment="参与人员（逗号分隔）")
    purpose = Column(String(500), comment="用途/目的")

    # 人工费用相关
    user_id = Column(Integer, ForeignKey("users.id"), comment="人员ID（人工费用）")
    user_name = Column(String(50), comment="人员姓名（冗余）")
    hours = Column(Numeric(10, 2), comment="工时（人工费用）")
    hourly_rate = Column(Numeric(10, 2), comment="时薪（人工费用）")

    # 来源信息
    source_type = Column(String(50), default="FINANCIAL_UPLOAD", comment="来源类型：FINANCIAL_UPLOAD（财务上传）")
    source_no = Column(String(100), comment="来源单号（如报销单号、发票号等）")
    invoice_no = Column(String(100), comment="发票号")

    # 上传信息
    upload_batch_no = Column(String(50), comment="上传批次号")
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传人ID（财务部）")

    # 状态
    is_verified = Column(Boolean, default=False, comment="是否已核实")
    verified_by = Column(Integer, ForeignKey("users.id"), comment="核实人ID")
    verified_at = Column(DateTime, comment="核实时间")

    # 关系
    project = relationship("Project", back_populates="financial_costs")
    machine = relationship("Machine")
    user = relationship("User", foreign_keys=[user_id])
    uploader = relationship("User", foreign_keys=[uploaded_by])
    verifier = relationship("User", foreign_keys=[verified_by])

    __table_args__ = (
        Index("idx_financial_cost_project", "project_id"),
        Index("idx_financial_cost_type", "cost_type"),
        Index("idx_financial_cost_category", "cost_category"),
        Index("idx_financial_cost_date", "cost_date"),
        Index("idx_financial_cost_month", "cost_month"),
        Index("idx_financial_cost_upload_batch", "upload_batch_no"),
        {"comment": "财务历史项目成本表"}
    )

    def __repr__(self):
        return f"<FinancialProjectCost {self.project_code}-{self.cost_type}>"
