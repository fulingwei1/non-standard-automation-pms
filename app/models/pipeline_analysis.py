# -*- coding: utf-8 -*-
"""
全链条分析与断链检测数据模型
"""

from sqlalchemy import Column, Integer, String, Date, DateTime, Text, Numeric, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class PipelineBreakRecord(Base, TimestampMixin):
    """断链记录表"""
    
    __tablename__ = "pipeline_break_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    pipeline_id = Column(String(50), nullable=False, comment="流程ID（线索/商机/报价/合同ID）")
    pipeline_type = Column(String(20), nullable=False, comment="流程类型：LEAD/OPPORTUNITY/QUOTE/CONTRACT")
    break_stage = Column(String(20), nullable=False, comment="断链环节：LEAD_TO_OPP/OPP_TO_QUOTE/QUOTE_TO_CONTRACT/CONTRACT_TO_PROJECT/PROJECT_TO_INVOICE/INVOICE_TO_PAYMENT")
    break_reason = Column(String(100), comment="断链原因")
    break_date = Column(Date, nullable=False, comment="断链日期")
    responsible_person_id = Column(Integer, ForeignKey("users.id"), comment="责任人ID")
    responsible_department = Column(String(50), comment="责任部门")
    cost_impact = Column(Numeric(14, 2), comment="成本影响")
    opportunity_cost = Column(Numeric(14, 2), comment="机会成本")
    
    # 关系
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])
    
    __table_args__ = (
        Index('idx_pipeline_type', 'pipeline_type', 'break_stage'),
        Index('idx_break_date', 'break_date'),
        Index('idx_responsible', 'responsible_person_id'),
        {'comment': '断链记录表'}
    )


class PipelineHealthSnapshot(Base, TimestampMixin):
    """健康度快照表"""
    
    __tablename__ = "pipeline_health_snapshots"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    pipeline_id = Column(String(50), nullable=False, comment="流程ID")
    pipeline_type = Column(String(20), nullable=False, comment="流程类型：LEAD/OPPORTUNITY/QUOTE/CONTRACT")
    health_status = Column(String(10), nullable=False, comment="健康度状态：H1/H2/H3/H4")
    health_score = Column(Integer, comment="健康度评分（0-100）")
    risk_factors = Column(Text, comment="风险因素JSON")
    snapshot_date = Column(Date, nullable=False, comment="快照日期")
    
    __table_args__ = (
        Index('idx_pipeline', 'pipeline_type', 'pipeline_id'),
        Index('idx_snapshot_date', 'snapshot_date'),
        {'comment': '健康度快照表'}
    )


class AccountabilityRecord(Base, TimestampMixin):
    """责任记录表"""
    
    __tablename__ = "accountability_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    pipeline_id = Column(String(50), nullable=False, comment="流程ID")
    pipeline_type = Column(String(20), nullable=False, comment="流程类型")
    issue_type = Column(String(50), nullable=False, comment="问题类型：DELAY/COST_OVERRUN/INFORMATION_GAP/BREAK")
    responsible_person_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="责任人ID")
    responsible_department = Column(String(50), comment="责任部门")
    responsibility_ratio = Column(Numeric(5, 2), comment="责任比例（0-100）")
    cost_impact = Column(Numeric(14, 2), comment="成本影响")
    description = Column(Text, comment="责任描述")
    
    # 关系
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])
    
    __table_args__ = (
        Index('idx_person', 'responsible_person_id'),
        Index('idx_department', 'responsible_department'),
        Index('idx_issue_type', 'issue_type'),
        {'comment': '责任记录表'}
    )
