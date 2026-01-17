# -*- coding: utf-8 -*-
"""
项目预算管理 API endpoints

已拆分为模块化结构，详见 budget/ 目录：
- utils.py: 预算编号和版本号生成
- allocation_rules.py: 成本分摊规则CRUD
- budgets.py: 项目预算CRUD、提交、审批
- items.py: 预算明细CRUD
"""

from .budget import router

__all__ = ["router"]
