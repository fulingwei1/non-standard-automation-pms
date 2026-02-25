# -*- coding: utf-8 -*-
"""
绩效模型 - 申诉和调整
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class PerformanceAppeal(Base, TimestampMixin):
    """绩效申诉
    
    【状态】未启用 - 绩效申诉"""
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


class PerformanceAdjustmentHistory(Base, TimestampMixin):
    """绩效调整历史记录表"""
    __tablename__ = 'performance_adjustment_history'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    result_id = Column(Integer, ForeignKey('performance_result.id'), nullable=False, comment='绩效结果ID')

    # 调整前数据
    original_total_score = Column(Numeric(5, 2), comment='原始综合得分')
    original_dept_rank = Column(Integer, comment='原始部门排名')
    original_company_rank = Column(Integer, comment='原始公司排名')
    original_level = Column(String(20), comment='原始等级')

    # 调整后数据
    adjusted_total_score = Column(Numeric(5, 2), comment='调整后综合得分')
    adjusted_dept_rank = Column(Integer, comment='调整后部门排名')
    adjusted_company_rank = Column(Integer, comment='调整后公司排名')
    adjusted_level = Column(String(20), comment='调整后等级')

    # 调整信息
    adjustment_reason = Column(Text, nullable=False, comment='调整理由（必填）')
    adjusted_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='调整人ID')
    adjusted_by_name = Column(String(50), comment='调整人姓名')
    adjusted_at = Column(DateTime, default=datetime.now, comment='调整时间')

    # 关系
    result = relationship('PerformanceResult', back_populates='adjustment_history')
    adjuster = relationship('User', foreign_keys=[adjusted_by])

    __table_args__ = (
        Index('idx_adj_history_result', 'result_id'),
        Index('idx_adj_history_adjuster', 'adjusted_by'),
        Index('idx_adj_history_time', 'adjusted_at'),
        {'comment': '绩效调整历史记录表'}
    )
