# -*- coding: utf-8 -*-
"""
物料跟踪系统 - 数据模型
Team 5: 物料全流程追溯
"""
from datetime import datetime

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


class MaterialBatch(Base, TimestampMixin):
    """物料批次表 - 用于批次追溯"""
    __tablename__ = 'material_batch'
    __table_args__ = (
        Index('idx_mat_batch_no', 'batch_no'),
        Index('idx_mat_batch_material', 'material_id'),
        Index('idx_mat_batch_status', 'status'),
        Index('idx_mat_batch_date', 'production_date'),
        {'extend_existing': True, 'comment': '物料批次表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    batch_no = Column(String(100), unique=True, nullable=False, comment='批次号')
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    
    # 批次基本信息
    production_date = Column(Date, nullable=True, comment='生产日期')
    expire_date = Column(Date, nullable=True, comment='失效日期')
    supplier_id = Column(Integer, ForeignKey('vendors.id'), nullable=True, comment='供应商ID')
    supplier_batch_no = Column(String(100), nullable=True, comment='供应商批次号')
    
    # 数量信息
    initial_qty = Column(Numeric(14, 4), nullable=False, comment='初始数量')
    current_qty = Column(Numeric(14, 4), nullable=False, comment='当前库存数量')
    consumed_qty = Column(Numeric(14, 4), default=0, comment='已消耗数量')
    reserved_qty = Column(Numeric(14, 4), default=0, comment='预留数量')
    
    # 质量信息
    quality_status = Column(String(20), default='QUALIFIED', comment='质检状态')
    quality_report_no = Column(String(100), nullable=True, comment='质检报告编号')
    quality_inspector_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='质检员ID')
    quality_date = Column(DateTime, nullable=True, comment='质检日期')
    
    # 存储信息
    warehouse_location = Column(String(100), nullable=True, comment='仓库位置')
    
    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE-使用中, DEPLETED-已耗尽, EXPIRED-已过期, LOCKED-已锁定')
    
    # 条码/二维码
    barcode = Column(String(200), unique=True, nullable=True, comment='条形码')
    qrcode = Column(String(500), nullable=True, comment='二维码数据')
    
    remark = Column(Text, nullable=True, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

    # 关系
    material = relationship('Material')
    consumptions = relationship('MaterialConsumption', back_populates='batch', lazy='dynamic')

    def __repr__(self):
        return f'<MaterialBatch {self.batch_no}>'


class MaterialConsumption(Base, TimestampMixin):
    """物料消耗记录表"""
    __tablename__ = 'material_consumption'
    __table_args__ = (
        Index('idx_mat_cons_batch', 'batch_id'),
        Index('idx_mat_cons_material', 'material_id'),
        Index('idx_mat_cons_work_order', 'work_order_id'),
        Index('idx_mat_cons_date', 'consumption_date'),
        Index('idx_mat_cons_project', 'project_id'),
        {'extend_existing': True, 'comment': '物料消耗记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    consumption_no = Column(String(100), unique=True, nullable=False, comment='消耗单号')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    batch_id = Column(Integer, ForeignKey('material_batch.id'), nullable=True, comment='批次ID')
    material_code = Column(String(50), nullable=False, comment='物料编码(冗余)')
    material_name = Column(String(200), nullable=False, comment='物料名称(冗余)')
    
    # 消耗信息
    consumption_date = Column(DateTime, nullable=False, default=datetime.now, comment='消耗时间')
    consumption_qty = Column(Numeric(14, 4), nullable=False, comment='消耗数量')
    unit = Column(String(20), nullable=False, default='件', comment='单位')
    
    # 关联信息
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')
    requisition_id = Column(Integer, ForeignKey('material_requisition.id'), nullable=True, comment='领料单ID')
    
    # 消耗类型
    consumption_type = Column(String(20), default='PRODUCTION', comment='消耗类型: PRODUCTION-生产, TESTING-测试, WASTE-报废, REWORK-返工, OTHER-其他')
    
    # 标准消耗对比 (用于浪费识别)
    standard_qty = Column(Numeric(14, 4), nullable=True, comment='标准消耗数量')
    variance_qty = Column(Numeric(14, 4), default=0, comment='差异数量 (实际-标准)')
    variance_rate = Column(Numeric(5, 2), default=0, comment='差异比例(%)')
    is_waste = Column(Boolean, default=False, comment='是否异常浪费')
    
    # 操作信息
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='操作人ID')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='车间ID')
    
    # 成本信息
    unit_price = Column(Numeric(12, 4), default=0, comment='单价')
    total_cost = Column(Numeric(14, 2), default=0, comment='总成本')
    
    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    material = relationship('Material')
    batch = relationship('MaterialBatch', back_populates='consumptions')
    work_order = relationship('WorkOrder', foreign_keys=[work_order_id])
    project = relationship('Project', foreign_keys=[project_id])

    def __repr__(self):
        return f'<MaterialConsumption {self.consumption_no}>'


class MaterialAlert(Base, TimestampMixin):
    """物料预警记录表"""
    __tablename__ = 'material_alert'
    __table_args__ = (
        Index('idx_mat_alert_material', 'material_id'),
        Index('idx_mat_alert_type', 'alert_type'),
        Index('idx_mat_alert_status', 'status'),
        Index('idx_mat_alert_level', 'alert_level'),
        Index('idx_mat_alert_date', 'alert_date'),
        {'extend_existing': True, 'comment': '物料预警记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_no = Column(String(100), unique=True, nullable=False, comment='预警单号')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码(冗余)')
    material_name = Column(String(200), nullable=False, comment='物料名称(冗余)')
    
    # 预警信息
    alert_date = Column(DateTime, nullable=False, default=datetime.now, comment='预警时间')
    alert_type = Column(String(30), nullable=False, comment='预警类型: SHORTAGE-缺料, LOW_STOCK-低库存, EXPIRED-过期, SLOW_MOVING-呆滞, HIGH_WASTE-高浪费')
    alert_level = Column(String(20), default='WARNING', comment='预警级别: INFO-提示, WARNING-警告, CRITICAL-严重, URGENT-紧急')
    
    # 库存信息
    current_stock = Column(Numeric(14, 4), default=0, comment='当前库存')
    safety_stock = Column(Numeric(14, 4), default=0, comment='安全库存')
    required_qty = Column(Numeric(14, 4), default=0, comment='需求数量')
    shortage_qty = Column(Numeric(14, 4), default=0, comment='短缺数量')
    
    # 在途信息
    in_transit_qty = Column(Numeric(14, 4), default=0, comment='在途数量')
    expected_arrival_date = Column(Date, nullable=True, comment='预计到货日期')
    
    # 消耗速率信息
    avg_daily_consumption = Column(Numeric(14, 4), default=0, comment='平均日消耗')
    days_to_stockout = Column(Integer, default=0, comment='预计缺货天数')
    
    # 预警描述
    alert_message = Column(Text, nullable=False, comment='预警消息')
    recommendation = Column(Text, nullable=True, comment='建议措施')
    
    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE-活动, RESOLVED-已解决, IGNORED-已忽略, CLOSED-已关闭')
    
    # 处理信息
    assigned_to_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='指派人ID')
    resolved_by_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='解决人ID')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')
    resolution_note = Column(Text, nullable=True, comment='解决备注')
    
    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='关联项目ID')
    
    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    material = relationship('Material')
    assigned_to = relationship('User', foreign_keys=[assigned_to_id])
    resolved_by = relationship('User', foreign_keys=[resolved_by_id])

    def __repr__(self):
        return f'<MaterialAlert {self.alert_no}>'


