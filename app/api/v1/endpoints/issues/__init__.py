# -*- coding: utf-8 -*-
"""
问题管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中

模块结构:
├── utils.py          # 工具函数（预警创建/关闭、编号生成）
├── core.py           # 基础CRUD、状态管理、分配、解决、验证、跟进
├── statistics.py     # 统计概览、工程师设计问题分析、原因分析、快照
├── operations.py     # 关闭、取消、关联问题、删除
├── batch.py          # 批量分配、批量状态变更、批量关闭
├── import_export.py  # 导出Excel、从Excel导入
├── analytics.py      # 看板数据、趋势分析
├── related_lists.py  # 项目/机台/任务/验收问题列表
└── templates.py      # 问题模板CRUD、从模板创建问题
"""

from fastapi import APIRouter
from . import (
    core,
    statistics,
    operations,
    batch,
    import_export,
    analytics,
    related_lists,
    templates,
)

# 创建主路由
router = APIRouter()

# 创建模板专用路由
template_router = APIRouter()

# 聚合所有子路由
# 注意：路由的顺序很重要，更具体的路由应该放在前面

# 统计路由（/statistics/* 需要在 /{issue_id} 之前）
router.include_router(statistics.router, tags=["issue-statistics"])

# 分析路由（/board, /statistics/trend）
router.include_router(analytics.router, tags=["issue-analytics"])

# 批量操作路由（/batch-*）
router.include_router(batch.router, tags=["issue-batch"])

# 导入导出路由（/export, /import）
router.include_router(import_export.router, tags=["issue-import-export"])

# 关联列表路由（/projects/*, /machines/*, /tasks/*, /acceptance-orders/*）
router.include_router(related_lists.router, tags=["issue-related"])

# 核心路由（/, /{issue_id}, /{issue_id}/assign 等）
router.include_router(core.router, tags=["issue-core"])

# 操作路由（/{issue_id}/close, /{issue_id}/cancel 等）
router.include_router(operations.router, tags=["issue-operations"])

# 模板路由
template_router.include_router(templates.router, tags=["issue-templates"])

# 导出工具函数供外部使用
from .utils import (
    create_blocking_issue_alert,
    close_blocking_issue_alerts,
    generate_issue_no
)

__all__ = [
    "router",
    "template_router",
    "create_blocking_issue_alert",
    "close_blocking_issue_alerts",
    "generate_issue_no"
]
