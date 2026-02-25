"""
AI报价单自动生成模型
Team 5: AI Quotation Generator Models
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Enum, Boolean, ForeignKey, JSON, TIMESTAMP
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import Base


class QuotationType(str, enum.Enum):
    """报价单类型枚举"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class QuotationStatus(str, enum.Enum):
    """报价单状态枚举"""
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class TemplateType(str, enum.Enum):
    """模板类型枚举"""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"


class PresaleAIQuotation(Base):
    """AI报价单生成记录表"""
    __tablename__ = "presale_ai_quotation"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    presale_ticket_id = Column(Integer, nullable=False, comment="售前工单ID")
    customer_id = Column(Integer, nullable=True, comment="客户ID")
    quotation_number = Column(String(50), unique=True, nullable=False, comment="报价单编号")
    quotation_type = Column(Enum(QuotationType), nullable=False, comment="报价单类型")
    
    # 报价项清单 - JSON格式存储
    items = Column(JSON, nullable=False, comment="报价项清单")
    
    # 价格信息
    subtotal = Column(DECIMAL(12, 2), nullable=False, comment="小计")
    tax = Column(DECIMAL(12, 2), nullable=False, default=0, comment="税费")
    discount = Column(DECIMAL(12, 2), nullable=False, default=0, comment="折扣")
    total = Column(DECIMAL(12, 2), nullable=False, comment="总计")
    
    # 付款条款
    payment_terms = Column(Text, nullable=True, comment="付款条款")
    validity_days = Column(Integer, nullable=False, default=30, comment="有效期（天）")
    
    # 状态管理
    status = Column(Enum(QuotationStatus), nullable=False, default=QuotationStatus.DRAFT, comment="状态")
    pdf_url = Column(String(255), nullable=True, comment="PDF文件URL")
    version = Column(Integer, nullable=False, default=1, comment="版本号")
    
    # 创建信息
    created_by = Column(Integer, nullable=False, comment="创建人ID")
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=datetime.now, comment="更新时间")
    
    # AI生成相关
    ai_prompt = Column(Text, nullable=True, comment="AI生成时使用的提示词")
    ai_model = Column(String(50), nullable=True, comment="使用的AI模型")
    generation_time = Column(DECIMAL(5, 2), nullable=True, comment="生成耗时（秒）")
    
    # 备注
    notes = Column(Text, nullable=True, comment="备注")
    
    def __repr__(self):
        return f"<PresaleAIQuotation(id={self.id}, number={self.quotation_number}, type={self.quotation_type}, status={self.status})>"


class QuotationTemplate(Base):
    """报价单模板库
    
    【状态】未启用 - 报价模板"""
    __tablename__ = "quotation_templates"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(100), nullable=False, comment="模板名称")
    template_type = Column(Enum(TemplateType), nullable=False, comment="模板类型")
    
    # 模板内容 - JSON格式存储
    template_content = Column(JSON, nullable=False, comment="模板内容")
    
    # PDF模板路径
    pdf_template_path = Column(String(255), nullable=True, comment="PDF模板路径")
    
    # 模板配置
    default_validity_days = Column(Integer, nullable=False, default=30, comment="默认有效期")
    default_tax_rate = Column(DECIMAL(5, 4), nullable=False, default=0.13, comment="默认税率")
    default_discount_rate = Column(DECIMAL(5, 4), nullable=False, default=0, comment="默认折扣率")
    
    # 状态
    is_active = Column(Boolean, nullable=False, default=True, comment="是否启用")
    
    # 创建信息
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=datetime.now, comment="更新时间")
    created_by = Column(Integer, nullable=True, comment="创建人ID")
    
    # 描述
    description = Column(Text, nullable=True, comment="模板描述")
    
    def __repr__(self):
        return f"<QuotationTemplate(id={self.id}, name={self.name}, type={self.template_type})>"


class QuotationApproval(Base):
    """报价单审批记录"""
    __tablename__ = "quotation_approvals"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    quotation_id = Column(Integer, ForeignKey("presale_ai_quotation.id"), nullable=False, comment="报价单ID")
    approver_id = Column(Integer, nullable=False, comment="审批人ID")
    
    # 审批结果
    status = Column(Enum("pending", "approved", "rejected", name="approval_status"), 
                   nullable=False, default="pending", comment="审批状态")
    comments = Column(Text, nullable=True, comment="审批意见")
    
    # 时间
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")
    approved_at = Column(TIMESTAMP, nullable=True, comment="审批时间")
    
    # 关联
    quotation = relationship("PresaleAIQuotation", backref="approvals")
    
    def __repr__(self):
        return f"<QuotationApproval(id={self.id}, quotation_id={self.quotation_id}, status={self.status})>"


class QuotationVersion(Base):
    """报价单版本历史"""
    __tablename__ = "quotation_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    quotation_id = Column(Integer, ForeignKey("presale_ai_quotation.id"), nullable=False, comment="报价单ID")
    version = Column(Integer, nullable=False, comment="版本号")
    
    # 快照数据
    snapshot_data = Column(JSON, nullable=False, comment="版本快照数据")
    
    # 变更信息
    changed_by = Column(Integer, nullable=False, comment="变更人ID")
    change_summary = Column(Text, nullable=True, comment="变更摘要")
    created_at = Column(TIMESTAMP, nullable=False, default=datetime.now, comment="创建时间")
    
    # 关联
    quotation = relationship("PresaleAIQuotation", backref="versions")
    
    def __repr__(self):
        return f"<QuotationVersion(id={self.id}, quotation_id={self.quotation_id}, version={self.version})>"
