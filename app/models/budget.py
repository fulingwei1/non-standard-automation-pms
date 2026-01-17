# -*- coding: utf-8 -*-
"""
项目预算管理模块模型
包含：项目预算、预算版本、预算明细、预算审批
"""

from sqlalchemy import (
    JSON,
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


class ProjectBudget(Base, TimestampMixin):
    """项目预算表"""
    __tablename__ = 'project_budgets'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    budget_no = Column(String(50), unique=True, nullable=False, comment='预算编号')

    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')

    # 预算信息
    budget_name = Column(String(200), nullable=False, comment='预算名称')
    budget_type = Column(String(20), default='INITIAL', comment='预算类型：INITIAL/REVISED/SUPPLEMENT（初始/修订/补充）')
    version = Column(String(20), default='V1.0', comment='预算版本号')

    # 金额
    total_amount = Column(Numeric(14, 2), nullable=False, default=0, comment='预算总额')

    # 预算明细（JSON格式）
    budget_breakdown = Column(JSON, comment='预算明细（按成本类别分解）')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态：DRAFT/SUBMITTED/APPROVED/REJECTED')

    # 审批
    submitted_at = Column(DateTime, comment='提交时间')
    submitted_by = Column(Integer, ForeignKey('users.id'), comment='提交人ID')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approved_at = Column(DateTime, comment='审批时间')
    approval_note = Column(Text, comment='审批意见')

    # 生效
    effective_date = Column(Date, comment='生效日期')
    expiry_date = Column(Date, comment='失效日期')
    is_active = Column(Boolean, default=True, comment='是否生效')

    # 备注
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    project = relationship('Project')
    submitter = relationship('User', foreign_keys=[submitted_by])
    approver = relationship('User', foreign_keys=[approved_by])
    creator = relationship('User', foreign_keys=[created_by])
    items = relationship('ProjectBudgetItem', back_populates='budget', cascade='all, delete-orphan')

    __table_args__ = (
        Index('idx_budget_project', 'project_id'),
        Index('idx_budget_status', 'status'),
        Index('idx_budget_version', 'project_id', 'version'),
        {'comment': '项目预算表'}
    )

    def __repr__(self):
        return f'<ProjectBudget {self.budget_no}>'


class ProjectBudgetItem(Base, TimestampMixin):
    """项目预算明细表"""
    __tablename__ = 'project_budget_items'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    budget_id = Column(Integer, ForeignKey('project_budgets.id'), nullable=False, comment='预算ID')

    # 明细信息
    item_no = Column(Integer, nullable=False, comment='行号')
    cost_category = Column(String(50), nullable=False, comment='成本类别')
    cost_item = Column(String(200), nullable=False, comment='成本项')
    description = Column(Text, comment='说明')

    # 金额
    budget_amount = Column(Numeric(14, 2), nullable=False, default=0, comment='预算金额')

    # 关联
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='机台ID（可选）')

    # 备注
    remark = Column(Text, comment='备注')

    # 关系
    budget = relationship('ProjectBudget', back_populates='items')
    machine = relationship('Machine')

    __table_args__ = (
        Index('idx_budget_item_budget', 'budget_id'),
        Index('idx_budget_item_category', 'cost_category'),
        {'comment': '项目预算明细表'}
    )

    def __repr__(self):
        return f'<ProjectBudgetItem {self.budget_id}-{self.item_no}>'


class ProjectCostAllocationRule(Base, TimestampMixin):
    """项目成本分摊规则表"""
    __tablename__ = 'project_cost_allocation_rules'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_name = Column(String(100), nullable=False, comment='规则名称')
    rule_type = Column(String(20), nullable=False, comment='分摊类型：PROPORTION/MANUAL（按比例/手工）')

    # 分摊依据
    allocation_basis = Column(String(20), nullable=False, comment='分摊依据：MACHINE_COUNT/REVENUE/MANUAL（机台数量/收入/手工）')
    allocation_formula = Column(Text, comment='分摊公式（JSON格式）')

    # 适用范围
    cost_type = Column(String(50), comment='适用成本类型（空表示全部）')
    cost_category = Column(String(50), comment='适用成本分类（空表示全部）')
    project_ids = Column(JSON, comment='适用项目ID列表（空表示全部）')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    effective_date = Column(Date, comment='生效日期')
    expiry_date = Column(Date, comment='失效日期')

    # 备注
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_allocation_rule_name', 'rule_name'),
        Index('idx_allocation_rule_type', 'rule_type'),
        {'comment': '项目成本分摊规则表'}
    )

    def __repr__(self):
        return f'<ProjectCostAllocationRule {self.rule_name}>'






