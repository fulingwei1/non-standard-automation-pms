# -*- coding: utf-8 -*-
"""
工人效率记录模型
工人效率 = 标准工时 / 实际工时 × 100%
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
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


class WorkerEfficiencyRecord(Base, TimestampMixin):
    """工人效率记录表"""
    __tablename__ = 'worker_efficiency_record'
    __table_args__ = (
        Index('idx_worker_eff_worker_date', 'worker_id', 'record_date'),
        Index('idx_worker_eff_workshop', 'workshop_id'),
        Index('idx_worker_eff_date', 'record_date'),
        Index('idx_worker_eff_efficiency', 'efficiency'),
        {'extend_existing': True, 'comment': '工人效率记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联信息
    worker_id = Column(Integer, ForeignKey('worker.id'), nullable=False, comment='工人ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), nullable=True, comment='工位ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    
    # 时间信息
    record_date = Column(Date, nullable=False, comment='记录日期')
    shift = Column(String(20), nullable=True, comment='班次(早班/中班/晚班)')
    work_start_time = Column(DateTime, nullable=True, comment='开始工作时间')
    work_end_time = Column(DateTime, nullable=True, comment='结束工作时间')
    
    # 工时数据 (小时)
    standard_hours = Column(Numeric(10, 2), nullable=False, comment='标准工时(小时)')
    actual_hours = Column(Numeric(10, 2), nullable=False, comment='实际工时(小时)')
    overtime_hours = Column(Numeric(10, 2), default=0, comment='加班工时(小时)')
    break_hours = Column(Numeric(10, 2), default=0, comment='休息时间(小时)')
    idle_hours = Column(Numeric(10, 2), default=0, comment='空闲时间(小时,如等料)')
    
    # 产量数据
    completed_qty = Column(Integer, nullable=False, comment='完成数量(件)')
    qualified_qty = Column(Integer, nullable=False, comment='合格数量(件)')
    defect_qty = Column(Integer, default=0, comment='不良数量(件)')
    rework_qty = Column(Integer, default=0, comment='返工数量(件)')
    
    # 效率指标 (百分比 0-999.99, 可超过100%)
    efficiency = Column(Numeric(6, 2), nullable=False, comment='工作效率(%) = 标准工时/实际工时×100')
    quality_rate = Column(Numeric(5, 2), nullable=False, comment='合格率(%) = 合格数/完成数×100')
    utilization_rate = Column(Numeric(5, 2), nullable=False, comment='利用率(%) = (实际工时-空闲)/实际工时×100')
    
    # 综合效率 = 工作效率 × 合格率 × 利用率
    overall_efficiency = Column(Numeric(6, 2), nullable=False, comment='综合效率(%) = 效率×质量×利用率')
    
    # 技能相关
    skill_level = Column(String(20), nullable=True, comment='技能等级')
    process_type = Column(String(50), nullable=True, comment='工序类型')
    complexity_factor = Column(Numeric(3, 2), default=1.0, comment='复杂度系数(0.5-2.0)')
    
    # 绩效数据
    performance_score = Column(Numeric(5, 2), nullable=True, comment='绩效得分(0-100)')
    attendance_rate = Column(Numeric(5, 2), nullable=True, comment='出勤率(%)')
    safety_incidents = Column(Integer, default=0, comment='安全事件数')
    
    # 辅助信息
    task_description = Column(Text, nullable=True, comment='任务描述')
    inefficiency_reason = Column(Text, nullable=True, comment='低效原因')
    improvement_suggestion = Column(Text, nullable=True, comment='改进建议')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 计算标志
    is_auto_calculated = Column(Boolean, default=False, comment='是否自动计算')
    calculated_at = Column(DateTime, nullable=True, comment='计算时间')
    calculated_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='计算人ID')
    
    # 审核状态
    is_confirmed = Column(Boolean, default=False, comment='是否确认')
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='确认人ID')
    confirmed_at = Column(DateTime, nullable=True, comment='确认时间')
    
    # 关系
    worker = relationship('Worker', foreign_keys=[worker_id], backref='efficiency_records')
    workshop = relationship('Workshop', backref='worker_efficiency_records')
    workstation = relationship('Workstation', backref='worker_efficiency_records')
    work_order = relationship('WorkOrder', backref='worker_efficiency_records')
