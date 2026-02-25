# -*- coding: utf-8 -*-
"""
AI项目计划模板表
存储AI生成的项目计划模板和推荐
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, 
    Numeric, Boolean, JSON, ForeignKey, Index
)

from app.models.base import Base, TimestampMixin


class AIProjectPlanTemplate(Base, TimestampMixin):
    """AI项目计划模板表"""
    __tablename__ = 'ai_project_plan_templates'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    template_code = Column(String(50), unique=True, nullable=False, comment='模板编码')
    
    # 基础信息
    template_name = Column(String(200), nullable=False, comment='模板名称')
    project_type = Column(String(50), nullable=False, comment='项目类型')
    industry = Column(String(50), comment='行业')
    complexity_level = Column(String(20), comment='复杂度等级: LOW/MEDIUM/HIGH/CRITICAL')
    
    # AI生成信息
    ai_model_version = Column(String(50), comment='AI模型版本')
    generation_time = Column(DateTime, comment='生成时间')
    confidence_score = Column(Numeric(5, 2), comment='置信度分数(0-100)')
    
    # 模板内容
    description = Column(Text, comment='计划描述')
    phases = Column(JSON, comment='项目阶段定义 [{name, duration_days, deliverables}]')
    milestones = Column(JSON, comment='里程碑定义 [{name, phase, estimated_day}]')
    risk_factors = Column(JSON, comment='风险因素 [{category, description, mitigation}]')
    
    # 估算信息
    estimated_duration_days = Column(Integer, comment='预计工期(天)')
    estimated_effort_hours = Column(Numeric(10, 2), comment='预计工时(小时)')
    estimated_cost = Column(Numeric(14, 2), comment='预计成本')
    
    # 资源需求
    required_roles = Column(JSON, comment='所需角色 [{role, skill_level, count}]')
    recommended_team_size = Column(Integer, comment='推荐团队规模')
    
    # 参考数据
    reference_project_ids = Column(JSON, comment='参考的历史项目ID列表')
    reference_count = Column(Integer, default=0, comment='参考项目数量')
    
    # 使用统计
    usage_count = Column(Integer, default=0, comment='使用次数')
    success_rate = Column(Numeric(5, 2), comment='成功率(%)')
    avg_accuracy = Column(Numeric(5, 2), comment='平均准确度(%)')
    
    # 审核状态
    is_verified = Column(Boolean, default=False, comment='是否经过人工审核')
    verified_by = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    verified_at = Column(DateTime, comment='审核时间')
    verification_notes = Column(Text, comment='审核备注')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    is_recommended = Column(Boolean, default=False, comment='是否推荐')
    
    # 元数据
    tags = Column(JSON, comment='标签列表')
    extra_metadata = Column(JSON, comment='其他元数据')  # Renamed: SQLAlchemy reserved
    
    # 创建人
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')
    
    # 关联关系
    # verified_by_user = relationship('User', foreign_keys=[verified_by])
    # created_by_user = relationship('User', foreign_keys=[created_by])
    
    # 索引
    __table_args__ = (
        Index('idx_project_type', 'project_type'),
        Index('idx_plan_tmpl_complexity', 'complexity_level'),
        Index('idx_plan_tmpl_active', 'is_active'),
        Index('idx_confidence', 'confidence_score'),
        {'comment': 'AI项目计划模板表'}
    )
    
    def __repr__(self):
        return f"<AIProjectPlanTemplate(id={self.id}, name={self.template_name}, type={self.project_type})>"
