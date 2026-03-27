# -*- coding: utf-8 -*-
"""
知识自动沉淀模块路由聚合

模块结构:
 ├── extraction.py    # 经验教训自动提取
 ├── induction.py     # 最佳实践归纳
 ├── alerts.py        # 坑点预警
 └── search.py        # 知识检索
"""

from fastapi import APIRouter

from . import alerts, extraction, induction, search

router = APIRouter()

# 知识提取（项目结项时调用）
router.include_router(extraction.router, tags=["knowledge-extraction"])

# 最佳实践归纳
router.include_router(induction.router, tags=["knowledge-induction"])

# 坑点预警
router.include_router(alerts.router, tags=["knowledge-alerts"])

# 知识检索与管理
router.include_router(search.router, tags=["knowledge-search"])
