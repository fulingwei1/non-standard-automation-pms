# -*- coding: utf-8 -*-
"""
缺料管理扩展模块模型
包含：缺料上报、到货跟踪、物料替代、物料调拨、齐套检查、物料需求、预警日志、日报统计
"""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ShortageReport(Base, TimestampMixin):
    """缺料上报表"""
    __tablename__ = 'shortage_reports'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_no = Column(String(50), unique=True, nullable=False, comment='上报单号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), nullable=True, comment='机台ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')

    # 上报信息
    reporter_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='上报人ID')
    report_time = Column(DateTime, nullable=False, default=datetime.now, comment='上报时间')
    report_location = Column(String(200), comment='上报地点（车间/工位）')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    required_qty = Column(Numeric(10, 4), nullable=False, comment='需求数量')
    shortage_qty = Column(Numeric(10, 4), nullable=False, comment='缺料数量')
    urgent_level = Column(String(20), default='NORMAL', comment='紧急程度')

    # 状态
    status = Column(String(20), default='REPORTED', comment='状态：REPORTED/CONFIRMED/HANDLING/RESOLVED')
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='确认人ID（仓管）')
    confirmed_at = Column(DateTime, nullable=True, comment='确认时间')
    handler_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='处理人ID')
    resolved_at = Column(DateTime, nullable=True, comment='解决时间')

    # 处理信息
    solution_type = Column(String(20), comment='解决方案类型：PURCHASE/SUBSTITUTE/TRANSFER/OTHER')
    solution_note = Column(Text, comment='解决方案说明')

    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_shortage_report_no', 'report_no'),
        Index('idx_shortage_report_project', 'project_id'),
        Index('idx_shortage_report_status', 'status'),
        {'comment': '缺料上报表'}
    )


class MaterialArrival(Base, TimestampMixin):
    """到货跟踪表"""
    __tablename__ = 'material_arrivals'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    arrival_no = Column(String(50), unique=True, nullable=False, comment='到货跟踪单号')
    shortage_report_id = Column(Integer, ForeignKey('shortage_reports.id'), nullable=True, comment='关联缺料上报ID')
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), nullable=True, comment='关联采购订单ID')
    purchase_order_item_id = Column(Integer, ForeignKey('purchase_order_items.id'), nullable=True, comment='关联采购订单明细ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    expected_qty = Column(Numeric(10, 4), nullable=False, comment='预期到货数量')

    # 供应商信息
    supplier_id = Column(Integer, ForeignKey('suppliers.id'), nullable=True, comment='供应商ID')
    supplier_name = Column(String(200), comment='供应商名称')

    # 时间信息
    expected_date = Column(Date, nullable=False, comment='预期到货日期')
    actual_date = Column(Date, nullable=True, comment='实际到货日期')
    is_delayed = Column(Boolean, default=False, comment='是否延迟')
    delay_days = Column(Integer, default=0, comment='延迟天数')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态：PENDING/IN_TRANSIT/DELAYED/RECEIVED/CANCELLED')
    received_qty = Column(Numeric(10, 4), default=0, comment='实收数量')
    received_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='收货人ID')
    received_at = Column(DateTime, nullable=True, comment='收货时间')

    # 跟催信息
    follow_up_count = Column(Integer, default=0, comment='跟催次数')
    last_follow_up_at = Column(DateTime, nullable=True, comment='最后跟催时间')

    remark = Column(Text, comment='备注')

    # 关系
    shortage_report = relationship('ShortageReport')
    material = relationship('Material')
    supplier = relationship('Supplier')
    follow_ups = relationship('ArrivalFollowUp', back_populates='arrival', lazy='dynamic')

    __table_args__ = (
        Index('idx_arrival_no', 'arrival_no'),
        Index('idx_arrival_status', 'status'),
        Index('idx_arrival_expected_date', 'expected_date'),
        {'comment': '到货跟踪表'}
    )


