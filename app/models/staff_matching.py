# -*- coding: utf-8 -*-
"""
AI驱动人员智能匹配系统 ORM 模型
包含：标签字典、员工标签评估、员工扩展档案、项目绩效历史、项目人员需求、AI匹配日志
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

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

# ==================== 枚举定义 ====================

class TagTypeEnum(str, Enum):
    """标签类型"""
    SKILL = 'SKILL'           # 技能
    DOMAIN = 'DOMAIN'         # 领域
    ATTITUDE = 'ATTITUDE'     # 态度
    CHARACTER = 'CHARACTER'   # 性格
    SPECIAL = 'SPECIAL'       # 特殊能力


class StaffingPriorityEnum(str, Enum):
    """人员需求优先级"""
    P1 = 'P1'  # 最高优先级 - 阈值85分
    P2 = 'P2'  # 高优先级 - 阈值75分
    P3 = 'P3'  # 中等优先级 - 阈值65分
    P4 = 'P4'  # 低优先级 - 阈值55分
    P5 = 'P5'  # 最低优先级 - 阈值50分


class StaffingStatusEnum(str, Enum):
    """人员需求状态"""
    OPEN = 'OPEN'           # 开放
    MATCHING = 'MATCHING'   # 匹配中
    FILLED = 'FILLED'       # 已填满
    CANCELLED = 'CANCELLED' # 已取消


class RecommendationTypeEnum(str, Enum):
    """推荐类型"""
    STRONG = 'STRONG'           # 强烈推荐 (>阈值+15)
    RECOMMENDED = 'RECOMMENDED' # 推荐 (>=阈值)
    ACCEPTABLE = 'ACCEPTABLE'   # 可接受 (>=阈值-10)
    WEAK = 'WEAK'               # 较弱匹配 (<阈值-10)


class ContributionLevelEnum(str, Enum):
    """贡献等级"""
    CORE = 'CORE'       # 核心贡献
    MAJOR = 'MAJOR'     # 主要贡献
    NORMAL = 'NORMAL'   # 一般贡献
    MINOR = 'MINOR'     # 次要贡献


# ==================== 标签字典 ====================

class HrTagDict(Base, TimestampMixin):
    """标签字典表"""
    __tablename__ = 'hr_tag_dict'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    tag_code = Column(String(50), unique=True, nullable=False, comment='标签编码')
    tag_name = Column(String(100), nullable=False, comment='标签名称')
    tag_type = Column(String(20), nullable=False, comment='标签类型 (SKILL/DOMAIN/ATTITUDE/CHARACTER/SPECIAL)')
    parent_id = Column(Integer, ForeignKey('hr_tag_dict.id'), comment='父标签ID（支持层级）')
    weight = Column(Numeric(5, 2), default=1.0, comment='权重')
    is_required = Column(Boolean, default=False, comment='是否必需标签')
    description = Column(Text, comment='标签描述')
    sort_order = Column(Integer, default=0, comment='排序')
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 关系 - 自引用层级
    parent = relationship('HrTagDict', remote_side=[id], backref='children')
    # 关系 - 标签评估
    evaluations = relationship('HrEmployeeTagEvaluation', back_populates='tag')

    __table_args__ = (
        Index('idx_hr_tag_dict_type', 'tag_type'),
        Index('idx_hr_tag_dict_parent', 'parent_id'),
        Index('idx_hr_tag_dict_active', 'is_active'),
        {'comment': '标签字典表'}
    )

    def __repr__(self):
        return f"<HrTagDict {self.tag_code}: {self.tag_name}>"


# ==================== 员工标签评估 ====================

class HrEmployeeTagEvaluation(Base, TimestampMixin):
    """员工标签评估表"""
    __tablename__ = 'hr_employee_tag_evaluation'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    tag_id = Column(Integer, ForeignKey('hr_tag_dict.id'), nullable=False, comment='标签ID')
    score = Column(Integer, nullable=False, comment='评分1-5')
    evidence = Column(Text, comment='评分依据/证据')
    evaluator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评估人ID')
    evaluate_date = Column(Date, nullable=False, comment='评估日期')
    is_valid = Column(Boolean, default=True, comment='是否有效')

    # 关系
    employee = relationship('Employee', backref='tag_evaluations')
    tag = relationship('HrTagDict', back_populates='evaluations')
    evaluator = relationship('User', foreign_keys=[evaluator_id])

    __table_args__ = (
        Index('idx_hr_eval_employee', 'employee_id'),
        Index('idx_hr_eval_tag', 'tag_id'),
        Index('idx_hr_eval_evaluator', 'evaluator_id'),
        Index('idx_hr_eval_date', 'evaluate_date'),
        Index('idx_hr_eval_valid', 'is_valid'),
        {'comment': '员工标签评估表'}
    )

    def __repr__(self):
        return f"<HrEmployeeTagEvaluation employee={self.employee_id} tag={self.tag_id} score={self.score}>"


# ==================== 员工扩展档案 ====================

class HrEmployeeProfile(Base, TimestampMixin):
    """员工扩展档案表 - 用于AI匹配"""
    __tablename__ = 'hr_employee_profile'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('employees.id'), unique=True, nullable=False, comment='员工ID')

    # 各类标签聚合 (JSON格式: [{tag_id, score, tag_name, tag_code}])
    skill_tags = Column(JSON, comment='技能标签JSON')
    domain_tags = Column(JSON, comment='领域标签JSON')
    attitude_tags = Column(JSON, comment='态度标签JSON')
    character_tags = Column(JSON, comment='性格标签JSON')
    special_tags = Column(JSON, comment='特殊能力JSON')

    # 聚合得分
    attitude_score = Column(Numeric(5, 2), comment='态度得分（聚合）')
    quality_score = Column(Numeric(5, 2), comment='质量得分（聚合）')

    # 工作负载
    current_workload_pct = Column(Numeric(5, 2), default=0, comment='当前工作负载百分比')
    available_hours = Column(Numeric(10, 2), default=0, comment='可用工时')

    # 统计数据
    total_projects = Column(Integer, default=0, comment='参与项目总数')
    avg_performance_score = Column(Numeric(5, 2), comment='平均绩效得分')

    profile_updated_at = Column(DateTime, comment='档案更新时间')

    # 关系
    employee = relationship('Employee', backref='ai_profile')

    __table_args__ = (
        Index('idx_hr_profile_employee', 'employee_id'),
        Index('idx_hr_profile_workload', 'current_workload_pct'),
        Index('idx_hr_profile_quality', 'quality_score'),
        {'comment': '员工扩展档案表'}
    )

    def __repr__(self):
        return f"<HrEmployeeProfile employee={self.employee_id} workload={self.current_workload_pct}%>"


# ==================== 项目绩效历史 ====================

class HrProjectPerformance(Base, TimestampMixin):
    """项目绩效历史表"""
    __tablename__ = 'hr_project_performance'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, comment='员工ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    role_code = Column(String(50), nullable=False, comment='角色编码')
    role_name = Column(String(100), comment='角色名称')

    # 绩效得分
    performance_score = Column(Numeric(5, 2), comment='绩效得分')
    quality_score = Column(Numeric(5, 2), comment='质量得分')
    collaboration_score = Column(Numeric(5, 2), comment='协作得分')
    on_time_rate = Column(Numeric(5, 2), comment='按时完成率')

    # 贡献等级
    contribution_level = Column(String(20), comment='贡献等级 (CORE/MAJOR/NORMAL/MINOR)')
    hours_spent = Column(Numeric(10, 2), comment='投入工时')

    # 评估信息
    evaluation_date = Column(Date, comment='评估日期')
    evaluator_id = Column(Integer, ForeignKey('users.id'), comment='评估人ID')
    comments = Column(Text, comment='评价意见')

    # 关系
    employee = relationship('Employee', backref='project_performances')
    project = relationship('Project', backref='staff_performances')
    evaluator = relationship('User', foreign_keys=[evaluator_id])

    __table_args__ = (
        Index('idx_hr_perf_employee', 'employee_id'),
        Index('idx_hr_perf_project', 'project_id'),
        Index('idx_hr_perf_role', 'role_code'),
        Index('idx_hr_perf_contribution', 'contribution_level'),
        Index('idx_hr_perf_emp_proj', 'employee_id', 'project_id', unique=True),
        {'comment': '项目绩效历史表'}
    )

    def __repr__(self):
        return f"<HrProjectPerformance employee={self.employee_id} project={self.project_id} score={self.performance_score}>"


# ==================== 项目人员需求 ====================

class MesProjectStaffingNeed(Base, TimestampMixin):
    """项目人员需求表"""
    __tablename__ = 'mes_project_staffing_need'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    role_code = Column(String(50), nullable=False, comment='角色编码')
    role_name = Column(String(100), comment='角色名称')
    headcount = Column(Integer, default=1, comment='需求人数')

    # 技能要求 (JSON格式: [{tag_id, min_score}])
    required_skills = Column(JSON, nullable=False, comment='必需技能JSON')
    preferred_skills = Column(JSON, comment='优选技能JSON')
    required_domains = Column(JSON, comment='必需领域JSON')
    required_attitudes = Column(JSON, comment='必需态度JSON')

    min_level = Column(String(20), comment='最低等级')
    priority = Column(String(10), default='P3', comment='优先级 P1-P5')

    # 时间安排
    start_date = Column(Date, comment='开始日期')
    end_date = Column(Date, comment='结束日期')
    allocation_pct = Column(Numeric(5, 2), default=100, comment='分配比例')

    # 状态
    status = Column(String(20), default='OPEN', comment='状态 (OPEN/MATCHING/FILLED/CANCELLED)')
    requester_id = Column(Integer, ForeignKey('users.id'), comment='申请人ID')
    filled_count = Column(Integer, default=0, comment='已填充人数')
    remark = Column(Text, comment='备注')

    # 关系
    project = relationship('Project', backref='staffing_needs')
    requester = relationship('User', foreign_keys=[requester_id])
    matching_logs = relationship('HrAIMatchingLog', back_populates='staffing_need')

    __table_args__ = (
        Index('idx_staffing_project', 'project_id'),
        Index('idx_staffing_role', 'role_code'),
        Index('idx_staffing_priority', 'priority'),
        Index('idx_staffing_status', 'status'),
        Index('idx_staffing_requester', 'requester_id'),
        {'comment': '项目人员需求表'}
    )

    def __repr__(self):
        return f"<MesProjectStaffingNeed project={self.project_id} role={self.role_code} status={self.status}>"


# ==================== AI匹配日志 ====================

class HrAIMatchingLog(Base):
    """AI匹配日志表"""
    __tablename__ = 'hr_ai_matching_log'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    request_id = Column(String(50), nullable=False, comment='匹配请求ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    staffing_need_id = Column(Integer, ForeignKey('mes_project_staffing_need.id'), nullable=False, comment='人员需求ID')
    candidate_employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, comment='候选员工ID')

    # 匹配得分
    total_score = Column(Numeric(5, 2), nullable=False, comment='综合得分')
    dimension_scores = Column(JSON, nullable=False, comment='各维度得分JSON')
    rank = Column(Integer, nullable=False, comment='排名')
    recommendation_type = Column(String(20), comment='推荐类型 (STRONG/RECOMMENDED/ACCEPTABLE/WEAK)')

    # 采纳信息
    is_accepted = Column(Boolean, comment='是否被采纳')
    accept_time = Column(DateTime, comment='采纳时间')
    acceptor_id = Column(Integer, ForeignKey('users.id'), comment='采纳人ID')
    reject_reason = Column(Text, comment='拒绝原因')

    matching_time = Column(DateTime, default=datetime.now, comment='匹配时间')
    created_at = Column(DateTime, default=datetime.now, comment='创建时间')

    # 关系
    project = relationship('Project', backref='matching_logs')
    staffing_need = relationship('MesProjectStaffingNeed', back_populates='matching_logs')
    candidate = relationship('Employee', backref='matching_candidates')
    acceptor = relationship('User', foreign_keys=[acceptor_id])

    __table_args__ = (
        Index('idx_matching_request', 'request_id'),
        Index('idx_matching_project', 'project_id'),
        Index('idx_matching_need', 'staffing_need_id'),
        Index('idx_matching_candidate', 'candidate_employee_id'),
        Index('idx_matching_accepted', 'is_accepted'),
        Index('idx_matching_time', 'matching_time'),
        {'comment': 'AI匹配日志表'}
    )

    def __repr__(self):
        return f"<HrAIMatchingLog request={self.request_id} candidate={self.candidate_employee_id} score={self.total_score}>"
