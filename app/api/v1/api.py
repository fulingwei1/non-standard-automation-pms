# -*- coding: utf-8 -*-
"""
API路由聚合 - 中等版本（跳过有问题的模块）

基于api_lazy.py，但跳过导致递归错误的模块
"""

import importlib
import logging
from typing import Union

from fastapi import APIRouter

logger = logging.getLogger(__name__)


def _safe_include(
    parent: APIRouter,
    module_path: str,
    prefix: str,
    tags: list[str],
    *,
    attr: str = "router",
    include_in_schema: bool = True,
) -> bool:
    """安全注册路由：导入模块并注册 router，失败时记录警告但不阻塞启动"""
    try:
        mod = importlib.import_module(module_path, package="app.api.v1")
        router_obj = getattr(mod, attr)
        parent.include_router(
            router_obj, prefix=prefix, tags=tags,
            include_in_schema=include_in_schema,
        )
        logger.info(f"{prefix or tags[0]} 路由加载成功")
        return True
    except Exception as e:
        logger.warning(f"{prefix or tags[0]} 路由加载失败: {e}")
        return False


def _safe_include_group(
    parent: APIRouter,
    group_name: str,
    registrations: list[tuple[str, str, list[str]]],
) -> bool:
    """安全批量注册路由：同一 try 块内导入并注册多个 router，全部成功或全部跳过"""
    try:
        for module_path, prefix, tags in registrations:
            mod = importlib.import_module(module_path, package="app.api.v1")
            parent.include_router(getattr(mod, "router"), prefix=prefix, tags=tags)
        logger.info(f"{group_name}加载成功")
        return True
    except Exception as e:
        logger.warning(f"{group_name}加载失败: {e}")
        return False


