"""
AI报价单自动生成模型
Team 5: AI Quotation Generator Models
"""

import enum
from datetime import datetime

from sqlalchemy import (
    DECIMAL,
    JSON,
    TIMESTAMP,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

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


class PresaleAIQuotation(Base):
    """AI报价单生成记录表"""

    __tablename__ = "presale_ai_quotation"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
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
    status = Column(
        Enum(QuotationStatus), nullable=False, default=QuotationStatus.DRAFT, comment="状态"
    )
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


class QuotationVersion(Base):
    """报价单版本历史"""

    __tablename__ = "quotation_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, comment="租户ID")
    quotation_id = Column(
        Integer, ForeignKey("presale_ai_quotation.id"), nullable=False, comment="报价单ID"
    )
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
