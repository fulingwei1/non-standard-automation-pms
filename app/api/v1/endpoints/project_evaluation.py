# -*- coding: utf-8 -*-
"""
项目评价模块 API endpoints

已拆分为模块化结构，详见 project_evaluation/ 目录：
- statistics.py: 评价统计
- evaluations.py: 项目评价 CRUD
- dimensions.py: 评价维度配置

IMPORTANT: 路由顺序很重要！详见 project_evaluation/__init__.py
"""

from .project_evaluation import router

__all__ = ["router"]
