# -*- coding: utf-8 -*-
"""
报价相关模型
"""

from datetime import datetime

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

from app.models.base import Base, TimestampMixin
from app.models.enums import QuoteStatusEnum


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
    approvals = relationship("QuoteApproval", back_populates="quote", cascade="all, delete-orphan")

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
        Index("idx_quote_is_active", "is_active"),
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
        Index("idx_cost_approval_quote_id", "quote_id"),
        Index("idx_cost_approval_status", "approval_status"),
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
        Index("idx_cost_history_quote_id", "quote_id"),
        Index("idx_cost_history_created_at", "created_at"),
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
    supplier_id = Column(Integer, ForeignKey("vendors.id"), comment="供应商ID")
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
    # supplier = relationship("Supplier", foreign_keys=[supplier_id])  # 已禁用 - Supplier 是废弃模型
    submitter = relationship("User", foreign_keys=[submitted_by])

    __table_args__ = (
        Index("idx_material_code", "material_code"),
        Index("idx_material_name", "material_name"),
        Index("idx_purchase_material_type", "material_type"),
        Index("idx_is_standard", "is_standard_part"),
        Index("idx_purchase_material_is_active", "is_active"),
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
