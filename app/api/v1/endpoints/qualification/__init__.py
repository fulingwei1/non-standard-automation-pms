# -*- coding: utf-8 -*-
"""
任职资格管理模块

拆分自原 qualification.py (502行)，按功能域分为：
- levels: 任职资格等级管理
- models: 岗位能力模型管理
- employees: 员工任职资格管理
- assessments: 任职资格评估
"""

from fastapi import APIRouter

from .assessments import router as assessments_router
from .employees import router as employees_router
from .levels import router as levels_router
from .models import router as models_router

router = APIRouter()

# 任职资格等级管理
router.include_router(levels_router, tags=["资格等级"])

# 岗位能力模型管理
router.include_router(models_router, tags=["能力模型"])

# 员工任职资格管理
router.include_router(employees_router, tags=["员工资格"])

# 任职资格评估
router.include_router(assessments_router, tags=["资格评估"])
