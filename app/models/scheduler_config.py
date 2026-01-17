# -*- coding: utf-8 -*-
"""
定时服务配置管理模型
允许管理员通过界面配置定时服务的执行频率和启用状态
"""

import json

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    TypeDecorator,
)
from sqlalchemy.dialects.mysql import JSON as MySQLJSON
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


# JSON类型装饰器，兼容SQLite和MySQL
class JSONType(TypeDecorator):
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'mysql':
            return dialect.type_descriptor(MySQLJSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value, ensure_ascii=False)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    # 如果 JSON 解析失败，返回空字典或空列表
                    return {} if self.impl == Text else []
            return value
        # 返回 None 或默认值
        return None


class SchedulerTaskConfig(Base, TimestampMixin):
    """定时任务配置表"""
    __tablename__ = 'scheduler_task_configs'

    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    task_id = Column(String(100), unique=True, nullable=False, comment='任务ID（对应scheduler_config.py中的id）')

    # 任务基本信息（从scheduler_config.py同步，用于显示）
    task_name = Column(String(200), nullable=False, comment='任务名称')
    module = Column(String(200), nullable=False, comment='模块路径')
    callable_name = Column(String(100), nullable=False, comment='函数名')
    owner = Column(String(100), comment='负责人')
    category = Column(String(100), comment='分类')
    description = Column(Text, comment='描述')

    # 配置信息（可修改）
    is_enabled = Column(Boolean, default=True, nullable=False, comment='是否启用')
    cron_config = Column(JSONType, nullable=False, comment='Cron配置（JSON格式：{"hour": 7, "minute": 0}）')

    # 元数据（从scheduler_config.py同步，只读）
    dependencies_tables = Column(JSONType, comment='依赖的数据库表列表')
    risk_level = Column(String(20), comment='风险级别：LOW/MEDIUM/HIGH/CRITICAL')
    sla_config = Column(JSONType, comment='SLA配置（最大执行时间、重试策略等）')

    # 操作信息
    updated_by = Column(Integer, ForeignKey('users.id'), comment='最后更新人ID')

    # 关系
    updater = relationship('User', foreign_keys=[updated_by])

    __table_args__ = (
        Index('idx_scheduler_task_id', 'task_id'),
        Index('idx_scheduler_enabled', 'is_enabled'),
        Index('idx_scheduler_category', 'category'),
        {'comment': '定时任务配置表'},
    )

    def __repr__(self):
        return f'<SchedulerTaskConfig {self.task_id}: {self.task_name}>'
