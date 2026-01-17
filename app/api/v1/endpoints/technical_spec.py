# -*- coding: utf-8 -*-
"""
技术规格管理 API endpoints

已拆分为模块化结构，详见 technical_spec/ 目录：
- requirements.py: 技术规格要求CRUD
- match.py: 规格匹配检查
- extract.py: 规格提取
"""

from .technical_spec import router

__all__ = ["router"]