# ---------- 路由注册表 ----------
# 元素类型:
#   tuple[str, str, list[str]]  — 单路由: (module_path, prefix, tags)
#   tuple[str, list[...]]       — 分组路由: (group_name, [(module_path, prefix, tags), ...])
# 顺序决定注册顺序，不要随意调整
_ROUTE_REGISTRY: list[Union[
    tuple[str, str, list[str]],
    tuple[str, list[tuple[str, str, list[str]]]],
]] = [
    # ── 核心认证（auth 已在 main.py 优先注册，此处只注册 sessions/2fa） ──
    ("认证模块(sessions/2fa)", [
        (".endpoints.sessions",    "/auth",     ["sessions"]),
        (".endpoints.two_factor",  "/auth/2fa", ["2fa"]),
    ]),
    # ── 用户和组织 ──
    ("用户组织模块", [
        (".endpoints.users",         "/users", ["users"]),
        (".endpoints.organization",  "/org",   ["organization"]),
    ]),
    # ── 角色 & 权限（prefix 已在模块内定义） ──
    (".endpoints.roles",                     "",                      ["roles"]),
    (".endpoints.permissions",               "",                      ["permissions"]),
    # ── 项目 ──
    (".endpoints.projects",                  "/projects",             ["projects"]),
    # ── 生产管理 ──
    ("生产管理模块", [
        (".endpoints.production",              "/production",              ["production"]),
        (".endpoints.production.workers",      "/workers",                 ["workers"]),
        (".endpoints.production.exceptions",   "/production-exceptions",   ["production-exceptions"]),
        (".endpoints.production_daily_reports", "/production-daily-reports", ["production-daily-reports"]),
    ]),
    # ── 销售 ──
    (".endpoints.sales",                     "/sales",                ["sales"]),
    # ── 工时（analytics已禁用） ──
    (".endpoints.timesheet",                 "/timesheet",            ["timesheet"]),
    # ── 研发项目 ──
    (".endpoints.rd_project",                "/rd-projects",          ["rd-projects"]),
    # ── 审批 ──
    (".endpoints.approvals",                 "/approvals",            ["approvals"]),
    # ── 客户和供应商 ──
    ("客户供应商模块", [
        (".endpoints.customers",  "/customers",  ["customers"]),
        (".endpoints.suppliers",  "/suppliers",   ["suppliers"]),
    ]),
    # ── 物料和采购 ──
    ("物料采购模块", [
        (".endpoints.materials",  "/materials",  ["materials"]),
        (".endpoints.purchase",   "/purchase",   ["purchase"]),
        (".endpoints.bom",        "/bom",        ["bom"]),
    ]),
    # 采购智能管理 (暂时禁用 - 缺少MaterialShortage)
    # (".endpoints.purchase_intelligence", "/purchase", ["purchase-intelligence"]),
    # ── 库存（prefix 已在 inventory_router.py 定义） ──
    (".endpoints.inventory.inventory_router", "",                     ["inventory"]),
    # ── 缺料 ──
    (".endpoints.shortage",                  "/shortage",             ["shortage"]),
    (".endpoints.shortage.smart_alerts",     "/shortage/smart-alerts", ["smart-alerts"]),
    # ── 预售 ──
    (".endpoints.presale",                   "/presale",              ["presale"]),
    # ── 预售AI ──
    ("预售AI模块", [
        (".presale_ai_quotation",  "", ["presale-ai"]),
        (".presale_ai_win_rate",   "", ["presale-ai"]),
    ]),
    # ── 方案版本 ──
    (".solution_versions",                   "",                      ["solution-versions"]),
    # ── 验收 ──
    (".endpoints.acceptance",                "/acceptance",           ["acceptance"]),
    # ── 报表框架 ──
    (".endpoints.reports.unified",           "",                      ["reports"]),
    # ── 仓储 ──
    (".endpoints.warehouse",                 "/warehouse",            ["warehouse"]),
    (".endpoints.node_tasks",                "/node-tasks",           ["node_tasks"]),
    (".endpoints.dashboard_stats",           "",                      ["dashboard_stats"]),
    (".endpoints.dashboard_unified",         "",                      ["dashboard_unified"]),
    (".endpoints.notifications",             "/notifications",        ["notifications"]),
    # ── 预警 ──
    (".endpoints.alerts",                    "",                      ["alerts"]),
    # ── 问题 ──
    (".endpoints.issues",                    "/issues",               ["issues"]),
    # ── 奖金 ──
    (".endpoints.bonus",                     "",                      ["bonus"]),
    # ── 绩效 ──
    (".endpoints.engineer_performance",      "",                      ["engineer-performance"]),
    (".endpoints.performance",               "",                      ["performance"]),
    (".endpoints.performance_contract",      "/performance-contract", ["绩效合约"]),
    # ── AI战略 ──
    (".endpoints.ai_strategy",               "/ai-strategy",          ["AI战略辅助"]),
    # ── 人事 ──
    (".endpoints.hr_management",             "/hr",                   ["hr-management"]),
    (".endpoints.outsourcing",               "",                      ["outsourcing"]),
    (".endpoints.pmo",                       "",                      ["pmo"]),
    (".endpoints.staff_matching",            "/staff-matching",       ["staff-matching"]),
    (".endpoints.task_center",               "/task-center",          ["task-center"]),
    (".endpoints.technical_review",          "",                      ["technical-reviews"]),
    (".endpoints.scheduler",                 "/scheduler",            ["scheduler"]),
    (".endpoints.qualification",             "/qualifications",       ["qualifications"]),
    (".endpoints.documents",                 "/documents",            ["documents"]),
    (".endpoints.engineers",                 "/engineers",            ["engineers"]),
    (".endpoints.hourly_rate",               "/hourly-rates",         ["hourly-rates"]),
    (".endpoints.kit_rate",                  "",                      ["kit-rates"]),
    (".endpoints.report_center",             "/report-center",        ["report-center"]),
    (".endpoints.admin_stats",               "/admin",                ["admin-stats"]),
    (".endpoints.procurement_analysis",      "/procurement-analysis", ["procurement-analysis"]),
    (".endpoints.strategy",                  "/strategy",             ["战略管理"]),
    (".endpoints.supplier_price_trend",      "/supplier-price",       ["supplier-price"]),
    (".endpoints.ecn_bom",                   "",                      ["ecn-bom"]),
    (".endpoints.field_commissioning",       "",                      ["field-commissioning"]),
    (".endpoints.multi_currency",            "/currency",             ["multi-currency"]),
    (".endpoints.ecn",                       "",                      ["ecn"]),
    (".endpoints.installation_dispatch",     "/installation-dispatch", ["installation-dispatch"]),
    (".endpoints.stage_templates",           "/stage-templates",      ["stage-templates"]),
    (".endpoints.advantage_products",        "/advantage-products",   ["advantage-products"]),
    (".endpoints.assembly_kit",              "",                      ["assembly-kit"]),
    # ── AI 功能模块 ──
    ("AI 功能模块", [
        (".endpoints.engineer_scheduling",      "/engineer-scheduling",      ["engineer-scheduling"]),
        (".endpoints.requirement_extraction",    "/requirement-extraction",   ["requirement-extraction"]),
        (".endpoints.team_generation",           "/team-generation",          ["team-generation"]),
        (".endpoints.schedule_generation",       "/schedule-generation",      ["schedule-generation"]),
        (".endpoints.schedule_optimization",     "/schedule-optimization",    ["schedule-optimization"]),
    ]),
    # 预算管理: 特殊处理（见 create_api_router 内的 _SPECIAL_BUDGET）
    # 商务支持
    (".endpoints.business_support",          "",                        ["business-support"]),
    (".endpoints.business_support_orders",   "/business-support-orders", ["business-support-orders"]),
    (".endpoints.culture_wall",              "/culture-wall",           ["culture-wall"]),
    (".endpoints.data_import_export",        "/data-import-export",     ["data-import-export"]),
    (".endpoints.departments",               "/departments",            ["departments"]),
    (".endpoints.kit_check",                 "/kit-check",              ["kit-check"]),
    (".endpoints.management_rhythm",         "/management-rhythm",      ["management-rhythm"]),
    (".endpoints.material_demands",          "/material-demands",       ["material-demands"]),
    (".endpoints.my",                        "/my",                     ["my"]),
    (".endpoints.pitfalls",                  "/pitfalls",               ["pitfalls"]),
    # 预售分析: 特殊处理（见 create_api_router 内的 _SPECIAL_PRESALE_ANALYTICS）
    # 项目评审
    (".endpoints.project_review",            "/project-reviews",        ["project-reviews"]),
    (".endpoints.service",                   "",                        ["service"]),
    (".endpoints.sla",                       "/sla",                    ["sla"]),
    (".endpoints.solution_credits",          "/solution-credits",       ["solution-credits"]),
    (".endpoints.standard_costs",            "/standard-costs",         ["standard-costs"]),
    (".endpoints.technical_spec",            "/technical-specs",        ["technical-specs"]),
    (".endpoints.account_unlock",            "/account-unlock",         ["account-unlock"]),
    (".endpoints.audits",                    "/audits",                 ["audits"]),
    (".endpoints.backup",                    "/backup",                 ["backup"]),
    (".endpoints.change_impact",             "/change-impact",          ["change-impact"]),
    (".endpoints.culture_wall_config",       "/culture-wall-config",    ["culture-wall-config"]),
    (".endpoints.inventory_analysis",        "/inventory-analysis",     ["inventory-analysis"]),
    (".endpoints.itr",                       "/itr",                    ["itr"]),
    (".endpoints.pm_involvement",            "/pm-involvement",         ["pm-involvement"]),
    (".endpoints.presale_ai_requirement",    "",                        ["presale-ai-requirement"]),
    (".endpoints.presale_mobile",            "/presale-mobile",         ["presale-mobile"]),
    (".endpoints.project_contributions",     "/project-contributions",  ["project-contributions"]),
    (".endpoints.project_workspace",         "/project-workspace",      ["project-workspace"]),
    (".endpoints.quality_risk",              "/quality-risk",           ["quality-risk"]),
    # ── 资源调度 ──
    ("资源调度模块", [
        (".endpoints.resource_scheduling",      "/resource-scheduling",  ["resource-scheduling"]),
        (".endpoints.resource_overview",         "/resource-overview",    ["resource-overview"]),
        (".endpoints.margin_prediction",         "/margin-prediction",    ["margin-prediction"]),
        (".endpoints.cost_collection",           "/cost-collection",      ["cost-collection"]),
        (".endpoints.quote_actual_compare",      "/quote-compare",        ["quote-compare"]),
        (".endpoints.cost_variance_analysis",    "/cost-variance",        ["cost-variance"]),
        (".endpoints.gantt_dependency",          "/gantt",                ["gantt-dependency"]),
        (".endpoints.labor_cost_detail",         "/labor-cost",           ["labor-cost"]),
    ]),
    (".endpoints.lessons_learned",           "/lessons",                ["lessons-learned"]),
    (".endpoints.sales_regions",             "/sales-regions",          ["sales-regions"]),
    (".endpoints.sales_targets",             "/sales-targets",          ["sales-targets"]),
    (".endpoints.sales_teams",               "/sales-teams",            ["sales-teams"]),
    (".endpoints.tenants",                   "",                        ["tenants"]),
    (".endpoints.timesheet_reminders",       "/timesheet-reminders",    ["timesheet-reminders"]),
    (".endpoints.dashboard",                 "/dashboard",              ["dashboard"]),
    (".endpoints.report",                    "/report",                 ["report"]),
    # 成本管理（兼容旧版/costs/路径）
    (".endpoints.costs",                     "/costs",                  ["costs"]),
]


