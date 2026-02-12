# -*- coding: utf-8 -*-
"""
奖金激励模块 ORM 模型
包含：奖金规则、奖金计算记录、奖金发放记录、团队奖金分配
"""

from datetime import datetime

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

from app.models.base import Base, TimestampMixin

# ==================== 奖金规则 ====================

class BonusRule(Base, TimestampMixin):
    """奖金规则表"""
    __tablename__ = 'bonus_rules'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    rule_code = Column(String(50), unique=True, nullable=False, comment='规则编码')
    rule_name = Column(String(200), nullable=False, comment='规则名称')
    bonus_type = Column(String(20), nullable=False, comment='奖金类型')

    # 计算规则
    calculation_formula = Column(Text, comment='计算公式说明')
    base_amount = Column(Numeric(14, 2), comment='基础金额')
    coefficient = Column(Numeric(5, 2), comment='系数')

    # 触发条件
    trigger_condition = Column(JSON, comment='触发条件(JSON)')
    # 例如：{"performance_level": "EXCELLENT", "min_score": 90}
    # 例如：{"milestone_type": "FAT", "status": "COMPLETED"}

    # 适用范围
    apply_to_roles = Column(JSON, comment='适用角色列表')
    apply_to_depts = Column(JSON, comment='适用部门列表')
    apply_to_projects = Column(JSON, comment='适用项目类型列表')

    # 时间范围
    effective_start_date = Column(Date, comment='生效开始日期')
    effective_end_date = Column(Date, comment='生效结束日期')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    priority = Column(Integer, default=0, comment='优先级（数字越大越优先）')

    # 审批
    require_approval = Column(Boolean, default=True, comment='是否需要审批')
    approval_workflow = Column(JSON, comment='审批流程(JSON)')

    # 关系
    calculations = relationship('BonusCalculation', back_populates='rule')

    __table_args__ = (
        Index('idx_bonus_rule_code', 'rule_code'),
        Index('idx_bonus_rule_type', 'bonus_type'),
        Index('idx_bonus_rule_active', 'is_active'),
        {'comment': '奖金规则表'}
    )

    def __repr__(self):
        return f"<BonusRule {self.rule_code}>"


# ==================== 奖金计算记录 ====================

class BonusCalculation(Base, TimestampMixin):
    """奖金计算记录表"""
    __tablename__ = 'bonus_calculations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    calculation_code = Column(String(50), unique=True, nullable=False, comment='计算单号')
    rule_id = Column(Integer, ForeignKey('bonus_rules.id'), nullable=False, comment='规则ID')

    # 关联对象
    period_id = Column(Integer, ForeignKey('performance_period.id'), comment='考核周期ID（绩效奖金）')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID（项目奖金）')
    milestone_id = Column(Integer, ForeignKey('project_milestones.id'), comment='里程碑ID（里程碑奖金）')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='受益人ID')

    # 计算依据
    performance_result_id = Column(Integer, ForeignKey('performance_result.id'), comment='绩效结果ID')
    project_contribution_id = Column(Integer, ForeignKey('project_contribution.id'), comment='项目贡献ID')
    calculation_basis = Column(JSON, comment='计算依据详情(JSON)')

    # 计算结果
    calculated_amount = Column(Numeric(14, 2), nullable=False, comment='计算金额')
    calculation_detail = Column(JSON, comment='计算明细(JSON)')
    # 例如：{"base": 1000, "coefficient": 1.2, "bonus": 1200}

    # 状态
    status = Column(String(20), default='CALCULATED', comment='状态')

    # 审批
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')
    approval_comment = Column(Text, comment='审批意见')

    calculated_at = Column(DateTime, default=datetime.now, comment='计算时间')

    # 关系
    rule = relationship('BonusRule', back_populates='calculations')
    distributions = relationship('BonusDistribution', back_populates='calculation')

    __table_args__ = (
        Index('idx_bonus_calc_code', 'calculation_code'),
        Index('idx_bonus_calc_rule', 'rule_id'),
        Index('idx_bonus_calc_user', 'user_id'),
        Index('idx_bonus_calc_project', 'project_id'),
        Index('idx_bonus_calc_period', 'period_id'),
        Index('idx_bonus_calc_status', 'status'),
        {'comment': '奖金计算记录表'}
    )

    def __repr__(self):
        return f"<BonusCalculation {self.calculation_code}>"


# ==================== 奖金发放记录 ====================

