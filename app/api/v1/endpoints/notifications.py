# -*- coding: utf-8 -*-
"""
通知中心 API endpoints

已拆分为模块化结构，详见 notifications/ 目录：
- crud.py: 通知列表、已读标记、删除操作
- settings.py: 通知设置（用户偏好）
"""

from .notifications import router

__all__ = ["router"]
