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
    DisputeReasonCodeEnum,
    AssessmentSourceTypeEnum, AssessmentStatusEnum, AssessmentDecisionEnum,
    FreezeTypeEnum, OpenItemTypeEnum, OpenItemStatusEnum, ResponsiblePartyEnum,
    WorkflowTypeEnum, ApprovalRecordStatusEnum, ApprovalActionEnum
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

    # 技术评估扩展字段
    requirement_detail_id = Column(Integer, ForeignKey("lead_requirement_details.id"), comment="需求详情ID")
    assessment_id = Column(Integer, ForeignKey("technical_assessments.id"), comment="技术评估ID")
    completeness = Column(Integer, default=0, comment="完整度(0-100)")
    assignee_id = Column(Integer, ForeignKey("users.id"), comment="被指派的售前工程师ID")
    assessment_status = Column(String(20), comment="技术评估状态")

    # 关系
    owner = relationship("User", foreign_keys=[owner_id])
    opportunities = relationship("Opportunity", back_populates="lead")
    follow_ups = relationship("LeadFollowUp", back_populates="lead", cascade="all, delete-orphan")
    requirement_detail = relationship("LeadRequirementDetail", foreign_keys=[requirement_detail_id], uselist=False)
    assessment = relationship("TechnicalAssessment", foreign_keys=[assessment_id], uselist=False)
    assignee = relationship("User", foreign_keys=[assignee_id])

    __table_args__ = (
        Index('idx_lead_assessment', 'assessment_id'),
        Index('idx_lead_assignee', 'assignee_id'),
    )

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

    # 技术评估扩展字段
    assessment_id = Column(Integer, ForeignKey("technical_assessments.id"), comment="技术评估ID")
    requirement_maturity = Column(Integer, comment="需求成熟度(1-5)")
    assessment_status = Column(String(20), comment="技术评估状态")

    # 关系
    lead = relationship("Lead", back_populates="opportunities")
    customer = relationship("Customer", foreign_keys=[customer_id])
    owner = relationship("User", foreign_keys=[owner_id])
    requirements = relationship("OpportunityRequirement", back_populates="opportunity", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="opportunity")
    contracts = relationship("Contract", back_populates="opportunity")
    assessment = relationship("TechnicalAssessment", foreign_keys=[assessment_id], uselist=False)

    __table_args__ = (
        Index('idx_opportunity_assessment', 'assessment_id'),
    )

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
    
    # 成本管理扩展字段
    cost_template_id = Column(Integer, ForeignKey("quote_cost_templates.id"), comment="使用的成本模板ID")
    cost_breakdown_complete = Column(Boolean, default=False, comment="成本拆解是否完整")
    margin_warning = Column(Boolean, default=False, comment="毛利率预警标志")

    # 关系
    quote = relationship("Quote", back_populates="versions", foreign_keys=[quote_id])
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    items = relationship("QuoteItem", back_populates="quote_version", cascade="all, delete-orphan")
    contracts = relationship("Contract", back_populates="quote_version")
    cost_template = relationship("QuoteCostTemplate", foreign_keys=[cost_template_id])
    cost_approvals = relationship("QuoteCostApproval", back_populates="quote_version", foreign_keys="QuoteCostApproval.quote_version_id")
    cost_histories = relationship("QuoteCostHistory", back_populates="quote_version", foreign_keys="QuoteCostHistory.quote_version_id")

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
    
    # 成本管理扩展字段
    cost_category = Column(String(50), comment="成本分类")
    cost_source = Column(String(50), comment="成本来源：TEMPLATE/MANUAL/HISTORY")
    specification = Column(Text, comment="规格型号")
    unit = Column(String(20), comment="单位")

    # 关系
    quote_version = relationship("QuoteVersion", back_populates="items")

    def __repr__(self):
        return f"<QuoteItem {self.id}>"


# ==================== 报价成本管理 ====================

class QuoteCostTemplate(Base, TimestampMixin):
    """报价成本模板表"""
    
    __tablename__ = "quote_cost_templates"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    template_type = Column(String(50), comment="模板类型：STANDARD/CUSTOM/PROJECT")
    equipment_type = Column(String(50), comment="适用设备类型")
    industry = Column(String(50), comment="适用行业")
    
    # 模板内容（JSON格式）
    cost_structure = Column(JSON, comment="成本结构（分类、明细项、默认值）")
    
    # 统计信息
    total_cost = Column(Numeric(12, 2), comment="模板总成本")
    cost_categories = Column(Text, comment="成本分类（逗号分隔）")
    
    # 元数据
    description = Column(Text, comment="模板说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    usage_count = Column(Integer, default=0, comment="使用次数")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index("idx_template_type", "template_type"),
        Index("idx_equipment_type", "equipment_type"),
        Index("idx_is_active", "is_active"),
        {"comment": "报价成本模板表"}
    )
    
    def __repr__(self):
        return f"<QuoteCostTemplate {self.template_code}>"


