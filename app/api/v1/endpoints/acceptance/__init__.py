# -*- coding: utf-8 -*-
"""
验收管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中

模块结构:
├── utils.py      # 工具函数（验证规则、编号生成）
├── templates.py  # 验收模板CRUD
├── orders.py     # 验收单CRUD、检查项、流程控制
├── issues.py     # 验收问题管理
└── reports.py    # 签字、报告、客户文件上传、奖金计算
"""

from fastapi import APIRouter

from . import issues, orders, reports, templates

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
# 注意：路由的顺序很重要，更具体的路由应该放在前面

# 模板路由
router.include_router(templates.router, tags=["acceptance-templates"])

# 验收单路由
router.include_router(orders.router, tags=["acceptance-orders"])

# 问题路由
router.include_router(issues.router, tags=["acceptance-issues"])

# 报告和签字路由
router.include_router(reports.router, tags=["acceptance-reports"])

# 导出工具函数供外部使用
from .utils import (
    generate_issue_no,
    generate_order_no,
    validate_acceptance_rules,
    validate_completion_rules,
    validate_edit_rules,
)

__all__ = [
    "router",
    "validate_acceptance_rules",
    "validate_completion_rules",
    "validate_edit_rules",
    "generate_order_no",
    "generate_issue_no"
]
