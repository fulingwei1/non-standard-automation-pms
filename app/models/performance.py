# -*- coding: utf-8 -*-
"""
绩效管理模块 ORM 模型
包含：绩效考核周期、考核指标、绩效结果、绩效评价、排行榜快照
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Date, DateTime,
    Numeric, ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin
from enum import Enum


# ==================== 枚举定义 ====================

class PerformancePeriodTypeEnum(str, Enum):
    """考核周期类型"""
    WEEKLY = 'WEEKLY'        # 周
    MONTHLY = 'MONTHLY'      # 月
    QUARTERLY = 'QUARTERLY'  # 季度
    YEARLY = 'YEARLY'        # 年度


class PerformanceLevelEnum(str, Enum):
    """绩效等级"""
    EXCELLENT = 'EXCELLENT'              # 优秀 (A)
    GOOD = 'GOOD'                        # 良好 (B)
    QUALIFIED = 'QUALIFIED'              # 合格 (C)
    NEEDS_IMPROVEMENT = 'NEEDS_IMPROVEMENT'  # 待改进 (D)


class IndicatorTypeEnum(str, Enum):
    """指标类型"""
    WORKLOAD = 'WORKLOAD'        # 工作量指标
    TASK = 'TASK'                # 任务指标
    QUALITY = 'QUALITY'          # 质量指标
    COLLABORATION = 'COLLABORATION'  # 协作指标
    GROWTH = 'GROWTH'            # 成长指标


class PerformanceStatusEnum(str, Enum):
    """绩效状态"""
    PENDING = 'PENDING'          # 待计算
    CALCULATED = 'CALCULATED'    # 已计算
    REVIEWING = 'REVIEWING'      # 评审中
    CONFIRMED = 'CONFIRMED'      # 已确认
    APPEALING = 'APPEALING'      # 申诉中
    FINALIZED = 'FINALIZED'      # 已定稿


# ==================== 绩效考核周期 ====================

class PerformancePeriod(Base, TimestampMixin):
    """绩效考核周期"""
    __tablename__ = 'performance_period'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_code = Column(String(20), unique=True, nullable=False, comment='周期编码')
    period_name = Column(String(100), nullable=False, comment='周期名称')
    period_type = Column(String(20), nullable=False, comment='周期类型')
    
    # 时间范围
    start_date = Column(Date, nullable=False, comment='开始日期')
    end_date = Column(Date, nullable=False, comment='结束日期')
    
    # 状态
    status = Column(String(20), default='PENDING', comment='状态')
    is_active = Column(Boolean, default=True, comment='是否当前周期')
    
    # 计算/评审时间
    calculate_date = Column(Date, comment='计算日期')
    review_deadline = Column(Date, comment='评审截止日期')
    finalize_date = Column(Date, comment='定稿日期')
    
    # 备注
    remarks = Column(Text, comment='备注')
    
    # 关系
    results = relationship('PerformanceResult', back_populates='period')
    
    __table_args__ = (
        Index('idx_perf_period_code', 'period_code'),
        Index('idx_perf_period_dates', 'start_date', 'end_date'),
        {'comment': '绩效考核周期表'}
    )


# ==================== 绩效考核指标配置 ====================

class PerformanceIndicator(Base, TimestampMixin):
    """绩效考核指标配置"""
    __tablename__ = 'performance_indicator'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    indicator_code = Column(String(50), unique=True, nullable=False, comment='指标编码')
    indicator_name = Column(String(100), nullable=False, comment='指标名称')
    indicator_type = Column(String(20), nullable=False, comment='指标类型')
    
    # 计算方式
    calculation_formula = Column(Text, comment='计算公式说明')
    data_source = Column(String(100), comment='数据来源')
    
    # 权重
    weight = Column(Numeric(5, 2), default=0, comment='权重(%)')
    
    # 评分标准
    scoring_rules = Column(JSON, comment='评分规则(JSON)')
    max_score = Column(Integer, default=100, comment='最高分')
    min_score = Column(Integer, default=0, comment='最低分')
    
    # 适用范围
    apply_to_roles = Column(JSON, comment='适用角色列表')
    apply_to_depts = Column(JSON, comment='适用部门列表')
    
    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')
    
    # 排序
    sort_order = Column(Integer, default=0, comment='排序')
    
    __table_args__ = (
        Index('idx_perf_indicator_code', 'indicator_code'),
        Index('idx_perf_indicator_type', 'indicator_type'),
        {'comment': '绩效考核指标配置表'}
    )


# ==================== 绩效结果 ====================

class PerformanceResult(Base, TimestampMixin):
    """绩效结果"""
    __tablename__ = 'performance_result'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), nullable=False, comment='考核周期ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    user_name = Column(String(50), comment='用户姓名')
    department_id = Column(Integer, comment='部门ID')
    department_name = Column(String(100), comment='部门名称')
    
    # 综合得分
    total_score = Column(Numeric(5, 2), comment='综合得分')
    level = Column(String(20), comment='绩效等级')
    
    # 分项得分
    workload_score = Column(Numeric(5, 2), comment='工作量得分')
    task_score = Column(Numeric(5, 2), comment='任务得分')
    quality_score = Column(Numeric(5, 2), comment='质量得分')
    collaboration_score = Column(Numeric(5, 2), comment='协作得分')
    growth_score = Column(Numeric(5, 2), comment='成长得分')
    
    # 详细数据
    indicator_scores = Column(JSON, comment='各指标详细得分(JSON)')
    
    # 排名
    dept_rank = Column(Integer, comment='部门排名')
    company_rank = Column(Integer, comment='公司排名')
    
    # 环比
    score_change = Column(Numeric(5, 2), comment='得分变化')
    rank_change = Column(Integer, comment='排名变化')
    
    # 亮点与待改进
    highlights = Column(JSON, comment='亮点(JSON)')
    improvements = Column(JSON, comment='待改进(JSON)')
    
    # 状态
    status = Column(String(20), default='CALCULATED', comment='状态')
    
    # 计算时间
    calculated_at = Column(DateTime, comment='计算时间')
    
    # 关系
    period = relationship('PerformancePeriod', back_populates='results')
    evaluations = relationship('PerformanceEvaluation', back_populates='result')
    
    __table_args__ = (
        Index('idx_perf_result_period', 'period_id'),
        Index('idx_perf_result_user', 'user_id'),
        Index('idx_perf_result_dept', 'department_id'),
        Index('idx_perf_result_score', 'total_score'),
        {'comment': '绩效结果表'}
    )


# ==================== 绩效评价（上级评语） ====================

class PerformanceEvaluation(Base, TimestampMixin):
    """绩效评价（上级评语）"""
    __tablename__ = 'performance_evaluation'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    result_id = Column(Integer, ForeignKey('performance_result.id'), nullable=False, comment='绩效结果ID')
    
    # 评价人
    evaluator_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='评价人ID')
    evaluator_name = Column(String(50), comment='评价人姓名')
    evaluator_role = Column(String(50), comment='评价人角色')
    
    # 评价内容
    overall_comment = Column(Text, comment='总体评价')
    strength_comment = Column(Text, comment='优点评价')
    improvement_comment = Column(Text, comment='改进建议')
    
    # 调整
    adjusted_level = Column(String(20), comment='调整后等级')
    adjustment_reason = Column(Text, comment='调整原因')
    
    # 评价时间
    evaluated_at = Column(DateTime, default=datetime.now, comment='评价时间')
    
    # 关系
    result = relationship('PerformanceResult', back_populates='evaluations')
    
    __table_args__ = (
        Index('idx_perf_eval_result', 'result_id'),
        Index('idx_perf_eval_evaluator', 'evaluator_id'),
        {'comment': '绩效评价表'}
    )


# ==================== 绩效申诉 ====================

class PerformanceAppeal(Base, TimestampMixin):
    """绩效申诉"""
    __tablename__ = 'performance_appeal'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    result_id = Column(Integer, ForeignKey('performance_result.id'), nullable=False, comment='绩效结果ID')
    
    # 申诉人
    appellant_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='申诉人ID')
    appellant_name = Column(String(50), comment='申诉人姓名')
    
    # 申诉内容
    appeal_reason = Column(Text, nullable=False, comment='申诉理由')
    expected_score = Column(Numeric(5, 2), comment='期望得分')
    supporting_evidence = Column(Text, comment='支撑证据')
    attachments = Column(JSON, comment='附件')
    
    # 申诉时间
    appeal_time = Column(DateTime, default=datetime.now, comment='申诉时间')
    
    # 处理状态
    status = Column(String(20), default='PENDING', comment='状态:PENDING/ACCEPTED/REJECTED/CLOSED')
    
    # 处理结果
    handler_id = Column(Integer, ForeignKey('users.id'), comment='处理人ID')
    handler_name = Column(String(50), comment='处理人')
    handle_time = Column(DateTime, comment='处理时间')
    handle_result = Column(Text, comment='处理结果')
    new_score = Column(Numeric(5, 2), comment='调整后得分')
    new_level = Column(String(20), comment='调整后等级')
    
    __table_args__ = (
        Index('idx_appeal_result', 'result_id'),
        Index('idx_appeal_appellant', 'appellant_id'),
        Index('idx_appeal_status', 'status'),
        {'comment': '绩效申诉表'}
    )


# ==================== 项目贡献记录 ====================

class ProjectContribution(Base, TimestampMixin):
    """项目贡献记录"""
    __tablename__ = 'project_contribution'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), nullable=False, comment='考核周期ID')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='用户ID')
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, comment='项目ID')
    project_code = Column(String(50), comment='项目编号')
    project_name = Column(String(200), comment='项目名称')
    
    # 贡献统计
    task_count = Column(Integer, default=0, comment='任务数')
    completed_tasks = Column(Integer, default=0, comment='完成任务数')
    on_time_tasks = Column(Integer, default=0, comment='按时完成数')
    hours_spent = Column(Numeric(10, 2), default=0, comment='投入工时')
    hours_percentage = Column(Numeric(5, 2), comment='工时占比(%)')
    
    # 贡献评价
    contribution_level = Column(String(20), comment='贡献等级:CORE/MAJOR/NORMAL/MINOR')
    role_in_project = Column(String(50), comment='项目中角色')
    
    __table_args__ = (
        Index('idx_contrib_period', 'period_id'),
        Index('idx_contrib_user', 'user_id'),
        Index('idx_contrib_project', 'project_id'),
        {'comment': '项目贡献记录表'}
    )


# ==================== 排行榜快照 ====================

class PerformanceRankingSnapshot(Base, TimestampMixin):
    """排行榜快照"""
    __tablename__ = 'performance_ranking_snapshot'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    period_id = Column(Integer, ForeignKey('performance_period.id'), nullable=False, comment='考核周期ID')
    scope_type = Column(String(20), nullable=False, comment='范围类型:TEAM/DEPARTMENT/COMPANY')
    scope_id = Column(Integer, comment='范围ID')
    scope_name = Column(String(100), comment='范围名称')
    
    # 统计数据
    total_members = Column(Integer, comment='总人数')
    avg_score = Column(Numeric(5, 2), comment='平均分')
    max_score = Column(Numeric(5, 2), comment='最高分')
    min_score = Column(Numeric(5, 2), comment='最低分')
    median_score = Column(Numeric(5, 2), comment='中位数')
    
    # 等级分布
    level_distribution = Column(JSON, comment='等级分布(JSON)')
    
    # 排名数据
    ranking_data = Column(JSON, comment='排名数据(JSON)')
    
    # 快照时间
    snapshot_time = Column(DateTime, default=datetime.now, comment='快照时间')
    
    __table_args__ = (
        Index('idx_ranking_period', 'period_id'),
        Index('idx_ranking_scope', 'scope_type', 'scope_id'),
        {'comment': '排行榜快照表'}
    )

