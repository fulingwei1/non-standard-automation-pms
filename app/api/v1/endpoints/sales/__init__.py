# -*- coding: utf-8 -*-
"""
销售管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

# 只导入可工作的模块
from . import (
    assessments,
    contracts,
    expenses,
    leads,
    loss_analysis,
    opportunities,
    payments,
    priority,
    quotes,
    statistics,
)

# from . import invoices  # 新增：发票管理模块 - 暂时禁用，存在导入问题
# from . import templates  # 模板管理模块 - 已拆分为templates包 - 暂时禁用，存在导入问题

# 创建主路由
router = APIRouter()

# 注意：优先级路由需要在leads之前注册，避免路径冲突
# /sales/leads/priority-ranking 需要在 /sales/leads/{lead_id} 之前匹配
router.include_router(priority.router, tags=["sales-priority"])
router.include_router(leads.router, tags=["sales-leads"])
router.include_router(opportunities.router, tags=["sales-opportunities"])
router.include_router(quotes.router, tags=["sales-quotes"])
router.include_router(contracts.router, tags=["sales-contracts"])
# router.include_router(invoices.router, tags=["sales-invoices"])  # 新增：发票管理路由 - 暂时禁用
router.include_router(payments.router, tags=["sales-payments"])
router.include_router(statistics.router, tags=["sales-statistics"])
router.include_router(loss_analysis.router, tags=["sales-loss-analysis"])
router.include_router(expenses.router, tags=["sales-expenses"])
router.include_router(assessments.router, tags=["sales-assessments"])
# router.include_router(templates.router, tags=["sales-templates"])  # 暂时禁用，存在导入问题

# 以下模块暂时禁用（缺少 schema 定义）
# from . import cost_management
# from . import receivables, workflows, disputes
# from . import requirements, team, targets
# from . import pipeline_analysis, accountability, health
# from . import delay_analysis, cost_overrun, information_gap, cross_analysis
