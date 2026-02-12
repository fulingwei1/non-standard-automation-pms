# -*- coding: utf-8 -*-
"""
绩效模型 - 周期和指标
"""
from sqlalchemy import Boolean, Column, Date, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


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
