# -*- coding: utf-8 -*-
"""
ECN模型 - 日志
"""
from sqlalchemy import Column, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class EcnLog(Base, TimestampMixin):
    """ECN流转日志表"""
    __tablename__ = 'ecn_logs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    log_type = Column(String(20), nullable=False, comment='日志类型')
    log_action = Column(String(50), nullable=False, comment='操作动作')

    # 状态变更
    old_status = Column(String(20), comment='原状态')
    new_status = Column(String(20), comment='新状态')

    # 内容
    log_content = Column(Text, comment='日志内容')
    attachments = Column(JSON, comment='附件')

    created_by = Column(Integer, ForeignKey('users.id'), comment='操作人')

    # 关系
    ecn = relationship('Ecn', back_populates='logs')

    __table_args__ = (
        Index('idx_log_ecn', 'ecn_id'),
        Index('idx_log_time', 'created_at'),
    )
