# -*- coding: utf-8 -*-
"""
PMO模型 - 项目成本和会议
"""
from sqlalchemy import Column, Date, ForeignKey, Index, Integer, JSON, Numeric, String, Text, Time
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class PmoProjectCost(Base, TimestampMixin):
    """项目成本"""
    __tablename__ = 'pmo_project_cost'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 成本类别
    cost_category = Column(String(50), nullable=False, comment='成本类别')
    cost_item = Column(String(100), nullable=False, comment='成本项')

    # 金额
    budget_amount = Column(Numeric(12, 2), default=0, comment='预算金额')
    actual_amount = Column(Numeric(12, 2), default=0, comment='实际金额')

    # 时间
    cost_month = Column(String(7), comment='成本月份(YYYY-MM)')
    record_date = Column(Date, comment='记录日期')

    # 来源
    source_type = Column(String(50), comment='来源类型')
    source_id = Column(Integer, comment='来源ID')
    source_no = Column(String(50), comment='来源单号')

    # 备注
    remarks = Column(Text, comment='备注')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_pmo_cost_project', 'project_id'),
        Index('idx_pmo_cost_category', 'cost_category'),
        Index('idx_pmo_cost_month', 'cost_month'),
        {'comment': '项目成本表'}
    )


class PmoMeeting(Base, TimestampMixin):
    """项目会议"""
    __tablename__ = 'pmo_meeting'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID(可为空表示跨项目会议)')

    # 会议信息
    meeting_type = Column(String(20), nullable=False, comment='会议类型')
    meeting_name = Column(String(200), nullable=False, comment='会议名称')

    # 时间地点
    meeting_date = Column(Date, nullable=False, comment='会议日期')
    start_time = Column(Time, comment='开始时间')
    end_time = Column(Time, comment='结束时间')
    location = Column(String(100), comment='会议地点')

    # 人员
    organizer_id = Column(Integer, ForeignKey('users.id'), comment='组织者ID')
    organizer_name = Column(String(50), comment='组织者')
    attendees = Column(JSON, comment='参会人员')

    # 内容
    agenda = Column(Text, comment='会议议程')
    minutes = Column(Text, comment='会议纪要')
    decisions = Column(Text, comment='会议决议')
    action_items = Column(JSON, comment='待办事项')

    # 附件
    attachments = Column(JSON, comment='会议附件')

    # 状态
    status = Column(String(20), default='SCHEDULED', comment='状态:SCHEDULED/ONGOING/COMPLETED/CANCELLED')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    __table_args__ = (
        Index('idx_pmo_meeting_project', 'project_id'),
        Index('idx_pmo_meeting_date', 'meeting_date'),
        Index('idx_pmo_meeting_type', 'meeting_type'),
        {'comment': '项目会议表'}
    )
