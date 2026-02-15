# -*- coding: utf-8 -*-
"""
工位实时状态模型
记录工位当前的实时运行状态和产能利用情况
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


class WorkstationStatus(Base, TimestampMixin):
    """工位实时状态"""
    __tablename__ = 'workstation_status'
    __table_args__ = (
        Index('idx_ws_status_workstation', 'workstation_id'),
        Index('idx_ws_status_work_order', 'current_work_order_id'),
        Index('idx_ws_status_state', 'current_state'),
        Index('idx_ws_status_updated', 'status_updated_at'),
        {'extend_existing': True, 'comment': '工位实时状态表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), unique=True, nullable=False, comment='工位ID')
    
    # 当前状态
    current_state = Column(String(20), nullable=False, default='IDLE', 
                          comment='当前状态：IDLE/BUSY/PAUSED/MAINTENANCE/OFFLINE')
    current_work_order_id = Column(Integer, ForeignKey('work_order.id'), comment='当前工单ID')
    current_operator_id = Column(Integer, ForeignKey('worker.id'), comment='当前操作工ID')
    
    # 进度信息
    current_progress = Column(Integer, default=0, comment='当前工单进度(%)')
    completed_qty_today = Column(Integer, default=0, comment='今日完成数量')
    target_qty_today = Column(Integer, default=0, comment='今日目标数量')
    
    # 产能信息
    capacity_utilization = Column(Numeric(5, 2), default=0, comment='产能利用率(%)')
    work_hours_today = Column(Numeric(10, 2), default=0, comment='今日工作工时')
    idle_hours_today = Column(Numeric(10, 2), default=0, comment='今日空闲工时')
    planned_hours_today = Column(Numeric(10, 2), default=8, comment='今日计划工时')
    
    # 效率指标
    efficiency_rate = Column(Numeric(5, 2), comment='生产效率(%)')
    quality_rate = Column(Numeric(5, 2), default=100, comment='合格率(%)')
    
    # 预警信息
    is_bottleneck = Column(Integer, default=0, comment='是否瓶颈工位：0-否，1-是')
    bottleneck_level = Column(Integer, default=0, comment='瓶颈等级：0-正常，1-轻度，2-中度，3-严重')
    alert_count = Column(Integer, default=0, comment='今日预警次数')
    
    # 时间信息
    status_updated_at = Column(DateTime, nullable=False, comment='状态更新时间')
    last_work_start_time = Column(DateTime, comment='最后开工时间')
    last_work_end_time = Column(DateTime, comment='最后完工时间')
    
    # 备注
    remark = Column(Text, comment='备注')
    
    # 关系
    workstation = relationship('Workstation', backref='current_status')
    current_work_order = relationship('WorkOrder', foreign_keys=[current_work_order_id])
    current_operator = relationship('Worker', foreign_keys=[current_operator_id])

    def __repr__(self):
        return f"<WorkstationStatus workstation_id={self.workstation_id} state={self.current_state}>"
