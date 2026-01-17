# -*- coding: utf-8 -*-
"""
文档管理 API endpoints

已拆分为模块化结构，详见 documents/ 目录：
- crud.py: 文档列表、详情、创建
- operations.py: 更新、下载、版本管理、删除
"""

from .documents import router

__all__ = ["router"]
