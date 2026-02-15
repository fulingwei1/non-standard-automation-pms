"""
售前AI知识库案例模型
"""
from sqlalchemy import Column, Integer, String, Text, DECIMAL, Boolean, TIMESTAMP, JSON, BLOB
from sqlalchemy.sql import func
from app.models.base import Base


class PresaleKnowledgeCase(Base):
    """AI知识库案例表"""
    __tablename__ = 'presale_knowledge_case'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='案例ID')
    case_name = Column(String(200), nullable=False, comment='案例名称')
    industry = Column(String(100), nullable=True, comment='行业分类')
    equipment_type = Column(String(100), nullable=True, comment='设备类型')
    customer_name = Column(String(200), nullable=True, comment='客户名称')
    project_amount = Column(DECIMAL(12, 2), nullable=True, comment='项目金额')
    project_summary = Column(Text, nullable=True, comment='项目摘要')
    technical_highlights = Column(Text, nullable=True, comment='技术亮点')
    success_factors = Column(Text, nullable=True, comment='成功要素')
    lessons_learned = Column(Text, nullable=True, comment='失败教训')
    tags = Column(JSON, nullable=True, comment='标签数组')
    embedding = Column(BLOB, nullable=True, comment='向量嵌入')
    quality_score = Column(DECIMAL(3, 2), nullable=True, default=0.5, comment='案例质量评分 0-1')
    is_public = Column(Boolean, default=True, comment='是否公开')
    created_at = Column(TIMESTAMP, server_default=func.now(), comment='创建时间')
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    def __repr__(self):
        return f"<PresaleKnowledgeCase {self.id}: {self.case_name}>"

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'case_name': self.case_name,
            'industry': self.industry,
            'equipment_type': self.equipment_type,
            'customer_name': self.customer_name,
            'project_amount': float(self.project_amount) if self.project_amount else None,
            'project_summary': self.project_summary,
            'technical_highlights': self.technical_highlights,
            'success_factors': self.success_factors,
            'lessons_learned': self.lessons_learned,
            'tags': self.tags,
            'quality_score': float(self.quality_score) if self.quality_score else None,
            'is_public': self.is_public,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
