# -*- coding: utf-8 -*-
"""
AI资源分配建议表
存储AI生成的资源分配优化方案
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date,
    Numeric, Boolean, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AIResourceAllocation(Base, TimestampMixin):
    """AI资源分配建议表"""
    __tablename__ = 'ai_resource_allocations'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    allocation_code = Column(String(50), unique=True, nullable=False, comment='分配编码')
    
    # 关联项目和任务
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    wbs_suggestion_id = Column(Integer, ForeignKey('ai_wbs_suggestions.id'), comment='WBS建议ID')
    task_id = Column(Integer, ForeignKey('task_unified.id'), comment='实际任务ID')
    
    # AI生成信息
    ai_model_version = Column(String(50), comment='AI模型版本')
    generation_time = Column(DateTime, comment='生成时间')
    confidence_score = Column(Numeric(5, 2), comment='置信度分数(0-100)')
    optimization_method = Column(String(50), comment='优化算法: GENETIC/GREEDY/SIMULATED_ANNEALING')
    
    # 资源信息
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    role_name = Column(String(50), comment='角色名称')
    allocation_type = Column(String(20), comment='分配类型: PRIMARY/SECONDARY/BACKUP/REVIEWER')
    
    # 时间分配
    planned_start_date = Column(Date, comment='计划开始日期')
    planned_end_date = Column(Date, comment='计划结束日期')
    allocated_hours = Column(Numeric(8, 1), comment='分配工时(小时)')
    workload_percentage = Column(Numeric(5, 2), comment='工作负载百分比(0-100)')
    
    # 匹配度分析
    skill_match_score = Column(Numeric(5, 2), comment='技能匹配度(0-100)')
    experience_match_score = Column(Numeric(5, 2), comment='经验匹配度(0-100)')
    availability_score = Column(Numeric(5, 2), comment='可用性评分(0-100)')
    performance_score = Column(Numeric(5, 2), comment='历史绩效评分(0-100)')
    overall_match_score = Column(Numeric(5, 2), comment='综合匹配度(0-100)')
    
    # 技能要求匹配
    required_skills = Column(JSON, comment='所需技能 [{skill, level, weight}]')
    user_skills = Column(JSON, comment='用户技能 [{skill, level, experience_years}]')
    skill_gaps = Column(JSON, comment='技能差距 [{skill, required_level, current_level}]')
    
    # 可用性分析
    current_workload = Column(Numeric(5, 2), comment='当前工作负载(%)')
    concurrent_tasks = Column(Integer, comment='并行任务数')
    is_available = Column(Boolean, default=True, comment='是否可用')
    availability_notes = Column(Text, comment='可用性说明')
    conflicts = Column(JSON, comment='时间冲突 [{task_id, task_name, overlap_days}]')
    
    # 历史绩效
    similar_task_count = Column(Integer, comment='类似任务完成次数')
    avg_task_completion_rate = Column(Numeric(5, 2), comment='平均任务完成率(%)')
    avg_quality_score = Column(Numeric(5, 2), comment='平均质量评分(0-100)')
    avg_on_time_rate = Column(Numeric(5, 2), comment='平均按时完成率(%)')
    
    # 成本信息
    hourly_rate = Column(Numeric(10, 2), comment='小时费率')
    estimated_cost = Column(Numeric(12, 2), comment='预计成本')
    cost_efficiency_score = Column(Numeric(5, 2), comment='成本效益评分(0-100)')
    
    # 推荐理由
    recommendation_reason = Column(Text, comment='推荐理由')
    strengths = Column(JSON, comment='优势 [{category, description, score}]')
    weaknesses = Column(JSON, comment='劣势 [{category, description, impact}]')
    alternative_users = Column(JSON, comment='备选人员 [{user_id, match_score, notes}]')
    
    # 优先级
    priority = Column(String(20), comment='优先级: CRITICAL/HIGH/MEDIUM/LOW')
    is_mandatory = Column(Boolean, default=False, comment='是否必需分配')
    sequence = Column(Integer, comment='分配顺序')
    
    # 用户反馈
    is_accepted = Column(Boolean, comment='是否被采纳')
    is_modified = Column(Boolean, default=False, comment='是否被修改')
    actual_user_id = Column(Integer, ForeignKey('users.id'), comment='实际分配的用户ID')
    modification_reason = Column(Text, comment='修改原因')
    feedback_score = Column(Integer, comment='用户反馈评分(1-5)')
    feedback_notes = Column(Text, comment='用户反馈备注')
    
    # 实际执行对比
    actual_start_date = Column(Date, comment='实际开始日期')
    actual_end_date = Column(Date, comment='实际结束日期')
    actual_hours = Column(Numeric(8, 1), comment='实际工时(小时)')
    actual_cost = Column(Numeric(12, 2), comment='实际成本')
    performance_rating = Column(Integer, comment='任务绩效评分(1-5)')
    completion_quality = Column(Integer, comment='完成质量评分(1-5)')
    
    # 学习数据
    prediction_accuracy = Column(Numeric(5, 2), comment='预测准确度(%)')
    variance_hours = Column(Numeric(8, 1), comment='工时偏差(小时)')
    variance_cost = Column(Numeric(12, 2), comment='成本偏差')
    lessons_learned = Column(Text, comment='经验教训')
    
    # 状态
    status = Column(String(20), default='SUGGESTED', 
                   comment='状态: SUGGESTED/ACCEPTED/REJECTED/MODIFIED/IN_PROGRESS/COMPLETED')
    is_active = Column(Boolean, default=True, comment='是否有效')
    
    # 元数据
    tags = Column(JSON, comment='标签列表')
    extra_metadata = Column(JSON, comment='其他元数据')  # Renamed: SQLAlchemy reserved
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关联关系
    # project = relationship('Project', foreign_keys=[project_id])
    # wbs_suggestion = relationship('AIWbsSuggestion', foreign_keys=[wbs_suggestion_id])
    # task = relationship('TaskUnified', foreign_keys=[task_id])
    # user = relationship('User', foreign_keys=[user_id])
    # actual_user = relationship('User', foreign_keys=[actual_user_id])
    
    # 索引
    __table_args__ = (
        Index('idx_res_alloc_project', 'project_id'),
        Index('idx_wbs_suggestion_id', 'wbs_suggestion_id'),
        Index('idx_user_id', 'user_id'),
        Index('idx_res_alloc_status', 'status'),
        Index('idx_match_score', 'overall_match_score'),
        Index('idx_start_date', 'planned_start_date'),
        Index('idx_end_date', 'planned_end_date'),
        {'comment': 'AI资源分配建议表'}
    )
    
    def __repr__(self):
        return f"<AIResourceAllocation(id={self.id}, user_id={self.user_id}, match={self.overall_match_score})>"
