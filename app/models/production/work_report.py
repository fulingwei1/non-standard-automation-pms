# -*- coding: utf-8 -*-
"""
报工管理模型
"""
from datetime import datetime

from sqlalchemy import (
    Column,
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


class WorkReport(Base, TimestampMixin):
    """报工记录"""
    __tablename__ = 'work_report'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_no = Column(String(50), unique=True, nullable=False, comment='报工单号')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    worker_id = Column(Integer, ForeignKey('worker.id'), nullable=False, comment='工人ID')
    report_type = Column(String(20), nullable=False, comment='报工类型:START/PROGRESS/PAUSE/RESUME/COMPLETE')
    report_time = Column(DateTime, nullable=False, default=datetime.now, comment='报工时间')

    # 进度信息
    progress_percent = Column(Integer, nullable=True, comment='进度百分比')
    work_hours = Column(Numeric(10, 2), nullable=True, comment='本次工时(小时)')

    # 完工信息
    completed_qty = Column(Integer, nullable=True, comment='完成数量')
    qualified_qty = Column(Integer, nullable=True, comment='合格数量')
    defect_qty = Column(Integer, nullable=True, comment='不良数量')

    # 审核信息
    status = Column(String(20), nullable=False, default='PENDING', comment='状态')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审核人ID')
    approved_at = Column(DateTime, nullable=True, comment='审核时间')
    approve_comment = Column(Text, nullable=True, comment='审核意见')

    # 其他
    description = Column(Text, nullable=True, comment='工作描述')
    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    work_order = relationship('WorkOrder', back_populates='work_reports')
    worker = relationship('Worker', back_populates='work_reports')

    __table_args__ = (
        Index('idx_work_report_no', 'report_no'),
        Index('idx_work_report_order', 'work_order_id'),
        Index('idx_work_report_worker', 'worker_id'),
        Index('idx_work_report_type', 'report_type'),
        Index('idx_work_report_status', 'status'),
        Index('idx_work_report_time', 'report_time'),
        {'comment': '报工记录表'}
    )
