# -*- coding: utf-8 -*-
"""
项目里程碑管理模块

路由: /projects/{project_id}/milestones/
- GET / - 获取项目里程碑列表
- POST / - 创建里程碑
- GET /{milestone_id} - 获取里程碑详情
- PUT /{milestone_id} - 更新里程碑
- POST /{milestone_id}/complete - 完成里程碑
- DELETE /{milestone_id} - 删除里程碑
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .workflow import router as workflow_router

router = APIRouter()

router.include_router(crud_router, tags=["项目里程碑"])
router.include_router(workflow_router, tags=["里程碑工作流"])
