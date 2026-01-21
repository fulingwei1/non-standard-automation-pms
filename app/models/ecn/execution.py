# -*- coding: utf-8 -*-
"""
ECN模型 - 执行相关
"""
from sqlalchemy import (
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from ..base import Base, TimestampMixin


class EcnTask(Base, TimestampMixin):
    """ECN执行任务表"""
    __tablename__ = 'ecn_tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    ecn_id = Column(Integer, ForeignKey('ecn.id'), nullable=False, comment='ECN ID')
    task_no = Column(Integer, nullable=False, comment='任务序号')
    task_name = Column(String(200), nullable=False, comment='任务名称')
    task_type = Column(String(50), comment='任务类型')
    task_dept = Column(String(50), comment='责任部门')

    # 任务内容
    task_description = Column(Text, comment='任务描述')
    deliverables = Column(Text, comment='交付物要求')

    # 负责人
    assignee_id = Column(Integer, ForeignKey('users.id'), comment='负责人')
    assignee_name = Column(String(50), comment='负责人姓名')

    # 时间
    planned_start = Column(Date, comment='计划开始')
    planned_end = Column(Date, comment='计划结束')
    actual_start = Column(Date, comment='实际开始')
    actual_end = Column(Date, comment='实际结束')

    # 进度
    progress_pct = Column(Integer, default=0, comment='进度百分比')

    # 状态
    status = Column(String(20), default='PENDING', comment='状态')

    # 完成信息
    completion_note = Column(Text, comment='完成说明')
    attachments = Column(JSON, comment='附件')

    # 关系
    ecn = relationship('Ecn', back_populates='tasks')
    assignee = relationship('User')

    __table_args__ = (
        Index('idx_task_ecn', 'ecn_id'),
        Index('idx_ecn_task_assignee', 'assignee_id'),
        Index('idx_ecn_task_status', 'status'),
    )
