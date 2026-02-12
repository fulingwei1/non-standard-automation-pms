# -*- coding: utf-8 -*-
"""
时薪配置管理模块模型
支持按用户、角色、部门配置时薪
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

from .base import Base, TimestampMixin


class HourlyRateConfig(Base, TimestampMixin):
    """时薪配置表"""
    __tablename__ = 'hourly_rate_configs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')

    # 配置类型
    config_type = Column(String(20), nullable=False, comment='配置类型：USER/ROLE/DEPT/DEFAULT（用户/角色/部门/默认）')

    # 关联对象
    user_id = Column(Integer, ForeignKey('users.id'), comment='用户ID（config_type=USER时使用）')
    role_id = Column(Integer, ForeignKey('roles.id'), comment='角色ID（config_type=ROLE时使用）')
    dept_id = Column(Integer, ForeignKey('departments.id'), comment='部门ID（config_type=DEPT时使用）')

    # 时薪配置
    hourly_rate = Column(Numeric(10, 2), nullable=False, comment='时薪（元/小时）')

    # 生效时间
    effective_date = Column(Date, comment='生效日期')
    expiry_date = Column(Date, comment='失效日期')

    # 状态
    is_active = Column(Boolean, default=True, comment='是否启用')

    # 备注
    remark = Column(Text, comment='备注')
    created_by = Column(Integer, ForeignKey('users.id'), comment='创建人ID')

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    role = relationship('Role', foreign_keys=[role_id])
    dept = relationship('Department', foreign_keys=[dept_id])
    creator = relationship('User', foreign_keys=[created_by])

    __table_args__ = (
        Index('idx_hourly_rate_type', 'config_type'),
        Index('idx_hourly_rate_user', 'user_id'),
        Index('idx_hourly_rate_role', 'role_id'),
        Index('idx_hourly_rate_dept', 'dept_id'),
        Index('idx_hourly_rate_active', 'is_active'),
        {'comment': '时薪配置表'}
    )

    def __repr__(self):
        return f'<HourlyRateConfig {self.config_type}-{self.hourly_rate}>'






