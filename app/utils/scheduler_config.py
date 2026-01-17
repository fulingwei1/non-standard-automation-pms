# -*- coding: utf-8 -*-
"""
Scheduler metadata describing all background jobs - 兼容层

此文件保持向后兼容性，从拆分后的模块导入所有任务配置。
原有功能已拆分为 utils/scheduler_config/ 目录下的模块。

字段说明：
- dependencies_tables: 任务依赖的数据库表列表，用于评估表结构变更影响
- risk_level: 风险级别 (LOW/MEDIUM/HIGH/CRITICAL)，用于评估任务失败影响
- sla: 服务级别协议，包含 max_execution_time_seconds（最大执行时间，秒）和 retry_on_failure（失败是否重试）
"""

# 从调度器配置模块导入所有任务
from app.utils.scheduler_config import SCHEDULER_TASKS

__all__ = ["SCHEDULER_TASKS"]
