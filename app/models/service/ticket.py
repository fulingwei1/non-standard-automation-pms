# -*- coding: utf-8 -*-
"""
服务模型 - 服务工单
"""
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class ServiceTicket(Base, TimestampMixin):
    """服务工单表"""
    __tablename__ = 'service_tickets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_no = Column(String(50), unique=True, nullable=False, comment='工单号')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, comment='客户ID')

    # 问题信息
    problem_type = Column(String(20), nullable=False, comment='问题类型')
    problem_desc = Column(Text, nullable=False, comment='问题描述')
    urgency = Column(String(20), nullable=False, comment='紧急程度')

    # 兼容别名字段
    priority = Column(String(20), comment='优先级(兼容字段)')
    ticket_type = Column(String(20), comment='工单类型(兼容字段)')

    # 报告人信息
    reported_by = Column(String(50), nullable=False, comment='报告人')
    reported_time = Column(DateTime, nullable=False, comment='报告时间')

    # 处理人信息
    assigned_to_id = Column(Integer, ForeignKey('users.id'), comment='处理人ID')
    assigned_to_name = Column(String(50), comment='处理人姓名')
    assigned_time = Column(DateTime, comment='分配时间')

    # 状态和时间
    status = Column(String(20), default='PENDING', nullable=False, comment='状态')
    response_time = Column(DateTime, comment='响应时间')
    resolved_time = Column(DateTime, comment='解决时间')

    # 解决方案
    solution = Column(Text, comment='解决方案')
    root_cause = Column(Text, comment='根本原因')
    preventive_action = Column(Text, comment='预防措施')

    # 满意度
    satisfaction = Column(Integer, comment='满意度1-5')
    feedback = Column(Text, comment='客户反馈')

    # 时间线（JSON格式存储）
    timeline = Column(JSON, comment='时间线记录')

    # 关系
    project = relationship('Project', foreign_keys=[project_id])
    customer = relationship('Customer', foreign_keys=[customer_id])
    assignee = relationship('User', foreign_keys=[assigned_to_id])

    __table_args__ = (
        Index('idx_service_ticket_project', 'project_id'),
        Index('idx_service_ticket_customer', 'customer_id'),
        Index('idx_service_ticket_status', 'status'),
        {'comment': '服务工单表'},
    )

    # 多项目关联关系
    related_projects = relationship(
        'ServiceTicketProject',
        back_populates='ticket',
        cascade='all, delete-orphan'
    )

    # 抄送人员关系
    cc_users = relationship(
        'ServiceTicketCcUser',
        back_populates='ticket',
        cascade='all, delete-orphan'
    )

    # 关联问题关系
    related_issues = relationship(
        'Issue',
        foreign_keys='Issue.service_ticket_id',
        back_populates='service_ticket'
    )

    def __repr__(self):
        return f'<ServiceTicket {self.ticket_no}>'


class ServiceTicketProject(Base, TimestampMixin):
    """工单项目关联表（支持多对多）"""
    __tablename__ = 'service_ticket_projects'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('service_tickets.id', ondelete='CASCADE'), nullable=False, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    is_primary = Column(Boolean, default=False, comment='是否主项目')

    # 关系
    ticket = relationship('ServiceTicket', back_populates='related_projects')
    project = relationship('Project', foreign_keys=[project_id])

    __table_args__ = (
        Index('idx_ticket_projects_ticket', 'ticket_id'),
        Index('idx_ticket_projects_project', 'project_id'),
        {'comment': '工单项目关联表'},
    )

    def __repr__(self):
        return f'<ServiceTicketProject ticket_id={self.ticket_id} project_id={self.project_id}>'


class ServiceTicketCcUser(Base, TimestampMixin):
    """工单抄送人员表"""
    __tablename__ = 'service_ticket_cc_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('service_tickets.id', ondelete='CASCADE'), nullable=False, comment='工单ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    notified_at = Column(DateTime, comment='通知时间')
    read_at = Column(DateTime, comment='阅读时间')

    # 关系
    ticket = relationship('ServiceTicket', back_populates='cc_users')
    user = relationship('User', foreign_keys=[user_id])

    __table_args__ = (
        Index('idx_ticket_cc_ticket', 'ticket_id'),
        Index('idx_ticket_cc_user', 'user_id'),
        {'comment': '工单抄送人员表'},
    )

    def __repr__(self):
        return f'<ServiceTicketCcUser ticket_id={self.ticket_id} user_id={self.user_id}>'