class QuoteCostApproval(Base, TimestampMixin):
    """报价成本审批表"""
    
    __tablename__ = "quote_cost_approvals"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价ID")
    quote_version_id = Column(Integer, ForeignKey("quote_versions.id"), nullable=False, comment="报价版本ID")
    
    # 审批信息
    approval_status = Column(String(20), default="PENDING", comment="审批状态：PENDING/APPROVED/REJECTED")
    approval_level = Column(Integer, default=1, comment="审批层级（1=销售经理，2=销售总监，3=财务）")
    current_approver_id = Column(Integer, ForeignKey("users.id"), comment="当前审批人ID")
    
    # 成本检查结果
    total_price = Column(Numeric(12, 2), comment="总价")
    total_cost = Column(Numeric(12, 2), comment="总成本")
    gross_margin = Column(Numeric(5, 2), comment="毛利率")
    margin_threshold = Column(Numeric(5, 2), default=20.00, comment="毛利率阈值")
    margin_status = Column(String(20), comment="毛利率状态：PASS/WARNING/FAIL")
    
    # 检查项
    cost_complete = Column(Boolean, default=False, comment="成本拆解是否完整")
    delivery_check = Column(Boolean, default=False, comment="交期校验是否通过")
    risk_terms_check = Column(Boolean, default=False, comment="风险条款是否检查")
    
    # 审批记录
    approval_comment = Column(Text, comment="审批意见")
    approved_by = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approved_at = Column(DateTime, comment="审批时间")
    rejected_reason = Column(Text, comment="驳回原因")
    
    # 关系
    quote = relationship("Quote", foreign_keys=[quote_id])
    quote_version = relationship("QuoteVersion", foreign_keys=[quote_version_id])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
    approver = relationship("User", foreign_keys=[approved_by])
    
    __table_args__ = (
        Index("idx_quote_id", "quote_id"),
        Index("idx_approval_status", "approval_status"),
        {"comment": "报价成本审批表"}
    )
    
    def __repr__(self):
        return f"<QuoteCostApproval {self.quote_id}-{self.approval_level}>"


class QuoteCostHistory(Base):
    """报价成本历史记录表"""
    
    __tablename__ = "quote_cost_histories"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False, comment="报价ID")
    quote_version_id = Column(Integer, ForeignKey("quote_versions.id"), nullable=False, comment="报价版本ID")
    
    # 成本快照
    total_price = Column(Numeric(12, 2), comment="总价")
    total_cost = Column(Numeric(12, 2), comment="总成本")
    gross_margin = Column(Numeric(5, 2), comment="毛利率")
    
    # 成本明细快照（JSON）
    cost_breakdown = Column(JSON, comment="成本拆解明细")
    
    # 变更信息
    change_type = Column(String(50), comment="变更类型：CREATE/UPDATE/DELETE/APPROVE")
    change_reason = Column(Text, comment="变更原因")
    changed_by = Column(Integer, ForeignKey("users.id"), comment="变更人ID")
    
    created_at = Column(DateTime, default=datetime.now, nullable=False, comment="创建时间")
    
    # 关系
    quote = relationship("Quote", foreign_keys=[quote_id])
    quote_version = relationship("QuoteVersion", foreign_keys=[quote_version_id])
    changer = relationship("User", foreign_keys=[changed_by])
    
    __table_args__ = (
        Index("idx_quote_id", "quote_id"),
        Index("idx_created_at", "created_at"),
        {"comment": "报价成本历史记录表"}
    )
    
    def __repr__(self):
        return f"<QuoteCostHistory {self.quote_id}-{self.change_type}>"


