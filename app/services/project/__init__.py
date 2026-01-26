# -*- coding: utf-8 -*-
"""
项目管理聚合服务

整合原有分散的服务为 5 个核心服务：
- core_service: 项目核心 CRUD + 状态管理
- execution_service: 阶段 + 进度 + 里程碑
- resource_service: 成员 + 工时 + 工作量
- finance_service: 成本 + 预算 + 付款
- analytics_service: 仪表盘 + 统计 + 报表
"""

# 服务将在后续任务中逐步实现

from .milestone_service import ProjectMilestoneService
from .machine_service import ProjectMachineService

__all__ = [
    "ProjectMilestoneService",
    "ProjectMachineService",
]
