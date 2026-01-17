# -*- coding: utf-8 -*-
"""
客户管理 API endpoints

已拆分为模块化结构，详见 customers/ 目录：
- crud.py: 客户基本CRUD操作
- related.py: 关联数据查询
- view360.py: 客户360视图
"""

from .customers import router

__all__ = ["router"]
