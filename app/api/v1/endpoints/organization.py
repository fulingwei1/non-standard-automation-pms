# -*- coding: utf-8 -*-
"""
组织管理 API endpoints

已拆分为模块化结构，详见 organization/ 目录：
- utils.py: 辅助工具函数
- departments.py: 部门管理
- employees.py: 员工管理
- employee_import.py: 员工批量导入
- hr_profiles.py: 人事档案管理
"""

from .organization import router

__all__ = ["router"]
