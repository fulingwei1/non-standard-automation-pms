# -*- coding: utf-8 -*-
"""
项目扩展端点 - 兼容层

本文件现为兼容层，所有实现已迁移至以下模块：
- dashboard.py: 概览和仪表盘端点
- sync.py: 数据同步和ERP集成端点
- reviews.py: 项目复盘管理端点
- lessons.py: 经验教训管理端点
- best_practices.py: 最佳实践管理端点
- analysis.py: 高级分析端点（资源优化、关联分析、风险矩阵、变更影响）
- costs.py: 项目成本和概览端点

新代码请直接使用新模块。
"""

from fastapi import APIRouter

# 创建空路由（保持向后兼容）
router = APIRouter()

# 注意：所有路由已迁移到新模块，由 __init__.py 统一聚合
# 此文件仅保留以防有外部代码直接引用 extended.router
