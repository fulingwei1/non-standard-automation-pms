# -*- coding: utf-8 -*-
"""
用户管理 API endpoints

已拆分为模块化结构，详见 users/ 目录：
- models.py: 请求/响应模型
- utils.py: 辅助工具函数
- crud.py: 用户 CRUD 操作
- sync.py: 用户同步（员工同步、账号创建、状态管理）
- time_allocation.py: 工时分配统计
"""

from .users import router

__all__ = ["router"]
