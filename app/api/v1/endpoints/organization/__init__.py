# -*- coding: utf-8 -*-
"""
组织管理模块

拆分自原 organization.py (801行)，按功能域分为：
- utils: 辅助工具函数
- departments: 部门管理
- employees: 员工管理
- employee_import: 员工批量导入
- hr_profiles: 人事档案管理
"""

from fastapi import APIRouter

from .departments import router as departments_router
from .departments_refactored import router as departments_refactored_router
from .employee_import import router as import_router
from .employees import router as employees_router
from .hr_profiles import router as hr_router
from .units import router as units_router
from .positions import router as positions_router
from .job_levels import router as job_levels_router
from .assignments import router as assignments_router

router = APIRouter()

# 部门管理（使用重构版本，统一响应格式）
router.include_router(departments_refactored_router, tags=["部门管理"])
# 原版本保留作为参考
# router.include_router(departments_router, tags=["部门管理"])

# 员工管理
router.include_router(employees_router, tags=["员工管理"])

# 员工导入
router.include_router(import_router, tags=["员工导入"])

# 人事档案
router.include_router(hr_router, tags=["人事档案"])

# 组织单元管理 (新)
router.include_router(units_router, prefix="/units", tags=["组织单元"])

# 岗位管理 (新)
router.include_router(positions_router, prefix="/positions", tags=["岗位管理"])

# 职级管理 (新)
router.include_router(job_levels_router, prefix="/job-levels", tags=["职级管理"])

# 员工分配 (新)
router.include_router(assignments_router, prefix="/assignments", tags=["员工分配"])
