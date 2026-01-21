# -*- coding: utf-8 -*-
"""
组织/PMO 维度 API 模块

提供全局分析视角的数据访问：
- /analytics/projects/health - 项目健康度汇总
- /analytics/projects/progress - 跨项目进度对比
- /analytics/workload/overview - 全局工作量概览
- /analytics/costs/summary - 成本汇总
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/projects/health")
async def get_projects_health():
    """项目健康度汇总 - 待实现"""
    return {"message": "Coming soon"}


@router.get("/workload/overview")
async def get_workload_overview():
    """全局工作量概览 - 待实现"""
    return {"message": "Coming soon"}
