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
    customers,
    contacts,
    customer_tags,
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
    quote_cost_analysis,
    quote_cost_breakdown,
    quote_cost_calculations,
    quote_delivery,
    quote_exports,
    quote_items,
    quote_quotes_crud,
    quote_status,
    quote_templates,
    quote_versions,
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
from .contracts import contracts as contracts_contracts

# 创建主路由
router = APIRouter()

# 注意：优先级路由需要在leads之前注册，避免路径冲突
# /sales/leads/priority-ranking 需要在 /sales/leads/{lead_id} 之前匹配
router.include_router(customers.router, tags=["sales-customers"])
router.include_router(contacts.router, tags=["sales-contacts"])
router.include_router(customer_tags.router, tags=["sales-customer-tags"])
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
router.include_router(accountability.router, tags=["sales-accountability"])
router.include_router(health.router, tags=["sales-health"])
router.include_router(delay_analysis.router, tags=["sales-delay-analysis"])
router.include_router(cost_overrun.router, tags=["sales-cost-overrun"])
router.include_router(information_gap.router, tags=["sales-information-gap"])
router.include_router(cross_analysis.router, tags=["sales-cross-analysis"])

# 合同创建项目路由
router.include_router(contracts_contracts.router, tags=["sales-contracts-projects"])

# 报价详细模块路由
router.include_router(quote_cost_analysis.router, tags=["sales-quote-cost-analysis"])
router.include_router(quote_cost_breakdown.router, tags=["sales-quote-cost-breakdown"])
router.include_router(quote_cost_calculations.router, tags=["sales-quote-cost-calculations"])
router.include_router(quote_delivery.router, tags=["sales-quote-delivery"])
router.include_router(quote_exports.router, tags=["sales-quote-exports"])
router.include_router(quote_items.router, tags=["sales-quote-items"])
router.include_router(quote_quotes_crud.router, tags=["sales-quote-crud"])
router.include_router(quote_status.router, tags=["sales-quote-status"])
router.include_router(quote_templates.router, tags=["sales-quote-templates"])
router.include_router(quote_versions.router, tags=["sales-quote-versions"])

# 新增AI销售助手、报价智能化、销售自动化路由
from . import ai_sales_assistant, sales_intelligent_quote, sales_automation

router.include_router(ai_sales_assistant.router, prefix="/ai", tags=["sales-ai-assistant"])
router.include_router(sales_intelligent_quote.router, tags=["sales-intelligent-quote"])
router.include_router(sales_automation.router, tags=["sales-automation"])

# 销售漏斗优化路由
from . import sales_funnel_optimization
router.include_router(sales_funnel_optimization.router, prefix="/funnel", tags=["sales-funnel-optimization"])

# 客户 360°画像路由
from . import customer_360
router.include_router(customer_360.router, prefix="/customer-360", tags=["sales-customer-360"])

# 销售绩效与激励路由
from . import sales_performance
router.include_router(sales_performance.router, prefix="/performance", tags=["sales-performance-incentive"])

# 销售协同路由
from . import sales_collaboration
router.include_router(sales_collaboration.router, prefix="/collaboration", tags=["sales-collaboration"])

# 移动端支持路由
from . import sales_mobile
router.include_router(sales_mobile.router, prefix="/mobile", tags=["sales-mobile"])

# 销售预测仪表盘路由
from . import sales_forecast
router.include_router(sales_forecast.router, prefix="/forecast", tags=["sales-forecast-dashboard"])

# 增强版销售预测路由
from . import sales_forecast_enhanced
router.include_router(sales_forecast_enhanced.router, prefix="/forecast-enhanced", tags=["sales-forecast-enhanced"])

# 商务关系成熟度路由
from . import relationship_maturity
router.include_router(relationship_maturity.router, prefix="/relationship", tags=["sales-relationship-maturity"])

# 综合赢单率预测路由
from . import win_rate_prediction
router.include_router(win_rate_prediction.router, prefix="/win-rate", tags=["sales-win-rate-prediction"])

# 竞争对手分析路由
from . import competitor_analysis
router.include_router(competitor_analysis.router, prefix="/competitor", tags=["sales-competitor-analysis"])

# 销售组织架构路由
from . import sales_organization
router.include_router(sales_organization.router, prefix="/organization", tags=["sales-organization"])