class PurchaseMaterialCost(Base, TimestampMixin):
    """采购物料成本清单表（采购部维护的标准件成本信息）"""
    
    __tablename__ = "purchase_material_costs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 物料信息
    material_code = Column(String(50), comment="物料编码")
    material_name = Column(String(200), nullable=False, comment="物料名称")
    specification = Column(String(500), comment="规格型号")
    brand = Column(String(100), comment="品牌")
    unit = Column(String(20), default="件", comment="单位")
    
    # 物料类型
    material_type = Column(String(50), comment="物料类型：标准件/电气件/机械件等")
    is_standard_part = Column(Boolean, default=True, comment="是否标准件")
    
    # 成本信息
    unit_cost = Column(Numeric(12, 4), nullable=False, comment="单位成本")
    currency = Column(String(10), default="CNY", comment="币种")
    
    # 供应商信息
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), comment="供应商ID")
    supplier_name = Column(String(200), comment="供应商名称")
    
    # 采购信息
    purchase_date = Column(Date, comment="采购日期")
    purchase_order_no = Column(String(50), comment="采购订单号")
    purchase_quantity = Column(Numeric(10, 4), comment="采购数量")
    
    # 交期信息
    lead_time_days = Column(Integer, comment="交期(天)")
    
    # 匹配相关
    is_active = Column(Boolean, default=True, comment="是否启用（用于自动匹配）")
    match_priority = Column(Integer, default=0, comment="匹配优先级（数字越大优先级越高）")
    match_keywords = Column(Text, comment="匹配关键词（逗号分隔，用于模糊匹配）")
    
    # 统计信息
    usage_count = Column(Integer, default=0, comment="使用次数（被匹配次数）")
    last_used_at = Column(DateTime, comment="最后使用时间")
    
    # 备注
    remark = Column(Text, comment="备注")
    submitted_by = Column(Integer, ForeignKey("users.id"), comment="提交人ID（采购部）")
    
    # 关系
    supplier = relationship("Supplier", foreign_keys=[supplier_id])
    submitter = relationship("User", foreign_keys=[submitted_by])
    
    __table_args__ = (
        Index("idx_material_code", "material_code"),
        Index("idx_material_name", "material_name"),
        Index("idx_material_type", "material_type"),
        Index("idx_is_standard", "is_standard_part"),
        Index("idx_is_active", "is_active"),
        Index("idx_match_priority", "match_priority"),
        {"comment": "采购物料成本清单表"}
    )
    
    def __repr__(self):
        return f"<PurchaseMaterialCost {self.material_name}>"


class MaterialCostUpdateReminder(Base, TimestampMixin):
    """物料成本更新提醒表"""
    
    __tablename__ = "material_cost_update_reminders"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 提醒配置
    reminder_type = Column(String(50), default="PERIODIC", comment="提醒类型：PERIODIC（定期）/MANUAL（手动）")
    reminder_interval_days = Column(Integer, default=30, comment="提醒间隔（天），默认30天")
    
    # 提醒状态
    last_reminder_date = Column(Date, comment="最后提醒日期")
    next_reminder_date = Column(Date, comment="下次提醒日期")
    is_enabled = Column(Boolean, default=True, comment="是否启用提醒")
    
    # 提醒范围
    material_type_filter = Column(String(50), comment="物料类型筛选（为空表示全部）")
    include_standard = Column(Boolean, default=True, comment="包含标准件")
    include_non_standard = Column(Boolean, default=True, comment="包含非标准件")
    
    # 提醒对象
    notify_roles = Column(JSON, comment="通知角色列表（JSON数组）")
    notify_users = Column(JSON, comment="通知用户ID列表（JSON数组）")
    
    # 统计信息
    reminder_count = Column(Integer, default=0, comment="提醒次数")
    last_updated_by = Column(Integer, ForeignKey("users.id"), comment="最后更新人ID")
    last_updated_at = Column(DateTime, comment="最后更新时间")
    
    # 关系
    updater = relationship("User", foreign_keys=[last_updated_by])
    
    __table_args__ = (
        Index("idx_reminder_type", "reminder_type"),
        Index("idx_next_reminder_date", "next_reminder_date"),
        Index("idx_is_enabled", "is_enabled"),
        {"comment": "物料成本更新提醒表"}
    )
    
    def __repr__(self):
        return f"<MaterialCostUpdateReminder {self.reminder_type}>"


class CpqRuleSet(Base, TimestampMixin):
    """CPQ 规则集"""

    __tablename__ = "cpq_rule_sets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(50), unique=True, nullable=False, comment="规则集编码")
    rule_name = Column(String(200), nullable=False, comment="规则集名称")
    description = Column(Text, comment="描述")
    status = Column(String(20), default="ACTIVE", comment="状态")
    base_price = Column(Numeric(14, 2), default=0, comment="基准价格")
    currency = Column(String(10), default="CNY", comment="币种")
    config_schema = Column(JSON, comment="配置项定义")
    pricing_matrix = Column(JSON, comment="价格矩阵")
    approval_threshold = Column(JSON, comment="审批阈值配置")
    visibility_scope = Column(String(30), default="ALL", comment="可见范围")
    is_default = Column(Boolean, default=False, comment="是否默认")
    owner_role = Column(String(50), comment="负责角色")

    # 关系
    quote_template_versions = relationship("QuoteTemplateVersion", back_populates="rule_set")

    __table_args__ = (
        Index("idx_cpq_rule_set_status", "status"),
        Index("idx_cpq_rule_set_default", "is_default"),
    )

    def __repr__(self):
        return f"<CpqRuleSet {self.rule_code}>"


