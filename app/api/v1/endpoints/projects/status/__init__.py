# -*- coding: utf-8 -*-
"""
项目状态管理模块

拆分自原 status.py (904行)，按功能域分为：
- status_crud: 状态 CRUD 操作 (阶段/状态/健康度更新)
- health: 健康度计算与批量计算
- stages: 阶段管理 (初始化/推进/阶段门校验)
- batch: 批量操作 (批量更新状态/阶段/分配PM)
"""

from fastapi import APIRouter

from .batch import router as batch_router
from .health import router as health_router
from .stages import router as stages_router
from .status_crud import router as status_crud_router

router = APIRouter()

# 状态 CRUD 操作
router.include_router(status_crud_router, tags=["项目状态"])

# 健康度相关
router.include_router(health_router, tags=["项目健康度"])

# 阶段管理
router.include_router(stages_router, tags=["项目阶段"])

# 批量操作
router.include_router(batch_router, tags=["项目批量操作"])
