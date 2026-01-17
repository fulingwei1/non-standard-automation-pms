# -*- coding: utf-8 -*-
"""
生产计划模型
"""
from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProductionPlan(Base, TimestampMixin):
    """生产计划"""
    __tablename__ = 'production_plan'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    plan_no = Column(String(50), unique=True, nullable=False, comment='计划编号')
    plan_name = Column(String(200), nullable=False, comment='计划名称')
    plan_type = Column(String(20), nullable=False, default='MASTER', comment='计划类型:MASTER/WORKSHOP')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='关联项目ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID(车间计划)')
    plan_start_date = Column(Date, nullable=False, comment='计划开始日期')
    plan_end_date = Column(Date, nullable=False, comment='计划结束日期')
    status = Column(String(20), nullable=False, default='DRAFT', comment='状态')
    progress = Column(Integer, default=0, comment='进度(%)')
    description = Column(Text, nullable=True, comment='计划说明')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    work_orders = relationship('WorkOrder', back_populates='production_plan')

    __table_args__ = (
        Index('idx_prod_plan_no', 'plan_no'),
        Index('idx_prod_plan_project', 'project_id'),
        Index('idx_prod_plan_workshop', 'workshop_id'),
        Index('idx_prod_plan_status', 'status'),
        Index('idx_prod_plan_dates', 'plan_start_date', 'plan_end_date'),
        {'comment': '生产计划表'}
    )
