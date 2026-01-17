# -*- coding: utf-8 -*-
"""
方案生成积分管理API

已拆分为模块化结构，详见 solution_credits/ 目录：
- schemas.py: Schema定义
- user.py: 用户端API
- admin.py: 管理员API
- internal.py: 内部调用API
"""

from .solution_credits import router

__all__ = ["router"]
