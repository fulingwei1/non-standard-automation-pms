# -*- coding: utf-8 -*-
"""
成本管理 API endpoints - 路由聚合

已拆分为模块化结构：
- cost_templates.py: 报价成本模板管理（CRUD）
- purchase_material_costs.py: 采购物料成本清单管理（CRUD）
- cost_matching.py: 物料成本匹配
- cost_reminder.py: 物料成本更新提醒
"""

from fastapi import APIRouter

from . import cost_matching, cost_reminder, cost_templates, purchase_material_costs

router = APIRouter()

# 聚合所有子路由
router.include_router(cost_templates.router)
router.include_router(purchase_material_costs.router)
router.include_router(cost_matching.router)
router.include_router(cost_reminder.router)
