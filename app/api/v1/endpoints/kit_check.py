# -*- coding: utf-8 -*-
"""
齐套检查 API endpoints

已拆分为模块化结构，详见 kit_check/ 目录：
- utils.py: 编号生成和齐套率计算
- work_orders.py: 工单列表和齐套详情
- check.py: 执行检查和开工确认
- history.py: 检查历史查询
"""

from .kit_check import router

__all__ = ["router"]
