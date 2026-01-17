# -*- coding: utf-8 -*-
"""
机台管理 API endpoints

已拆分为模块化结构，详见 machines/ 目录：
- crud.py: 机台CRUD、BOM查询
- service_history.py: 服务历史记录
- documents.py: 文档上传、下载、版本管理
"""

from .machines import router

__all__ = ["router"]
