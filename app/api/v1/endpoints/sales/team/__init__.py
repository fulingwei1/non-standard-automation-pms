# -*- coding: utf-8 -*-
"""
销售团队管理路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

from . import crud, members, pk, ranking, statistics, teams_ranking

# 创建主路由
router = APIRouter()

# 聚合所有子模块路由
router.include_router(ranking.router, tags=["sales-team-ranking"])
router.include_router(statistics.router, tags=["sales-team-statistics"])
router.include_router(crud.router, tags=["sales-team-crud"])
router.include_router(members.router, tags=["sales-team-members"])
router.include_router(pk.router, tags=["sales-team-pk"])
router.include_router(teams_ranking.router, tags=["sales-teams-ranking"])