class ArrivalFollowUp(Base, TimestampMixin):
    """到货跟催记录表"""
    __tablename__ = 'arrival_follow_ups'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    arrival_id = Column(Integer, ForeignKey('material_arrivals.id'), nullable=False, comment='到货跟踪ID')
    follow_up_type = Column(String(20), default='CALL', comment='跟催方式：CALL/EMAIL/VISIT/OTHER')
    follow_up_note = Column(Text, nullable=False, comment='跟催内容')
    followed_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='跟催人ID')
    followed_at = Column(DateTime, nullable=False, default=datetime.now, comment='跟催时间')
    supplier_response = Column(Text, comment='供应商反馈')
    next_follow_up_date = Column(Date, comment='下次跟催日期')

    # 关系
    arrival = relationship('MaterialArrival', back_populates='follow_ups')

    __table_args__ = (
        Index('idx_follow_up_arrival', 'arrival_id'),
        {'comment': '到货跟催记录表'}
    )


class MaterialSubstitution(Base, TimestampMixin):
    """物料替代表"""
    __tablename__ = 'material_substitutions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    substitution_no = Column(String(50), unique=True, nullable=False, comment='替代单号')
    shortage_report_id = Column(Integer, ForeignKey('shortage_reports.id'), nullable=True, comment='关联缺料上报ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), nullable=True, comment='BOM行ID')

    # 原物料
    original_material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='原物料ID')
    original_material_code = Column(String(50), nullable=False, comment='原物料编码')
    original_material_name = Column(String(200), nullable=False, comment='原物料名称')
    original_qty = Column(Numeric(10, 4), nullable=False, comment='原物料数量')

    # 替代物料
    substitute_material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='替代物料ID')
    substitute_material_code = Column(String(50), nullable=False, comment='替代物料编码')
    substitute_material_name = Column(String(200), nullable=False, comment='替代物料名称')
    substitute_qty = Column(Numeric(10, 4), nullable=False, comment='替代物料数量')

    # 替代原因
    substitution_reason = Column(Text, nullable=False, comment='替代原因')
    technical_impact = Column(Text, comment='技术影响分析')
    cost_impact = Column(Numeric(14, 2), default=0, comment='成本影响')

    # 审批
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/TECH_PENDING/PROD_PENDING/APPROVED/REJECTED/EXECUTED')
    tech_approver_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='技术审批人ID')
    tech_approved_at = Column(DateTime, nullable=True, comment='技术审批时间')
    tech_approval_note = Column(Text, comment='技术审批意见')
    prod_approver_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='生产审批人ID')
    prod_approved_at = Column(DateTime, nullable=True, comment='生产审批时间')
    prod_approval_note = Column(Text, comment='生产审批意见')

    # 执行
    executed_at = Column(DateTime, nullable=True, comment='执行时间')
    executed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='执行人ID')
    execution_note = Column(Text, comment='执行说明')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')

    # 关系
    project = relationship('Project')
    original_material = relationship('Material', foreign_keys=[original_material_id])
    substitute_material = relationship('Material', foreign_keys=[substitute_material_id])

    __table_args__ = (
        Index('idx_substitution_no', 'substitution_no'),
        Index('idx_substitution_project', 'project_id'),
        Index('idx_substitution_status', 'status'),
        {'comment': '物料替代表'}
    )


class MaterialTransfer(Base, TimestampMixin):
    """物料调拨表"""
    __tablename__ = 'material_transfers'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    transfer_no = Column(String(50), unique=True, nullable=False, comment='调拨单号')
    shortage_report_id = Column(Integer, ForeignKey('shortage_reports.id'), nullable=True, comment='关联缺料上报ID')

    # 调拨信息
    from_project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='调出项目ID')
    from_location = Column(String(200), comment='调出位置')
    to_project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='调入项目ID')
    to_location = Column(String(200), comment='调入位置')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=False, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    transfer_qty = Column(Numeric(10, 4), nullable=False, comment='调拨数量')
    available_qty = Column(Numeric(10, 4), default=0, comment='可调拨数量')

    # 调拨原因
    transfer_reason = Column(Text, nullable=False, comment='调拨原因')
    urgent_level = Column(String(20), default='NORMAL', comment='紧急程度')

    # 审批
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/PENDING/APPROVED/REJECTED/EXECUTED/CANCELLED')
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    approval_note = Column(Text, comment='审批意见')

    # 执行
    executed_at = Column(DateTime, nullable=True, comment='执行时间')
    executed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='执行人ID')
    actual_qty = Column(Numeric(10, 4), nullable=True, comment='实际调拨数量')
    execution_note = Column(Text, comment='执行说明')

    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='创建人ID')

    # 关系
    from_project = relationship('Project', foreign_keys=[from_project_id])
    to_project = relationship('Project', foreign_keys=[to_project_id])
    material = relationship('Material')

    __table_args__ = (
        Index('idx_transfer_no', 'transfer_no'),
        Index('idx_transfer_from_project', 'from_project_id'),
        Index('idx_transfer_to_project', 'to_project_id'),
        Index('idx_transfer_status', 'status'),
        {'comment': '物料调拨表'}
    )


