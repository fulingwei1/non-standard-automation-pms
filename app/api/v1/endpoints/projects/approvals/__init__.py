# -*- coding: utf-8 -*-
"""
项目审批管理 API 模块统一导出

模块结构:
 ├── utils.py   # 工具函数
 ├── submit.py  # 提交审批
 ├── action.py  # 执行审批操作
 ├── status.py  # 获取审批状态
 ├── history.py # 获取审批历史
 └── cancel.py  # 取消审批
"""

from fastapi import APIRouter

from . import action, cancel, history, status, submit, utils

# 项目审批的实体类型常量（从utils导入以避免循环导入）
from .utils import ENTITY_TYPE_PROJECT

# 创建主路由
router = APIRouter()

# 聚合所有子路由
router.include_router(submit.router, tags=["项目审批"])
router.include_router(action.router, tags=["项目审批"])
router.include_router(status.router, tags=["项目审批"])
router.include_router(history.router, tags=["项目审批"])
router.include_router(cancel.router, tags=["项目审批"])

__all__ = ["router", "ENTITY_TYPE_PROJECT"]
