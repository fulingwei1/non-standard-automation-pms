# -*- coding: utf-8 -*-
"""
质检记录模型
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


class QualityInspection(Base, TimestampMixin):
    """质检记录"""
    __tablename__ = 'quality_inspection'
    __table_args__ = (
        Index('idx_quality_inspection_work_order', 'work_order_id'),
        Index('idx_quality_inspection_material', 'material_id'),
        Index('idx_quality_inspection_result', 'inspection_result'),
        Index('idx_quality_inspection_date', 'inspection_date'),
        Index('idx_quality_inspection_batch', 'batch_no'),
        {'extend_existing': True, 'comment': '质检记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    inspection_no = Column(String(50), unique=True, nullable=False, comment='质检单号')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
    batch_no = Column(String(50), nullable=True, comment='批次号')
    
    # 检验信息
    inspection_type = Column(String(20), nullable=False, default='PROCESS', comment='检验类型: IQC(来料)/IPQC(过程)/FQC(成品)/OQC(出货)')
    inspection_date = Column(DateTime, nullable=False, comment='检验时间')
    inspector_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='检验员ID')
    
    # 数量信息
    inspection_qty = Column(Integer, nullable=False, comment='检验数量')
    qualified_qty = Column(Integer, default=0, comment='合格数量')
    defect_qty = Column(Integer, default=0, comment='不良数量')
    
    # 检验结果
    inspection_result = Column(String(20), nullable=False, default='PENDING', comment='检验结果: PASS/FAIL/PENDING')
    defect_rate = Column(Numeric(5, 2), default=0.0, comment='不良率(%)')
    
    # 测量数据 (用于SPC分析)
    measured_value = Column(Numeric(12, 4), nullable=True, comment='测量值')
    spec_upper_limit = Column(Numeric(12, 4), nullable=True, comment='规格上限')
    spec_lower_limit = Column(Numeric(12, 4), nullable=True, comment='规格下限')
    measurement_unit = Column(String(20), nullable=True, comment='测量单位')
    
    # 不良信息
    defect_type = Column(String(50), nullable=True, comment='不良类型')
    defect_description = Column(Text, nullable=True, comment='不良描述')
    defect_images = Column(Text, nullable=True, comment='不良照片(JSON数组)')
    
    # 处理信息
    handling_result = Column(String(20), nullable=True, comment='处理结果: REWORK(返工)/SCRAP(报废)/CONCESSION(让步接收)')
    rework_order_id = Column(Integer, ForeignKey('rework_order.id'), nullable=True, comment='返工单ID')
    
    # 其他
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

    # 关系
    inspector = relationship('User', foreign_keys=[inspector_id])
    rework_order = relationship('ReworkOrder', back_populates='inspections')


class DefectAnalysis(Base, TimestampMixin):
    """不良品分析"""
    __tablename__ = 'defect_analysis'
    __table_args__ = (
        Index('idx_defect_analysis_inspection', 'inspection_id'),
        Index('idx_defect_analysis_type', 'defect_type'),
        Index('idx_defect_analysis_date', 'analysis_date'),
        {'extend_existing': True, 'comment': '不良品分析表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    inspection_id = Column(Integer, ForeignKey('quality_inspection.id'), nullable=False, comment='质检记录ID')
    analysis_no = Column(String(50), unique=True, nullable=False, comment='分析单号')
    
    # 分析信息
    analysis_date = Column(DateTime, nullable=False, comment='分析时间')
    analyst_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='分析员ID')
    defect_type = Column(String(50), nullable=False, comment='不良类型')
    defect_qty = Column(Integer, nullable=False, comment='不良数量')
    
    # 根因分析 (5M1E)
    root_cause_man = Column(Text, nullable=True, comment='人因(Man)')
    root_cause_machine = Column(Text, nullable=True, comment='机因(Machine)')
    root_cause_material = Column(Text, nullable=True, comment='料因(Material)')
    root_cause_method = Column(Text, nullable=True, comment='法因(Method)')
    root_cause_measurement = Column(Text, nullable=True, comment='测因(Measurement)')
    root_cause_environment = Column(Text, nullable=True, comment='环因(Environment)')
    
    # 关联信息
    related_equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True, comment='关联设备ID')
    related_worker_id = Column(Integer, ForeignKey('worker.id'), nullable=True, comment='关联工人ID')
    related_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='关联物料ID')
    
    # 纠正措施
    corrective_action = Column(Text, nullable=True, comment='纠正措施')
    preventive_action = Column(Text, nullable=True, comment='预防措施')
    responsible_person_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='责任人ID')
    due_date = Column(DateTime, nullable=True, comment='完成期限')
    completion_date = Column(DateTime, nullable=True, comment='实际完成时间')
    
    # 效果验证
    verification_result = Column(String(20), nullable=True, comment='验证结果: EFFECTIVE/INEFFECTIVE')
    verification_date = Column(DateTime, nullable=True, comment='验证时间')
    verifier_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='验证人ID')
    
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

    # 关系
    analyst = relationship('User', foreign_keys=[analyst_id])


class QualityAlertRule(Base, TimestampMixin):
    """质量预警规则"""
    __tablename__ = 'quality_alert_rule'
    __table_args__ = (
        Index('idx_quality_alert_rule_enabled', 'enabled'),
        Index('idx_quality_alert_rule_type', 'alert_type'),
        {'extend_existing': True, 'comment': '质量预警规则表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_no = Column(String(50), unique=True, nullable=False, comment='规则编号')
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    
    # 规则配置
    alert_type = Column(String(20), nullable=False, comment='预警类型: DEFECT_RATE/SPC_UCL/SPC_LCL/TREND')
    target_material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='目标物料ID(空则全局)')
    target_process_id = Column(Integer, ForeignKey('process_dict.id'), nullable=True, comment='目标工序ID')
    
    # 阈值配置
    threshold_value = Column(Numeric(12, 4), nullable=False, comment='阈值')
    threshold_operator = Column(String(10), nullable=False, default='GT', comment='比较运算符: GT/GTE/LT/LTE/EQ')
    time_window_hours = Column(Integer, default=24, comment='时间窗口(小时)')
    min_sample_size = Column(Integer, default=5, comment='最小样本数')
    
    # 预警配置
    alert_level = Column(String(20), nullable=False, default='WARNING', comment='预警级别: INFO/WARNING/CRITICAL')
    notify_users = Column(Text, nullable=True, comment='通知用户ID列表(JSON)')
    notify_channels = Column(Text, nullable=True, comment='通知渠道(JSON): EMAIL/SMS/WECHAT')
    
    # 状态
    enabled = Column(Integer, default=1, comment='是否启用: 0-禁用/1-启用')
    last_triggered_at = Column(DateTime, nullable=True, comment='最后触发时间')
    trigger_count = Column(Integer, default=0, comment='触发次数')
    
    description = Column(Text, nullable=True, comment='规则描述')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')


class ReworkOrder(Base, TimestampMixin):
    """返工单"""
    __tablename__ = 'rework_order'
    __table_args__ = (
        Index('idx_rework_order_no', 'rework_order_no'),
        Index('idx_rework_order_status', 'status'),
        Index('idx_rework_order_work_order', 'original_work_order_id'),
        Index('idx_rework_order_inspection', 'quality_inspection_id'),
        {'extend_existing': True, 'comment': '返工单表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rework_order_no = Column(String(50), unique=True, nullable=False, comment='返工单号')
    original_work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='原工单ID')
    quality_inspection_id = Column(Integer, ForeignKey('quality_inspection.id'), nullable=True, comment='质检记录ID')
    
    # 返工信息
    rework_qty = Column(Integer, nullable=False, comment='返工数量')
    rework_reason = Column(Text, nullable=False, comment='返工原因')
    defect_type = Column(String(50), nullable=True, comment='不良类型')
    
    # 派工信息
    assigned_to = Column(Integer, ForeignKey('worker.id'), nullable=True, comment='指派给(工人ID)')
    assigned_at = Column(DateTime, nullable=True, comment='派工时间')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    workstation_id = Column(Integer, ForeignKey('workstation.id'), nullable=True, comment='工位ID')
    
    # 时间信息
    plan_start_date = Column(DateTime, nullable=True, comment='计划开始时间')
    plan_end_date = Column(DateTime, nullable=True, comment='计划结束时间')
    actual_start_time = Column(DateTime, nullable=True, comment='实际开始时间')
    actual_end_time = Column(DateTime, nullable=True, comment='实际结束时间')
    
    # 完成信息
    completed_qty = Column(Integer, default=0, comment='完成数量')
    qualified_qty = Column(Integer, default=0, comment='合格数量')
    scrap_qty = Column(Integer, default=0, comment='报废数量')
    actual_hours = Column(Numeric(10, 2), default=0, comment='实际工时')
    
    # 成本信息
    rework_cost = Column(Numeric(12, 2), default=0, comment='返工成本')
    
    # 状态
    status = Column(String(20), nullable=False, default='PENDING', comment='状态: PENDING/IN_PROGRESS/COMPLETED/CANCELLED')
    completion_note = Column(Text, nullable=True, comment='完成说明')
    
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

    # 关系
    original_work_order = relationship('WorkOrder', foreign_keys=[original_work_order_id])
    assigned_worker = relationship('Worker', foreign_keys=[assigned_to])
    inspections = relationship('QualityInspection', back_populates='rework_order')
