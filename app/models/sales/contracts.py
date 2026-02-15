# -*- coding: utf-8 -*-
"""
合同相关模型
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

from app.models.base import Base, TimestampMixin
from app.models.enums import ContractStatusEnum


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

    versions = relationship("ContractTemplateVersion", back_populates="template", cascade="all, delete-orphan", foreign_keys="ContractTemplateVersion.template_id")
    current_version = relationship("ContractTemplateVersion", foreign_keys=[current_version_id], post_update=True, uselist=False)
    owner = relationship("User", foreign_keys=[owner_id])

    __table_args__ = (Index("idx_contract_template_status", "status"), Index("idx_contract_template_scope", "visibility_scope"))

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

    template = relationship("ContractTemplate", back_populates="versions", foreign_keys=[template_id])
    creator = relationship("User", foreign_keys=[created_by], backref="contract_template_versions_created")
    publisher = relationship("User", foreign_keys=[published_by], backref="contract_template_versions_published")

    __table_args__ = (Index("idx_contract_template_version_template", "template_id"), Index("idx_contract_template_version_status", "status"))

    def __repr__(self):
        return f"<ContractTemplateVersion {self.template_id}-{self.version_no}>"


class Contract(Base, TimestampMixin):
    """合同主表"""
    __tablename__ = "contracts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_code = Column(String(50), unique=True, nullable=False, comment="合同编码（内部）")
    contract_name = Column(String(200), nullable=False, comment="合同名称")
    contract_type = Column(String(20), nullable=False, comment="合同类型: sales/purchase/framework")
    customer_contract_no = Column(String(100), comment="客户合同编号（外部）")
    
    # 关联信息
    opportunity_id = Column(Integer, ForeignKey("opportunities.id"), comment="商机ID")
    quote_id = Column(Integer, ForeignKey("quote_versions.id"), comment="报价ID")
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, comment="客户ID")
    project_id = Column(Integer, ForeignKey("projects.id"), comment="项目ID")
    
    # 金额信息
    total_amount = Column(Numeric(15, 2), nullable=False, comment="合同总额")
    received_amount = Column(Numeric(15, 2), default=0, comment="已收款")
    unreceived_amount = Column(Numeric(15, 2), comment="未收款")
    
    # 期限信息
    signing_date = Column(Date, comment="签订日期")
    effective_date = Column(Date, comment="生效日期")
    expiry_date = Column(Date, comment="到期日期")
    contract_period = Column(Integer, comment="合同期限（月）")
    
    # 合同内容
    contract_subject = Column(Text, comment="合同标的")
    payment_terms = Column(Text, comment="付款条件")
    delivery_terms = Column(Text, comment="交付期限")
    
    # 状态管理
    status = Column(String(20), default='draft', comment="状态: draft/pending_approval/approving/approved/signed/executing/completed/voided")
    
    # 责任人
    sales_owner_id = Column(Integer, ForeignKey("users.id"), comment="签约销售ID")
    contract_manager_id = Column(Integer, ForeignKey("users.id"), comment="合同管理员ID")

    # 关系
    opportunity = relationship("Opportunity", back_populates="contracts")
    quote_version = relationship("QuoteVersion", back_populates="contracts", foreign_keys=[quote_id])
    customer = relationship("Customer", foreign_keys=[customer_id])
    project = relationship("Project", foreign_keys=[project_id])
    sales_owner = relationship("User", foreign_keys=[sales_owner_id])
    contract_manager = relationship("User", foreign_keys=[contract_manager_id])
    deliverables = relationship("ContractDeliverable", back_populates="contract", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="contract")
    amendments = relationship("ContractAmendment", back_populates="contract", cascade="all, delete-orphan")
    approvals = relationship("ContractApproval", back_populates="contract", cascade="all, delete-orphan")
    terms = relationship("ContractTerm", back_populates="contract", cascade="all, delete-orphan")
    attachments = relationship("ContractAttachment", back_populates="contract", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_contract_customer', 'customer_id'),
        Index('idx_contract_project', 'project_id'),
        Index('idx_contract_status', 'status'),
        Index('idx_contract_expiry_date', 'expiry_date'),
    )

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
    old_value = Column(Text, comment="原值（JSON）")
    new_value = Column(Text, comment="新值（JSON）")
    amount_change = Column(Numeric(12, 2), comment="金额变化")
    schedule_impact = Column(Text, comment="进度影响")
    other_impact = Column(Text, comment="其他影响")
    requestor_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="申请人ID")
    request_date = Column(Date, nullable=False, comment="申请日期")
    status = Column(String(20), default="PENDING", comment="状态：PENDING/APPROVED/REJECTED")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approval_date = Column(Date, comment="审批日期")
    approval_comment = Column(Text, comment="审批意见")
    attachments = Column(Text, comment="附件列表JSON")

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


class ContractApproval(Base, TimestampMixin):
    """合同审批表"""
    __tablename__ = "contract_approvals"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    approval_level = Column(Integer, nullable=False, comment="审批层级")
    approval_role = Column(String(50), nullable=False, comment="审批角色")
    approver_id = Column(Integer, ForeignKey("users.id"), comment="审批人ID")
    approver_name = Column(String(50), comment="审批人姓名")
    approval_status = Column(String(20), default="pending", comment="审批状态: pending/approved/rejected")
    approval_opinion = Column(Text, comment="审批意见")
    approved_at = Column(DateTime, comment="审批时间")
    
    contract = relationship("Contract", back_populates="approvals")
    approver = relationship("User", foreign_keys=[approver_id])

    __table_args__ = (
        Index("idx_contract_approval_contract", "contract_id"),
        Index("idx_contract_approval_approver", "approver_id"),
        Index("idx_contract_approval_status", "approval_status"),
    )

    def __repr__(self):
        return f"<ContractApproval {self.contract_id}-L{self.approval_level}>"


class ContractTerm(Base, TimestampMixin):
    """合同条款表"""
    __tablename__ = "contract_terms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    term_type = Column(String(20), nullable=False, comment="条款类型: subject/price/delivery/payment/warranty/breach")
    term_content = Column(Text, nullable=False, comment="条款内容")
    
    contract = relationship("Contract", back_populates="terms")

    __table_args__ = (
        Index("idx_contract_term_contract", "contract_id"),
    )

    def __repr__(self):
        return f"<ContractTerm {self.contract_id}-{self.term_type}>"


class ContractAttachment(Base, TimestampMixin):
    """合同附件表"""
    __tablename__ = "contract_attachments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False, comment="合同ID")
    file_name = Column(String(200), nullable=False, comment="文件名")
    file_path = Column(String(500), nullable=False, comment="文件路径")
    file_type = Column(String(50), comment="文件类型")
    file_size = Column(Integer, comment="文件大小（字节）")
    uploaded_by = Column(Integer, ForeignKey("users.id"), comment="上传人ID")
    
    contract = relationship("Contract", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    __table_args__ = (
        Index("idx_contract_attachment_contract", "contract_id"),
    )

    def __repr__(self):
        return f"<ContractAttachment {self.file_name}>"
