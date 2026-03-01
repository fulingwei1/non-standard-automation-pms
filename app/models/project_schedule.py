# -*- coding: utf-8 -*-
"""
项目智能排程模型
"""

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
    Date,
    DateTime,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ProjectSchedulePlan(Base, TimestampMixin):
    """
    项目进度计划表
    
    AI 生成，支持正常/高强度两种模式
    """
    __tablename__ = 'project_schedule_plans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_no = Column(String(50), unique=True, comment='计划编号')
    
    # 项目关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目 ID')
    project_name = Column(String(200), comment='项目名称')
    
    # 计划模式
    schedule_mode = Column(String(20), nullable=False, comment='计划模式 NORMAL/INTENSIVE')
    mode_name = Column(String(50), comment='模式名称')
    
    # 计划信息
    version = Column(Integer, default=1, comment='版本号')
    generated_by = Column(String(50), default='AI', comment='生成方式')
    
    # 时间信息
    start_date = Column(Date, comment='计划开始日期')
    end_date = Column(Date, comment='计划结束日期')
    total_days = Column(Integer, comment='总工期 (天)')
    working_days = Column(Integer, comment='工作日数')
    
    # 效率系数（基于团队能力）
    team_efficiency_factor = Column(Float, default=1.0, comment='团队效率系数')
    ai_boost_factor = Column(Float, default=1.0, comment='AI 效率提升系数')
    historical_baseline_days = Column(Integer, comment='历史基准工期')
    
    # 计划详情
    phases = Column(Text, comment='阶段计划 JSON')
    tasks = Column(Text, comment='任务列表 JSON')
    milestones = Column(Text, comment='里程碑 JSON')
    resource_allocation = Column(Text, comment='资源分配 JSON')
    
    # 风险评估
    risk_assessment = Column(Text, comment='风险评估 JSON')
    buffer_days = Column(Integer, default=0, comment='缓冲天数')
    
    # 状态
    status = Column(String(20), default='DRAFT', comment='状态 DRAFT/PENDING/APPROVED/ACTIVE/COMPLETED')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人 ID')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='批准人 ID')
    
    # 关系
    project = relationship('Project')
    creator = relationship('User', foreign_keys=[created_by])
    tasks_rel = relationship('ScheduleTask', back_populates='schedule_plan', cascade='all, delete-orphan')
    
    __table_args__ = (
        {'comment': '项目进度计划表'}
    )
    
    def __repr__(self):
        return f'<ProjectSchedulePlan {self.plan_no}>'


class ScheduleTask(Base, TimestampMixin):
    """
    进度计划任务表
    """
    __tablename__ = 'schedule_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 计划关联
    schedule_plan_id = Column(Integer, ForeignKey('project_schedule_plans.id'), nullable=False, comment='计划 ID')
    
    # 任务信息
    task_no = Column(String(50), comment='任务编号')
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_type = Column(String(50), comment='任务类型 DESIGN/PROCUREMENT/ASSEMBLY/DEBUG/etc')
    phase = Column(String(50), comment='所属阶段')
    
    # 时间安排
    planned_start_date = Column(Date, comment='计划开始日期')
    planned_end_date = Column(Date, comment='计划结束日期')
    duration_days = Column(Integer, comment='工期 (天)')
    working_hours = Column(Float, comment='工时 (小时)')
    
    # 依赖关系
    predecessor_tasks = Column(Text, comment='前置任务 JSON [task_id, ...]')
    dependency_type = Column(String(20), default='FS', comment='依赖类型 FS/SS/FF/SF')
    lag_days = Column(Integer, default=0, comment='延迟天数')
    
    # 资源分配
    assigned_engineer_id = Column(Integer, ForeignKey('users.id'), comment='负责工程师 ID')
    assigned_engineer_name = Column(String(100), comment='负责工程师姓名')
    allocation_percentage = Column(Float, default=100, comment='投入比例 (%)')
    
    # 效率调整
    base_duration = Column(Integer, comment='基准工期 (历史平均)')
    efficiency_adjusted_duration = Column(Integer, comment='效率调整后工期')
    efficiency_factors = Column(Text, comment='效率因子 JSON')
    
    # 状态
    status = Column(String(20), default='PLANNED', comment='状态 PLANNED/IN_PROGRESS/COMPLETED')
    progress_percentage = Column(Float, default=0, comment='进度百分比')
    
    # 关系
    schedule_plan = relationship('ProjectSchedulePlan', back_populates='tasks_rel')
    assigned_engineer = relationship('User')
    
    __table_args__ = (
        {'comment': '进度计划任务表'}
    )
    
    def __repr__(self):
        return f'<ScheduleTask {self.task_name}>'
