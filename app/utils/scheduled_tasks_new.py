# -*- coding: utf-8 -*-
"""
定时任务调度中心 - 重构版本
统一管理和调度所有业务域的定时任务
"""
import logging

# 导入调度中心
from .scheduled_tasks import (
    SCHEDULED_TASKS,
    TASK_GROUPS,
    execute_task,
    get_task,
    get_tasks_by_group,
    list_all_tasks,
)

# 模块级 logger
logger = logging.getLogger(__name__)

# 为了向后兼容，导出所有任务函数
__all__ = list(SCHEDULED_TASKS.keys()) + [
    'SCHEDULED_TASKS',
    'TASK_GROUPS',
    'get_task',
    'get_tasks_by_group',
    'list_all_tasks',
    'execute_task',
]

# 向后兼容：将所有任务函数直接导出到模块级别
for task_name, task_func in SCHEDULED_TASKS.items():
    locals()[task_name] = task_func
