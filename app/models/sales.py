# -*- coding: utf-8 -*-
"""
销售管理模块 ORM 模型
包含：线索、商机、报价、合同、发票、回款争议
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import (
    LeadStatusEnum, OpportunityStageEnum, GateStatusEnum,
    QuoteStatusEnum, ContractStatusEnum, InvoiceStatusEnum,
    InvoiceTypeEnum, QuoteItemTypeEnum, DisputeStatusEnum,
    DisputeReasonCodeEnum
)


class Lead(Base, TimestampMixin):
    """线索表"""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_code = Column(String(20), unique=True, nullable=False, comment="线索编码")
    source = Column(String(50), comment="来源")
    customer_name = Column(String(100), comment="客户名称")
    industry = Column(String(50), comment="行业")
    contact_name = Column(String(50), comment="联系人")
    contact_phone = Column(String(20), comment="联系电话")
    demand_summary = Column(Text, comment="需求摘要")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    status = Column(String(20), default=LeadStatusEnum.NEW, comment="状态")
    next_action_at = Column(DateTime, comment="下次行动时间")

    # 关系
    owner = relationship("User", foreign_keys=[owner_id])
    opportunities = relationship("Opportunity", back_populates="lead")
    follow_ups = relationship("LeadFollowUp", back_populates="lead", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Lead {self.lead_code}>"


class LeadFollowUp(Base, TimestampMixin):
    """线索跟进记录表"""

    __tablename__ = "lead_follow_ups"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, comment="线索ID")
    follow_up_type = Column(String(20), nullable=False, comment="跟进类型：CALL/EMAIL/VISIT/MEETING/OTHER")
    content = Column(Text, nullable=False, comment="跟进内容")
    next_action = Column(Text, comment="下一步行动")
    next_action_at = Column(DateTime, comment="下次行动时间")
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    attachments = Column(Text, comment="附件列表JSON")

    # 关系
    lead = relationship("Lead", back_populates="follow_ups")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_lead_follow_up_lead', 'lead_id'),
        Index('idx_lead_follow_up_created', 'created_at'),
    )

    def __repr__(self):
        return f"<LeadFollowUp {self.id}>"


class Opportunity(Base, TimestampMixin):
    """商机表"""

    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opp_code = Column(String(20), unique=True, nullable=False, comment="商机编码")
    lead_id = Column(Integer, ForeignKey("leads.id"), comment="线索ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    opp_name = Column(String(200), nullable=False, comment="商机名称")
    project_type = Column(String(20), comment="项目类型")
    equipment_type = Column(String(20), comment="设备类型")
    stage = Column(String(20), default=OpportunityStageEnum.DISCOVERY, comment="阶段")
    est_amount = Column(Numeric(12, 2), comment="预估金额")
    est_margin = Column(Numeric(5, 2), comment="预估毛利率")
    budget_range = Column(String(50), comment="预算范围")
    decision_chain = Column(Text, comment="决策链")
    delivery_window = Column(String(50), comment="交付窗口")
    acceptance_basis = Column(Text, comment="验收依据")
    score = Column(Integer, default=0, comment="评分")
    risk_level = Column(String(10), comment="风险等级")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    gate_status = Column(String(20), default=GateStatusEnum.PENDING, comment="阶段门状态")
    gate_passed_at = Column(DateTime, comment="阶段门通过时间")

    # 关系
    lead = relationship("Lead", back_populates="opportunities")
    customer = relationship("Customer", foreign_keys=[customer_id])
    owner = relationship("User", foreign_keys=[owner_id])
    requirements = relationship("OpportunityRequirement", back_populates="opportunity", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="opportunity")
    contracts = relationship("Contract", back_populates="opportunity")

    def __repr__(self):
        return f"<Opportunity {self.opp_code}>"


class OpportunityRequirement(Base, TimestampMixin):
    """商机需求结构化表"""

    __tablename__ = "opportunity_requirements"

    id = Column(Integer, primary_key=True, autoincrement=True)
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, comment="商机ID")
    product_object = Column(String(100), comment="产品对象")
    ct_seconds = Column(Integer, comment="节拍(秒)")
    interface_desc = Column(Text, comment="接口/通信协议")
    site_constraints = Column(Text, comment="现场约束")
    acceptance_criteria = Column(Text, comment="验收依据")
    safety_requirement = Column(Text, comment="安全要求")
    attachments = Column(Text, comment="需求附件")
    extra_json = Column(Text, comment="其他补充(JSON)")

    # 关系
    opportunity = relationship("Opportunity", back_populates="requirements")

    def __repr__(self):
        return f"<OpportunityRequirement {self.id}>"


class Quote(Base, TimestampMixin):
    """报价主表"""

    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_code = Column(String(20), unique=True, nullable=False, comment="报价编码")
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, comment="商机ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    status = Column(String(20), default=QuoteStatusEnum.DRAFT, comment="状态")
    current_version_id = Column(Integer, ForeignKey("quote_versions.id"), comment="当前版本ID")
    valid_until = Column(Date, comment="有效期至")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")

    # 关系
    opportunity = relationship("Opportunity", back_populates="quotes")
    customer = relationship("Customer", foreign_keys=[customer_id])
    owner = relationship("User", foreign_keys=[owner_id])
    versions = relationship("QuoteVersion", back_populates="quote", cascade="all, delete-orphan", foreign_keys="QuoteVersion.quote_id")
    current_version = relationship("QuoteVersion", foreign_keys=[current_version_id], post_update=True)

    def __repr__(self):
        return f"<Quote {self.quote_code}>"


class QuoteVersion(Base, TimestampMixin):
    """报价版本表"""

    __tablename__ = "quote_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价ID")
    version_no = Column(String(10), nullable=False, comment="版本号")
    total_price = Column(Numeric(12, 2), comment="总价")
    cost_total = Column(Numeric(12, 2), comment="成本总计")
    gross_margin = Column(Numeric(5, 2), comment="毛利率")
    lead_time_days = Column(Integer, comment="交期(天)")
    risk_terms = Column(Text, comment="风险条款")
    delivery_date = Column(Date, comment="交付日期")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")

    # 关系
    quote = relationship("Quote", back_populates="versions", foreign_keys=[quote_id])
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    items = relationship("QuoteItem", back_populates="quote_version", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="quote_version")

    def __repr__(self):
        return f"<QuoteVersion {self.quote_id}-{self.version_no}>"


class QuoteItem(Base):
    """报价明细表"""

    __tablename__ = "quote_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_version_id = Column(Integer, ForeignKey("quote_versions.id"), nullable=False, comment="报价版本ID")
    item_type = Column(String(20), comment="明细类型")
    item_name = Column(String(200), comment="明细名称")
    qty = Column(Numeric(10, 2), comment="数量")
    unit_price = Column(Numeric(12, 2), comment="单价")
    cost = Column(Numeric(12, 2), comment="成本")
    lead_time_days = Column(Integer, comment="交期(天)")
    remark = Column(Text, comment="备注")

    # 关系
    quote_version = relationship("QuoteVersion", back_populates="items")

    def __repr__(self):
        return f"<QuoteItem {self.id}>"


class Contract(Base, TimestampMixin):
    """合同主表"""

    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_code = Column(String(20), unique=True, nullable=False, comment="合同编码")
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), nullable=False, comment="商机ID")
    quote_version_id = Column(Integer, ForeignKey("quote_versions.id"), comment="报价版本ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    contract_amount = Column(Numeric(12, 2), comment="合同金额")
    signed_date = Column(Date, comment="签订日期")
    status = Column(String(20), default=ContractStatusEnum.DRAFT, comment="状态")
    payment_terms_summary = Column(Text, comment="付款条款摘要")
    acceptance_summary = Column(Text, comment="验收摘要")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")

    # 关系
    opportunity = relationship("Opportunity", back_populates="contracts")
    quote_version = relationship("QuoteVersion", back_populates="contracts")
    customer = relationship("Customer", foreign_keys=[customer_id])
    project = relationship("Project", foreign_keys=[project_id])
    owner = relationship("User", foreign_keys=[owner_id])
    deliverables = relationship("ContractDeliverable", back_populates="contract", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="contract")
    amendments = relationship("ContractAmendment", back_populates="contract", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Contract {self.contract_code}>"


class ContractDeliverable(Base, TimestampMixin):
    """合同交付物清单表"""

    __tablename__ = "contract_deliverables"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    deliverable_name = Column(String(100), comment="交付物名称")
    deliverable_type = Column(String(50), comment="交付物类型")
    required_for_payment = Column(Boolean, default=True, comment="是否付款必需")
    template_ref = Column(String(100), comment="模板引用")

    # 关系
    contract = relationship("Contract", back_populates="deliverables")

    def __repr__(self):
        return f"<ContractDeliverable {self.id}>"


class ContractAmendment(Base, TimestampMixin):
    """合同变更记录表"""

    __tablename__ = "contract_amendments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    amendment_no = Column(String(50), unique=True, nullable=False, comment="变更编号")
    amendment_type = Column(String(20), nullable=False, comment="变更类型：AMOUNT/DELIVERY_DATE/TERMS/OTHER")
    title = Column(String(200), nullable=False, comment="变更标题")
    description = Column(Text, nullable=False, comment="变更描述")
    reason = Column(Text, comment="变更原因")
    
    # 变更内容（JSON格式存储变更前后的值）
    old_value = Column(Text, comment="原值（JSON）")
    new_value = Column(Text, comment="新值（JSON）")
    
    # 影响评估
    amount_change = Column(Numeric(12, 2), comment="金额变化")
    schedule_impact = Column(Text, comment="进度影响")
    other_impact = Column(Text, comment="其他影响")
    
    # 申请人
    requestor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    request_date = Column(Date, nullable=False, comment="申请日期")
    
    # 审批状态
    status = Column(String(20), default="PENDING", comment="状态：PENDING/APPROVED/REJECTED")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approval_date = Column(Date, comment="审批日期")
    approval_comment = Column(Text, comment="审批意见")
    
    # 附件
    attachments = Column(Text, comment="附件列表JSON")

    # 关系
    contract = relationship("Contract", back_populates="amendments")
    requestor = relationship("User", foreign_keys=[requestor_id])
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index('idx_contract_amendment_contract', 'contract_id'),
        Index('idx_contract_amendment_status', 'status'),
        Index('idx_contract_amendment_date', 'request_date'),
    )

    def __repr__(self):
        return f"<ContractAmendment {self.amendment_no}>"


class Invoice(Base, TimestampMixin):
    """发票表"""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_code = Column(String(30), unique=True, nullable=False, comment="发票编码")
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    payment_id = Column(Integer, ForeignKey("payments.id"), comment="关联应收节点ID")
    invoice_type = Column(String(20), comment="发票类型")
    amount = Column(Numeric(12, 2), comment="金额")
    tax_rate = Column(Numeric(5, 2), comment="税率")
    tax_amount = Column(Numeric(12, 2), comment="税额")
    total_amount = Column(Numeric(12, 2), comment="含税总额")
    status = Column(String(20), default=InvoiceStatusEnum.DRAFT, comment="状态")
    payment_status = Column(String(20), comment="收款状态")
    issue_date = Column(Date, comment="开票日期")
    due_date = Column(Date, comment="到期日期")
    paid_amount = Column(Numeric(12, 2), default=0, comment="已收款金额")
    paid_date = Column(Date, comment="收款日期")
    buyer_name = Column(String(100), comment="购买方名称")
    buyer_tax_no = Column(String(30), comment="购买方税号")
    remark = Column(Text, comment="备注")

    # 关系
    contract = relationship("Contract", back_populates="invoices")
    project = relationship("Project", foreign_keys=[project_id])
    # payment 关系暂时注释，等待 Payment 模型定义
    # payment = relationship("Payment", foreign_keys=[payment_id])

    def __repr__(self):
        return f"<Invoice {self.invoice_code}>"


class ReceivableDispute(Base, TimestampMixin):
    """回款争议/卡点表"""

    __tablename__ = "receivable_disputes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, comment="付款节点ID")
    reason_code = Column(String(30), comment="原因代码")
    description = Column(Text, comment="描述")
    status = Column(String(20), default=DisputeStatusEnum.OPEN, comment="状态")
    responsible_dept = Column(String(50), comment="责任部门")
    responsible_id = Column(Integer, ForeignKey("users.id"), comment="责任人ID")
    expect_resolve_date = Column(Date, comment="预期解决日期")

    # 关系
    # payment 关系暂时注释，等待 Payment 模型定义
    # payment = relationship("Payment", foreign_keys=[payment_id])
    responsible = relationship("User", foreign_keys=[responsible_id])

    def __repr__(self):
        return f"<ReceivableDispute {self.id}>"


class QuoteApproval(Base, TimestampMixin):
    """报价审批表"""

    __tablename__ = "quote_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价ID")
    approval_level = Column(Integer, nullable=False, comment="审批层级")
    approval_role = Column(String(50), nullable=False, comment="审批角色")

    # 审批人
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")

    # 审批结果
    approval_result = Column(String(20), comment="审批结果")
    approval_opinion = Column(Text, comment="审批意见")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    approved_at = Column(DateTime, comment="审批时间")

    # 超时
    due_date = Column(DateTime, comment="审批期限")
    is_overdue = Column(Boolean, default=False, comment="是否超期")

    # 关系
    quote = relationship("Quote", foreign_keys=[quote_id])
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_quote_approval_quote", "quote_id"),
        Index("idx_quote_approval_approver", "approver_id"),
        Index("idx_quote_approval_status", "status"),
    )

    def __repr__(self):
        return f"<QuoteApproval {self.quote_id}-L{self.approval_level}>"


class ContractApproval(Base, TimestampMixin):
    """合同审批表"""

    __tablename__ = "contract_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    approval_level = Column(Integer, nullable=False, comment="审批层级")
    approval_role = Column(String(50), nullable=False, comment="审批角色")

    # 审批人
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")

    # 审批结果
    approval_result = Column(String(20), comment="审批结果")
    approval_opinion = Column(Text, comment="审批意见")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    approved_at = Column(DateTime, comment="审批时间")

    # 超时
    due_date = Column(DateTime, comment="审批期限")
    is_overdue = Column(Boolean, default=False, comment="是否超期")

    # 关系
    contract = relationship("Contract", foreign_keys=[contract_id])
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_contract_approval_contract", "contract_id"),
        Index("idx_contract_approval_approver", "approver_id"),
        Index("idx_contract_approval_status", "status"),
    )

    def __repr__(self):
        return f"<ContractApproval {self.contract_id}-L{self.approval_level}>"


class InvoiceApproval(Base, TimestampMixin):
    """发票审批表"""

    __tablename__ = "invoice_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, comment="发票ID")
    approval_level = Column(Integer, nullable=False, comment="审批层级")
    approval_role = Column(String(50), nullable=False, comment="审批角色")

    # 审批人
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")

    # 审批结果
    approval_result = Column(String(20), comment="审批结果")
    approval_opinion = Column(Text, comment="审批意见")

    # 状态
    status = Column(String(20), default="PENDING", comment="状态")
    approved_at = Column(DateTime, comment="审批时间")

    # 超时
    due_date = Column(DateTime, comment="审批期限")
    is_overdue = Column(Boolean, default=False, comment="是否超期")

    # 关系
    invoice = relationship("Invoice", foreign_keys=[invoice_id])
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_invoice_approval_invoice", "invoice_id"),
        Index("idx_invoice_approval_approver", "approver_id"),
        Index("idx_invoice_approval_status", "status"),
    )

    def __repr__(self):
        return f"<InvoiceApproval {self.invoice_id}-L{self.approval_level}>"

