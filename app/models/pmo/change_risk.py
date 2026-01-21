# -*- coding: utf-8 -*-
"""
PMO模型 - 项目变更和风险
"""
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class PmoChangeRequest(Base, TimestampMixin):
    """项目变更申请"""
    __tablename__ = 'pmo_change_request'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    change_no = Column(String(50), unique=True, nullable=False, comment='变更编号')

    # 变更信息
    change_type = Column(String(20), nullable=False, comment='变更类型')
    change_level = Column(String(20), default='MINOR', comment='变更级别')
    title = Column(String(200), nullable=False, comment='变更标题')
    description = Column(Text, nullable=False, comment='变更描述')
    reason = Column(Text, comment='变更原因')

    # 影响评估
    schedule_impact = Column(Text, comment='进度影响')
    cost_impact = Column(Numeric(12, 2), comment='成本影响')
    quality_impact = Column(Text, comment='质量影响')
    resource_impact = Column(Text, comment='资源影响')

    # 申请人
    requestor_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申请人ID')
    requestor_name = Column(String(50), comment='申请人')
    request_time = Column(DateTime, default=datetime.now, comment='申请时间')

    # 审批状态
    status = Column(String(20), default='DRAFT', comment='状态')

    # 审批记录
    pm_approval = Column(Boolean, comment='项目经理审批')
    pm_approval_time = Column(DateTime, comment='项目经理审批时间')
    manager_approval = Column(Boolean, comment='部门经理审批')
    manager_approval_time = Column(DateTime, comment='部门经理审批时间')
    customer_approval = Column(Boolean, comment='客户确认')
    customer_approval_time = Column(DateTime, comment='客户确认时间')

    # 执行情况
    execution_status = Column(String(20), comment='执行状态:PENDING/EXECUTING/COMPLETED')
    execution_notes = Column(Text, comment='执行说明')
    completed_time = Column(DateTime, comment='完成时间')

    __table_args__ = (
        Index('idx_pmo_change_project', 'project_id'),
        Index('idx_pmo_change_no', 'change_no'),
        Index('idx_pmo_change_status', 'status'),
        {'comment': '项目变更申请表'}
    )


class PmoProjectRisk(Base, TimestampMixin):
    """项目风险"""
    __tablename__ = 'pmo_project_risk'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    risk_no = Column(String(50), unique=True, nullable=False, comment='风险编号')

    # 风险信息
    risk_category = Column(String(20), nullable=False, comment='风险类别')
    risk_name = Column(String(200), nullable=False, comment='风险名称')
    description = Column(Text, comment='风险描述')

    # 风险评估
    probability = Column(String(20), comment='发生概率:LOW/MEDIUM/HIGH')
    impact = Column(String(20), comment='影响程度:LOW/MEDIUM/HIGH')
    risk_level = Column(String(20), comment='风险等级:LOW/MEDIUM/HIGH/CRITICAL')

    # 应对措施
    response_strategy = Column(String(20), comment='应对策略:AVOID/MITIGATE/TRANSFER/ACCEPT')
    response_plan = Column(Text, comment='应对措施')

    # 责任人
    owner_id = Column(Integer, ForeignKey('users.id'), comment='责任人ID')
    owner_name = Column(String(50), comment='责任人')

    # 状态
    status = Column(String(20), default='IDENTIFIED', comment='状态')

    # 跟踪
    follow_up_date = Column(Date, comment='跟踪日期')
    last_update = Column(Text, comment='最新进展')

    # 触发/关闭
    trigger_condition = Column(Text, comment='触发条件')
    is_triggered = Column(Boolean, default=False, comment='是否已触发')
    triggered_date = Column(Date, comment='触发日期')
    closed_date = Column(Date, comment='关闭日期')
    closed_reason = Column(Text, comment='关闭原因')

    __table_args__ = (
        Index('idx_pmo_risk_project', 'project_id'),
        Index('idx_pmo_risk_level', 'risk_level'),
        Index('idx_pmo_risk_status', 'status'),
        {'comment': '项目风险表'}
    )
