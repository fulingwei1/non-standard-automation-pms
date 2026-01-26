# -*- coding: utf-8 -*-
"""
组织/PMO 维度 API 模块

提供全局分析视角的数据访问：
- /analytics/projects/health - 项目健康度汇总
- /analytics/projects/progress - 跨项目进度对比
- /analytics/workload/overview - 全局工作量概览
- /analytics/costs/summary - 成本汇总
- /analytics/resource-conflicts - 资源冲突分析
"""

from fastapi import APIRouter

from .resource_conflicts import router as resource_conflicts_router
from .skill_matrix import router as skill_matrix_router
from .workload import router as workload_router

router = APIRouter()

# 资源冲突分析路由
router.include_router(resource_conflicts_router, tags=["analytics-resource-conflicts"])

# 工作负载分析路由
router.include_router(workload_router, tags=["analytics-workload"])

# 技能矩阵分析路由
router.include_router(skill_matrix_router, tags=["analytics-skill-matrix"])


@router.get("/projects/health")
async def get_projects_health():
    """项目健康度汇总 - 待实现"""
    return {"message": "Coming soon"}


@router.get("/workload/overview")
async def get_workload_overview():
    """全局工作量概览 - 待实现"""
    return {"message": "Coming soon"}