class WorkOrderBom(Base, TimestampMixin):
    """工单BOM明细表"""
    __tablename__ = 'mat_work_order_bom'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=False, comment='工单ID')
    work_order_no = Column(String(32), comment='工单号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(200), comment='规格型号')
    unit = Column(String(20), default='件', comment='单位')

    # 数量信息
    bom_qty = Column(Numeric(12, 4), nullable=False, comment='BOM用量')
    required_qty = Column(Numeric(12, 4), nullable=False, comment='需求数量')
    required_date = Column(Date, nullable=False, comment='需求日期')

    # 物料类型
    material_type = Column(String(20), default='purchase', comment='物料类型：purchase/make/outsource')
    lead_time = Column(Integer, default=0, comment='采购提前期(天)')
    is_key_material = Column(Boolean, default=False, comment='是否关键物料')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_work_order_bom_wo', 'work_order_id'),
        Index('idx_work_order_bom_material', 'material_code'),
        Index('idx_work_order_bom_date', 'required_date'),
        {'comment': '工单BOM明细表'}
    )


class MaterialRequirement(Base, TimestampMixin):
    """物料需求汇总表"""
    __tablename__ = 'mat_material_requirement'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    requirement_no = Column(String(32), unique=True, nullable=False, comment='需求编号')

    # 来源信息
    source_type = Column(String(20), nullable=False, comment='来源类型：work_order/project/manual')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(200), comment='规格型号')
    unit = Column(String(20), comment='单位')

    # 数量信息
    required_qty = Column(Numeric(12, 4), nullable=False, comment='需求数量')
    stock_qty = Column(Numeric(12, 4), default=0, comment='库存可用')
    allocated_qty = Column(Numeric(12, 4), default=0, comment='已分配')
    in_transit_qty = Column(Numeric(12, 4), default=0, comment='在途数量')
    shortage_qty = Column(Numeric(12, 4), default=0, comment='缺料数量')
    required_date = Column(Date, nullable=False, comment='需求日期')

    # 状态
    status = Column(String(20), default='pending', comment='状态：pending/partial/fulfilled/cancelled')
    fulfill_method = Column(String(20), nullable=True, comment='满足方式：stock/purchase/substitute/transfer')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_requirement_no', 'requirement_no'),
        Index('idx_requirement_wo', 'work_order_id'),
        Index('idx_requirement_material', 'material_code'),
        Index('idx_requirement_status', 'status'),
        Index('idx_requirement_date', 'required_date'),
        {'comment': '物料需求汇总表'}
    )


