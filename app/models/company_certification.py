"""
公司资质证书模型
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.sql import func

from app.models.base import Base


class CompanyCertification(Base):
    """公司资质证书"""
    
    __tablename__ = "company_certifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 证书基本信息
    cert_name = Column(String(200), nullable=False, comment="证书名称")
    cert_type = Column(String(100), nullable=False, comment="证书类型")
    cert_number = Column(String(100), comment="证书编号")
    issuing_authority = Column(String(200), comment="发证机构")
    
    # 证书时间
    issue_date = Column(Date, comment="发证日期")
    expiry_date = Column(Date, comment="到期日期")
    
    # 证书状态
    status = Column(String(50), default="有效", comment="证书状态：有效/即将到期/已过期")
    
    # 证书详情
    description = Column(Text, comment="证书描述")
    scope = Column(Text, comment="认证范围")
    
    # 附件信息
    attachment_path = Column(String(500), comment="附件路径")
    
    # 审计字段
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<CompanyCertification(id={self.id}, cert_name='{self.cert_name}')>"
