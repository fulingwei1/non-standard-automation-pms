# -*- coding: utf-8 -*-
"""
AI WBS分解建议表
存储AI生成的工作分解结构建议
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    Numeric, Boolean, JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class AIWbsSuggestion(Base, TimestampMixin):
    """AI WBS分解建议表"""
    __tablename__ = 'ai_wbs_suggestions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    suggestion_code = Column(String(50), unique=True, nullable=False, comment='建议编码')
    
    # 关联项目
    project_id = Column(Integer, ForeignKey('projects.id'), comment='项目ID')
    template_id = Column(Integer, ForeignKey('ai_project_plan_templates.id'), comment='使用的模板ID')
    
    # AI生成信息
    ai_model_version = Column(String(50), comment='AI模型版本')
    generation_time = Column(DateTime, comment='生成时间')
    confidence_score = Column(Numeric(5, 2), comment='置信度分数(0-100)')
    
    # WBS层级结构
    wbs_level = Column(Integer, comment='WBS层级 1-根任务, 2-子任务, 3-孙任务...')
    parent_wbs_id = Column(Integer, ForeignKey('ai_wbs_suggestions.id'), comment='父任务ID')
    wbs_code = Column(String(50), comment='WBS编码 例如: 1.2.3')
    sequence = Column(Integer, comment='同级任务序号')
    
    # 任务信息
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_description = Column(Text, comment='任务描述')
    task_type = Column(String(50), comment='任务类型: 设计/开发/测试/部署等')
    category = Column(String(50), comment='任务分类')
    
    # 工作量估算
    estimated_duration_days = Column(Numeric(6, 1), comment='预计工期(天)')
    estimated_effort_hours = Column(Numeric(8, 1), comment='预计工时(小时)')
    estimated_cost = Column(Numeric(12, 2), comment='预计成本')
    complexity = Column(String(20), comment='复杂度: SIMPLE/MEDIUM/COMPLEX/CRITICAL')
    
    # 依赖关系
    dependencies = Column(JSON, comment='依赖的任务ID列表 [{"task_id": 1, "type": "FS"}]')
    dependency_type = Column(String(20), comment='依赖类型: FS(完成-开始)/SS/FF/SF')
    is_critical_path = Column(Boolean, default=False, comment='是否在关键路径上')
    
    # 资源需求
    required_skills = Column(JSON, comment='所需技能 [{"skill": "Python", "level": "Senior"}]')
    required_roles = Column(JSON, comment='所需角色 [{"role": "开发", "count": 2}]')
    recommended_assignees = Column(JSON, comment='推荐的执行人ID列表')
    
    # 交付物
    deliverables = Column(JSON, comment='交付物列表 [{name, type, description}]')
    acceptance_criteria = Column(Text, comment='验收标准')
    
    # 风险评估
    risk_level = Column(String(20), comment='风险等级: LOW/MEDIUM/HIGH/CRITICAL')
    risk_factors = Column(JSON, comment='风险因素 [{factor, probability, impact}]')
    mitigation_strategies = Column(JSON, comment='缓解策略')
    
    # 参考数据
    reference_task_ids = Column(JSON, comment='参考的历史任务ID列表')
    similarity_score = Column(Numeric(5, 2), comment='与历史任务相似度(0-100)')
    
    # 用户反馈
    is_accepted = Column(Boolean, comment='是否被采纳')
    is_modified = Column(Boolean, default=False, comment='是否被修改')
    actual_task_id = Column(Integer, ForeignKey('task_unified.id'), comment='实际创建的任务ID')
    feedback_score = Column(Integer, comment='用户反馈评分(1-5)')
    feedback_notes = Column(Text, comment='用户反馈备注')
    
    # 实际执行对比
    actual_duration_days = Column(Numeric(6, 1), comment='实际工期(天)')
    actual_effort_hours = Column(Numeric(8, 1), comment='实际工时(小时)')
    actual_cost = Column(Numeric(12, 2), comment='实际成本')
    variance_duration = Column(Numeric(6, 1), comment='工期偏差(天)')
    variance_effort = Column(Numeric(8, 1), comment='工时偏差(小时)')
    variance_cost = Column(Numeric(12, 2), comment='成本偏差')
    
    # 状态
    status = Column(String(20), default='SUGGESTED', 
                   comment='状态: SUGGESTED/ACCEPTED/REJECTED/MODIFIED/COMPLETED')
    is_active = Column(Boolean, default=True, comment='是否有效')
    
    # 元数据
    tags = Column(JSON, comment='标签列表')
    extra_metadata = Column(JSON, comment='其他元数据')  # Renamed: SQLAlchemy reserved
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关联关系
    # project = relationship('Project', foreign_keys=[project_id])
    # template = relationship('AIProjectPlanTemplate', foreign_keys=[template_id])
    # parent_wbs = relationship('AIWbsSuggestion', foreign_keys=[parent_wbs_id], remote_side=[id])
    # actual_task = relationship('TaskUnified', foreign_keys=[actual_task_id])
    
    # 索引
    __table_args__ = (
        Index('idx_project_id', 'project_id'),
        Index('idx_template_id', 'template_id'),
        Index('idx_wbs_level', 'wbs_level'),
        Index('idx_parent_wbs', 'parent_wbs_id'),
        Index('idx_status', 'status'),
        Index('idx_critical_path', 'is_critical_path'),
        {'comment': 'AI WBS分解建议表'}
    )
    
    def __repr__(self):
        return f"<AIWbsSuggestion(id={self.id}, task={self.task_name}, level={self.wbs_level})>"
