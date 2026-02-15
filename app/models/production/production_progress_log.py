# -*- coding: utf-8 -*-
"""
生产进度日志模型
记录工单级别的进度变化历史
"""
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


class ProductionProgressLog(Base, TimestampMixin):
    """生产进度日志"""
    __tablename__ = 'production_progress_log'
    __table_args__ = (
        Index('idx_prod_progress_work_order', 'work_order_id'),
        Index('idx_prod_progress_workstation', 'workstation_id'),
        Index('idx_prod_progress_logged_at', 'logged_at'),
        Index('idx_prod_progress_status', 'status'),
        {'extend_existing': True, 'comment': '生产进度日志表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), nullable=True, comment='工位ID')
    
    # 进度信息
    previous_progress = Column(Integer, default=0, comment='之前进度(%)')
    current_progress = Column(Integer, nullable=False, comment='当前进度(%)')
    progress_delta = Column(Integer, comment='进度变化量(%)')
    
    # 产量信息
    completed_qty = Column(Integer, default=0, comment='已完成数量')
    qualified_qty = Column(Integer, default=0, comment='合格数量')
    defect_qty = Column(Integer, default=0, comment='不良数量')
    
    # 工时信息
    work_hours = Column(Numeric(10, 2), comment='本次工时(小时)')
    cumulative_hours = Column(Numeric(10, 2), comment='累计工时(小时)')
    
    # 状态信息
    status = Column(String(20), nullable=False, comment='工单状态：PENDING/IN_PROGRESS/PAUSED/COMPLETED/CANCELLED')
    previous_status = Column(String(20), comment='之前状态')
    
    # 记录信息
    logged_at = Column(DateTime, nullable=False, comment='记录时间')
    logged_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='记录人ID')
    note = Column(Text, comment='备注说明')
    
    # 偏差信息
    plan_progress = Column(Integer, comment='计划进度(%)')
    deviation = Column(Integer, comment='进度偏差(%)：实际-计划')
    is_delayed = Column(Integer, default=0, comment='是否延期：0-正常，1-延期')
    
    # 关系
    work_order = relationship('WorkOrder', backref='production_progress_logs')
    workstation = relationship('Workstation', backref='production_progress_logs')
    logger = relationship('User', foreign_keys=[logged_by])

    def __repr__(self):
        return f"<ProductionProgressLog work_order_id={self.work_order_id} progress={self.current_progress}%>"
