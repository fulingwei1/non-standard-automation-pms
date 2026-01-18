# -*- coding: utf-8 -*-
"""
奖金分配明细表 - 路由聚合

已拆分为模块化结构：
- allocation_helpers.py: 辅助函数（编号生成）
- allocation_sheets.py: 分配表管理（template, upload, list, get, confirm, distribute, download, rows）
"""

from fastapi import APIRouter

from . import allocation_sheets

router = APIRouter()

# 聚合所有子路由
router.include_router(allocation_sheets.router)
