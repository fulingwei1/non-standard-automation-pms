# -*- coding: utf-8 -*-
"""
人员管理模型
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin


class Worker(Base, TimestampMixin):
    """生产人员"""
    __tablename__ = 'worker'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    worker_no = Column(String(50), unique=True, nullable=False, comment='工号')
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='关联用户ID')
    worker_name = Column(String(50), nullable=False, comment='姓名')
    workshop_id = Column(Integer, ForeignKey('workshop.id'), nullable=True, comment='所属车间ID')
    position = Column(String(50), nullable=True, comment='岗位')
    skill_level = Column(String(20), nullable=True, default='JUNIOR', comment='技能等级')
    phone = Column(String(20), nullable=True, comment='联系电话')
    entry_date = Column(Date, nullable=True, comment='入职日期')
    status = Column(String(20), nullable=False, default='ACTIVE', comment='状态')
    hourly_rate = Column(Numeric(10, 2), nullable=True, comment='时薪(元)')
    remark = Column(Text, nullable=True, comment='备注')
    is_active = Column(Boolean, default=True, nullable=False, comment='是否在职')

    # 关系
    workshop = relationship('Workshop', back_populates='workers')
    skills = relationship('WorkerSkill', back_populates='worker')
    work_orders = relationship('WorkOrder', back_populates='assigned_worker', foreign_keys='WorkOrder.assigned_to')
    work_reports = relationship('WorkReport', back_populates='worker')

    __table_args__ = (
        Index('idx_worker_no', 'worker_no'),
        Index('idx_worker_workshop', 'workshop_id'),
        Index('idx_worker_status', 'status'),
        {'comment': '生产人员表'}
    )


class WorkerSkill(Base, TimestampMixin):
    """工人技能"""
    __tablename__ = 'worker_skill'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    worker_id = Column(Integer, ForeignKey('worker.id'), nullable=False, comment='工人ID')
    process_id = Column(Integer, ForeignKey('process_dict.id'), nullable=False, comment='工序ID')
    skill_level = Column(String(20), nullable=False, default='JUNIOR', comment='技能等级')
    certified_date = Column(Date, nullable=True, comment='认证日期')
    expiry_date = Column(Date, nullable=True, comment='有效期')
    remark = Column(Text, nullable=True, comment='备注')

    # 关系
    worker = relationship('Worker', back_populates='skills')
    process = relationship('ProcessDict', back_populates='worker_skills')

    __table_args__ = (
        Index('idx_worker_skill_worker', 'worker_id'),
        Index('idx_worker_skill_process', 'process_id'),
        {'comment': '工人技能表'}
    )
