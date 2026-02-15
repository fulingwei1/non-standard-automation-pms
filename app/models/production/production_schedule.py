# -*- coding: utf-8 -*-
"""
生产排程模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class ProductionSchedule(Base, TimestampMixin):
    """生产排程表"""
    __tablename__ = 'production_schedule'
    __table_args__ = (
        Index('idx_schedule_work_order', 'work_order_id'),
        Index('idx_schedule_equipment', 'equipment_id'),
        Index('idx_schedule_worker', 'worker_id'),
        Index('idx_schedule_status', 'status'),
        Index('idx_schedule_time', 'scheduled_start_time', 'scheduled_end_time'),
        Index('idx_schedule_plan', 'schedule_plan_id'),
        {'extend_existing': True, 'comment': '生产排程表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联信息
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    schedule_plan_id = Column(Integer, nullable=True, comment='排程方案ID')
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True, comment='设备ID')
    worker_id = Column(Integer, ForeignKey('worker.id'), nullable=True, comment='工人ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    process_id = Column(Integer, ForeignKey('process_dict.id'), nullable=True, comment='工序ID')
    
    # 排程时间
    scheduled_start_time = Column(DateTime, nullable=False, comment='计划开始时间')
    scheduled_end_time = Column(DateTime, nullable=False, comment='计划结束时间')
    duration_hours = Column(Float, nullable=False, comment='计划时长(小时)')
    
    # 实际执行时间
    actual_start_time = Column(DateTime, nullable=True, comment='实际开始时间')
    actual_end_time = Column(DateTime, nullable=True, comment='实际结束时间')
    actual_duration_hours = Column(Float, nullable=True, comment='实际时长(小时)')
    
    # 优先级和状态
    priority_score = Column(Float, default=0, comment='优先级评分')
    status = Column(String(20), nullable=False, default='PENDING', comment='状态: PENDING/CONFIRMED/IN_PROGRESS/COMPLETED/CANCELLED')
    is_urgent = Column(Boolean, default=False, comment='是否紧急插单')
    
    # 排程算法信息
    algorithm_version = Column(String(50), nullable=True, comment='排程算法版本')
    score = Column(Float, nullable=True, comment='排程评分')
    constraints_met = Column(JSON, nullable=True, comment='约束条件满足情况')
    
    # 调整信息
    is_manually_adjusted = Column(Boolean, default=False, comment='是否手动调整')
    adjustment_reason = Column(Text, nullable=True, comment='调整原因')
    adjusted_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='调整人ID')
    adjusted_at = Column(DateTime, nullable=True, comment='调整时间')
    
    # 其他
    sequence_no = Column(Integer, nullable=True, comment='排序号')
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='确认人ID')
    confirmed_at = Column(DateTime, nullable=True, comment='确认时间')
    
    # 关系
    work_order = relationship('WorkOrder', foreign_keys=[work_order_id])
    equipment = relationship('Equipment', foreign_keys=[equipment_id])
    worker = relationship('Worker', foreign_keys=[worker_id])
    workshop = relationship('Workshop', foreign_keys=[workshop_id])
    conflicts = relationship('ResourceConflict', back_populates='schedule', foreign_keys='ResourceConflict.schedule_id')
    adjustments = relationship('ScheduleAdjustmentLog', back_populates='schedule')


class ResourceConflict(Base, TimestampMixin):
    """资源冲突记录表"""
    __tablename__ = 'resource_conflict'
    __table_args__ = (
        Index('idx_conflict_schedule', 'schedule_id'),
        Index('idx_conflict_type', 'conflict_type'),
        Index('idx_conflict_status', 'status'),
        Index('idx_conflict_resource', 'resource_type', 'resource_id'),
        {'extend_existing': True, 'comment': '资源冲突记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 排程信息
    schedule_id = Column(Integer, ForeignKey('production_schedule.id'), nullable=False, comment='排程ID')
    conflicting_schedule_id = Column(Integer, ForeignKey('production_schedule.id'), nullable=True, comment='冲突的排程ID')
    
    # 冲突类型
    conflict_type = Column(String(50), nullable=False, comment='冲突类型: EQUIPMENT/WORKER/TIME_OVERLAP/SKILL_MISMATCH/CAPACITY_EXCEEDED')
    resource_type = Column(String(50), nullable=True, comment='资源类型: equipment/worker/workshop')
    resource_id = Column(Integer, nullable=True, comment='资源ID')
    
    # 冲突详情
    conflict_description = Column(Text, nullable=True, comment='冲突描述')
    conflict_details = Column(JSON, nullable=True, comment='冲突详细信息')
    severity = Column(String(20), nullable=False, default='MEDIUM', comment='严重程度: LOW/MEDIUM/HIGH/CRITICAL')
    
    # 时间冲突信息
    conflict_start_time = Column(DateTime, nullable=True, comment='冲突开始时间')
    conflict_end_time = Column(DateTime, nullable=True, comment='冲突结束时间')
    overlap_duration_hours = Column(Float, nullable=True, comment='重叠时长(小时)')
    
    # 解决方案
    resolution_suggestion = Column(Text, nullable=True, comment='建议解决方案')
    resolution_action = Column(Text, nullable=True, comment='实际解决措施')
    status = Column(String(20), nullable=False, default='UNRESOLVED', comment='状态: UNRESOLVED/RESOLVED/IGNORED')
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='解决人ID')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')
    
    # 其他
    detected_at = Column(DateTime, nullable=False, comment='检测时间')
    detected_by = Column(String(50), nullable=True, comment='检测来源: AUTO/MANUAL')
    remark = Column(Text, nullable=True, comment='备注')
    
    # 关系
    schedule = relationship('ProductionSchedule', back_populates='conflicts', foreign_keys=[schedule_id])
    conflicting_schedule = relationship('ProductionSchedule', foreign_keys=[conflicting_schedule_id])


class ScheduleAdjustmentLog(Base, TimestampMixin):
    """排程调整日志表"""
    __tablename__ = 'schedule_adjustment_log'
    __table_args__ = (
        Index('idx_adjustment_schedule', 'schedule_id'),
        Index('idx_adjustment_type', 'adjustment_type'),
        Index('idx_adjustment_time', 'adjusted_at'),
        Index('idx_adjustment_user', 'adjusted_by'),
        {'extend_existing': True, 'comment': '排程调整日志表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 排程信息
    schedule_id = Column(Integer, ForeignKey('production_schedule.id'), nullable=False, comment='排程ID')
    schedule_plan_id = Column(Integer, nullable=True, comment='排程方案ID')
    
    # 调整类型
    adjustment_type = Column(String(50), nullable=False, comment='调整类型: TIME_CHANGE/RESOURCE_CHANGE/PRIORITY_CHANGE/URGENT_INSERT/CANCEL/RESTORE')
    trigger_source = Column(String(50), nullable=False, comment='触发源: MANUAL/AUTO_OPTIMIZE/CONFLICT_RESOLUTION/URGENT_ORDER')
    
    # 调整前后对比
    before_data = Column(JSON, nullable=True, comment='调整前数据')
    after_data = Column(JSON, nullable=True, comment='调整后数据')
    changes_summary = Column(Text, nullable=True, comment='变更摘要')
    
    # 调整原因和影响
    reason = Column(Text, nullable=False, comment='调整原因')
    impact_analysis = Column(JSON, nullable=True, comment='影响分析')
    affected_schedules_count = Column(Integer, default=0, comment='影响的排程数量')
    
    # 调整人信息
    adjusted_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='调整人ID')
    adjusted_at = Column(DateTime, nullable=False, comment='调整时间')
    
    # 审批信息
    requires_approval = Column(Boolean, default=False, comment='是否需要审批')
    approval_status = Column(String(20), nullable=True, comment='审批状态: PENDING/APPROVED/REJECTED')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    approval_comment = Column(Text, nullable=True, comment='审批意见')
    
    # 其他
    remark = Column(Text, nullable=True, comment='备注')
    metadata = Column(JSON, nullable=True, comment='元数据')
    
    # 关系
    schedule = relationship('ProductionSchedule', back_populates='adjustments')
