# -*- coding: utf-8 -*-
"""
里程碑管理 API endpoints

已拆分为模块化结构，详见 milestones/ 目录：
- crud.py: 里程碑列表、详情、创建、更新
- workflow.py: 完成里程碑（触发开票）、删除
"""

from .milestones import router

__all__ = ["router"]
