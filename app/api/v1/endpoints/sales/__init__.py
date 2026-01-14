# -*- coding: utf-8 -*-
"""
销售管理模块路由聚合

将拆分后的各个子模块路由聚合到统一的router中
"""

from fastapi import APIRouter
from . import leads, opportunities, quotes, cost_management, assessments, statistics, templates, contracts, payments, receivables, invoices, workflows, disputes, requirements, team, targets, loss_analysis, expenses, priority, pipeline_analysis, accountability, health, delay_analysis, cost_overrun, information_gap, cross_analysis

# 创建主路由
router = APIRouter()

# 聚合所有子路由（保持原有路由路径）
router.include_router(leads.router, tags=["sales-leads"])
router.include_router(opportunities.router, tags=["sales-opportunities"])
router.include_router(quotes.router, tags=["sales-quotes"])
router.include_router(cost_management.router, tags=["sales-cost-management"])
router.include_router(assessments.router, tags=["sales-assessments"])
router.include_router(statistics.router, tags=["sales-statistics"])
router.include_router(templates.router, tags=["sales-templates"])
router.include_router(contracts.router, tags=["sales-contracts"])
router.include_router(payments.router, tags=["sales-payments"])
router.include_router(receivables.router, tags=["sales-receivables"])
router.include_router(invoices.router, tags=["sales-invoices"])
router.include_router(workflows.router, tags=["sales-workflows"])
router.include_router(disputes.router, tags=["sales-disputes"])
router.include_router(requirements.router, tags=["sales-requirements"])
router.include_router(team.router, tags=["sales-team"])
router.include_router(targets.router, tags=["sales-targets"])
router.include_router(loss_analysis.router, tags=["sales-loss-analysis"])
router.include_router(expenses.router, tags=["sales-expenses"])
router.include_router(priority.router, tags=["sales-priority"])
router.include_router(pipeline_analysis.router, tags=["sales-pipeline-analysis"])
router.include_router(accountability.router, tags=["sales-accountability"])
router.include_router(health.router, tags=["sales-health"])
router.include_router(delay_analysis.router, tags=["sales-delay-analysis"])
router.include_router(cost_overrun.router, tags=["sales-cost-overrun"])
router.include_router(information_gap.router, tags=["sales-information-gap"])
router.include_router(cross_analysis.router, tags=["sales-cross-analysis"])