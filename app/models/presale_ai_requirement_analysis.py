"""
AI需求理解记录模型
记录AI对售前需求的分析结果
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Text, JSON, DECIMAL, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base


class PresaleAIRequirementAnalysis(Base):
    """AI需求理解记录表"""
    __tablename__ = "presale_ai_requirement_analysis"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    presale_ticket_id = Column(Integer, ForeignKey("presale_support_ticket.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 原始需求
    raw_requirement = Column(Text, nullable=False, comment="客户原始需求描述")
    
    # AI分析结果
    structured_requirement = Column(JSON, nullable=True, comment="结构化需求数据")
    clarification_questions = Column(JSON, nullable=True, comment="澄清问题列表")
    
    # 置信度和可行性分析
    confidence_score = Column(DECIMAL(3, 2), nullable=True, comment="需求理解置信度 0.00-1.00")
    feasibility_analysis = Column(JSON, nullable=True, comment="技术可行性分析")
    
    # 提取的关键信息
    equipment_list = Column(JSON, nullable=True, comment="识别的设备清单")
    process_flow = Column(JSON, nullable=True, comment="工艺流程数据")
    technical_parameters = Column(JSON, nullable=True, comment="技术参数规格")
    acceptance_criteria = Column(JSON, nullable=True, comment="验收标准建议")
    
    # AI模型信息
    ai_model_used = Column(String(100), nullable=True, comment="使用的AI模型")
    ai_analysis_version = Column(String(50), nullable=True, comment="分析算法版本")
    
    # 状态管理
    status = Column(String(50), default="draft", comment="状态: draft/reviewed/approved/rejected")
    is_refined = Column(Boolean, default=False, comment="是否已精炼")
    refinement_count = Column(Integer, default=0, comment="精炼次数")
    
    # 元数据
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    # presale_ticket = relationship("PresaleTicket", back_populates="ai_analyses")
    creator = relationship("User", foreign_keys=[created_by])
    # TODO: 修复循环引用问题后再启用
    # solutions = relationship('PresaleAISolution', back_populates='requirement_analysis')

    def __repr__(self):
        return f"<PresaleAIRequirementAnalysis(id={self.id}, ticket_id={self.presale_ticket_id}, confidence={self.confidence_score})>"
