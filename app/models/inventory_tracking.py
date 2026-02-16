# -*- coding: utf-8 -*-
"""
库存跟踪系统 - 数据模型
Team 2: 物料全流程跟踪系统
实现物料从采购到消耗的全生命周期跟踪
"""
from datetime import datetime
from decimal import Decimal

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


class MaterialTransaction(Base, TimestampMixin):
    """物料交易记录表 - 全流程跟踪"""
    __tablename__ = 'material_transaction'
    __table_args__ = (
        Index('idx_mat_trans_material', 'material_id'),
        Index('idx_mat_trans_type', 'transaction_type'),
        Index('idx_mat_trans_date', 'transaction_date'),
        Index('idx_mat_trans_batch', 'batch_number'),
        Index('idx_mat_trans_order', 'related_order_id'),
        Index('idx_mat_trans_location', 'source_location', 'target_location'),
        {'extend_existing': True, 'comment': '物料交易记录表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码(冗余)')
    material_name = Column(String(200), nullable=False, comment='物料名称(冗余)')
    
    # 交易类型
    transaction_type = Column(
        String(20), 
        nullable=False, 
        comment='交易类型: PURCHASE_IN-采购入库, TRANSFER_IN-调拨入库, ISSUE-领用出库, RETURN-退料入库, ADJUST-盘点调整, SCRAP-报废'
    )
    
    # 数量和金额
    quantity = Column(Numeric(14, 4), nullable=False, comment='交易数量')
    unit = Column(String(20), default='件', comment='单位')
    unit_price = Column(Numeric(12, 4), default=0, comment='单价')
    total_amount = Column(Numeric(14, 2), default=0, comment='总金额')
    
    # 位置信息
    source_location = Column(String(100), comment='来源位置/仓库')
    target_location = Column(String(100), comment='目标位置/仓库')
    
    # 批次信息
    batch_number = Column(String(100), comment='批次号')
    
    # 关联单据
    related_order_id = Column(Integer, comment='关联订单ID')
    related_order_type = Column(String(30), comment='关联单据类型: PURCHASE_ORDER-采购单, WORK_ORDER-工单, REQUISITION-领料单, COUNT_TASK-盘点任务')
    related_order_no = Column(String(50), comment='关联单据编号')
    
    # 时间信息
    transaction_date = Column(DateTime, nullable=False, default=datetime.now, comment='交易时间')
    
    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), comment='操作人ID')
    
    # 备注
    remark = Column(Text, comment='备注说明')
    
    # 成本核算方法
    cost_method = Column(String(20), default='WEIGHTED_AVG', comment='成本核算方法: FIFO-先进先出, LIFO-后进先出, WEIGHTED_AVG-加权平均')

    # 关系
    material = relationship('Material')
    operator = relationship('User', foreign_keys=[operator_id])

    def __repr__(self):
        return f'<MaterialTransaction {self.transaction_type} {self.material_code} {self.quantity}>'


