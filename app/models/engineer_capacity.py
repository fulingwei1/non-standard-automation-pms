# -*- coding: utf-8 -*-
"""
工程师能力与承载力模型
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
    Float,
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class EngineerCapacity(Base, TimestampMixin):
    """
    工程师能力模型表
    
    从历史工作数据自动提取：
    - 同时负责项目数（承载力）
    - 各阶段工作效率
    - 技能标签
    - 质量评分
    """
    __tablename__ = 'engineer_capacity'

    id = Column(Integer, primary_key=True, autoincrement=True)
    engineer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='工程师 ID')
    engineer_name = Column(String(100), comment='工程师姓名')
    department_id = Column(Integer, comment='部门 ID')
    
    # 承载力评估
    avg_concurrent_projects = Column(Float, default=1.0, comment='平均同时负责项目数（从历史数据计算）')
    max_concurrent_projects = Column(Integer, default=1, comment='最大同时负责项目数')
    current_project_count = Column(Integer, default=0, comment='当前负责项目数')
    
    # 工作效率（小时/任务类型）
    mech_design_efficiency = Column(Float, default=1.0, comment='机械设计效率系数')
    electric_design_efficiency = Column(Float, default=1.0, comment='电气设计效率系数')
    assembly_efficiency = Column(Float, default=1.0, comment='装配效率系数')
    debugging_efficiency = Column(Float, default=1.0, comment='调试效率系数')
    
    # 质量评分
    avg_quality_score = Column(Float, default=5.0, comment='平均质量评分（1-10 分）')
    on_time_delivery_rate = Column(Float, default=100.0, comment='按时交付率（%）')
    rework_rate = Column(Float, default=0.0, comment='返工率（%）')
    

    # 技能标签
    skill_tags = Column(Text, comment='技能标签 JSON ["PLC", "伺服", "视觉", ...]')
    specialty_areas = Column(Text, comment='擅长领域 JSON ["机械", "电气", "软件"]')
    

    # AI 能力评估
    ai_skill_level = Column(String(20), default='NONE', comment='AI 技能等级 NONE/BASIC/INTERMEDIATE/ADVANCED/EXPERT')
    ai_tools = Column(Text, comment='常用 AI 工具 JSON ["Copilot", "Cursor", "Claude", "ChatGPT"]')
    ai_usage_frequency = Column(String(20), default='NEVER', comment='使用频率 NEVER/RARELY/SOMETIMES/OFTEN/DAILY')
    ai_efficiency_boost = Column(Float, default=1.0, comment='AI 带来的效率提升系数 (1.0=无提升，2.0=效率翻倍)')
    ai_code_acceptance_rate = Column(Float, default=0.0, comment='AI 代码/方案采纳率 (%)')
    ai_saved_hours = Column(Float, default=0.0, comment='AI 节省的工时 (小时/周)')
    ai_learning_score = Column(Float, default=0.0, comment='AI 学习能力评分 (1-10 分)')
    
    # 核心能力评估
    multi_project_capacity = Column(Integer, default=1, comment='多项目并行能力 (同时负责项目数上限)')
    multi_project_efficiency = Column(Float, default=1.0, comment='多项目效率系数 (>1 表示多任务处理效率高)')
    context_switch_cost = Column(Float, default=0.2, comment='上下文切换成本 (0-1, 越低越好)')
    
    # 标准化/模块化能力
    standardization_score = Column(Float, default=0.0, comment='标准化能力评分 (1-10 分)')
    modularity_score = Column(Float, default=0.0, comment='模块化能力评分 (1-10 分)')
    reuse_rate = Column(Float, default=0.0, comment='方案复用率 (%)')
    standard_modules_created = Column(Integer, default=0, comment='创建的标准模块数量')
    documentation_quality = Column(Float, default=0.0, comment='文档质量评分 (1-10 分)')


    
    # 工作状态
    workload_status = Column(String(20), default='NORMAL', comment='工作负载状态 OVERLOAD/NORMAL/IDLE')
    available_hours_per_week = Column(Float, default=40.0, comment='每周可用工时')
    booked_hours_per_week = Column(Float, default=0.0, comment='已排班工时')
    
    # 更新时间
    last_evaluation_date = Column(Date, comment='最后评估日期')
    
    # 关系
    engineer = relationship('User', foreign_keys=[engineer_id])
    
    __table_args__ = (
        Index('idx_engineer_capacity_engineer', 'engineer_id'),
        Index('idx_engineer_capacity_workload', 'workload_status'),
        {'comment': '工程师能力模型表'}
    )
    
    def __repr__(self):
        return f'<EngineerCapacity {self.engineer_name}>'


class EngineerTaskAssignment(Base, TimestampMixin):
    """
    工程师任务分配表
    """
    __tablename__ = 'engineer_task_assignments'

    id = Column(Integer, primary_key=True, autoincrement=True)
    assignment_no = Column(String(50), unique=True, comment='分配单号')
    
    # 任务信息
    engineer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='工程师 ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目 ID')
    machine_id = Column(Integer, ForeignKey('machines.id'), comment='机台 ID')
    task_type = Column(String(50), comment='任务类型（机械设计/电气设计/装配/调试）')
    task_description = Column(Text, comment='任务描述')
    
    # 工作量评估
    estimated_hours = Column(Float, default=0, comment='预估工时')
    actual_hours = Column(Float, default=0, comment='实际工时')
    
    # 时间安排
    planned_start_date = Column(Date, comment='计划开始日期')
    planned_end_date = Column(Date, comment='计划结束日期')
    actual_start_date = Column(Date, comment='实际开始日期')
    actual_end_date = Column(Date, comment='实际结束日期')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态 PENDING/IN_PROGRESS/COMPLETED/CANCELLED')
    priority = Column(Integer, default=50, comment='优先级 1-100')
    
    # 质量评估
    quality_score = Column(Float, comment='质量评分（1-10 分）')
    is_on_time = Column(Boolean, default=True, comment='是否按时交付')
    has_rework = Column(Boolean, default=False, comment='是否有返工')
    
    # 冲突检测
    has_conflict = Column(Boolean, default=False, comment='是否有时间冲突')
    conflict_description = Column(Text, comment='冲突描述')
    
    # 关系
    engineer = relationship('User', foreign_keys=[engineer_id])
    project = relationship('Project')
    
    __table_args__ = (
        Index('idx_task_assign_engineer', 'engineer_id'),
        Index('idx_task_assign_project', 'project_id'),
        Index('idx_task_assign_status', 'status'),
        Index('idx_task_assign_dates', 'planned_start_date', 'planned_end_date'),
        {'comment': '工程师任务分配表'}
    )
    
    def __repr__(self):
        return f'<EngineerTaskAssignment {self.assignment_no}>'


class WorkloadWarning(Base, TimestampMixin):
    """
    工作量预警表
    """
    __tablename__ = 'workload_warnings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    warning_no = Column(String(50), unique=True, comment='预警单号')
    
    # 预警对象
    engineer_id = Column(Integer, ForeignKey('users.id'), comment='工程师 ID（个人预警）')
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目 ID（项目预警）')
    department_id = Column(Integer, comment='部门 ID（部门预警）')
    
    # 预警类型
    warning_type = Column(String(50), nullable=False, comment='预警类型 OVERLOAD/CONFLICT/DELAY/QUALITY')
    warning_level = Column(String(20), default='MEDIUM', comment='预警级别 LOW/MEDIUM/HIGH/CRITICAL')
    
    # 预警内容
    title = Column(String(200), nullable=False, comment='预警标题')
    description = Column(Text, comment='预警详情')
    impact = Column(Text, comment='影响分析')
    suggestion = Column(Text, comment='处理建议')
    
    # 数据支持
    data_snapshot = Column(Text, comment='数据快照 JSON')
    
    # 状态
    status = Column(String(20), default='ACTIVE', comment='状态 ACTIVE/ACKNOWLEDGED/RESOLVED/IGNORED')
    acknowledged_by = Column(Integer, ForeignKey('users.id'), comment='确认人 ID')
    acknowledged_at = Column(DateTime, comment='确认时间')
    resolved_at = Column(DateTime, comment='解决时间')
    
    # 关系
    engineer = relationship('User', foreign_keys=[engineer_id])
    project = relationship('Project')
    acknowledged_user = relationship('User', foreign_keys=[acknowledged_by])
    
    __table_args__ = (
        Index('idx_warning_engineer', 'engineer_id'),
        Index('idx_warning_project', 'project_id'),
        Index('idx_warning_type', 'warning_type'),
        Index('idx_warning_status', 'status'),
        {'comment': '工作量预警表'}
    )
    
    def __repr__(self):
        return f'<WorkloadWarning {self.warning_no}>'
