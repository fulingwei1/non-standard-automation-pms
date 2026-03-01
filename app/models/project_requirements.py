# -*- coding: utf-8 -*-
"""
项目需求与工程师能力匹配模型
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
)
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ProjectRequirement(Base, TimestampMixin):
    """
    项目需求表
    
    从项目文档/合同/BOM 中 AI 抽取
    """
    __tablename__ = 'project_requirements'

    id = Column(Integer, primary_key=True, autoincrement=True)
    requirement_no = Column(String(50), unique=True, comment='需求编号')
    
    # 项目关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目 ID')
    project_name = Column(String(200), comment='项目名称')
    
    # 需求类型
    requirement_type = Column(String(50), nullable=False, comment='需求类型 PRODUCTION/SERVICE/DESIGN/DEBUG')
    
    # 需求内容（AI 抽取）
    requirement_text = Column(Text, comment='原始需求描述')
    extracted_features = Column(Text, comment='抽取的特征 JSON')
    
    # 生产能力需求
    production_complexity = Column(String(20), comment='生产复杂度 LOW/MEDIUM/HIGH/EXPERT')
    required_skills = Column(Text, comment='所需技能 JSON ["机械装配", "电气接线", "PLC 调试"]')
    estimated_hours = Column(Float, default=0, comment='预估工时')
    required_certifications = Column(Text, comment='所需资质 JSON ["电工证", "高空作业证"]')
    
    # 售后服务需求
    service_type = Column(String(50), comment='服务类型 INSTALLATION/TRAINING/MAINTENANCE/REPAIR')
    service_location = Column(String(200), comment='服务地点')
    service_duration = Column(Integer, comment='服务天数')
    required_experience_years = Column(Integer, default=0, comment='所需经验年限')
    customer_facing = Column(Boolean, default=False, comment='是否需要面对客户')
    language_requirements = Column(Text, comment='语言要求 JSON ["中文", "英文"]')
    
    # 能力要求
    min_multi_project_capacity = Column(Integer, default=1, comment='最低多项目能力')
    min_standardization_score = Column(Float, default=0, comment='最低标准化评分')
    min_ai_skill_level = Column(String(20), default='NONE', comment='最低 AI 技能等级')
    
    # 优先级
    priority = Column(Integer, default=50, comment='优先级 1-100')
    deadline = Column(Date, comment='截止日期')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态 PENDING/ASSIGNED/COMPLETED')
    assigned_engineer_id = Column(Integer, ForeignKey('users.id'), comment='分配工程师 ID')
    
    # 关系
    project = relationship('Project')
    assigned_engineer = relationship('User', foreign_keys=[assigned_engineer_id])
    
    __table_args__ = (
        {'comment': '项目需求表'}
    )
    
    def __repr__(self):
        return f'<ProjectRequirement {self.requirement_no}>'


class EngineerRecommendation(Base, TimestampMixin):
    """
    工程师推荐表
    
    AI 根据需求匹配工程师能力
    """
    __tablename__ = 'engineer_recommendations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    recommendation_no = Column(String(50), unique=True, comment='推荐编号')
    
    # 需求关联
    requirement_id = Column(Integer, ForeignKey('project_requirements.id'), nullable=False, comment='需求 ID')
    
    # 推荐工程师
    engineer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='工程师 ID')
    engineer_name = Column(String(100), comment='工程师姓名')
    
    # 匹配度评分
    overall_match_score = Column(Float, default=0, comment='综合匹配度 0-100')
    skill_match_score = Column(Float, default=0, comment='技能匹配度 0-100')
    capacity_match_score = Column(Float, default=0, comment='能力匹配度 0-100')
    availability_score = Column(Float, default=0, comment='可用性评分 0-100')
    location_match_score = Column(Float, default=0, comment='地点匹配度 0-100')
    
    # 匹配详情
    matched_skills = Column(Text, comment='匹配的技能 JSON')
    missing_skills = Column(Text, comment='缺失的技能 JSON')
    advantages = Column(Text, comment='优势 JSON')
    risks = Column(Text, comment='风险 JSON')
    
    # 推荐原因
    recommendation_reason = Column(Text, comment='推荐理由')
    
    # 排序
    rank = Column(Integer, default=999, comment='推荐排名')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态 PENDING/ACCEPTED/REJECTED')
    
    # 关系
    requirement = relationship('ProjectRequirement')
    engineer = relationship('User')
    
    __table_args__ = (
        {'comment': '工程师推荐表'}
    )
    
    def __repr__(self):
        return f'<EngineerRecommendation {self.recommendation_no}>'