class BonusDistribution(Base, TimestampMixin):
    """奖金发放记录表"""
    __tablename__ = 'bonus_distributions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    distribution_code = Column(String(50), unique=True, nullable=False, comment='发放单号')
    calculation_id = Column(Integer, ForeignKey('bonus_calculations.id'), nullable=False, comment='计算记录ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='受益人ID')

    # 发放信息
    distributed_amount = Column(Numeric(14, 2), nullable=False, comment='发放金额')
    distribution_date = Column(Date, nullable=False, comment='发放日期')
    payment_method = Column(String(20), comment='发放方式')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    # 财务信息
    voucher_no = Column(String(50), comment='凭证号')
    payment_account = Column(String(100), comment='付款账户')
    payment_remark = Column(Text, comment='付款备注')

    paid_by = Column(Integer, ForeignKey('users.id'), comment='发放人')
    paid_at = Column(DateTime, comment='发放时间')

    # 关系
    calculation = relationship('BonusCalculation', back_populates='distributions')

    __table_args__ = (
        Index('idx_bonus_dist_code', 'distribution_code'),
        Index('idx_bonus_dist_calc', 'calculation_id'),
        Index('idx_bonus_dist_user', 'user_id'),
        Index('idx_bonus_dist_status', 'status'),
        Index('idx_bonus_dist_date', 'distribution_date'),
        {'comment': '奖金发放记录表'}
    )

    def __repr__(self):
        return f"<BonusDistribution {self.distribution_code}>"


# ==================== 团队奖金分配 ====================

class TeamBonusAllocation(Base, TimestampMixin):
    """团队奖金分配表"""
    __tablename__ = 'team_bonus_allocations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), comment='周期ID')
    total_bonus_amount = Column(Numeric(14, 2), nullable=False, comment='团队总奖金')

    # 分配规则
    allocation_method = Column(String(20), comment='分配方式')
    allocation_detail = Column(JSON, comment='分配明细(JSON)')
    # 例如：[{"user_id": 1, "ratio": 0.3, "amount": 3000}, ...]

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='审批人')
    approved_at = Column(DateTime, comment='审批时间')

    __table_args__ = (
        Index('idx_team_bonus_project', 'project_id'),
        Index('idx_team_bonus_period', 'period_id'),
        Index('idx_team_bonus_status', 'status'),
        {'comment': '团队奖金分配表'}
    )

    def __repr__(self):
        return f"<TeamBonusAllocation project_id={self.project_id}>"


# ==================== 奖金分配明细表上传记录 ====================

class BonusAllocationSheet(Base, TimestampMixin):
    """奖金分配明细表上传记录表"""
    __tablename__ = 'bonus_allocation_sheets'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    sheet_code = Column(String(50), unique=True, nullable=False, comment='明细表编号')
    sheet_name = Column(String(200), nullable=False, comment='明细表名称')

    # 文件信息
    file_path = Column(String(500), nullable=False, comment='文件路径')
    file_name = Column(String(200), comment='原始文件名')
    file_size = Column(Integer, comment='文件大小（字节）')

    # 关联信息
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID（可选）')
    period_id = Column(Integer, ForeignKey('performance_period.id'), comment='考核周期ID（可选）')

    # 统计信息
    total_rows = Column(Integer, default=0, comment='总行数')
    valid_rows = Column(Integer, default=0, comment='有效行数')
    invalid_rows = Column(Integer, default=0, comment='无效行数')

    # 状态
    status = Column(String(20), default='UPLOADED', comment='状态：UPLOADED/PARSED/DISTRIBUTED')

    # 解析结果
    parse_result = Column(JSON, comment='解析结果(JSON)')
    parse_errors = Column(JSON, comment='解析错误(JSON)')

    # 线下确认标记（记录线下确认完成）
    finance_confirmed = Column(Boolean, default=False, comment='财务部确认')
    hr_confirmed = Column(Boolean, default=False, comment='人力资源部确认')
    manager_confirmed = Column(Boolean, default=False, comment='总经理确认')
    confirmed_at = Column(DateTime, comment='确认完成时间')

    # 发放信息
    distributed_at = Column(DateTime, comment='发放时间')
    distributed_by = Column(Integer, ForeignKey('users.id'), comment='发放人')
    distribution_count = Column(Integer, default=0, comment='发放记录数')

    uploaded_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='上传人')

    # 关系
    project = relationship('Project')
    period = relationship('PerformancePeriod')
    uploader = relationship('User', foreign_keys=[uploaded_by])
    distributor = relationship('User', foreign_keys=[distributed_by])

    __table_args__ = (
        Index('idx_bonus_sheet_code', 'sheet_code'),
        Index('idx_bonus_sheet_status', 'status'),
        Index('idx_bonus_sheet_project', 'project_id'),
        Index('idx_bonus_sheet_period', 'period_id'),
        {'comment': '奖金分配明细表上传记录表'}
    )

    def __repr__(self):
        return f"<BonusAllocationSheet {self.sheet_code}>"





