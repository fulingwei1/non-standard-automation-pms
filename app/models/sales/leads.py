# -*- coding: utf-8 -*-
"""
线索和商机模型
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
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
from app.models.enums import (
    GateStatusEnum,
    LeadStatusEnum,
    OpportunityStageEnum,
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

    # 优势产品相关字段
    selected_advantage_products = Column(Text, comment="选择的优势产品ID列表(JSON Array)")
    product_match_type = Column(String(20), default="UNKNOWN", comment="产品匹配类型: ADVANTAGE/NEW/UNKNOWN")
    is_advantage_product = Column(Boolean, default=False, comment="是否优势产品")

    # 技术评估扩展字段
    requirement_detail_id = Column(Integer, ForeignKey("lead_requirement_details.id"), comment="需求详情ID")
    assessment_id = Column(Integer, ForeignKey("technical_assessments.id"), comment="技术评估ID")
    completeness = Column(Integer, default=0, comment="完整度(0-100)")
    assignee_id = Column(Integer, ForeignKey("users.id"), comment="被指派的售前工程师ID")
    assessment_status = Column(String(20), comment="技术评估状态")

    # 优先级评分字段
    priority_score = Column(Integer, default=0, comment="优先级得分(0-100)")

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
        Index('idx_leads_advantage_product', 'is_advantage_product'),
        Index('idx_leads_product_match_type', 'product_match_type'),
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
    probability = Column(Integer, default=0, comment="成交概率(0-100)")
    est_amount = Column(Numeric(12, 2), comment="预估金额")
    est_margin = Column(Numeric(5, 2), comment="预估毛利率")
    expected_close_date = Column(Date, comment="预计成交日期")
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

    # 优先级评分字段
    priority_score = Column(Integer, default=0, comment="优先级得分(0-100)")

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