class QuoteTemplate(Base, TimestampMixin):
    """报价模板"""

    __tablename__ = "quote_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    category = Column(String(50), comment="模板分类")
    description = Column(Text, comment="描述")
    status = Column(String(20), default="DRAFT", comment="状态")
    visibility_scope = Column(String(30), default="TEAM", comment="可见范围")
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    current_version_id = Column(Integer, ForeignKey("quote_template_versions.id"), comment="当前版本ID")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")

    # 关系
    versions = relationship(
        "QuoteTemplateVersion",
        back_populates="template",
        cascade="all, delete-orphan",
        foreign_keys="QuoteTemplateVersion.template_id",
    )
    current_version = relationship("QuoteTemplateVersion", foreign_keys=[current_version_id], post_update=True, uselist=False)
    owner = relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_quote_template_status", "status"),
        Index("idx_quote_template_scope", "visibility_scope"),
    )

    def __repr__(self):
        return f"<QuoteTemplate {self.template_code}>"


class QuoteTemplateVersion(Base, TimestampMixin):
    """报价模板版本"""

    __tablename__ = "quote_template_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("quote_templates.id"), nullable=False, comment="模板ID")
    version_no = Column(String(20), nullable=False, comment="版本号")
    status = Column(String(20), default="DRAFT", comment="状态")
    sections = Column(JSON, comment="模板结构配置")
    pricing_rules = Column(JSON, comment="价格规则")
    config_schema = Column(JSON, comment="配置项定义")
    discount_rules = Column(JSON, comment="折扣规则")
    release_notes = Column(Text, comment="版本说明")
    rule_set_id = Column(Integer, ForeignKey("cpq_rule_sets.id"), comment="关联规则集")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    published_by = Column(Integer, ForeignKey("users.id"), comment="发布人")
    published_at = Column(DateTime, comment="发布时间")

    # 关系
    template = relationship("QuoteTemplate", back_populates="versions", foreign_keys=[template_id])
    rule_set = relationship("CpqRuleSet", back_populates="quote_template_versions")
    creator = relationship("User", foreign_keys=[created_by], backref="quote_template_versions_created")
    publisher = relationship("User", foreign_keys=[published_by], backref="quote_template_versions_published")

    __table_args__ = (
        Index("idx_quote_template_version_template", "template_id"),
        Index("idx_quote_template_version_status", "status"),
    )

    def __repr__(self):
        return f"<QuoteTemplateVersion {self.template_id}-{self.version_no}>"


class ContractTemplate(Base, TimestampMixin):
    """合同模板"""

    __tablename__ = "contract_templates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment="模板编码")
    template_name = Column(String(200), nullable=False, comment="模板名称")
    contract_type = Column(String(50), comment="合同类型")
    description = Column(Text, comment="描述")
    status = Column(String(20), default="DRAFT", comment="状态")
    visibility_scope = Column(String(30), default="TEAM", comment="可见范围")
    is_default = Column(Boolean, default=False, comment="是否默认模板")
    current_version_id = Column(Integer, ForeignKey("contract_template_versions.id"), comment="当前版本ID")
    owner_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")

    # 关系
    versions = relationship(
        "ContractTemplateVersion",
        back_populates="template",
        cascade="all, delete-orphan",
        foreign_keys="ContractTemplateVersion.template_id",
    )
    current_version = relationship("ContractTemplateVersion", foreign_keys=[current_version_id], post_update=True, uselist=False)
    owner = relationship("User", foreign_keys=[owner_id])

    __table_args__ = (
        Index("idx_contract_template_status", "status"),
        Index("idx_contract_template_scope", "visibility_scope"),
    )

    def __repr__(self):
        return f"<ContractTemplate {self.template_code}>"


