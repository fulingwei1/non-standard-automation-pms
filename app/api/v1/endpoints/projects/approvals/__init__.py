# -*- coding: utf-8 -*-
"""
项目审批管理 API 模块统一导出

[DEPRECATED] 此模块已废弃，请使用统一审批 API: /api/v1/approvals/
- 提交审批: POST /api/v1/approvals/instances/submit
- 审批/驳回: POST /api/v1/approvals/tasks/{task_id}/approve 或 /reject
- 撤回审批: POST /api/v1/approvals/instances/{instance_id}/withdraw
- 查询状态: GET /api/v1/approvals/instances/{instance_id}
- 查询历史: GET /api/v1/approvals/instances/{instance_id} (含 logs)

此模块将在未来版本中移除，请尽快迁移。

原有端点（已废弃）：
  ├── submit_new.py  # 提交审批
  ├── action_new.py  # 审批/驳回
  ├── cancel_new.py  # 撤回审批
  ├── status_new.py  # 查询审批状态
  └── history_new.py # 查询审批历史
"""

import warnings
from fastapi import APIRouter

from . import submit_new, action_new, cancel_new, status_new, history_new
from .submit_new import ENTITY_TYPE_PROJECT

# 发出废弃警告（模块级）
warnings.warn(
    "projects.approvals 模块已废弃，请使用 /api/v1/approvals/ 统一审批 API",
    DeprecationWarning,
    stacklevel=2,
)

router = APIRouter(
    deprecated=True,  # OpenAPI 文档中标记为废弃
)

router.include_router(submit_new.router, tags=["项目审批-已废弃"])
router.include_router(action_new.router, tags=["项目审批-已废弃"])
router.include_router(cancel_new.router, tags=["项目审批-已废弃"])
router.include_router(status_new.router, tags=["项目审批-已废弃"])
router.include_router(history_new.router, tags=["项目审批-已废弃"])

__all__ = ["router", "ENTITY_TYPE_PROJECT"]
