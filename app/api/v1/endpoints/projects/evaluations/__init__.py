# -*- coding: utf-8 -*-
"""
项目评价管理模块

路由: /projects/{project_id}/evaluations/
- GET / - 获取项目评价列表
- POST / - 创建项目评价
- GET /latest - 获取项目最新评价
- GET /{eval_id} - 获取评价详情
- PUT /{eval_id} - 更新评价
- POST /{eval_id}/confirm - 确认评价
"""

from fastapi import APIRouter

from .crud import router as crud_router

router = APIRouter()

router.include_router(crud_router)
