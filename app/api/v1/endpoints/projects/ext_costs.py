# -*- coding: utf-8 -*-
"""
项目成本管理
包含：成本记录CRUD、成本统计、成本分析
注意：成本管理端点已迁移至 app/api/v1/endpoints/costs/basic.py 以消除重复。
"""

from fastapi import APIRouter

router = APIRouter()
