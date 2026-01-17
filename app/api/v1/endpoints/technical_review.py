# -*- coding: utf-8 -*-
"""
技术评审管理 API endpoints

已拆分为模块化架构:
- technical_review/utils.py: 辅助工具函数
- technical_review/reviews.py: 评审主表CRUD
- technical_review/participants.py: 参与人管理
- technical_review/materials.py: 材料管理
- technical_review/checklists.py: 检查项记录
- technical_review/issues.py: 问题管理

此文件保留向后兼容的路由聚合
"""

from .technical_review import router

__all__ = ["router"]
