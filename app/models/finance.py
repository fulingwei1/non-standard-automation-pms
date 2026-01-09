# -*- coding: utf-8 -*-
"""
融资管理模块 ORM 模型
包含：融资轮次、投资方、融资记录、股权结构、融资用途
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


class FundingRound(Base, TimestampMixin):
    """融资轮次表"""
    
    __tablename__ = "funding_rounds"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    round_code = Column(String(50), unique=True, nullable=False, comment="轮次编码")
    round_name = Column(String(100), nullable=False, comment="轮次名称")
    round_type = Column(String(20), nullable=False, comment="轮次类型：SEED/A/B/C/D/E/PRE_IPO/IPO")
    round_order = Column(Integer, nullable=False, comment="轮次顺序（1,2,3...）")
    
    # 融资信息
    target_amount = Column(Numeric(15, 2), nullable=False, comment="目标融资金额")
    actual_amount = Column(Numeric(15, 2), default=0, comment="实际融资金额")
    currency = Column(String(10), default="CNY", comment="币种")
    valuation_pre = Column(Numeric(15, 2), comment="投前估值")
    valuation_post = Column(Numeric(15, 2), comment="投后估值")
    
    # 时间信息
    launch_date = Column(Date, comment="启动日期")
    closing_date = Column(Date, comment="交割日期")
    expected_closing_date = Column(Date, comment="预期交割日期")
    
    # 状态
    status = Column(String(20), default="PLANNING", comment="状态：PLANNING/IN_PROGRESS/CLOSED/CANCELLED")
    
    # 负责人
    lead_investor_id = Column(Integer, ForeignKey("investors.id"), comment="领投方ID")
    lead_investor_name = Column(String(200), comment="领投方名称（冗余）")
    responsible_person_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    responsible_person_name = Column(String(50), comment="负责人姓名（冗余）")
    
    # 备注
    description = Column(Text, comment="轮次说明")
    notes = Column(Text, comment="备注")
    
    # 关系
    lead_investor = relationship("Investor", foreign_keys=[lead_investor_id])
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])
    funding_records = relationship("FundingRecord", back_populates="funding_round", cascade="all, delete-orphan")
    equity_structures = relationship("EquityStructure", back_populates="funding_round", cascade="all, delete-orphan")
    funding_usages = relationship("FundingUsage", back_populates="funding_round", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_funding_round_code", "round_code"),
        Index("idx_funding_round_type", "round_type"),
        Index("idx_funding_round_status", "status"),
        Index("idx_funding_round_order", "round_order"),
        {"comment": "融资轮次表"}
    )
    
    def __repr__(self):
        return f"<FundingRound {self.round_code}>"


class Investor(Base, TimestampMixin):
    """投资方表"""
    
    __tablename__ = "investors"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    investor_code = Column(String(50), unique=True, nullable=False, comment="投资方编码")
    investor_name = Column(String(200), nullable=False, comment="投资方名称")
    investor_type = Column(String(20), nullable=False, comment="投资方类型：VC/PE/ANGEL/STRATEGIC/GOVERNMENT/CORPORATE/INDIVIDUAL")
    
    # 基本信息
    legal_name = Column(String(200), comment="法人名称")
    registration_no = Column(String(100), comment="注册号/统一社会信用代码")
    country = Column(String(50), default="中国", comment="国家")
    region = Column(String(50), comment="地区（省/市）")
    address = Column(String(500), comment="地址")
    
    # 联系信息
    contact_person = Column(String(50), comment="联系人")
    contact_phone = Column(String(50), comment="联系电话")
    contact_email = Column(String(100), comment="联系邮箱")
    website = Column(String(200), comment="官网")
    
    # 投资信息
    investment_focus = Column(Text, comment="投资领域/关注行业")
    investment_stage = Column(String(100), comment="投资阶段偏好（如：A轮-B轮）")
    typical_ticket_size = Column(Numeric(15, 2), comment="典型投资金额")
    portfolio_companies = Column(Text, comment="投资组合（JSON或文本）")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否有效")
    is_lead_investor = Column(Boolean, default=False, comment="是否曾作为领投方")
    
    # 备注
    description = Column(Text, comment="投资方说明")
    notes = Column(Text, comment="备注")
    
    # 关系
    funding_records = relationship("FundingRecord", back_populates="investor", cascade="all, delete-orphan")
    equity_structures = relationship("EquityStructure", back_populates="investor", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_investor_code", "investor_code"),
        Index("idx_investor_type", "investor_type"),
        Index("idx_investor_name", "investor_name"),
        {"comment": "投资方表"}
    )
    
    def __repr__(self):
        return f"<Investor {self.investor_code}>"


class FundingRecord(Base, TimestampMixin):
    """融资记录表（记录每笔具体的投资）"""
    
    __tablename__ = "funding_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    record_code = Column(String(50), unique=True, nullable=False, comment="记录编码")
    
    # 关联信息
    funding_round_id = Column(Integer, ForeignKey("funding_rounds.id"), nullable=False, comment="融资轮次ID")
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=False, comment="投资方ID")
    
    # 投资信息
    investment_amount = Column(Numeric(15, 2), nullable=False, comment="投资金额")
    currency = Column(String(10), default="CNY", comment="币种")
    share_percentage = Column(Numeric(8, 4), comment="持股比例（%）")
    share_count = Column(Numeric(15, 2), comment="持股数量")
    price_per_share = Column(Numeric(10, 4), comment="每股价格")
    
    # 时间信息
    commitment_date = Column(Date, comment="承诺日期")
    payment_date = Column(Date, comment="付款日期")
    actual_payment_date = Column(Date, comment="实际付款日期")
    
    # 付款信息
    payment_method = Column(String(20), comment="付款方式：WIRE/CHECK/CASH/OTHER")
    payment_status = Column(String(20), default="PENDING", comment="付款状态：PENDING/PARTIAL/COMPLETED")
    paid_amount = Column(Numeric(15, 2), default=0, comment="已付金额")
    remaining_amount = Column(Numeric(15, 2), comment="剩余金额")
    
    # 合同信息
    contract_no = Column(String(100), comment="合同编号")
    contract_date = Column(Date, comment="合同签署日期")
    contract_file = Column(String(500), comment="合同文件路径")
    
    # 状态
    status = Column(String(20), default="COMMITTED", comment="状态：COMMITTED/PAID/CANCELLED")
    
    # 备注
    description = Column(Text, comment="投资说明")
    notes = Column(Text, comment="备注")
    
    # 关系
    funding_round = relationship("FundingRound", back_populates="funding_records")
    investor = relationship("Investor", back_populates="funding_records")
    
    __table_args__ = (
        Index("idx_funding_record_round", "funding_round_id"),
        Index("idx_funding_record_investor", "investor_id"),
        Index("idx_funding_record_status", "status"),
        Index("idx_funding_record_payment", "payment_status"),
        {"comment": "融资记录表"}
    )
    
    def __repr__(self):
        return f"<FundingRecord {self.record_code}>"


class EquityStructure(Base, TimestampMixin):
    """股权结构表（记录每个轮次后的股权结构）"""
    
    __tablename__ = "equity_structures"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 关联信息
    funding_round_id = Column(Integer, ForeignKey("funding_rounds.id"), nullable=False, comment="融资轮次ID")
    investor_id = Column(Integer, ForeignKey("investors.id"), nullable=True, comment="投资方ID（为空表示创始人/员工等）")
    
    # 股东信息
    shareholder_name = Column(String(200), nullable=False, comment="股东名称")
    shareholder_type = Column(String(20), nullable=False, comment="股东类型：FOUNDER/EMPLOYEE/INVESTOR/OTHER")
    
    # 股权信息
    share_percentage = Column(Numeric(8, 4), nullable=False, comment="持股比例（%）")
    share_count = Column(Numeric(15, 2), comment="持股数量")
    share_class = Column(String(20), comment="股份类别：COMMON/PREFERRED/OPTION")
    
    # 时间信息
    effective_date = Column(Date, nullable=False, comment="生效日期")
    
    # 备注
    description = Column(Text, comment="说明")
    notes = Column(Text, comment="备注")
    
    # 关系
    funding_round = relationship("FundingRound", back_populates="equity_structures")
    investor = relationship("Investor", foreign_keys=[investor_id])
    
    __table_args__ = (
        Index("idx_equity_round", "funding_round_id"),
        Index("idx_equity_investor", "investor_id"),
        Index("idx_equity_type", "shareholder_type"),
        Index("idx_equity_date", "effective_date"),
        {"comment": "股权结构表"}
    )
    
    def __repr__(self):
        return f"<EquityStructure {self.shareholder_name}>"


class FundingUsage(Base, TimestampMixin):
    """融资用途表（记录融资资金的使用计划）"""
    
    __tablename__ = "funding_usages"
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    
    # 关联信息
    funding_round_id = Column(Integer, ForeignKey("funding_rounds.id"), nullable=False, comment="融资轮次ID")
    
    # 用途信息
    usage_category = Column(String(50), nullable=False, comment="用途分类：R&D/MARKETING/OPERATIONS/EQUIPMENT/FACILITIES/WORKING_CAPITAL/OTHER")
    usage_item = Column(String(200), nullable=False, comment="用途项目")
    planned_amount = Column(Numeric(15, 2), nullable=False, comment="计划金额")
    actual_amount = Column(Numeric(15, 2), default=0, comment="实际金额")
    percentage = Column(Numeric(5, 2), comment="占比（%）")
    
    # 时间信息
    planned_start_date = Column(Date, comment="计划开始日期")
    planned_end_date = Column(Date, comment="计划结束日期")
    actual_start_date = Column(Date, comment="实际开始日期")
    actual_end_date = Column(Date, comment="实际结束日期")
    
    # 状态
    status = Column(String(20), default="PLANNED", comment="状态：PLANNED/IN_PROGRESS/COMPLETED/CANCELLED")
    
    # 负责人
    responsible_person_id = Column(Integer, ForeignKey("users.id"), comment="负责人ID")
    responsible_person_name = Column(String(50), comment="负责人姓名（冗余）")
    
    # 备注
    description = Column(Text, comment="用途说明")
    notes = Column(Text, comment="备注")
    
    # 关系
    funding_round = relationship("FundingRound", back_populates="funding_usages")
    responsible_person = relationship("User", foreign_keys=[responsible_person_id])
    
    __table_args__ = (
        Index("idx_funding_usage_round", "funding_round_id"),
        Index("idx_funding_usage_category", "usage_category"),
        Index("idx_funding_usage_status", "status"),
        {"comment": "融资用途表"}
    )
    
    def __repr__(self):
        return f"<FundingUsage {self.usage_item}>"
