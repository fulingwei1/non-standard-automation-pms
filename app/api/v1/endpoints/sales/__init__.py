# -*- coding: utf-8 -*-
"""
销售管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter

# 导入所有模块
from . import (
    assessments,
    contracts,
    cost_management,
    disputes,
    expenses,
    invoices,
    leads,
    loss_analysis,
    opportunities,
    payments,
    priority,
    quotes,
    quote_approval,
    statistics,
    team,
    targets,
    requirements,
    pipeline_analysis,
    accountability,
    health,
    delay_analysis,
    cost_overrun,
    information_gap,
    cross_analysis,
    workflows,
    receivables,
    templates,
)

# 创建主路由
router = APIRouter()

# 注意：优先级路由需要在leads之前注册，避免路径冲突
# /sales/leads/priority-ranking 需要在 /sales/leads/{lead_id} 之前匹配
router.include_router(priority.router, tags=["sales-priority"])
router.include_router(leads.router, tags=["sales-leads"])
router.include_router(opportunities.router, tags=["sales-opportunities"])
router.include_router(quotes.router, tags=["sales-quotes"])
router.include_router(quote_approval.router, tags=["sales-quote-approval"])
router.include_router(contracts.router, tags=["sales-contracts"])
router.include_router(invoices.router, tags=["sales-invoices"])
router.include_router(payments.router, tags=["sales-payments"])
router.include_router(statistics.router, tags=["sales-statistics"])
router.include_router(loss_analysis.router, tags=["sales-loss-analysis"])
router.include_router(expenses.router, tags=["sales-expenses"])
router.include_router(assessments.router, tags=["sales-assessments"])
router.include_router(disputes.router, tags=["sales-disputes"])
router.include_router(targets.router, tags=["sales-targets"])
router.include_router(team.router, tags=["sales-team"])
router.include_router(templates.router, tags=["sales-templates"])

# 以下模块暂时禁用（缺少 schema 定义）
# from . import cost_management
# from . import receivables, workflows, requirements
# from . import pipeline_analysis, accountability, health
# from . import delay_analysis, cost_overrun, information_gap, cross_analysis

# 已启用的模块（包含 schema 定义）
router.include_router(cost_management.router, tags=["sales-cost-management"])
router.include_router(receivables.router, tags=["sales-receivables"])
router.include_router(workflows.router, tags=["sales-workflows"])
router.include_router(requirements.router, tags=["sales-requirements"])
router.include_router(pipeline_analysis.router, tags=["sales-pipeline-analysis"])
# router.include_router(accountability.router, tags=["sales-accountability"])
# router.include_router(health.router, tags=["sales-health"])
# router.include_router(delay_analysis.router, tags=["sales-delay-analysis"])
# router.include_router(cost_overrun.router, tags=["sales-cost-overrun"])
# router.include_router(information_gap.router, tags=["sales-information-gap"])
# router.include_router(cross_analysis.router, tags=["sales-cross-analysis"])