class MaterialAlertRule(Base, TimestampMixin):
    """物料预警规则配置表"""
    __tablename__ = 'material_alert_rule'
    __table_args__ = (
        Index('idx_mat_alert_rule_material', 'material_id'),
        Index('idx_mat_alert_rule_type', 'alert_type'),
        Index('idx_mat_alert_rule_active', 'is_active'),
        {'extend_existing': True, 'comment': '物料预警规则表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_name = Column(String(200), nullable=False, comment='规则名称')
    
    # 物料范围
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID (NULL表示全局规则)')
    category_id = Column(Integer, ForeignKey('material_categories.id'), nullable=True, comment='物料分类ID')
    
    # 预警类型
    alert_type = Column(String(30), nullable=False, comment='预警类型')
    alert_level = Column(String(20), default='WARNING', comment='预警级别')
    
    # 规则参数 (JSON格式或单独字段)
    threshold_type = Column(String(20), default='PERCENTAGE', comment='阈值类型: PERCENTAGE-百分比, FIXED-固定值, DAYS-天数')
    threshold_value = Column(Numeric(14, 4), nullable=False, comment='阈值')
    
    # 安全库存计算参数
    safety_days = Column(Integer, default=7, comment='安全库存天数')
    lead_time_days = Column(Integer, default=0, comment='采购周期天数')
    buffer_ratio = Column(Numeric(5, 2), default=1.2, comment='安全系数')
    
    # 通知设置
    notify_users = Column(Text, nullable=True, comment='通知用户ID列表(逗号分隔)')
    notify_roles = Column(Text, nullable=True, comment='通知角色列表(逗号分隔)')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    priority = Column(Integer, default=0, comment='优先级(数字越大优先级越高)')
    
    description = Column(Text, nullable=True, comment='规则描述')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='创建人ID')

    # 关系
    material = relationship('Material')

    def __repr__(self):
        return f'<MaterialAlertRule {self.rule_name}>'
