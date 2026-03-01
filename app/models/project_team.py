# -*- coding: utf-8 -*-
"""
项目组团队模型
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


class ProjectTeamPlan(Base, TimestampMixin):
    """
    项目组团队方案表
    
    AI 自动生成，项目经理审核
    """
    __tablename__ = 'project_team_plans'

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_no = Column(String(50), unique=True, comment='方案编号')
    
    # 项目关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目 ID')
    project_name = Column(String(200), comment='项目名称')
    
    # 方案信息
    version = Column(Integer, default=1, comment='版本号')
    generated_by = Column(String(50), default='AI', comment='生成方式 AI/MANUAL')
    
    # 团队规模
    total_members = Column(Integer, default=0, comment='团队总人数')
    total_estimated_hours = Column(Float, default=0, comment='总预估工时')
    estimated_duration_days = Column(Integer, default=0, comment='预计工期 (天)')
    
    # 方案评分
    overall_score = Column(Float, default=0, comment='综合评分 0-100')
    skill_coverage = Column(Float, default=0, comment='技能覆盖率 0-100')
    capacity_balance = Column(Float, default=0, comment='负载均衡度 0-100')
    cost_efficiency = Column(Float, default=0, comment='成本效率 0-100')
    
    # 方案详情
    team_structure = Column(Text, comment='团队结构 JSON')
    role_assignments = Column(Text, comment='角色分配 JSON')
    timeline = Column(Text, comment='时间线 JSON')
    
    # 优势与风险
    advantages = Column(Text, comment='方案优势 JSON')
    risks = Column(Text, comment='潜在风险 JSON')
    recommendations = Column(Text, comment='优化建议 JSON')
    
    # 审核状态
    status = Column(String(20), default='DRAFT', comment='状态 DRAFT/PENDING/APPROVED/REJECTED/ARCHIVED')
    submitted_by = Column(Integer, ForeignKey('users.id'), comment='提交人 ID')
    submitted_at = Column(DateTime, comment='提交时间')
    approved_by = Column(Integer, ForeignKey('users.id'), comment='批准人 ID')
    approved_at = Column(DateTime, comment='批准时间')
    rejected_reason = Column(Text, comment='拒绝原因')
    
    # 关系
    project = relationship('Project')
    submitter = relationship('User', foreign_keys=[submitted_by])
    approver = relationship('User', foreign_keys=[approved_by])
    members = relationship('ProjectTeamMember', back_populates='team_plan', cascade='all, delete-orphan')
    
    __table_args__ = (
        {'comment': '项目组团队方案表'}
    )
    
    def __repr__(self):
        return f'<ProjectTeamPlan {self.plan_no}>'


class ProjectTeamMember(Base, TimestampMixin):
    """
    项目组成员表
    """
    __tablename__ = 'project_team_members'

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 团队方案关联
    team_plan_id = Column(Integer, ForeignKey('project_team_plans.id'), nullable=False, comment='团队方案 ID')
    
    # 工程师信息
    engineer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='工程师 ID')
    engineer_name = Column(String(100), comment='工程师姓名')
    
    # 角色与职责
    role = Column(String(50), nullable=False, comment='角色 PM/TECH_LEAD/MECH_ENG/ELEC_ENG/SERVICE_ENG')
    role_name = Column(String(100), comment='角色名称')
    responsibilities = Column(Text, comment='职责描述 JSON')
    
    # 工作量
    estimated_hours = Column(Float, default=0, comment='预估工时')
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    allocation_percentage = Column(Float, default=100, comment='投入比例 (%)')
    
    # 匹配度
    match_score = Column(Float, default=0, comment='匹配度评分 0-100')
    match_reason = Column(Text, comment='匹配理由')
    
    # 状态
    status = Column(String(20), default='PLANNED', comment='状态 PLANNED/CONFIRMED/IN_PROGRESS/COMPLETED')
    confirmed_by_engineer = Column(Boolean, default=False, comment='工程师是否确认')
    
    # 关系
    team_plan = relationship('ProjectTeamPlan', back_populates='members')
    engineer = relationship('User')
    
    __table_args__ = (
        {'comment': '项目组成员表'}
    )
    
    def __repr__(self):
        return f'<ProjectTeamMember {self.engineer_name} - {self.role}>'


class ProjectTeamApproval(Base, TimestampMixin):
    """
    项目组方案审批记录
    """
    __tablename__ = 'project_team_approvals'

    id = Column(Integer, primary_key=True, autoincrement=True)
    approval_no = Column(String(50), unique=True, comment='审批编号')
    
    # 方案关联
    team_plan_id = Column(Integer, ForeignKey('project_team_plans.id'), nullable=False, comment='团队方案 ID')
    
    # 审批人
    approver_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='审批人 ID')
    approver_name = Column(String(100), comment='审批人姓名')
    approver_role = Column(String(50), comment='审批人角色')
    
    # 审批意见
    decision = Column(String(20), nullable=False, comment='决策 APPROVE/REJECT/MODIFY')
    comments = Column(Text, comment='审批意见')
    modifications = Column(Text, comment='修改内容 JSON')
    
    # 关系
    team_plan = relationship('ProjectTeamPlan')
    approver = relationship('User')
    
    __table_args__ = (
        {'comment': '项目组方案审批记录表'}
    )
    
    def __repr__(self):
        return f'<ProjectTeamApproval {self.approval_no}>'
