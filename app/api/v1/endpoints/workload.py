# -*- coding: utf-8 -*-
"""
资源排程与负荷管理 API endpoints

已拆分为模块化架构:
- workload/utils.py: 辅助工具函数
- workload/user_workload.py: 用户负荷查询
- workload/team_workload.py: 团队负荷概览和看板
- workload/visualization.py: 热力图、甘特图、可用资源
- workload/skills.py: 技能管理和匹配

此文件保留向后兼容的路由聚合
"""

from .workload import router

__all__ = ["router"]
