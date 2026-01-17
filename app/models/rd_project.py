# -*- coding: utf-8 -*-
"""
研发项目管理模块模型
包含：研发项目、项目分类、研发费用、费用类型、费用分摊规则、报表记录
适用场景：IPO合规、高新技术企业认定、研发费用加计扣除
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


class RdProjectCategory(Base, TimestampMixin):
    """研发项目分类表"""
    __tablename__ = 'rd_project_category'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    category_code = Column(String(20), unique=True, nullable=False, comment='分类编码')
    category_name = Column(String(50), nullable=False, comment='分类名称')
    category_type = Column(String(20), nullable=False, comment='分类类型：SELF/ENTRUST/COOPERATION（自主/委托/合作）')
    description = Column(Text, comment='分类说明')
    sort_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        Index('idx_rd_category_code', 'category_code'),
        Index('idx_rd_category_type', 'category_type'),
        {'comment': '研发项目分类表'}
    )


class RdProject(Base, TimestampMixin):
    """研发项目主表"""
    __tablename__ = 'rd_project'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_no = Column(String(50), unique=True, nullable=False, comment='研发项目编号')
    project_name = Column(String(200), nullable=False, comment='研发项目名称')

    # 分类信息
    category_id = Column(Integer, ForeignKey('rd_project_category.id'), nullable=True, comment='项目分类ID')
    category_type = Column(String(20), nullable=False, comment='项目类型：SELF/ENTRUST/COOPERATION')

    # 立项信息
    initiation_date = Column(Date, nullable=False, comment='立项日期')
    planned_start_date = Column(Date, nullable=True, comment='计划开始日期')
    planned_end_date = Column(Date, nullable=True, comment='计划结束日期')
    actual_start_date = Column(Date, nullable=True, comment='实际开始日期')
    actual_end_date = Column(Date, nullable=True, comment='实际结束日期')

    # 项目负责人
    project_manager_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='项目负责人ID')
    project_manager_name = Column(String(50), comment='项目负责人姓名')

    # 立项信息
    initiation_reason = Column(Text, comment='立项原因')
    research_goal = Column(Text, comment='研发目标')
    research_content = Column(Text, comment='研发内容')
    expected_result = Column(Text, comment='预期成果')
    budget_amount = Column(Numeric(12, 2), default=0, comment='预算金额')

    # 关联非标项目
    linked_project_id = Column(Integer, ForeignKey('projects.id'), nullable=True, comment='关联的非标项目ID')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/PENDING/APPROVED/IN_PROGRESS/COMPLETED/CANCELLED')
    approval_status = Column(String(20), default='PENDING', comment='审批状态：PENDING/APPROVED/REJECTED')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')
    approval_remark = Column(Text, comment='审批意见')

    # 结项信息
    close_date = Column(Date, nullable=True, comment='结项日期')
    close_reason = Column(Text, comment='结项原因')
    close_result = Column(Text, comment='结项成果')
    closed_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='结项人ID')

    # 统计信息
    total_cost = Column(Numeric(12, 2), default=0, comment='总费用')
    total_hours = Column(Numeric(10, 2), default=0, comment='总工时')
    participant_count = Column(Integer, default=0, comment='参与人数')

    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    category = relationship('RdProjectCategory')
    project_manager = relationship('User', foreign_keys=[project_manager_id])
    linked_project = relationship('Project')
    documents = relationship(
        'ProjectDocument',
        back_populates='rd_project',
        lazy='dynamic'
    )

    __table_args__ = (
        Index('idx_rd_project_no', 'project_no'),
        Index('idx_rd_project_category', 'category_id'),
        Index('idx_rd_project_status', 'status'),
        Index('idx_rd_project_manager', 'project_manager_id'),
        Index('idx_rd_project_linked', 'linked_project_id'),
        {'comment': '研发项目主表'}
    )


class RdCostType(Base, TimestampMixin):
    """研发费用类型表"""
    __tablename__ = 'rd_cost_type'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    type_code = Column(String(20), unique=True, nullable=False, comment='费用类型编码')
    type_name = Column(String(50), nullable=False, comment='费用类型名称')
    category = Column(String(20), nullable=False, comment='费用大类：LABOR/MATERIAL/DEPRECIATION/OTHER（人工/材料/折旧/其他）')
    description = Column(Text, comment='类型说明')
    sort_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 加计扣除相关
    is_deductible = Column(Boolean, default=True, comment='是否可加计扣除')
    deduction_rate = Column(Numeric(5, 2), default=100.00, comment='加计扣除比例(%)')

    __table_args__ = (
        Index('idx_rd_cost_type_code', 'type_code'),
        Index('idx_rd_cost_type_category', 'category'),
        {'comment': '研发费用类型表'}
    )


class RdCost(Base, TimestampMixin):
    """研发费用表"""
    __tablename__ = 'rd_cost'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cost_no = Column(String(50), unique=True, nullable=False, comment='费用编号')

    # 关联信息
    rd_project_id = Column(Integer, ForeignKey('rd_project.id'), nullable=False, comment='研发项目ID')
    cost_type_id = Column(Integer, ForeignKey('rd_cost_type.id'), nullable=False, comment='费用类型ID')

    # 费用信息
    cost_date = Column(Date, nullable=False, comment='费用发生日期')
    cost_amount = Column(Numeric(12, 2), nullable=False, comment='费用金额')
    cost_description = Column(Text, comment='费用说明')

    # 人工费用相关（如果费用类型是人工）
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='人员ID（人工费用）')
    hours = Column(Numeric(10, 2), nullable=True, comment='工时（人工费用）')
    hourly_rate = Column(Numeric(10, 2), nullable=True, comment='时薪（人工费用）')

    # 材料费用相关（如果费用类型是材料）
    material_id = Column(Integer, ForeignKey('materials.id'), nullable=True, comment='物料ID（材料费用）')
    material_qty = Column(Numeric(10, 4), nullable=True, comment='物料数量（材料费用）')
    material_price = Column(Numeric(10, 2), nullable=True, comment='物料单价（材料费用）')

    # 折旧费用相关（如果费用类型是折旧）
    equipment_id = Column(Integer, ForeignKey('equipment.id'), nullable=True, comment='设备ID（折旧费用）')
    depreciation_period = Column(String(20), nullable=True, comment='折旧期间（折旧费用）')

    # 来源信息
    source_type = Column(String(20), comment='来源类型：MANUAL/CALCULATED/ALLOCATED（手工录入/自动计算/分摊）')
    source_id = Column(Integer, nullable=True, comment='来源ID（如关联的项目成本ID）')

    # 分摊信息
    is_allocated = Column(Boolean, default=False, comment='是否分摊费用')
    allocation_rule_id = Column(Integer, ForeignKey('rd_cost_allocation_rule.id'), nullable=True, comment='分摊规则ID')
    allocation_rate = Column(Numeric(5, 2), nullable=True, comment='分摊比例(%)')

    # 加计扣除
    deductible_amount = Column(Numeric(12, 2), nullable=True, comment='可加计扣除金额')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/APPROVED/CANCELLED')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='审批人ID')
    approved_at = Column(DateTime, nullable=True, comment='审批时间')

    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    rd_project = relationship('RdProject')
    cost_type = relationship('RdCostType')
    user = relationship('User', foreign_keys=[user_id])
    material = relationship('Material')
    equipment = relationship('Equipment')
    allocation_rule = relationship('RdCostAllocationRule')

    __table_args__ = (
        Index('idx_rd_cost_no', 'cost_no'),
        Index('idx_rd_cost_project', 'rd_project_id'),
        Index('idx_rd_cost_type', 'cost_type_id'),
        Index('idx_rd_cost_date', 'cost_date'),
        Index('idx_rd_cost_status', 'status'),
        {'comment': '研发费用表'}
    )


class RdCostAllocationRule(Base, TimestampMixin):
    """研发费用分摊规则表"""
    __tablename__ = 'rd_cost_allocation_rule'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    rule_type = Column(String(20), nullable=False, comment='分摊类型：PROPORTION/MANUAL（按比例/手工）')

    # 分摊依据
    allocation_basis = Column(String(20), nullable=False, comment='分摊依据：HOURS/REVENUE/HEADCOUNT（工时/收入/人数）')
    allocation_formula = Column(Text, comment='分摊公式（JSON格式）')

    # 适用范围
    cost_type_ids = Column(JSON, comment='适用费用类型ID列表')
    project_ids = Column(JSON, comment='适用项目ID列表（空表示全部）')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    effective_date = Column(Date, nullable=True, comment='生效日期')
    expiry_date = Column(Date, nullable=True, comment='失效日期')

    # 备注
    remark = Column(Text, comment='备注')

    __table_args__ = (
        Index('idx_rd_allocation_rule_name', 'rule_name'),
        Index('idx_rd_allocation_rule_type', 'rule_type'),
        {'comment': '研发费用分摊规则表'}
    )


class RdReportRecord(Base, TimestampMixin):
    """研发报表记录表"""
    __tablename__ = 'rd_report_record'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_no = Column(String(50), unique=True, nullable=False, comment='报表编号')
    report_type = Column(String(50), nullable=False, comment='报表类型：AUXILIARY_LEDGER/DEDUCTION_DETAIL/HIGH_TECH等')
    report_name = Column(String(200), nullable=False, comment='报表名称')

    # 报表参数
    report_params = Column(JSON, comment='报表参数（JSON格式）')
    start_date = Column(Date, nullable=True, comment='开始日期')
    end_date = Column(Date, nullable=True, comment='结束日期')
    project_ids = Column(JSON, comment='项目ID列表')

    # 生成信息
    generated_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='生成人ID')
    generated_at = Column(DateTime, nullable=False, default=datetime.now, comment='生成时间')
    file_path = Column(String(500), nullable=True, comment='文件路径')
    file_size = Column(Integer, nullable=True, comment='文件大小（字节）')

    # 状态
    status = Column(String(20), default='GENERATED', comment='状态：GENERATED/DOWNLOADED/ARCHIVED')

    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    generator = relationship('User')

    __table_args__ = (
        Index('idx_rd_report_no', 'report_no'),
        Index('idx_rd_report_type', 'report_type'),
        Index('idx_rd_report_date', 'generated_at'),
        {'comment': '研发报表记录表'}
    )
