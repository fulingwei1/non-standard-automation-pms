# -*- coding: utf-8 -*-
"""
PMO模型 - 项目立项和阶段
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text

from ..base import Base, TimestampMixin


class PmoProjectInitiation(Base, TimestampMixin):
    """项目立项申请"""
    __tablename__ = 'pmo_project_initiation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    application_no = Column(String(50), unique=True, nullable=False, comment='申请编号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID(审批通过后关联)')

    # 申请信息
    project_name = Column(String(200), nullable=False, comment='项目名称')
    project_type = Column(String(20), default='NEW', comment='项目类型:NEW/UPGRADE/MAINTAIN')
    project_level = Column(String(5), comment='建议级别:A/B/C')

    # 客户合同
    customer_name = Column(String(100), nullable=False, comment='客户名称')
    contract_no = Column(String(50), comment='合同编号')
    contract_amount = Column(Numeric(14, 2), comment='合同金额')

    # 时间要求
    required_start_date = Column(Date, comment='要求开始日期')
    required_end_date = Column(Date, comment='要求交付日期')

    # 技术信息
    technical_solution_id = Column(Integer, comment='关联技术方案ID')
    requirement_summary = Column(Text, comment='需求概述')
    technical_difficulty = Column(String(20), comment='技术难度:LOW/MEDIUM/HIGH')

    # 资源需求
    estimated_hours = Column(Integer, comment='预估工时')
    resource_requirements = Column(Text, comment='资源需求说明')

    # 风险评估
    risk_assessment = Column(Text, comment='初步风险评估')

    # 申请人
    applicant_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID')
    applicant_name = Column(String(50), comment='申请人姓名')
    apply_time = Column(DateTime, default=datetime.now, comment='申请时间')

    # 审批状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 审批信息
    review_result = Column(Text, comment='评审结论')
    approved_pm_id = Column(Integer, ForeignKey('users.id'), comment='指定项目经理ID')
    approved_level = Column(String(5), comment='评定级别:A/B/C')
    approved_at = Column(DateTime, comment='审批时间')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')

    __table_args__ = (
        Index('idx_pmo_init_no', 'application_no'),
        Index('idx_pmo_init_status', 'status'),
        Index('idx_pmo_init_applicant', 'applicant_id'),
        {'comment': '项目立项申请表'}
    )


class PmoProjectPhase(Base, TimestampMixin):
    """项目阶段"""
    __tablename__ = 'pmo_project_phase'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 阶段信息
    phase_code = Column(String(20), nullable=False, comment='阶段编码')
    phase_name = Column(String(50), nullable=False, comment='阶段名称')
    phase_order = Column(Integer, default=0, comment='阶段顺序')

    # 时间
    plan_start_date = Column(Date, comment='计划开始')
    plan_end_date = Column(Date, comment='计划结束')
    actual_start_date = Column(Date, comment='实际开始')
    actual_end_date = Column(Date, comment='实际结束')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    progress = Column(Integer, default=0, comment='进度(%)')

    # 入口/出口条件
    entry_criteria = Column(Text, comment='入口条件')
    exit_criteria = Column(Text, comment='出口条件')
    entry_check_result = Column(Text, comment='入口检查结果')
    exit_check_result = Column(Text, comment='出口检查结果')

    # 评审
    review_required = Column(Boolean, default=True, comment='是否需要评审')
    review_date = Column(Date, comment='评审日期')
    review_result = Column(String(20), comment='评审结果:PASSED/CONDITIONAL/FAILED')
    review_notes = Column(Text, comment='评审记录')

    __table_args__ = (
        Index('idx_pmo_phase_project', 'project_id'),
        Index('idx_pmo_phase_code', 'phase_code'),
        {'comment': '项目阶段表'}
    )
