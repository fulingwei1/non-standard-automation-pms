# -*- coding: utf-8 -*-
"""
PMO模型 - 资源分配和项目结项
"""
from sqlalchemy import Column, Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class PmoResourceAllocation(Base, TimestampMixin):
    """项目资源分配"""
    __tablename__ = 'pmo_resource_allocation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    task_id = Column(Integer, comment='任务ID')

    # 资源信息
    resource_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='资源ID(人员ID)')
    resource_name = Column(String(50), comment='资源名称')
    resource_dept = Column(String(50), comment='所属部门')
    resource_role = Column(String(50), comment='项目角色')

    # 分配信息
    allocation_percent = Column(Integer, default=100, comment='分配比例(%)')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    planned_hours = Column(Integer, comment='计划工时')
    actual_hours = Column(Integer, default=0, comment='实际工时')

    # 状态
    status = Column(String(20), default='PLANNED', comment='状态')

    __table_args__ = (
        Index('idx_pmo_alloc_project', 'project_id'),
        Index('idx_pmo_alloc_resource', 'resource_id'),
        Index('idx_pmo_alloc_dates', 'start_date', 'end_date'),
        {'comment': '项目资源分配表'}
    )


class PmoProjectClosure(Base, TimestampMixin):
    """项目结项"""
    __tablename__ = 'pmo_project_closure'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, unique=True, comment='项目ID')

    # 验收信息
    acceptance_date = Column(Date, comment='验收日期')
    acceptance_result = Column(String(20), comment='验收结果:PASSED/CONDITIONAL/FAILED')
    acceptance_notes = Column(Text, comment='验收说明')

    # 项目总结
    project_summary = Column(Text, comment='项目总结')
    achievement = Column(Text, comment='项目成果')
    lessons_learned = Column(Text, comment='经验教训')
    improvement_suggestions = Column(Text, comment='改进建议')

    # 成本核算
    final_budget = Column(Numeric(14, 2), comment='最终预算')
    final_cost = Column(Numeric(14, 2), comment='最终成本')
    cost_variance = Column(Numeric(14, 2), comment='成本偏差')

    # 工时核算
    final_planned_hours = Column(Integer, comment='最终计划工时')
    final_actual_hours = Column(Integer, comment='最终实际工时')
    hours_variance = Column(Integer, comment='工时偏差')

    # 进度核算
    plan_duration = Column(Integer, comment='计划周期(天)')
    actual_duration = Column(Integer, comment='实际周期(天)')
    schedule_variance = Column(Integer, comment='进度偏差(天)')

    # 质量评估
    quality_score = Column(Integer, comment='质量评分')
    customer_satisfaction = Column(Integer, comment='客户满意度')

    # 文档归档
    archive_status = Column(String(20), comment='归档状态:PENDING/ARCHIVING/COMPLETED')
    archive_path = Column(String(500), comment='归档路径')

    # 结项评审
    closure_date = Column(Date, comment='结项日期')
    reviewed_by = Column(Integer, ForeignKey('users.id'), comment='评审人')
    review_date = Column(Date, comment='评审日期')
    review_result = Column(String(20), comment='评审结果:APPROVED/REJECTED')

    __table_args__ = (
        {'comment': '项目结项表'}
    )