class KitCheck(Base, TimestampMixin):
    """齐套检查记录表"""
    __tablename__ = 'mat_kit_check'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    check_no = Column(String(32), unique=True, nullable=False, comment='检查编号')

    # 检查对象
    check_type = Column(String(20), nullable=False, comment='检查类型：work_order/project/batch')
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')

    # 检查结果
    total_items = Column(Integer, default=0, comment='物料总项')
    fulfilled_items = Column(Integer, default=0, comment='已齐套项')
    shortage_items = Column(Integer, default=0, comment='缺料项')
    in_transit_items = Column(Integer, default=0, comment='在途项')
    kit_rate = Column(Numeric(5, 2), default=0, comment='齐套率(%)')
    kit_status = Column(String(20), default='shortage', comment='齐套状态：complete/partial/shortage')
    shortage_summary = Column(JSON, comment='缺料汇总JSON')

    # 检查信息
    check_time = Column(DateTime, nullable=False, default=datetime.now, comment='检查时间')
    check_method = Column(String(20), default='auto', comment='检查方式：auto/manual')
    checked_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='检查人ID')

    # 开工确认
    can_start = Column(Boolean, default=False, comment='是否可开工')
    start_confirmed = Column(Boolean, default=False, comment='已确认开工')
    confirm_time = Column(DateTime, nullable=True, comment='确认时间')
    confirmed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='确认人ID')
    confirm_remark = Column(Text, comment='确认备注')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    checker = relationship('User', foreign_keys=[checked_by])
    confirmer = relationship('User', foreign_keys=[confirmed_by])

    __table_args__ = (
        Index('idx_kit_check_no', 'check_no'),
        Index('idx_kit_check_wo', 'work_order_id'),
        Index('idx_kit_check_project', 'project_id'),
        Index('idx_kit_check_status', 'kit_status'),
        Index('idx_kit_check_time', 'check_time'),
        {'comment': '齐套检查记录表'}
    )


class AlertHandleLog(Base, TimestampMixin):
    """预警处理日志表"""
    __tablename__ = 'mat_alert_log'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_id = Column(Integer, nullable=False, comment='预警ID')

    # 操作信息
    action_type = Column(String(20), nullable=False, comment='操作类型：create/handle/update/escalate/resolve/close')
    action_description = Column(Text, comment='操作描述')

    # 操作人
    operator_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='操作人ID')
    operator_name = Column(String(50), comment='操作人姓名')
    action_time = Column(DateTime, nullable=False, default=datetime.now, comment='操作时间')

    # 操作前后状态
    before_status = Column(String(20), comment='操作前状态')
    after_status = Column(String(20), comment='操作后状态')
    before_level = Column(String(20), comment='操作前级别')
    after_level = Column(String(20), comment='操作后级别')

    # 扩展数据
    extra_data = Column(JSON, comment='扩展数据JSON')

    # 关系
    operator = relationship('User')

    __table_args__ = (
        Index('idx_alert_log_alert', 'alert_id'),
        Index('idx_alert_log_time', 'action_time'),
        Index('idx_alert_log_operator', 'operator_id'),
        {'comment': '预警处理日志表'}
    )


class ShortageDailyReport(Base, TimestampMixin):
    """缺料统计日报表"""
    __tablename__ = 'mat_shortage_daily_report'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_date = Column(Date, unique=True, nullable=False, comment='报告日期')

    # 预警统计
    new_alerts = Column(Integer, default=0, comment='新增预警数')
    resolved_alerts = Column(Integer, default=0, comment='已解决预警数')
    pending_alerts = Column(Integer, default=0, comment='待处理预警数')
    overdue_alerts = Column(Integer, default=0, comment='逾期预警数')
    level1_count = Column(Integer, default=0, comment='一级预警数')
    level2_count = Column(Integer, default=0, comment='二级预警数')
    level3_count = Column(Integer, default=0, comment='三级预警数')
    level4_count = Column(Integer, default=0, comment='四级预警数')

    # 上报统计
    new_reports = Column(Integer, default=0, comment='新增上报数')
    resolved_reports = Column(Integer, default=0, comment='已解决上报数')

    # 工单统计
    total_work_orders = Column(Integer, default=0, comment='总工单数')
    kit_complete_count = Column(Integer, default=0, comment='齐套完成工单数')
    kit_rate = Column(Numeric(5, 2), default=0, comment='平均齐套率')

    # 到货统计
    expected_arrivals = Column(Integer, default=0, comment='预期到货数')
    actual_arrivals = Column(Integer, default=0, comment='实际到货数')
    delayed_arrivals = Column(Integer, default=0, comment='延迟到货数')
    on_time_rate = Column(Numeric(5, 2), default=0, comment='准时到货率')

    # 响应时效
    avg_response_minutes = Column(Integer, default=0, comment='平均响应时间(分钟)')
    avg_resolve_hours = Column(Numeric(5, 2), default=0, comment='平均解决时间(小时)')

    # 停工统计
    stoppage_count = Column(Integer, default=0, comment='停工次数')
    stoppage_hours = Column(Numeric(8, 2), default=0, comment='停工时长(小时)')

    __table_args__ = (
        Index('idx_daily_report_date', 'report_date'),
        {'comment': '缺料统计日报表'}
    )


