# -*- coding: utf-8 -*-
"""
任职资格管理 API endpoints

已拆分为模块化结构，详见 qualification/ 目录：
- levels.py: 任职资格等级管理
- models.py: 岗位能力模型管理
- employees.py: 员工任职资格管理
- assessments.py: 任职资格评估
"""

from .qualification import router

__all__ = ["router"]