class ContractTemplateVersion(Base, TimestampMixin):
    """合同模板版本"""

    __tablename__ = "contract_template_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_id = Column(Integer, ForeignKey("contract_templates.id"), nullable=False, comment="模板ID")
    version_no = Column(String(20), nullable=False, comment="版本号")
    status = Column(String(20), default="DRAFT", comment="状态")
    clause_sections = Column(JSON, comment="条款结构")
    clause_library = Column(JSON, comment="条款库引用")
    attachment_refs = Column(JSON, comment="附件引用")
    approval_flow = Column(JSON, comment="审批流配置")
    release_notes = Column(Text, comment="版本说明")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人")
    published_by = Column(Integer, ForeignKey("users.id"), comment="发布人")
    published_at = Column(DateTime, comment="发布时间")

    # 关系
    template = relationship("ContractTemplate", back_populates="versions", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by], backref="contract_template_versions_created")
    publisher = relationship("User", foreign_keys=[published_by], backref="contract_template_versions_published")

    __table_args__ = (
        Index("idx_contract_template_version_template", "template_id"),
        Index("idx_contract_template_version_status", "status"),
    )

    def __repr__(self):
        return f"<ContractTemplateVersion {self.template_id}-{self.version_no}>"


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
    payment_id = Column(Integer, ForeignKey("project_payment_plans.id"), comment="关联应收节点ID")
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
    payment_id = Column(Integer, ForeignKey("project_payment_plans.id"), nullable=False, comment="付款节点ID")
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


# ==================== 技术评估相关 ====================

class TechnicalAssessment(Base, TimestampMixin):
    """技术评估结果表"""
    
    __tablename__ = "technical_assessments"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 关联来源（支持线索和商机）
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID（Lead.id 或 Opportunity.id）")
    
    # 评估信息
    evaluator_id = Column(Integer, ForeignKey("users.id"), comment="评估人ID（技术工程师）")
    status = Column(String(20), default=AssessmentStatusEnum.PENDING, comment="评估状态")
    
    # 评分结果
    total_score = Column(Integer, comment="总分")
    dimension_scores = Column(Text, comment="五维分数详情(JSON)")
    veto_triggered = Column(Boolean, default=False, comment="是否触发一票否决")
    veto_rules = Column(Text, comment="触发的否决规则(JSON)")
    
    # 决策建议
    decision = Column(String(30), comment="决策建议：推荐立项/有条件立项/暂缓/不建议立项")
    risks = Column(Text, comment="风险列表(JSON)")
    similar_cases = Column(Text, comment="相似失败案例(JSON)")
    ai_analysis = Column(Text, comment="AI分析报告")
    conditions = Column(Text, comment="立项条件(JSON)")
    
    # 评估时间
    evaluated_at = Column(DateTime, comment="评估完成时间")
    
    # 关系
    evaluator = relationship("User", foreign_keys=[evaluator_id])
    
    __table_args__ = (
        Index('idx_assessment_source', 'source_type', 'source_id'),
        Index('idx_assessment_status', 'status'),
        Index('idx_assessment_evaluator', 'evaluator_id'),
        Index('idx_assessment_decision', 'decision'),
    )
    
    def __repr__(self):
        return f"<TechnicalAssessment {self.id}>"


class ScoringRule(Base, TimestampMixin):
    """评分规则配置表"""
    
    __tablename__ = "scoring_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    version = Column(String(20), unique=True, nullable=False, comment="版本号")
    rules_json = Column(Text, nullable=False, comment="完整规则配置(JSON)")
    is_active = Column(Boolean, default=False, comment="是否启用")
    description = Column(Text, comment="描述")
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index('idx_scoring_rule_active', 'is_active'),
        Index('idx_scoring_rule_version', 'version'),
    )
    
    def __repr__(self):
        return f"<ScoringRule {self.version}>"


class FailureCase(Base, TimestampMixin):
    """失败案例库表"""
    
    __tablename__ = "failure_cases"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    case_code = Column(String(50), unique=True, nullable=False, comment="案例编号")
    project_name = Column(String(200), nullable=False, comment="项目名称")
    industry = Column(String(50), nullable=False, comment="行业")
    product_types = Column(Text, comment="产品类型(JSON Array)")
    processes = Column(Text, comment="工序/测试类型(JSON Array)")
    takt_time_s = Column(Integer, comment="节拍时间(秒)")
    annual_volume = Column(Integer, comment="年产量")
    budget_status = Column(String(50), comment="预算状态")
    customer_project_status = Column(String(50), comment="客户项目状态")
    spec_status = Column(String(50), comment="规范状态")
    price_sensitivity = Column(String(50), comment="价格敏感度")
    delivery_months = Column(Integer, comment="交付周期(月)")
    
    failure_tags = Column(Text, nullable=False, comment="失败标签(JSON Array)")
    core_failure_reason = Column(Text, nullable=False, comment="核心失败原因")
    early_warning_signals = Column(Text, nullable=False, comment="预警信号(JSON Array)")
    final_result = Column(String(100), comment="最终结果")
    lesson_learned = Column(Text, nullable=False, comment="教训总结")
    keywords = Column(Text, nullable=False, comment="关键词(JSON Array)")
    
    created_by = Column(Integer, ForeignKey("users.id"), comment="创建人ID")
    
    # 关系
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index('idx_failure_case_industry', 'industry'),
        Index('idx_failure_case_code', 'case_code'),
    )
    
    def __repr__(self):
        return f"<FailureCase {self.case_code}>"


