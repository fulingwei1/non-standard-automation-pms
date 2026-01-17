# -*- coding: utf-8 -*-
"""
优势产品管理 API 端点

已拆分为模块化结构，详见 advantage_products/ 目录：
- categories.py: 产品类别CRUD
- products.py: 优势产品CRUD
- import_excel.py: Excel批量导入
- match.py: 产品匹配检查
"""

from .advantage_products import router

__all__ = ["router"]
