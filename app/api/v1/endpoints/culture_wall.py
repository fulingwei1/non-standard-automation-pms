# -*- coding: utf-8 -*-
"""
文化墙 API endpoints

已拆分为模块化结构，详见 culture_wall/ 目录：
- summary.py: 文化墙汇总（用于滚动播放）
- contents.py: 文化墙内容管理
- goals.py: 个人目标管理
"""

from .culture_wall import router

__all__ = ["router"]
