# -*- coding: utf-8 -*-
"""
批量操作 - 路由聚合

已拆分为模块化结构：
- batch_helpers.py: 辅助函数（编号生成、操作日志）
- batch_status.py: 状态相关操作（complete, start, pause, delete）
- batch_attributes.py: 属性相关操作（transfer, priority, progress, tag, urge）
- batch_statistics.py: 统计功能
"""

from fastapi import APIRouter

from . import batch_attributes, batch_statistics, batch_status

router = APIRouter()

# 聚合所有子路由
router.include_router(batch_status.router)
router.include_router(batch_attributes.router)
router.include_router(batch_statistics.router)
