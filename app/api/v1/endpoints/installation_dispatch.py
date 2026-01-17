# -*- coding: utf-8 -*-
"""
安装调试派工 API endpoints

已拆分为模块化结构，详见 installation_dispatch/ 目录：
- utils.py: 辅助函数（generate_order_no）
- statistics.py: 派工统计
- orders.py: 派工单 CRUD
- workflow.py: 状态流转（派工、开始、进度、完成、取消）
"""

from .installation_dispatch import router

__all__ = ["router"]
