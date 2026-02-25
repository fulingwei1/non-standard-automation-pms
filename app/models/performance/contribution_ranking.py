# -*- coding: utf-8 -*-
"""
绩效模型 - 贡献和排行榜
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String

from ..base import Base, TimestampMixin


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


class PerformanceRankingSnapshot(Base, TimestampMixin):
    """排行榜快照
    
    【状态】未启用 - 绩效排名快照"""
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
