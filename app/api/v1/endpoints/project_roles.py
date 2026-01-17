# -*- coding: utf-8 -*-
"""
项目角色类型与负责人管理 API

已拆分为模块化结构，详见 project_roles/ 目录：
- role_types.py: 角色类型字典管理
- role_configs.py: 项目角色配置管理
- leads.py: 项目负责人管理
- team_members.py: 团队成员管理
- overview.py: 项目角色概览
"""

from .project_roles import router

__all__ = ["router"]