class LeadRequirementDetail(Base, TimestampMixin):
    """线索需求详情表"""
    
    __tablename__ = "lead_requirement_details"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, comment="线索ID")
    
    # 基础信息扩展
    customer_factory_location = Column(String(200), comment="客户工厂/地点")
    target_object_type = Column(String(100), comment="被测对象类型")
    application_scenario = Column(String(100), comment="应用场景")
    delivery_mode = Column(String(100), comment="计划交付模式")
    expected_delivery_date = Column(DateTime, comment="期望交付日期")
    requirement_source = Column(String(100), comment="需求来源")
    participant_ids = Column(Text, comment="参与人员(JSON Array)")
    
    # 需求成熟度与关键约束
    requirement_maturity = Column(Integer, comment="需求成熟度(1-5级)")
    has_sow = Column(Boolean, comment="是否有客户SOW/URS")
    has_interface_doc = Column(Boolean, comment="是否有接口协议文档")
    has_drawing_doc = Column(Boolean, comment="是否有图纸/原理/IO清单")
    sample_availability = Column(Text, comment="样品可提供情况(JSON)")
    customer_support_resources = Column(Text, comment="客户配合资源(JSON)")
    key_risk_factors = Column(Text, comment="关键风险初判(JSON Array)")
    veto_triggered = Column(Boolean, default=False, comment="一票否决触发")
    veto_reason = Column(Text, comment="一票否决原因")
    
    # 产线与节拍/产能
    target_capacity_uph = Column(Numeric(10, 2), comment="目标产能(UPH)")
    target_capacity_daily = Column(Numeric(10, 2), comment="目标产能(日)")
    target_capacity_shift = Column(Numeric(10, 2), comment="目标产能(班)")
    cycle_time_seconds = Column(Numeric(10, 2), comment="节拍要求(CT秒)")
    workstation_count = Column(Integer, comment="工位数/并行数")
    changeover_method = Column(String(100), comment="换型方式")
    yield_target = Column(Numeric(5, 2), comment="良率目标")
    retest_allowed = Column(Boolean, comment="是否允许复测")
    retest_max_count = Column(Integer, comment="复测次数")
    traceability_type = Column(String(50), comment="追溯要求")
    data_retention_period = Column(Integer, comment="数据保留期限(天)")
    data_format = Column(String(100), comment="数据格式")
    
    # 测试范围与验收口径
    test_scope = Column(Text, comment="测试范围(JSON Array)")
    key_metrics_spec = Column(Text, comment="关键指标口径(JSON)")
    coverage_boundary = Column(Text, comment="覆盖边界(JSON)")
    exception_handling = Column(Text, comment="允许的异常处理(JSON)")
    acceptance_method = Column(String(100), comment="验收方式")
    acceptance_basis = Column(Text, comment="验收依据")
    delivery_checklist = Column(Text, comment="验收交付物清单(JSON Array)")
    
    # 接口与I/O
    interface_types = Column(Text, comment="被测对象接口类型(JSON Array)")
    io_point_estimate = Column(Text, comment="IO点数估算(JSON)")
    communication_protocols = Column(Text, comment="通讯协议(JSON Array)")
    upper_system_integration = Column(Text, comment="与上位系统对接(JSON)")
    data_field_list = Column(Text, comment="数据字段清单(JSON Array)")
    it_security_restrictions = Column(Text, comment="IT安全/网络限制(JSON)")
    
    # 现场条件与EHS
    power_supply = Column(Text, comment="供电(JSON)")
    air_supply = Column(Text, comment="气源(JSON)")
    environment = Column(Text, comment="环境(JSON)")
    safety_requirements = Column(Text, comment="安全要求(JSON)")
    space_and_logistics = Column(Text, comment="占地与物流(JSON)")
    customer_site_standards = Column(Text, comment="客户现场规范(JSON)")
    
    # 关键物料与供应链约束
    customer_supplied_materials = Column(Text, comment="客供物料清单(JSON Array)")
    restricted_brands = Column(Text, comment="禁用品牌(JSON Array)")
    specified_brands = Column(Text, comment="指定品牌(JSON Array)")
    long_lead_items = Column(Text, comment="长周期件提示(JSON Array)")
    spare_parts_requirement = Column(Text, comment="备品备件要求(JSON)")
    after_sales_support = Column(Text, comment="售后支持要求(JSON)")
    
    # 版本与冻结
    requirement_version = Column(String(50), comment="需求包版本号")
    is_frozen = Column(Boolean, default=False, comment="是否冻结")
    frozen_at = Column(DateTime, comment="冻结时间")
    frozen_by = Column(Integer, ForeignKey("users.id"), comment="冻结人ID")
    
    # 关系
    lead = relationship("Lead", foreign_keys=[lead_id])
    frozen_by_user = relationship("User", foreign_keys=[frozen_by])
    
    __table_args__ = (
        Index('idx_requirement_detail_lead', 'lead_id'),
        Index('idx_requirement_detail_frozen', 'is_frozen'),
    )
    
    def __repr__(self):
        return f"<LeadRequirementDetail {self.id}>"


