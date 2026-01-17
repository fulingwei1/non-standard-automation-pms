# -*- coding: utf-8 -*-
"""
项目成员 API endpoints

已拆分为模块化结构，详见 members/ 目录：
- crud.py: 成员 CRUD 操作
- conflicts.py: 冲突检查
- batch.py: 批量操作
- extended.py: 扩展操作（通知、部门用户列表）
"""

from .members import router

__all__ = ["router"]
