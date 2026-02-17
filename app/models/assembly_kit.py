# -*- coding: utf-8 -*-
"""
装配工艺齐套分析模块模型
基于装配工艺路径的智能齐套分析系统
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

from .base import Base, TimestampMixin

# ==================== 装配阶段定义 ====================

class AssemblyStage(Base, TimestampMixin):
    """装配阶段定义表"""
    __tablename__ = 'mes_assembly_stage'

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_code = Column(String(20), unique=True, nullable=False, comment='阶段编码')
    stage_name = Column(String(50), nullable=False, comment='阶段名称')
    stage_order = Column(Integer, nullable=False, comment='阶段顺序(1-6)')
    description = Column(Text, comment='阶段描述')
    default_duration = Column(Integer, default=0, comment='默认工期(小时)')
    color_code = Column(String(20), comment='显示颜色')
    icon = Column(String(50), comment='图标')
    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        Index('idx_assembly_stage_order', 'stage_order'),
        Index('idx_assembly_stage_active', 'is_active'),
    )

    def __repr__(self):
        return f'<AssemblyStage {self.stage_code}: {self.stage_name}>'


# ==================== 装配工艺模板 ====================

class AssemblyTemplate(Base, TimestampMixin):
    """装配工艺模板表"""
    __tablename__ = 'mes_assembly_template'

    id = Column(Integer, primary_key=True, autoincrement=True)
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    template_name = Column(String(200), nullable=False, comment='模板名称')
    equipment_type = Column(String(50), nullable=False, comment='设备类型')
    description = Column(Text, comment='模板描述')
    stage_config = Column(Text, comment='阶段配置JSON')
    is_default = Column(Boolean, default=False, comment='是否默认模板')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_assembly_template_type', 'equipment_type'),
        Index('idx_assembly_template_active', 'is_active'),
    )

    def __repr__(self):
        return f'<AssemblyTemplate {self.template_code}: {self.template_name}>'


# ==================== 物料分类映射 ====================

class CategoryStageMapping(Base, TimestampMixin):
    """物料分类与装配阶段映射表"""
    __tablename__ = 'mes_category_stage_mapping'

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey('material_categories.id'), comment='物料分类ID')
    category_code = Column(String(50), nullable=False, comment='物料分类编码/关键词')
    category_name = Column(String(100), comment='分类名称')
    stage_code = Column(String(20), nullable=False, comment='默认装配阶段')
    priority = Column(Integer, default=50, comment='优先级(1-100)')
    is_blocking = Column(Boolean, default=False, comment='是否阻塞性物料')
    can_postpone = Column(Boolean, default=True, comment='是否可后补')
    importance_level = Column(String(20), default='NORMAL', comment='重要程度')
    lead_time_buffer = Column(Integer, default=0, comment='提前期缓冲(天)')
    keywords = Column(Text, comment='匹配关键词(JSON)')
    remark = Column(Text, comment='备注')
    is_active = Column(Boolean, default=True, comment='是否启用')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    category = relationship('MaterialCategory', foreign_keys=[category_id])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_category_stage_category', 'category_id'),
        Index('idx_category_stage_stage', 'stage_code'),
        Index('idx_category_stage_active', 'is_active'),
    )

    def __repr__(self):
        return f'<CategoryStageMapping {self.category_code} -> {self.stage_code}>'


# ==================== BOM物料装配属性 ====================

class BomItemAssemblyAttrs(Base, TimestampMixin):
    """BOM物料装配属性扩展表"""
    __tablename__ = 'bom_item_assembly_attrs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    bom_item_id = Column(Integer, ForeignKey('bom_items.id', ondelete='CASCADE'),
                         unique=True, nullable=False, comment='BOM明细ID')
    bom_id = Column(Integer, ForeignKey('bom_headers.id'), nullable=False, comment='BOM表头ID')

    # 装配阶段
    assembly_stage = Column(String(20), nullable=False, comment='装配阶段')
    stage_order = Column(Integer, default=0, comment='阶段内排序')

    # 重要程度
    importance_level = Column(String(20), default='NORMAL', comment='重要程度')
    is_blocking = Column(Boolean, default=False, comment='是否阻塞性')
    can_postpone = Column(Boolean, default=True, comment='是否可后补')

    # 时间要求
    required_before_stage = Column(Boolean, default=True, comment='是否需要在阶段开始前到货')
    lead_time_days = Column(Integer, default=0, comment='提前期要求(天)')

    # 替代信息
    has_substitute = Column(Boolean, default=False, comment='是否有替代料')
    substitute_material_ids = Column(Text, comment='替代物料ID列表(JSON)')

    # 备注
    assembly_remark = Column(Text, comment='装配备注')

    # 设置来源
    setting_source = Column(String(20), default='AUTO', comment='设置来源')

    # 审核
    confirmed = Column(Boolean, default=False, comment='是否已确认')
    confirmed_by = Column(Integer, ForeignKey('users.id'), comment='确认人ID')
    confirmed_at = Column(DateTime, comment='确认时间')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    bom_item = relationship('BomItem', backref='assembly_attrs_rel')
    bom_header = relationship('BomHeader')
    confirmer = relationship('User', foreign_keys=[confirmed_by])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_bom_assembly_bom', 'bom_id'),
        Index('idx_bom_assembly_stage', 'assembly_stage'),
        Index('idx_bom_assembly_blocking', 'is_blocking'),
        Index('idx_bom_assembly_importance', 'importance_level'),
    )

    def __repr__(self):
        return f'<BomItemAssemblyAttrs item={self.bom_item_id} stage={self.assembly_stage}>'


# ==================== 齐套分析结果 ====================

class MaterialReadiness(Base, TimestampMixin):
    """齐套分析结果表"""
    __tablename__ = 'mes_material_readiness'

    id = Column(Integer, primary_key=True, autoincrement=True)
    readiness_no = Column(String(50), unique=True, nullable=False, comment='分析单号')

    # 分析对象
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='机台ID')
    bom_id = Column(Integer, ForeignKey('bom_headers.id'), comment='BOM ID')

    # 计划信息
    planned_start_date = Column(Date, comment='计划开工日期')
    target_stage = Column(String(20), comment='目标分析阶段')

    # 整体齐套率
    overall_kit_rate = Column(Numeric(5, 2), default=0, comment='整体齐套率(%)')
    blocking_kit_rate = Column(Numeric(5, 2), default=0, comment='阻塞性齐套率(%)')

    # 分阶段齐套率
    stage_kit_rates = Column(Text, comment='各阶段齐套率JSON')

    # 统计数据
    total_items = Column(Integer, default=0, comment='物料总项数')
    fulfilled_items = Column(Integer, default=0, comment='已齐套项数')
    shortage_items = Column(Integer, default=0, comment='缺料项数')
    in_transit_items = Column(Integer, default=0, comment='在途项数')
    blocking_total = Column(Integer, default=0, comment='阻塞性物料总数')
    blocking_fulfilled = Column(Integer, default=0, comment='阻塞性已齐套数')

    # 金额统计
    total_amount = Column(Numeric(14, 2), default=0, comment='物料总金额')
    shortage_amount = Column(Numeric(14, 2), default=0, comment='缺料金额')

    # 分析结果
    can_start = Column(Boolean, default=False, comment='是否可开工')
    current_workable_stage = Column(String(20), comment='当前可进行到的阶段')
    first_blocked_stage = Column(String(20), comment='首个阻塞阶段')
    estimated_ready_date = Column(Date, comment='预计完全齐套日期')

    # 分析信息
    analysis_time = Column(DateTime, nullable=False, comment='分析时间')
    analysis_type = Column(String(20), default='AUTO', comment='分析类型')
    analyzed_by = Column(Integer, ForeignKey('users.id'), comment='分析人ID')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')
    confirmed_by = Column(Integer, ForeignKey('users.id'), comment='确认人ID')
    confirmed_at = Column(DateTime, comment='确认时间')
    expired_at = Column(DateTime, comment='过期时间')
    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    bom = relationship('BomHeader')
    analyzer = relationship('User', foreign_keys=[analyzed_by])
    confirmer = relationship('User', foreign_keys=[confirmed_by])
    shortage_details = relationship('ShortageDetail', back_populates='readiness',
                                    cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        Index('idx_readiness_no', 'readiness_no'),
        Index('idx_readiness_project', 'project_id'),
        Index('idx_readiness_machine', 'machine_id'),
        Index('idx_readiness_bom', 'bom_id'),
        Index('idx_readiness_status', 'status'),
        Index('idx_readiness_time', 'analysis_time'),
        Index('idx_readiness_can_start', 'can_start'),
    )

    def __repr__(self):
        return f'<MaterialReadiness {self.readiness_no} rate={self.overall_kit_rate}%>'


# ==================== 缺料明细 ====================

class ShortageDetail(Base, TimestampMixin):
    """缺料明细表"""
    __tablename__ = 'mes_shortage_detail'

    id = Column(Integer, primary_key=True, autoincrement=True)
    readiness_id = Column(Integer, ForeignKey('mes_material_readiness.id', ondelete='CASCADE'),
                          nullable=False, comment='齐套分析ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), nullable=False, comment='BOM明细ID')

    # 物料信息
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')
    unit = Column(String(20), comment='单位')

    # 装配阶段属性
    assembly_stage = Column(String(20), nullable=False, comment='所属装配阶段')
    is_blocking = Column(Boolean, default=False, comment='是否阻塞性')
    can_postpone = Column(Boolean, default=True, comment='是否可后补')
    importance_level = Column(String(20), default='NORMAL', comment='重要程度')

    # 数量信息
    required_qty = Column(Numeric(12, 4), nullable=False, comment='需求数量')
    stock_qty = Column(Numeric(12, 4), default=0, comment='库存数量')
    allocated_qty = Column(Numeric(12, 4), default=0, comment='已分配')
    in_transit_qty = Column(Numeric(12, 4), default=0, comment='在途数量')
    available_qty = Column(Numeric(12, 4), default=0, comment='可用数量')
    shortage_qty = Column(Numeric(12, 4), default=0, comment='缺料数量')

    # 金额
    unit_price = Column(Numeric(12, 4), default=0, comment='单价')
    shortage_amount = Column(Numeric(14, 2), default=0, comment='缺料金额')

    # 时间
    required_date = Column(Date, comment='需求日期')
    expected_arrival = Column(Date, comment='预计到货日期')
    delay_days = Column(Integer, default=0, comment='预计延误天数')

    # 采购信息
    purchase_order_id = Column(Integer, ForeignKey('purchase_orders.id'), comment='关联采购订单ID')
    purchase_order_no = Column(String(50), comment='关联采购订单号')
    supplier_id = Column(Integer, ForeignKey('vendors.id'), comment='供应商ID')
    supplier_name = Column(String(200), comment='供应商名称')

    # 状态
    shortage_status = Column(String(20), default='OPEN', comment='缺料状态')

    # 预警
    alert_level = Column(String(20), comment='预警级别')
    alert_time = Column(DateTime, comment='预警时间')

    # 处理
    handler_id = Column(Integer, ForeignKey('users.id'), comment='处理人ID')
    handle_note = Column(Text, comment='处理说明')
    handled_at = Column(DateTime, comment='处理时间')

    # 关系
    readiness = relationship('MaterialReadiness', back_populates='shortage_details')
    bom_item = relationship('BomItem')
    material = relationship('Material')
    purchase_order = relationship('PurchaseOrder')
    # supplier = relationship('Supplier')  # 已禁用 - Supplier 是废弃模型
    handler = relationship('User', foreign_keys=[handler_id])

    __table_args__ = (
        Index('idx_shortage_detail_readiness', 'readiness_id'),
        Index('idx_shortage_detail_material', 'material_code'),
        Index('idx_shortage_detail_stage', 'assembly_stage'),
        Index('idx_shortage_detail_blocking', 'is_blocking'),
        Index('idx_shortage_detail_status', 'shortage_status'),
        Index('idx_shortage_detail_alert', 'alert_level'),
    )

    def __repr__(self):
        return f'<ShortageDetail {self.material_code} shortage={self.shortage_qty}>'


# ==================== 预警规则 ====================

class ShortageAlertRule(Base, TimestampMixin):
    """缺料预警规则配置表"""
    __tablename__ = 'mes_shortage_alert_rule'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_code = Column(String(50), unique=True, nullable=False, comment='规则编码')
    rule_name = Column(String(200), nullable=False, comment='规则名称')
    alert_level = Column(String(10), nullable=False, comment='预警级别')
    days_before_required = Column(Integer, nullable=False, comment='距需求日期天数')
    only_blocking = Column(Boolean, default=False, comment='仅阻塞性物料')
    importance_levels = Column(Text, comment='适用重要程度(JSON)')
    min_shortage_amount = Column(Numeric(14, 2), default=0, comment='最小缺料金额')
    notify_roles = Column(Text, comment='通知角色(JSON)')
    notify_channels = Column(Text, comment='通知渠道')
    auto_escalate = Column(Boolean, default=False, comment='是否自动升级')
    escalate_after_hours = Column(Integer, default=0, comment='超时后自动升级(小时)')
    escalate_to_level = Column(String(10), comment='升级到的级别')
    response_deadline_hours = Column(Integer, default=24, comment='响应时限(小时)')
    priority = Column(Integer, default=50, comment='优先级')
    is_active = Column(Boolean, default=True, comment='是否启用')
    description = Column(Text, comment='规则描述')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_alert_rule_level', 'alert_level'),
        Index('idx_alert_rule_active', 'is_active'),
        Index('idx_alert_rule_priority', 'priority'),
    )

    def __repr__(self):
        return f'<ShortageAlertRule {self.rule_code} level={self.alert_level}>'


# ==================== 排产建议 ====================

class SchedulingSuggestion(Base, TimestampMixin):
    """排产建议表"""
    __tablename__ = 'mes_scheduling_suggestion'

    id = Column(Integer, primary_key=True, autoincrement=True)
    suggestion_no = Column(String(50), unique=True, nullable=False, comment='建议单号')
    readiness_id = Column(Integer, ForeignKey('mes_material_readiness.id'), comment='关联齐套分析ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='机台ID')
    suggestion_type = Column(String(20), nullable=False, comment='建议类型')
    suggestion_title = Column(String(200), nullable=False, comment='建议标题')
    suggestion_content = Column(Text, nullable=False, comment='建议详情')
    priority_score = Column(Numeric(5, 2), default=0, comment='优先级得分')
    factors = Column(Text, comment='影响因素(JSON)')
    suggested_start_date = Column(Date, comment='建议开工日期')
    original_start_date = Column(Date, comment='原计划开工日期')
    delay_days = Column(Integer, default=0, comment='建议延期天数')
    impact_description = Column(Text, comment='影响描述')
    risk_level = Column(String(20), comment='风险级别')
    status = Column(String(20), default='PENDING', comment='状态')
    accepted_by = Column(Integer, ForeignKey('users.id'), comment='接受人ID')
    accepted_at = Column(DateTime, comment='接受时间')
    reject_reason = Column(Text, comment='拒绝原因')
    generated_at = Column(DateTime, nullable=False, comment='生成时间')
    valid_until = Column(DateTime, comment='有效期至')
    remark = Column(Text, comment='备注')

    # 关系
    readiness = relationship('MaterialReadiness')
    project = relationship('Project')
    machine = relationship('Machine')
    accepter = relationship('User', foreign_keys=[accepted_by])

    __table_args__ = (
        Index('idx_suggestion_no', 'suggestion_no'),
        Index('idx_suggestion_project', 'project_id'),
        Index('idx_suggestion_machine', 'machine_id'),
        Index('idx_sched_sugg_status', 'status'),
        Index('idx_sched_sugg_type', 'suggestion_type'),
    )

    def __repr__(self):
        return f'<SchedulingSuggestion {self.suggestion_no} type={self.suggestion_type}>'


# ==================== 齐套率历史快照 ====================

class KitRateSnapshot(Base):
    """
    齐套率历史快照表

    用于记录项目/机台每日的齐套率状态，支持历史趋势分析。
    快照来源：
    - DAILY: 每日凌晨定时任务自动生成
    - STAGE_CHANGE: 项目阶段切换时自动生成
    - MANUAL: 用户手动触发
    """
    __tablename__ = 'mes_kit_rate_snapshot'

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 快照对象
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='机台ID（可选，不填则为项目级快照）')

    # 快照时间
    snapshot_date = Column(Date, nullable=False, comment='快照日期')
    snapshot_time = Column(DateTime, nullable=False, comment='快照精确时间')

    # 快照来源
    snapshot_type = Column(
        String(20),
        nullable=False,
        default='DAILY',
        comment='快照类型：DAILY/STAGE_CHANGE/MANUAL'
    )
    trigger_event = Column(String(100), comment='触发事件（如：S3->S4阶段切换）')

    # 齐套率数据
    kit_rate = Column(Numeric(5, 2), nullable=False, default=0, comment='齐套率(%)')
    kit_status = Column(
        String(20),
        nullable=False,
        default='shortage',
        comment='齐套状态：complete/partial/shortage'
    )

    # 物料统计
    total_items = Column(Integer, default=0, comment='BOM物料总项数')
    fulfilled_items = Column(Integer, default=0, comment='已齐套项数')
    shortage_items = Column(Integer, default=0, comment='缺料项数')
    in_transit_items = Column(Integer, default=0, comment='在途项数')

    # 阻塞性物料统计
    blocking_total = Column(Integer, default=0, comment='阻塞性物料总数')
    blocking_fulfilled = Column(Integer, default=0, comment='阻塞性已齐套数')
    blocking_kit_rate = Column(Numeric(5, 2), default=0, comment='阻塞性齐套率(%)')

    # 金额统计
    total_amount = Column(Numeric(14, 2), default=0, comment='物料总金额')
    shortage_amount = Column(Numeric(14, 2), default=0, comment='缺料金额')

    # 项目阶段信息（快照时的状态）
    project_stage = Column(String(20), comment='项目当前阶段')
    project_health = Column(String(10), comment='项目健康度')

    # 分阶段齐套率（JSON格式）
    stage_kit_rates = Column(Text, comment='各装配阶段齐套率JSON')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')

    __table_args__ = (
        # 每个项目每天只有一条 DAILY 快照（但可以有多条 STAGE_CHANGE）
        Index('idx_kit_snapshot_project_date', 'project_id', 'snapshot_date'),
        Index('idx_kit_snapshot_machine_date', 'machine_id', 'snapshot_date'),
        Index('idx_kit_snapshot_type', 'snapshot_type'),
        Index('idx_kit_snapshot_date', 'snapshot_date'),
        # 用于快速查询某项目的历史
        Index('idx_kit_snapshot_project_time', 'project_id', 'snapshot_time'),
    )

    def __repr__(self):
        return f'<KitRateSnapshot project={self.project_id} date={self.snapshot_date} rate={self.kit_rate}%>'
