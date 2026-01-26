# -*- coding: utf-8 -*-
"""
项目审批管理 API 模块统一导出

使用统一审批引擎的新端点：
  ├── submit_new.py  # 提交审批
  ├── action_new.py  # 审批/驳回
  ├── cancel_new.py  # 撤回审批
  ├── status_new.py  # 查询审批状态
  └── history_new.py # 查询审批历史

旧文件（已弃用，待删除）：
  ├── submit.py, action.py, cancel.py, status.py, history.py, utils.py
"""

from fastapi import APIRouter

from . import submit_new, action_new, cancel_new, status_new, history_new
from .submit_new import ENTITY_TYPE_PROJECT

router = APIRouter()

router.include_router(submit_new.router, tags=["项目审批"])
router.include_router(action_new.router, tags=["项目审批"])
router.include_router(cancel_new.router, tags=["项目审批"])
router.include_router(status_new.router, tags=["项目审批"])
router.include_router(history_new.router, tags=["项目审批"])

# 旧端点（已注释，待完全删除）
# from . import submit, action, cancel, status, history, utils
# from .utils import ENTITY_TYPE_PROJECT
# router.include_router(submit.router, tags=["项目审批"])
# router.include_router(action.router, tags=["项目审批"])
# router.include_router(status.router, tags=["项目审批"])
# router.include_router(history.router, tags=["项目审批"])
# router.include_router(cancel.router, tags=["项目审批"])

__all__ = ["router", "ENTITY_TYPE_PROJECT"]