def create_api_router() -> APIRouter:
    """
    创建API路由（跳过有问题的模块）

    跳过的模块:
    - timesheet.analytics (Pydantic递归错误)
    - 其他可能有问题的模块
    """
    api_router = APIRouter()

    logger.info("开始加载API路由...")

    # ── 批量注册：按注册表顺序逐条/逐组加载 ──
    for entry in _ROUTE_REGISTRY:
        if isinstance(entry[1], list):
            # 分组路由: (group_name, [(module, prefix, tags), ...])
            _safe_include_group(api_router, entry[0], entry[1])
        else:
            # 单路由: (module_path, prefix, tags)
            _safe_include(api_router, entry[0], entry[1], entry[2])

    # ── 特殊注册：同一 router 注册多个 prefix ──

    # 预算管理：/budget + /budgets（兼容测试）
    try:
        mod = importlib.import_module(".endpoints.budget", package="app.api.v1")
        api_router.include_router(mod.router, prefix="/budget", tags=["budget"])
        api_router.include_router(mod.router, prefix="/budgets", tags=["budgets"])
        logger.info("预算管理模块加载成功")
    except Exception as e:
        logger.warning(f"预算管理模块加载失败: {e}")

    # 预售分析：/presale-analytics + /presales（兼容旧前端）
    try:
        mod = importlib.import_module(".endpoints.presale_analytics", package="app.api.v1")
        api_router.include_router(mod.router, prefix="/presale-analytics", tags=["presale-analytics"])
        api_router.include_router(mod.router, prefix="/presales", tags=["presales-compat"], include_in_schema=False)
        logger.info("预售分析模块加载成功")
    except Exception as e:
        logger.warning(f"预售分析模块加载失败: {e}")

    # ── Stub Endpoints (必须放最后作为 fallback) ──
    _safe_include(api_router, ".endpoints.stub_endpoints", "", ["stub-未实现"])

    logger.info("API路由加载完成，共 %d 个路由", len(api_router.routes))
    return api_router


# 创建全局API路由实例
logger.debug("app/api/v1/api.py: 准备调用 create_api_router()")
try:
    api_router = create_api_router()
    logger.debug("app/api/v1/api.py: 成功创建api_router，路由数=%d", len(api_router.routes))
except Exception as e:
    logger.error("app/api/v1/api.py: create_api_router() 失败: %s", e)
    logger.exception("create_api_router() traceback:")
    # 创建空路由器作为fallback
    api_router = APIRouter()
    logger.warning("app/api/v1/api.py: 使用空路由器作为fallback")