class ShortageAlert(Base, TimestampMixin):
    """缺料预警表（完整版，对齐设计文档）"""
    __tablename__ = 'mat_shortage_alert'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    alert_no = Column(String(32), unique=True, nullable=False, comment='预警编号')

    # 关联信息
    work_order_id = Column(Integer, ForeignKey('work_order.id'), nullable=True, comment='工单ID')
    work_order_no = Column(String(32), comment='工单号')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='项目ID')
    project_name = Column(String(200), comment='项目名称')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(200), comment='规格型号')
    shortage_qty = Column(Numeric(12, 4), nullable=False, comment='缺料数量')
    shortage_value = Column(Numeric(12, 2), comment='缺料金额')
    required_date = Column(Date, nullable=False, comment='需求日期')
    days_to_required = Column(Integer, comment='距离需求日期天数')

    # 预警级别: level1=提醒, level2=警告, level3=紧急, level4=严重
    alert_level = Column(String(20), default='level1', comment='预警级别：level1/level2/level3/level4')

    # 影响评估
    impact_type = Column(String(20), default='none', comment='影响类型：none/delay/stop/delivery')
    impact_description = Column(Text, comment='影响描述')
    affected_process = Column(String(100), comment='受影响工序')
    estimated_delay_days = Column(Integer, default=0, comment='预计延迟天数')

    # 通知信息
    notify_time = Column(DateTime, nullable=True, comment='通知时间')
    notify_count = Column(Integer, default=0, comment='通知次数')
    notified_users = Column(JSON, comment='已通知用户列表（JSON）')
    response_deadline = Column(DateTime, nullable=True, comment='响应时限')
    is_overdue = Column(Boolean, default=False, comment='是否逾期')

    # 处理状态
    status = Column(String(20), default='pending', comment='状态：pending/handling/resolved/escalated/closed')

    # 处理人信息
    handler_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='处理人ID')
    handler_name = Column(String(50), comment='处理人姓名')
    handle_start_time = Column(DateTime, nullable=True, comment='开始处理时间')
    handle_plan = Column(Text, comment='处理方案')
    handle_method = Column(String(20), comment='处理方式：wait_arrival/expedite/substitute/transfer/urgent_purchase/adjust_schedule/other')
    expected_resolve_time = Column(DateTime, nullable=True, comment='预计解决时间')

    # 解决信息
    resolve_time = Column(DateTime, nullable=True, comment='实际解决时间')
    resolve_method = Column(String(50), comment='解决方式')
    resolve_description = Column(Text, comment='解决说明')
    actual_delay_days = Column(Integer, default=0, comment='实际延迟天数')

    # 升级信息
    escalated = Column(Boolean, default=False, comment='是否已升级')
    escalate_time = Column(DateTime, nullable=True, comment='升级时间')
    escalate_to = Column(Integer, ForeignKey('users.id'), nullable=True, comment='升级给谁（用户ID）')
    escalate_reason = Column(Text, comment='升级原因')

    # 关联单据
    related_po_no = Column(String(50), comment='关联采购订单号')
    related_transfer_no = Column(String(50), comment='关联调拨单号')
    related_substitute_no = Column(String(50), comment='关联替代单号')

    # 关系
    work_order = relationship('WorkOrder')
    project = relationship('Project')
    material = relationship('Material')
    handler = relationship('User', foreign_keys=[handler_id])
    escalate_to_user = relationship('User', foreign_keys=[escalate_to])

    __table_args__ = (
        Index('idx_alert_no', 'alert_no'),
        Index('idx_alert_work_order', 'work_order_id'),
        Index('idx_alert_material', 'material_code'),
        Index('idx_shortage_alert_level', 'alert_level'),
        Index('idx_shortage_alert_status', 'status'),
        Index('idx_alert_handler', 'handler_id'),
        Index('idx_alert_required_date', 'required_date'),
        {'comment': '缺料预警表'}
    )

