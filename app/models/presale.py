# -*- coding: utf-8 -*-
"""
售前技术支持模块 ORM 模型
包含：支持工单、交付物、进度、技术方案、成本明细、方案模板、客户技术档案、投标记录
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
from enum import Enum


# ==================== 枚举定义 ====================

class TicketTypeEnum(str, Enum):
    """工单类型"""
    CONSULT = 'CONSULT'        # 技术咨询
    SURVEY = 'SURVEY'          # 需求调研
    SOLUTION = 'SOLUTION'      # 方案设计
    QUOTATION = 'QUOTATION'    # 报价支持
    TENDER = 'TENDER'          # 投标支持
    MEETING = 'MEETING'        # 技术交流
    SITE_VISIT = 'SITE_VISIT'  # 现场勘查


class TicketUrgencyEnum(str, Enum):
    """工单紧急程度"""
    NORMAL = 'NORMAL'          # 普通
    URGENT = 'URGENT'          # 紧急
    VERY_URGENT = 'VERY_URGENT'  # 非常紧急


class TicketStatusEnum(str, Enum):
    """工单状态"""
    PENDING = 'PENDING'        # 待接单
    ACCEPTED = 'ACCEPTED'      # 已接单
    PROCESSING = 'PROCESSING'  # 处理中
    REVIEW = 'REVIEW'          # 待审核
    COMPLETED = 'COMPLETED'    # 已完成
    CLOSED = 'CLOSED'          # 已关闭
    CANCELLED = 'CANCELLED'    # 已取消


class DeliverableStatusEnum(str, Enum):
    """交付物状态"""
    DRAFT = 'DRAFT'        # 草稿
    SUBMITTED = 'SUBMITTED'  # 已提交
    APPROVED = 'APPROVED'    # 已通过
    REJECTED = 'REJECTED'    # 已驳回


class SolutionStatusEnum(str, Enum):
    """方案状态"""
    DRAFT = 'DRAFT'          # 草稿
    REVIEW = 'REVIEW'        # 待审核
    APPROVED = 'APPROVED'    # 已批准
    DELIVERED = 'DELIVERED'  # 已交付
    WON = 'WON'              # 已中标
    LOST = 'LOST'            # 已落标


class TenderResultEnum(str, Enum):
    """投标结果"""
    PENDING = 'PENDING'    # 等待中
    WON = 'WON'            # 中标
    LOST = 'LOST'          # 落标
    CANCELLED = 'CANCELLED'  # 取消


# ==================== 支持工单 ====================

class PresaleSupportTicket(Base, TimestampMixin):
    """售前支持工单"""
    __tablename__ = 'presale_support_ticket'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ticket_no = Column(String(50), unique=True, nullable=False, comment='工单编号')
    
    # 申请信息
    title = Column(String(200), nullable=False, comment='工单标题')
    ticket_type = Column(String(20), nullable=False, comment='工单类型')
    urgency = Column(String(20), default='NORMAL', comment='紧急程度')
    description = Column(Text, comment='详细描述')
    
    # 关联信息
    customer_id = Column(Integer, comment='客户ID')
    customer_name = Column(String(100), comment='客户名称')
    opportunity_id = Column(Integer, comment='关联商机ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='关联项目ID')
    
    # 申请人信息
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID(销售)')
    applicant_name = Column(String(50), comment='申请人姓名')
    applicant_dept = Column(String(100), comment='申请人部门')
    apply_time = Column(DateTime, default=datetime.now, comment='申请时间')
    
    # 处理人信息
    assignee_id = Column(Integer, ForeignKey('users.id'), comment='指派处理人ID')
    assignee_name = Column(String(50), comment='处理人姓名')
    accept_time = Column(DateTime, comment='接单时间')
    
    # 时间要求
    expected_date = Column(Date, comment='期望完成日期')
    deadline = Column(DateTime, comment='截止时间')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    
    # 完成信息
    complete_time = Column(DateTime, comment='完成时间')
    actual_hours = Column(Numeric(10, 2), comment='实际工时')
    
    # 评价
    satisfaction_score = Column(Integer, comment='满意度评分(1-5)')
    feedback = Column(Text, comment='反馈意见')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关系
    deliverables = relationship('PresaleTicketDeliverable', back_populates='ticket')
    progress_records = relationship('PresaleTicketProgress', back_populates='ticket')
    
    __table_args__ = (
        Index('idx_presale_ticket_no', 'ticket_no'),
        Index('idx_presale_ticket_status', 'status'),
        Index('idx_presale_ticket_applicant', 'applicant_id'),
        Index('idx_presale_ticket_assignee', 'assignee_id'),
        Index('idx_presale_ticket_customer', 'customer_id'),
        {'comment': '售前支持工单表'}
    )


# ==================== 工单交付物 ====================

class PresaleTicketDeliverable(Base, TimestampMixin):
    """工单交付物"""
    __tablename__ = 'presale_ticket_deliverable'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ticket_id = Column(Integer, ForeignKey('presale_support_ticket.id'), nullable=False, comment='工单ID')
    
    # 交付物信息
    name = Column(String(200), nullable=False, comment='文件名称')
    file_type = Column(String(50), comment='文件类型')
    file_path = Column(String(500), comment='文件路径')
    file_size = Column(Integer, comment='文件大小(bytes)')
    version = Column(String(20), default='V1.0', comment='版本号')
    
    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')
    
    # 审核信息
    reviewer_id = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    review_time = Column(DateTime, comment='审核时间')
    review_comment = Column(Text, comment='审核意见')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关系
    ticket = relationship('PresaleSupportTicket', back_populates='deliverables')
    
    __table_args__ = (
        Index('idx_deliverable_ticket', 'ticket_id'),
        {'comment': '工单交付物表'}
    )


# ==================== 工单进度 ====================

class PresaleTicketProgress(Base):
    """工单进度记录"""
    __tablename__ = 'presale_ticket_progress'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ticket_id = Column(Integer, ForeignKey('presale_support_ticket.id'), nullable=False, comment='工单ID')
    
    # 进度信息
    progress_type = Column(String(20), nullable=False, comment='进度类型')
    content = Column(Text, comment='进度内容')
    progress_percent = Column(Integer, comment='进度百分比')
    
    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='操作人ID')
    operator_name = Column(String(50), comment='操作人')
    
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')
    
    # 关系
    ticket = relationship('PresaleSupportTicket', back_populates='progress_records')
    
    __table_args__ = (
        Index('idx_progress_ticket', 'ticket_id'),
        {'comment': '工单进度记录表'}
    )


# ==================== 技术方案 ====================

class PresaleSolution(Base, TimestampMixin):
    """技术方案"""
    __tablename__ = 'presale_solution'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    solution_no = Column(String(50), unique=True, nullable=False, comment='方案编号')
    
    # 方案信息
    name = Column(String(200), nullable=False, comment='方案名称')
    solution_type = Column(String(20), default='CUSTOM', comment='方案类型:STANDARD/CUSTOM')
    industry = Column(String(50), comment='所属行业')
    test_type = Column(String(100), comment='测试类型')
    
    # 关联信息
    ticket_id = Column(Integer, ForeignKey('presale_support_ticket.id'), comment='关联工单ID')
    customer_id = Column(Integer, comment='客户ID')
    opportunity_id = Column(Integer, comment='商机ID')
    
    # 方案内容
    requirement_summary = Column(Text, comment='需求概述')
    solution_overview = Column(Text, comment='方案概述')
    technical_spec = Column(Text, comment='技术规格')
    
    # 成本估算
    estimated_cost = Column(Numeric(12, 2), comment='预估成本')
    suggested_price = Column(Numeric(12, 2), comment='建议报价')
    cost_breakdown = Column(JSON, comment='成本明细(JSON)')
    
    # 工时估算
    estimated_hours = Column(Integer, comment='预估工时(小时)')
    estimated_duration = Column(Integer, comment='预估周期(天)')
    
    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')
    
    # 版本控制
    version = Column(String(20), default='V1.0', comment='版本')
    parent_id = Column(Integer, ForeignKey('presale_solution.id'), comment='父版本ID')
    
    # 审核
    reviewer_id = Column(Integer, ForeignKey('users.id'), comment='审核人')
    review_time = Column(DateTime, comment='审核时间')
    review_status = Column(String(20), comment='审核状态:PENDING/APPROVED/REJECTED')
    review_comment = Column(Text, comment='审核意见')
    
    # 编制人
    author_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='编制人ID')
    author_name = Column(String(50), comment='编制人姓名')
    
    # 关系
    cost_items = relationship('PresaleSolutionCost', back_populates='solution')
    parent_version = relationship('PresaleSolution', remote_side=[id], backref='child_versions')
    
    __table_args__ = (
        Index('idx_solution_no', 'solution_no'),
        Index('idx_solution_ticket', 'ticket_id'),
        Index('idx_solution_customer', 'customer_id'),
        Index('idx_solution_industry', 'industry'),
        {'comment': '技术方案表'}
    )


# ==================== 方案成本明细 ====================

class PresaleSolutionCost(Base, TimestampMixin):
    """方案成本明细"""
    __tablename__ = 'presale_solution_cost'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    solution_id = Column(Integer, ForeignKey('presale_solution.id'), nullable=False, comment='方案ID')
    
    # 成本项
    category = Column(String(50), nullable=False, comment='成本类别')
    item_name = Column(String(200), nullable=False, comment='项目名称')
    specification = Column(String(200), comment='规格型号')
    unit = Column(String(20), comment='单位')
    quantity = Column(Numeric(10, 2), comment='数量')
    unit_price = Column(Numeric(12, 2), comment='单价')
    amount = Column(Numeric(12, 2), comment='金额')
    
    # 备注
    remark = Column(String(500), comment='备注')
    
    # 排序
    sort_order = Column(Integer, default=0, comment='排序')
    
    # 关系
    solution = relationship('PresaleSolution', back_populates='cost_items')
    
    __table_args__ = (
        Index('idx_cost_solution', 'solution_id'),
        {'comment': '方案成本明细表'}
    )


# ==================== 方案模板库 ====================

class PresaleSolutionTemplate(Base, TimestampMixin):
    """方案模板库"""
    __tablename__ = 'presale_solution_template'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_no = Column(String(50), unique=True, nullable=False, comment='模板编号')
    
    # 模板信息
    name = Column(String(200), nullable=False, comment='模板名称')
    industry = Column(String(50), comment='适用行业')
    test_type = Column(String(100), comment='测试类型')
    description = Column(Text, comment='模板描述')
    
    # 模板内容
    content_template = Column(Text, comment='内容模板')
    cost_template = Column(JSON, comment='成本模板')
    
    # 附件
    attachments = Column(JSON, comment='附件列表')
    
    # 使用统计
    use_count = Column(Integer, default=0, comment='使用次数')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    __table_args__ = (
        Index('idx_template_no', 'template_no'),
        Index('idx_template_industry', 'industry'),
        {'comment': '方案模板库表'}
    )


# ==================== 售前人员工作负荷 ====================

class PresaleWorkload(Base, TimestampMixin):
    """售前人员工作负荷"""
    __tablename__ = 'presale_workload'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='人员ID')
    stat_date = Column(Date, nullable=False, comment='统计日期')
    
    # 工单统计
    pending_tickets = Column(Integer, default=0, comment='待处理工单数')
    processing_tickets = Column(Integer, default=0, comment='进行中工单数')
    completed_tickets = Column(Integer, default=0, comment='已完成工单数')
    
    # 工时统计
    planned_hours = Column(Numeric(10, 2), default=0, comment='计划工时')
    actual_hours = Column(Numeric(10, 2), default=0, comment='实际工时')
    
    # 方案统计
    solutions_count = Column(Integer, default=0, comment='方案数量')
    
    __table_args__ = (
        Index('idx_workload_user_date', 'user_id', 'stat_date', unique=True),
        Index('idx_workload_date', 'stat_date'),
        {'comment': '售前人员工作负荷表'}
    )


# ==================== 客户技术档案 ====================

class PresaleCustomerTechProfile(Base, TimestampMixin):
    """客户技术档案"""
    __tablename__ = 'presale_customer_tech_profile'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    customer_id = Column(Integer, nullable=False, unique=True, comment='客户ID')
    
    # 基本信息
    industry = Column(String(50), comment='所属行业')
    business_scope = Column(Text, comment='业务范围')
    
    # 技术需求特点
    common_test_types = Column(String(500), comment='常见测试类型')
    technical_requirements = Column(Text, comment='技术要求特点')
    quality_standards = Column(String(500), comment='质量标准要求')
    
    # 设备现状
    existing_equipment = Column(Text, comment='现有设备情况')
    it_infrastructure = Column(Text, comment='IT基础设施')
    mes_system = Column(String(100), comment='MES系统类型')
    
    # 合作历史
    cooperation_history = Column(Text, comment='合作历史')
    success_cases = Column(Text, comment='成功案例')
    
    # 关键联系人
    technical_contacts = Column(JSON, comment='技术联系人')
    
    # 备注
    notes = Column(Text, comment='备注')
    
    __table_args__ = (
        {'comment': '客户技术档案表'}
    )


# ==================== 投标记录 ====================

class PresaleTenderRecord(Base, TimestampMixin):
    """投标记录"""
    __tablename__ = 'presale_tender_record'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    ticket_id = Column(Integer, ForeignKey('presale_support_ticket.id'), comment='关联工单ID')
    opportunity_id = Column(Integer, comment='关联商机ID')
    
    # 投标信息
    tender_no = Column(String(50), comment='招标编号')
    tender_name = Column(String(200), nullable=False, comment='项目名称')
    customer_name = Column(String(100), comment='招标单位')
    
    # 时间节点
    publish_date = Column(Date, comment='发布日期')
    deadline = Column(DateTime, comment='投标截止时间')
    bid_opening_date = Column(Date, comment='开标日期')
    
    # 投标要求
    budget_amount = Column(Numeric(14, 2), comment='预算金额')
    qualification_requirements = Column(Text, comment='资质要求')
    technical_requirements = Column(Text, comment='技术要求')
    
    # 我方投标
    our_bid_amount = Column(Numeric(14, 2), comment='我方报价')
    technical_score = Column(Numeric(5, 2), comment='技术得分')
    commercial_score = Column(Numeric(5, 2), comment='商务得分')
    total_score = Column(Numeric(5, 2), comment='总得分')
    
    # 竞争对手
    competitors = Column(JSON, comment='竞争对手信息')
    
    # 结果
    result = Column(String(20), default='PENDING', comment='结果')
    result_reason = Column(Text, comment='中标/落标原因分析')
    
    # 负责人
    leader_id = Column(Integer, ForeignKey('users.id'), comment='投标负责人')
    team_members = Column(JSON, comment='投标团队')
    
    __table_args__ = (
        Index('idx_tender_opportunity', 'opportunity_id'),
        Index('idx_tender_result', 'result'),
        {'comment': '投标记录表'}
    )
