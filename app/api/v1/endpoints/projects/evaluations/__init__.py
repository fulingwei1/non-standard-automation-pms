# -*- coding: utf-8 -*-
"""
项目评价管理模块（重构版本）

路由: /projects/{project_id}/evaluations/
- GET / - 获取项目评价列表（支持分页、搜索、排序、筛选）
- POST / - 创建项目评价（使用服务层）
- GET /latest - 获取项目最新评价（自定义端点）
- GET /{eval_id} - 获取评价详情
- PUT /{eval_id} - 更新评价（使用服务层重新计算得分）
- DELETE /{eval_id} - 删除评价
- POST /{eval_id}/confirm - 确认评价（自定义端点）
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .custom import router as custom_router

router = APIRouter()

# 注意：路由顺序很重要！
# 静态路径（如 /latest）必须在动态路径（如 /{eval_id}）之前注册

# 先注册自定义端点（静态路径）
router.include_router(custom_router)

# 再注册CRUD路由（动态路径）
router.include_router(crud_router)
