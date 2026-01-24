# -*- coding: utf-8 -*-
"""
项目成本管理模块（重构版本）

路由: /projects/{project_id}/costs/
- GET / - 获取项目成本列表（支持分页、搜索、排序、筛选）
- POST / - 添加成本记录
- GET /{cost_id} - 获取成本详情
- PUT /{cost_id} - 更新成本
- DELETE /{cost_id} - 删除成本（由CRUD基类提供）
- GET /summary - 成本汇总（自定义端点）
"""

from fastapi import APIRouter

from .crud import router as crud_router
from .summary import router as summary_router

router = APIRouter()

# 注意：路由顺序很重要！
# 静态路径（如 /summary）必须在动态路径（如 /{cost_id}）之前注册
# 否则 /summary 会被 /{cost_id} 匹配，导致 "summary" 被解析为整数失败

# 先注册自定义端点（成本汇总）- 静态路径
router.include_router(summary_router)

# 再注册CRUD路由（由基类提供）- 动态路径
router.include_router(crud_router)