class RequirementFreeze(Base, TimestampMixin):
    """需求冻结记录表"""
    
    __tablename__ = "requirement_freezes"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    freeze_type = Column(String(50), nullable=False, comment="冻结点类型")
    freeze_time = Column(DateTime, default=datetime.now, comment="冻结时间")
    frozen_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="冻结人ID")
    version_number = Column(String(50), nullable=False, comment="冻结版本号")
    requires_ecr = Column(Boolean, default=True, comment="冻结后变更是否必须走ECR/ECN")
    description = Column(Text, comment="冻结说明")
    
    # 关系
    frozen_by_user = relationship("User", foreign_keys=[frozen_by])
    
    __table_args__ = (
        Index('idx_requirement_freeze_source', 'source_type', 'source_id'),
        Index('idx_requirement_freeze_type', 'freeze_type'),
        Index('idx_requirement_freeze_time', 'freeze_time'),
    )
    
    def __repr__(self):
        return f"<RequirementFreeze {self.id}>"


class OpenItem(Base, TimestampMixin):
    """未决事项表"""
    
    __tablename__ = "open_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    item_code = Column(String(50), unique=True, nullable=False, comment="未决事项编号")
    item_type = Column(String(50), nullable=False, comment="问题类型")
    description = Column(Text, nullable=False, comment="问题描述")
    responsible_party = Column(String(50), nullable=False, comment="责任方")
    responsible_person_id = Column(Integer, ForeignKey("users.id"), comment="责任人ID")
    due_date = Column(DateTime, comment="截止日期")
    status = Column(String(20), default=OpenItemStatusEnum.PENDING, comment="当前状态")
    close_evidence = Column(Text, comment="关闭证据(附件/链接/记录)")
    blocks_quotation = Column(Boolean, default=False, comment="是否阻塞报价")
    closed_at = Column(DateTime, comment="关闭时间")
    
    # 关系
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])
    
    __table_args__ = (
        Index('idx_open_item_source', 'source_type', 'source_id'),
        Index('idx_open_item_status', 'status'),
        Index('idx_open_item_type', 'item_type'),
        Index('idx_open_item_blocks', 'blocks_quotation'),
        Index('idx_open_item_due_date', 'due_date'),
    )
    
    def __repr__(self):
        return f"<OpenItem {self.item_code}>"


class AIClarification(Base, TimestampMixin):
    """AI澄清记录表"""
    
    __tablename__ = "ai_clarifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    source_type = Column(String(20), nullable=False, comment="来源类型：LEAD/OPPORTUNITY")
    source_id = Column(Integer, nullable=False, comment="来源ID")
    round = Column(Integer, nullable=False, comment="澄清轮次")
    questions = Column(Text, nullable=False, comment="AI生成的问题(JSON Array)")
    answers = Column(Text, comment="用户回答(JSON Array)")
    
    __table_args__ = (
        Index('idx_ai_clarification_source', 'source_type', 'source_id'),
        Index('idx_ai_clarification_round', 'round'),
    )
    
    def __repr__(self):
        return f"<AIClarification {self.id}>"


# ==================== 审批工作流相关 ====================