class MaterialStock(Base, TimestampMixin):
    """物料库存表 - 实时库存"""
    __tablename__ = 'material_stock'
    __table_args__ = (
        Index('idx_mat_stock_material', 'material_id'),
        Index('idx_mat_stock_location', 'location'),
        Index('idx_mat_stock_batch', 'batch_number'),
        Index('idx_mat_stock_available', 'available_quantity'),
        Index('idx_mat_stock_unique', 'material_id', 'location', 'batch_number', unique=True),
        {'extend_existing': True, 'comment': '物料库存表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码(冗余)')
    material_name = Column(String(200), nullable=False, comment='物料名称(冗余)')
    
    # 位置和批次
    location = Column(String(100), nullable=False, comment='仓库位置')
    batch_number = Column(String(100), comment='批次号')
    
    # 数量信息
    quantity = Column(Numeric(14, 4), nullable=False, default=0, comment='库存总数量')
    available_quantity = Column(Numeric(14, 4), nullable=False, default=0, comment='可用数量(总数-预留)')
    reserved_quantity = Column(Numeric(14, 4), default=0, comment='预留数量')
    
    unit = Column(String(20), default='件', comment='单位')
    
    # 成本信息
    unit_price = Column(Numeric(12, 4), default=0, comment='单价(加权平均)')
    total_value = Column(Numeric(14, 2), default=0, comment='库存总价值')
    
    # 批次信息
    production_date = Column(Date, comment='生产日期')
    expire_date = Column(Date, comment='失效日期')
    
    # 状态
    status = Column(String(20), default='NORMAL', comment='状态: NORMAL-正常, LOW-低库存, LOCKED-锁定, EXPIRED-过期')
    
    # 最后更新
    last_in_date = Column(DateTime, comment='最后入库时间')
    last_out_date = Column(DateTime, comment='最后出库时间')
    last_update = Column(DateTime, default=datetime.now, comment='最后更新时间')

    # 关系
    material = relationship('Material')
    reservations = relationship('MaterialReservation', back_populates='stock', lazy='dynamic')

    def __repr__(self):
        return f'<MaterialStock {self.material_code} @ {self.location} qty={self.quantity}>'


class MaterialReservation(Base, TimestampMixin):
    """物料预留表"""
    __tablename__ = 'material_reservation'
    __table_args__ = (
        Index('idx_mat_res_material', 'material_id'),
        Index('idx_mat_res_stock', 'stock_id'),
        Index('idx_mat_res_project', 'project_id'),
        Index('idx_mat_res_status', 'status'),
        Index('idx_mat_res_date', 'expected_use_date'),
        {'extend_existing': True, 'comment': '物料预留表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 预留单号
    reservation_no = Column(String(50), unique=True, nullable=False, comment='预留单号')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    stock_id = Column(Integer, ForeignKey('material_stock.id'), comment='库存ID')
    
    # 预留数量
    reserved_quantity = Column(Numeric(14, 4), nullable=False, comment='预留数量')
    used_quantity = Column(Numeric(14, 4), default=0, comment='已使用数量')
    remaining_quantity = Column(Numeric(14, 4), comment='剩余数量')
    
    # 预留用途
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), comment='工单ID')
    
    # 时间信息
    reservation_date = Column(DateTime, nullable=False, default=datetime.now, comment='预留时间')
    expected_use_date = Column(Date, comment='预计使用日期')
    actual_use_date = Column(Date, comment='实际使用日期')
    
    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态: ACTIVE-生效中, PARTIAL_USED-部分使用, USED-已使用, CANCELLED-已取消, EXPIRED-已过期')
    
    # 操作人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    cancelled_by = Column(Integer, ForeignKey('users.id'), comment='取消人ID')
    cancelled_at = Column(DateTime, comment='取消时间')
    cancel_reason = Column(Text, comment='取消原因')
    
    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    material = relationship('Material')
    stock = relationship('MaterialStock', back_populates='reservations')
    project = relationship('Project', foreign_keys=[project_id])
    work_order = relationship('WorkOrder', foreign_keys=[work_order_id])
    creator = relationship('User', foreign_keys=[created_by])

    def __repr__(self):
        return f'<MaterialReservation {self.reservation_no} qty={self.reserved_quantity}>'


class StockAdjustment(Base, TimestampMixin):
    """库存调整表 - 盘点/损耗调整"""
    __tablename__ = 'stock_adjustment'
    __table_args__ = (
        Index('idx_stock_adj_material', 'material_id'),
        Index('idx_stock_adj_location', 'location'),
        Index('idx_stock_adj_type', 'adjustment_type'),
        Index('idx_stock_adj_date', 'adjustment_date'),
        Index('idx_stock_adj_status', 'status'),
        {'extend_existing': True, 'comment': '库存调整表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 调整单号
    adjustment_no = Column(String(50), unique=True, nullable=False, comment='调整单号')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码(冗余)')
    material_name = Column(String(200), nullable=False, comment='物料名称(冗余)')
    
    # 位置和批次
    location = Column(String(100), nullable=False, comment='仓库位置')
    batch_number = Column(String(100), comment='批次号')
    
    # 数量信息
    original_quantity = Column(Numeric(14, 4), nullable=False, comment='账面数量')
    actual_quantity = Column(Numeric(14, 4), nullable=False, comment='实盘数量')
    difference = Column(Numeric(14, 4), nullable=False, comment='差异数量(实盘-账面)')
    difference_rate = Column(Numeric(5, 2), comment='差异率(%)')
    
    # 调整类型
    adjustment_type = Column(
        String(20), 
        nullable=False, 
        comment='调整类型: INVENTORY-盘点调整, DAMAGE-破损, LOSS-丢失, CORRECTION-纠正, OTHER-其他'
    )
    
    # 原因
    reason = Column(Text, nullable=False, comment='调整原因')
    
    # 时间
    adjustment_date = Column(DateTime, nullable=False, default=datetime.now, comment='调整时间')
    
    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='操作人ID')
    
    # 审批
    status = Column(String(20), default='PENDING', comment='状态: PENDING-待审批, APPROVED-已批准, REJECTED-已拒绝')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approved_at = Column(DateTime, comment='审批时间')
    approval_comment = Column(Text, comment='审批意见')
    
    # 关联盘点任务
    count_task_id = Column(Integer, ForeignKey('stock_count_task.id'), comment='盘点任务ID')
    
    # 财务影响
    unit_price = Column(Numeric(12, 4), comment='单价')
    total_impact = Column(Numeric(14, 2), comment='总金额影响')
    
    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    material = relationship('Material')
    operator = relationship('User', foreign_keys=[operator_id])
    approver = relationship('User', foreign_keys=[approved_by])
    count_task = relationship('StockCountTask', back_populates='adjustments')

    def __repr__(self):
        return f'<StockAdjustment {self.adjustment_no} diff={self.difference}>'


class StockCountTask(Base, TimestampMixin):
    """库存盘点任务表"""
    __tablename__ = 'stock_count_task'
    __table_args__ = (
        Index('idx_count_task_no', 'task_no'),
        Index('idx_count_task_location', 'location'),
        Index('idx_count_task_status', 'status'),
        Index('idx_count_task_date', 'count_date'),
        {'extend_existing': True, 'comment': '库存盘点任务表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 盘点任务号
    task_no = Column(String(50), unique=True, nullable=False, comment='盘点任务号')
    
    # 盘点范围
    count_type = Column(String(20), default='FULL', comment='盘点类型: FULL-全盘, PARTIAL-抽盘, CYCLE-循环盘点')
    location = Column(String(100), comment='盘点位置/仓库')
    category_id = Column(Integer, ForeignKey('material_categories.id'), comment='物料分类ID')
    
    # 盘点时间
    count_date = Column(Date, nullable=False, comment='盘点日期')
    start_time = Column(DateTime, comment='开始时间')
    end_time = Column(DateTime, comment='结束时间')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态: PENDING-待盘点, IN_PROGRESS-盘点中, COMPLETED-已完成, CANCELLED-已取消')
    
    # 盘点人员
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')
    assigned_to = Column(Integer, ForeignKey('users.id'), comment='盘点人ID')
    
    # 审批
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approved_at = Column(DateTime, comment='审批时间')
    
    # 统计
    total_items = Column(Integer, default=0, comment='总物料数')
    counted_items = Column(Integer, default=0, comment='已盘点数')
    matched_items = Column(Integer, default=0, comment='账实相符数')
    diff_items = Column(Integer, default=0, comment='差异物料数')
    total_diff_value = Column(Numeric(14, 2), default=0, comment='总差异金额')
    
    # 备注
    remark = Column(Text, comment='备注说明')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    assigned_user = relationship('User', foreign_keys=[assigned_to])
    approver = relationship('User', foreign_keys=[approved_by])
    details = relationship('StockCountDetail', back_populates='task', lazy='dynamic')
    adjustments = relationship('StockAdjustment', back_populates='count_task', lazy='dynamic')

    def __repr__(self):
        return f'<StockCountTask {self.task_no} {self.status}>'


class StockCountDetail(Base, TimestampMixin):
    """库存盘点明细表"""
    __tablename__ = 'stock_count_detail'
    __table_args__ = (
        Index('idx_count_detail_task', 'task_id'),
        Index('idx_count_detail_material', 'material_id'),
        Index('idx_count_detail_status', 'status'),
        {'extend_existing': True, 'comment': '库存盘点明细表'}
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=False, comment='租户ID')
    
    # 盘点任务
    task_id = Column(Integer, ForeignKey('stock_count_task.id'), nullable=False, comment='盘点任务ID')
    
    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码(冗余)')
    material_name = Column(String(200), nullable=False, comment='物料名称(冗余)')
    
    # 批次和位置
    location = Column(String(100), comment='仓库位置')
    batch_number = Column(String(100), comment='批次号')
    
    # 数量信息
    system_quantity = Column(Numeric(14, 4), nullable=False, comment='系统数量(账面)')
    actual_quantity = Column(Numeric(14, 4), comment='实盘数量')
    difference = Column(Numeric(14, 4), comment='差异数量(实盘-账面)')
    difference_rate = Column(Numeric(5, 2), comment='差异率(%)')
    
    # 成本信息
    unit_price = Column(Numeric(12, 4), comment='单价')
    diff_value = Column(Numeric(14, 2), comment='差异金额')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态: PENDING-待盘点, COUNTED-已盘点, RECOUNTED-已复盘, CONFIRMED-已确认')
    
    # 盘点人
    counted_by = Column(Integer, ForeignKey('users.id'), comment='盘点人ID')
    counted_at = Column(DateTime, comment='盘点时间')
    
    # 复盘
    is_recounted = Column(Boolean, default=False, comment='是否复盘')
    recount_reason = Column(Text, comment='复盘原因')
    
    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    task = relationship('StockCountTask', back_populates='details')
    material = relationship('Material')
    counter = relationship('User', foreign_keys=[counted_by])

    def __repr__(self):
        return f'<StockCountDetail {self.material_code} sys={self.system_quantity} actual={self.actual_quantity}>'
