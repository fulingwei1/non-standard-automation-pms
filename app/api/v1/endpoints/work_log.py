# -*- coding: utf-8 -*-
"""
工作日志 API endpoints

已拆分为模块化结构，详见 work_log/ 目录：
- crud.py: 工作日志创建、列表、提及选项
- config.py: 工作日志配置管理
- ai.py: AI智能分析和项目推荐
- detail.py: 工作日志详情、更新、删除

IMPORTANT: 路由顺序很重要！详见 work_log/__init__.py
"""

from .work_log import router

__all__ = ["router"]