class ApprovalWorkflow(Base, TimestampMixin):
    """审批工作流配置表"""
    
    __tablename__ = "approval_workflows"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    workflow_type = Column(String(20), nullable=False, comment="工作流类型：QUOTE/CONTRACT/INVOICE")
    workflow_name = Column(String(100), nullable=False, comment="工作流名称")
    description = Column(Text, comment="工作流描述")
    
    # 审批路由规则（JSON格式，存储金额阈值等条件）
    routing_rules = Column(JSON, comment="审批路由规则（JSON）")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否启用")
    
    # 关系
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
    
    # 审批人配置
    approver_role = Column(String(50), comment="审批角色（如：SALES_MANAGER）")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="指定审批人ID（可选）")
    
    # 步骤配置
    is_required = Column(Boolean, default=True, comment="是否必需")
    can_delegate = Column(Boolean, default=True, comment="是否允许委托")
    can_withdraw = Column(Boolean, default=True, comment="是否允许撤回（在下一级审批前）")
    
    # 审批期限（小时）
    due_hours = Column(Integer, comment="审批期限（小时）")
    
    # 关系
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
    
    # 当前状态
    current_step = Column(Integer, default=1, comment="当前审批步骤（从1开始）")
    status = Column(String(20), default="PENDING", comment="审批状态：PENDING/APPROVED/REJECTED/CANCELLED")
    
    # 发起人
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发起人ID")
    
    # 关系
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
    
    # 审批人
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="审批人ID")
    
    # 审批操作
    action = Column(String(20), nullable=False, comment="审批操作：APPROVE/REJECT/DELEGATE/WITHDRAW")
    comment = Column(Text, comment="审批意见")
    
    # 委托信息（如果action是DELEGATE）
    delegate_to_id = Column(Integer, ForeignKey("users.id"), comment="委托给的用户ID")
    
    # 时间
    action_at = Column(DateTime, nullable=False, default=datetime.now, comment="操作时间")
    
    # 关系
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
    
    # 目标范围：PERSONAL(个人)/TEAM(团队)/DEPARTMENT(部门)
    target_scope = Column(String(20), nullable=False, comment="目标范围：PERSONAL/TEAM/DEPARTMENT")
    
    # 目标对象
    user_id = Column(Integer, ForeignKey("users.id"), comment="用户ID（个人目标）")
    department_id = Column(Integer, ForeignKey("departments.id"), comment="部门ID（部门目标）")
    team_id = Column(Integer, comment="团队ID（团队目标，暂未实现团队表）")
    
    # 目标类型：LEAD_COUNT(线索数量)/OPPORTUNITY_COUNT(商机数量)/CONTRACT_AMOUNT(合同金额)/COLLECTION_AMOUNT(回款金额)
    target_type = Column(String(20), nullable=False, comment="目标类型：LEAD_COUNT/OPPORTUNITY_COUNT/CONTRACT_AMOUNT/COLLECTION_AMOUNT")
    
    # 目标周期：MONTHLY(月度)/QUARTERLY(季度)/YEARLY(年度)
    target_period = Column(String(20), nullable=False, comment="目标周期：MONTHLY/QUARTERLY/YEARLY")
    
    # 周期标识：2025-01(月度)/2025-Q1(季度)/2025(年度)
    period_value = Column(String(20), nullable=False, comment="周期标识：2025-01/2025-Q1/2025")
    
    # 目标值
    target_value = Column(Numeric(14, 2), nullable=False, comment="目标值")
    
    # 实际完成值（计算字段，不存储，通过统计API计算）
    # actual_value = Column(Numeric(14, 2), comment="实际完成值")
    
    # 目标描述
    description = Column(Text, comment="目标描述")
    
    # 状态
    status = Column(String(20), default="ACTIVE", comment="状态：ACTIVE/COMPLETED/CANCELLED")
    
    # 创建人
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, comment="创建人ID")
    
    # 关系
    user = relationship("User", foreign_keys=[user_id])
    department = relationship("Department", foreign_keys=[department_id])
    creator = relationship("User", foreign_keys=[created_by])
    
    __table_args__ = (
        Index("idx_sales_target_scope", "target_scope", "user_id", "department_id"),
        Index("idx_sales_target_type_period", "target_type", "target_period", "period_value"),
        Index("idx_sales_target_status", "status"),
        Index("idx_sales_target_user", "user_id"),
        Index("idx_sales_target_department", "department_id"),
    )
    
    def __repr__(self):
        return f"<SalesTarget {self.target_type}-{self.period_value}>"
