# -*- coding: utf-8 -*-
"""
采购管理 API endpoints

已拆分为模块化结构，详见 purchase/ 目录：
- utils.py: 辅助函数（编号生成、序列化）
- orders.py: 采购订单CRUD
- requests.py: 采购申请CRUD
- receipts.py: 收货单CRUD
"""

from .purchase import router

__all__ = ["router"]
