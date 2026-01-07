# -*- coding: utf-8 -*-
"""
变更管理(ECN)模块模型
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey, Numeric, Index, JSON
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class EcnType(Base, TimestampMixin):
    """ECN类型配置表"""
    __tablename__ = 'ecn_types'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type_code = Column(String(20), unique=True, nullable=False, comment='类型编码')
    type_name = Column(String(50), nullable=False, comment='类型名称')
    description = Column(Text, comment='描述')
    required_depts = Column(JSON, comment='必需评估部门')
    optional_depts = Column(JSON, comment='可选评估部门')
    approval_matrix = Column(JSON, comment='审批矩阵')
    is_active = Column(Boolean, default=True, comment='是否启用')

    def __repr__(self):
        return f'<EcnType {self.type_code}>'


class EcnApprovalMatrix(Base, TimestampMixin):
    """ECN审批矩阵配置表"""
    __tablename__ = 'ecn_approval_matrix'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_type = Column(String(20), comment='ECN类型')
    condition_type = Column(String(20), nullable=False, comment='条件类型')
    condition_min = Column(Numeric(14, 2), comment='条件下限')
    condition_max = Column(Numeric(14, 2), comment='条件上限')
    approval_level = Column(Integer, nullable=False, comment='审批层级')
    approval_role = Column(String(50), nullable=False, comment='审批角色')
    is_active = Column(Boolean, default=True, comment='是否启用')

    __table_args__ = (
        Index('idx_matrix_type', 'ecn_type'),
    )


class Ecn(Base, TimestampMixin):
    """ECN主表"""
    __tablename__ = 'ecn'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_no = Column(String(50), unique=True, nullable=False, comment='ECN编号')
    ecn_title = Column(String(200), nullable=False, comment='ECN标题')
    ecn_type = Column(String(20), nullable=False, comment='变更类型')

    # 来源
    source_type = Column(String(20), nullable=False, comment='来源类型')
    source_no = Column(String(100), comment='来源单号')
    source_id = Column(Integer, comment='来源ID')

    # 关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='设备ID')

    # 变更内容
    change_reason = Column(Text, nullable=False, comment='变更原因')
    change_description = Column(Text, nullable=False, comment='变更内容描述')
    change_scope = Column(String(20), default='PARTIAL', comment='变更范围')

    # 优先级
    priority = Column(String(20), default='NORMAL', comment='优先级')
    urgency = Column(String(20), default='NORMAL', comment='紧急程度')

    # 影响评估
    cost_impact = Column(Numeric(14, 2), default=0, comment='成本影响')
    schedule_impact_days = Column(Integer, default=0, comment='工期影响(天)')
    quality_impact = Column(String(20), comment='质量影响')

    # 状态
    status = Column(String(20), default='DRAFT', comment='状态')
    current_step = Column(String(50), comment='当前步骤')

    # 申请人
    applicant_id = Column(Integer, ForeignKey('users.id'), comment='申请人')
    applicant_dept = Column(String(100), comment='申请部门')
    applied_at = Column(DateTime, comment='申请时间')

    # 审批结果
    approval_result = Column(String(20), comment='审批结果')
    approval_note = Column(Text, comment='审批意见')
    approved_at = Column(DateTime, comment='审批时间')

    # 执行
    execution_start = Column(DateTime, comment='执行开始')
    execution_end = Column(DateTime, comment='执行结束')
    execution_note = Column(Text, comment='执行说明')

    # 关闭
    closed_at = Column(DateTime, comment='关闭时间')
    closed_by = Column(Integer, ForeignKey('users.id'), comment='关闭人')

    # 附件
    attachments = Column(JSON, comment='附件')

    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人')

    # 关系
    project = relationship('Project')
    machine = relationship('Machine')
    applicant = relationship('User', foreign_keys=[applicant_id])
    evaluations = relationship('EcnEvaluation', back_populates='ecn', lazy='dynamic')
    approvals = relationship('EcnApproval', back_populates='ecn', lazy='dynamic')
    tasks = relationship('EcnTask', back_populates='ecn', lazy='dynamic')
    affected_materials = relationship('EcnAffectedMaterial', back_populates='ecn', lazy='dynamic')
    affected_orders = relationship('EcnAffectedOrder', back_populates='ecn', lazy='dynamic')
    logs = relationship('EcnLog', back_populates='ecn', lazy='dynamic')

    __table_args__ = (
        Index('idx_ecn_project', 'project_id'),
        Index('idx_ecn_status', 'status'),
        Index('idx_ecn_type', 'ecn_type'),
        Index('idx_ecn_applicant', 'applicant_id'),
    )

    def __repr__(self):
        return f'<Ecn {self.ecn_no}>'


class EcnEvaluation(Base, TimestampMixin):
    """ECN评估表"""
    __tablename__ = 'ecn_evaluations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    eval_dept = Column(String(50), nullable=False, comment='评估部门')

    # 评估人
    evaluator_id = Column(Integer, ForeignKey('users.id'), comment='评估人')
    evaluator_name = Column(String(50), comment='评估人姓名')

    # 评估内容
    impact_analysis = Column(Text, comment='影响分析')
    cost_estimate = Column(Numeric(14, 2), default=0, comment='成本估算')
    schedule_estimate = Column(Integer, default=0, comment='工期估算(天)')
    resource_requirement = Column(Text, comment='资源需求')
    risk_assessment = Column(Text, comment='风险评估')

    # 评估结论
    eval_result = Column(String(20), comment='评估结论')
    eval_opinion = Column(Text, comment='评估意见')
    conditions = Column(Text, comment='附加条件')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    evaluated_at = Column(DateTime, comment='评估时间')

    # 附件
    attachments = Column(JSON, comment='附件')

    # 关系
    ecn = relationship('Ecn', back_populates='evaluations')
    evaluator = relationship('User')

    __table_args__ = (
        Index('idx_eval_ecn', 'ecn_id'),
        Index('idx_eval_dept', 'eval_dept'),
        Index('idx_eval_status', 'status'),
    )


class EcnApproval(Base, TimestampMixin):
    """ECN审批表"""
    __tablename__ = 'ecn_approvals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    approval_level = Column(Integer, nullable=False, comment='审批层级')
    approval_role = Column(String(50), nullable=False, comment='审批角色')

    # 审批人
    approver_id = Column(Integer, ForeignKey('users.id'), comment='审批人ID')
    approver_name = Column(String(50), comment='审批人姓名')

    # 审批结果
    approval_result = Column(String(20), comment='审批结果')
    approval_opinion = Column(Text, comment='审批意见')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    approved_at = Column(DateTime, comment='审批时间')

    # 超时
    due_date = Column(DateTime, comment='审批期限')
    is_overdue = Column(Boolean, default=False, comment='是否超期')

    # 关系
    ecn = relationship('Ecn', back_populates='approvals')
    approver = relationship('User')

    __table_args__ = (
        Index('idx_approval_ecn', 'ecn_id'),
        Index('idx_approval_approver', 'approver_id'),
        Index('idx_approval_status', 'status'),
    )


class EcnTask(Base, TimestampMixin):
    """ECN执行任务表"""
    __tablename__ = 'ecn_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    task_no = Column(Integer, nullable=False, comment='任务序号')
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_type = Column(String(50), comment='任务类型')
    task_dept = Column(String(50), comment='责任部门')

    # 任务内容
    task_description = Column(Text, comment='任务描述')
    deliverables = Column(Text, comment='交付物要求')

    # 负责人
    assignee_id = Column(Integer, ForeignKey('users.id'), comment='负责人')
    assignee_name = Column(String(50), comment='负责人姓名')

    # 时间
    planned_start = Column(Date, comment='计划开始')
    planned_end = Column(Date, comment='计划结束')
    actual_start = Column(Date, comment='实际开始')
    actual_end = Column(Date, comment='实际结束')

    # 进度
    progress_pct = Column(Integer, default=0, comment='进度百分比')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    # 完成信息
    completion_note = Column(Text, comment='完成说明')
    attachments = Column(JSON, comment='附件')

    # 关系
    ecn = relationship('Ecn', back_populates='tasks')
    assignee = relationship('User')

    __table_args__ = (
        Index('idx_task_ecn', 'ecn_id'),
        Index('idx_task_assignee', 'assignee_id'),
        Index('idx_task_status', 'status'),
    )


class EcnAffectedMaterial(Base, TimestampMixin):
    """ECN受影响物料表"""
    __tablename__ = 'ecn_affected_materials'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    material_id = Column(Integer, ForeignKey('materials.id'), comment='物料ID')
    bom_item_id = Column(Integer, ForeignKey('bom_items.id'), comment='BOM行ID')

    # 物料信息
    material_code = Column(String(50), nullable=False, comment='物料编码')
    material_name = Column(String(200), nullable=False, comment='物料名称')
    specification = Column(String(500), comment='规格型号')

    # 变更类型
    change_type = Column(String(20), nullable=False, comment='变更类型')

    # 变更前
    old_quantity = Column(Numeric(10, 4), comment='原数量')
    old_specification = Column(String(500), comment='原规格')
    old_supplier_id = Column(Integer, ForeignKey('suppliers.id'), comment='原供应商')

    # 变更后
    new_quantity = Column(Numeric(10, 4), comment='新数量')
    new_specification = Column(String(500), comment='新规格')
    new_supplier_id = Column(Integer, ForeignKey('suppliers.id'), comment='新供应商')

    # 影响
    cost_impact = Column(Numeric(12, 2), default=0, comment='成本影响')

    # 处理状态
    status = Column(String(20), default='PENDING', comment='处理状态')
    processed_at = Column(DateTime, comment='处理时间')

    remark = Column(Text, comment='备注')

    # 关系
    ecn = relationship('Ecn', back_populates='affected_materials')
    material = relationship('Material')

    __table_args__ = (
        Index('idx_affected_mat_ecn', 'ecn_id'),
        Index('idx_affected_mat_material', 'material_id'),
    )


class EcnAffectedOrder(Base, TimestampMixin):
    """ECN受影响订单表"""
    __tablename__ = 'ecn_affected_orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    order_type = Column(String(20), nullable=False, comment='订单类型')
    order_id = Column(Integer, nullable=False, comment='订单ID')
    order_no = Column(String(50), nullable=False, comment='订单号')

    # 影响描述
    impact_description = Column(Text, comment='影响描述')

    # 处理方式
    action_type = Column(String(20), comment='处理方式')
    action_description = Column(Text, comment='处理说明')

    # 处理状态
    status = Column(String(20), default='PENDING', comment='处理状态')
    processed_by = Column(Integer, ForeignKey('users.id'), comment='处理人')
    processed_at = Column(DateTime, comment='处理时间')

    # 关系
    ecn = relationship('Ecn', back_populates='affected_orders')

    __table_args__ = (
        Index('idx_affected_order_ecn', 'ecn_id'),
    )


class EcnLog(Base, TimestampMixin):
    """ECN流转日志表"""
    __tablename__ = 'ecn_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    log_type = Column(String(20), nullable=False, comment='日志类型')
    log_action = Column(String(50), nullable=False, comment='操作动作')

    # 状态变更
    old_status = Column(String(20), comment='原状态')
    new_status = Column(String(20), comment='新状态')

    # 内容
    log_content = Column(Text, comment='日志内容')
    attachments = Column(JSON, comment='附件')

    created_by = Column(Integer, ForeignKey('users.id'), comment='操作人')

    # 关系
    ecn = relationship('Ecn', back_populates='logs')

    __table_args__ = (
        Index('idx_log_ecn', 'ecn_id'),
        Index('idx_log_time', 'created_at'),
    )
