# -*- coding: utf-8 -*-
"""
项目状态管理端点

已拆分为模块化架构:
- status/status_crud.py: 状态CRUD操作
- status/health.py: 健康度计算
- status/stages.py: 阶段管理
- status/batch.py: 批量操作

此文件保留向后兼容的路由聚合
"""

from .status import router

__all__ = ["router"]
