# -*- coding: utf-8 -*-
"""
Scheduler metadata describing all background jobs.

This module aggregates all scheduled tasks from various categories.

字段说明：
- dependencies_tables: 任务依赖的数据库表列表，用于评估表结构变更影响
- risk_level: 风险级别 (LOW/MEDIUM/HIGH/CRITICAL)，用于评估任务失败影响
- sla: 服务级别协议，包含 max_execution_time_seconds（最大执行时间，秒）和 retry_on_failure（失败是否重试）
"""

from .alerting import ALERTING_TASKS
from .finance import FINANCE_TASKS
from .issue_management import ISSUE_MANAGEMENT_TASKS
from .milestone import MILESTONE_TASKS
from .other import OTHER_TASKS
from .production import PRODUCTION_TASKS
from .project_health import PROJECT_HEALTH_TASKS
from .risk import RISK_TASKS
from .schedule import SCHEDULE_TASKS
from .shortage import SHORTAGE_TASKS
from .timesheet import TIMESHEET_TASKS

# 合并所有任务
SCHEDULER_TASKS = (
    PROJECT_HEALTH_TASKS +
    RISK_TASKS +
    ISSUE_MANAGEMENT_TASKS +
    MILESTONE_TASKS +
    SHORTAGE_TASKS +
    PRODUCTION_TASKS +
    FINANCE_TASKS +
    SCHEDULE_TASKS +
    ALERTING_TASKS +
    TIMESHEET_TASKS +
    OTHER_TASKS
)

__all__ = ["SCHEDULER_TASKS"]
