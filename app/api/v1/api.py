from fastapi import APIRouter

from app.api.v1.endpoints import (  # projects,  # 已拆分为projects包; costs,  # 已拆分为costs包; shortage_alerts,  # 已拆分为shortage_alerts包; shortage,  # 已拆分为shortage包; sales,  # 已拆分为sales包; production,  # 已拆分为production包; ecn,  # 已拆分为ecn包; outsourcing,  # 已拆分为outsourcing包; task_center,  # 已拆分为task_center包; pmo,  # 已拆分为pmo包; presale,  # 已拆分为presale包; timesheet,  # 已拆分为timesheet包; data_import_export,  # 已拆分为data_import_export包; report_center,  # 已拆分为report_center包; performance,  # 已拆分为performance包; business_support,  # 已拆分为business_support包; service,  # 已拆分为service包; rd_project,  # 已拆分为rd_project包; bonus,  # 已拆分为bonus包; assembly_kit,  # 已拆分为assembly_kit包; management_rhythm,  # 已拆分为management_rhythm包
    acceptance,
    admin_stats,
    advantage_products,
    dashboard_unified,
    dashboard_stats,
    alerts,
    audits,
    auth,
    bom,
    budget,
    culture_wall,
    customers,
    documents,
    engineers,
    hourly_rate,
    hr_management,
    installation_dispatch,
    inventory_analysis,
    issues,
    itr,
    kit_check,
    kit_rate,
    material_demands,
    materials,
    notifications,
    organization,
    procurement_analysis,
    project_contributions,
    project_workspace,
    purchase,
    qualification,
    scheduler,
    sla,
    solution_credits,
    staff_matching,
    technical_review,
    technical_spec,
    users,
)

# 导入suppliers端点

from app.api.v1.endpoints.suppliers import router as suppliers_router

# 统一审批路由
from app.api.v1.endpoints.approvals import router as approvals_router

api_router = APIRouter()

api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
# 项目模块已拆分为子模块，从projects包导入
from app.api.v1.endpoints.projects import router as projects_router

api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
# 使用重构后的suppliers端点（使用通用CRUD路由生成器和统一响应格式）
api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(organization.router, prefix="/org", tags=["organization"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(budget.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(
    issues.template_router, prefix="/issue-templates", tags=["issue-templates"]
)
api_router.include_router(
    technical_spec.router, prefix="/technical-spec", tags=["technical-spec"]
)
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(purchase.router, prefix="/purchase-orders", tags=["purchase"])
api_router.include_router(bom.router, prefix="/bom", tags=["bom"])
api_router.include_router(kit_rate.router, prefix="", tags=["kit-rate"])
api_router.include_router(kit_check.router, prefix="", tags=["kit-check"])

# 缺料管理模块（三层架构重构）
# 结构: detection（预警检测）-> handling（问题处理）-> analytics（统计报表）
from app.api.v1.endpoints.shortage import router as shortage_router

api_router.include_router(shortage_router, prefix="/shortage", tags=["shortage"])
# 销售模块已拆分为子模块，从sales包导入
from app.api.v1.endpoints.sales import router as sales_router

api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["notifications"]
)
# 生产模块已拆分为子模块，从production包导入
from app.api.v1.endpoints.production import router as production_router

api_router.include_router(production_router, prefix="", tags=["production"])
api_router.include_router(alerts.router, prefix="", tags=["alerts"])
# ECN模块已拆分为子模块，从ecn包导入
from app.api.v1.endpoints.ecn import router as ecn_router

api_router.include_router(ecn_router, prefix="", tags=["ecn"])
# 外协管理模块已拆分为outsourcing包
from app.api.v1.endpoints.outsourcing import router as outsourcing_router

api_router.include_router(outsourcing_router, prefix="", tags=["outsourcing"])
api_router.include_router(acceptance.router, prefix="", tags=["acceptance"])
api_router.include_router(material_demands.router, prefix="", tags=["material-demands"])
# 任务中心模块已拆分为task_center包
from app.api.v1.endpoints.task_center import router as task_center_router

api_router.include_router(task_center_router, prefix="", tags=["task-center"])

# 工时管理模块已拆分为timesheet包
from app.api.v1.endpoints.timesheet import router as timesheet_router

api_router.include_router(timesheet_router, prefix="", tags=["timesheet"])
# PMO模块已拆分为pmo包
from app.api.v1.endpoints.pmo import router as pmo_router

api_router.include_router(pmo_router, prefix="", tags=["pmo"])
# 售前模块已拆分为presale包
from app.api.v1.endpoints.presale import router as presale_router

api_router.include_router(presale_router, prefix="", tags=["presale"])
# 绩效管理模块已拆分为performance包
from app.api.v1.endpoints.performance import router as performance_router

api_router.include_router(performance_router, prefix="", tags=["performance"])
# 报表中心模块已拆分为report_center包
from app.api.v1.endpoints.report_center import router as report_center_router

api_router.include_router(report_center_router, prefix="", tags=["report-center"])
# 商务支持模块已拆分为子模块，从business_support包导入
from app.api.v1.endpoints.business_support import router as business_support_router

api_router.include_router(
    business_support_router, prefix="/business-support", tags=["business-support"]
)
# 商务支持订单模块已拆分为子模块，从business_support_orders包导入
from app.api.v1.endpoints.business_support_orders import (
    router as business_support_orders_router,
)

api_router.include_router(
    business_support_orders_router,
    prefix="/business-support/orders",
    tags=["business-support-orders"],
)
api_router.include_router(
    installation_dispatch.router,
    prefix="/installation-dispatch",
    tags=["installation-dispatch"],
)
# 售后服务模块已拆分为service包
from app.api.v1.endpoints.service import router as service_router

api_router.include_router(service_router, prefix="", tags=["service"])
# 数据导入导出模块已拆分为data_import_export包
from app.api.v1.endpoints.data_import_export import router as data_import_export_router

api_router.include_router(
    data_import_export_router, prefix="/import", tags=["data-import-export"]
)
api_router.include_router(sla.router, prefix="/sla", tags=["sla"])
api_router.include_router(itr.router, prefix="/itr", tags=["itr"])
# 研发项目模块已拆分为rd_project包
from app.api.v1.endpoints.rd_project import router as rd_project_router

api_router.include_router(rd_project_router, prefix="", tags=["rd-project"])
api_router.include_router(engineers.router, prefix="/engineers", tags=["engineers"])
api_router.include_router(technical_review.router, prefix="", tags=["technical-review"])
# 奖金管理模块已拆分为bonus包
from app.api.v1.endpoints.bonus import router as bonus_router

api_router.include_router(bonus_router, prefix="", tags=["bonus"])
api_router.include_router(
    hourly_rate.router, prefix="/hourly-rates", tags=["hourly-rates"]
)
api_router.include_router(
    qualification.router, prefix="/qualifications", tags=["qualifications"]
)
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
# 装配套件模块已拆分为assembly_kit包
from app.api.v1.endpoints.assembly_kit import router as assembly_kit_router

api_router.include_router(assembly_kit_router, prefix="", tags=["assembly-kit"])
api_router.include_router(
    staff_matching.router, prefix="/staff-matching", tags=["staff-matching"]
)
# 租户管理模块（仅超级管理员可访问）
from app.api.v1.endpoints.tenants import router as tenants_router

api_router.include_router(tenants_router, tags=["tenants"])

# 系统角色管理模块（替代废弃的 project_roles）
from app.api.v1.endpoints.roles import router as roles_router

api_router.include_router(roles_router, tags=["roles"])

# 权限管理模块
from app.api.v1.endpoints.permissions import router as permissions_router

api_router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])

# 管理节律模块已拆分为management_rhythm包
from app.api.v1.endpoints.management_rhythm import router as management_rhythm_router

api_router.include_router(
    management_rhythm_router, prefix="", tags=["management-rhythm"]
)
api_router.include_router(culture_wall.router, prefix="", tags=["culture-wall"])
from app.api.v1.endpoints import culture_wall_config

api_router.include_router(
    culture_wall_config.router, prefix="", tags=["culture-wall-config"]
)
api_router.include_router(
    project_workspace.router, prefix="", tags=["project-workspace"]
)
api_router.include_router(
    project_contributions.router, prefix="", tags=["project-contributions"]
)
api_router.include_router(admin_stats.router, prefix="", tags=["admin-stats"])
api_router.include_router(
    dashboard_unified.router, prefix="", tags=["dashboard-unified"]
)
api_router.include_router(dashboard_stats.router, prefix="", tags=["dashboard-stats"])
api_router.include_router(hr_management.router, prefix="/hr", tags=["hr-management"])
# 售前数据分析模块（从 presales_integration 重命名）
from app.api.v1.endpoints.presale_analytics import router as presale_analytics_router

api_router.include_router(
    presale_analytics_router, prefix="/presale-analytics", tags=["presale-analytics"]
)
api_router.include_router(
    advantage_products.router, prefix="/advantage-products", tags=["advantage-products"]
)
api_router.include_router(
    procurement_analysis.router,
    prefix="/procurement-analysis",
    tags=["procurement-analysis"],
)
api_router.include_router(
    inventory_analysis.router, prefix="/inventory-analysis", tags=["inventory-analysis"]
)

# 工程师绩效评价模块
from app.api.v1.endpoints.engineer_performance import (
    router as engineer_performance_router,
)

api_router.include_router(
    engineer_performance_router, prefix="", tags=["engineer-performance"]
)

# 方案生成积分模块
api_router.include_router(
    solution_credits.router, prefix="/solution-credits", tags=["solution-credits"]
)

# 阶段模板管理模块
from app.api.v1.endpoints import stage_templates, node_tasks

api_router.include_router(
    stage_templates.router, prefix="/stage-templates", tags=["stage-templates"]
)
api_router.include_router(node_tasks.router, prefix="/node-tasks", tags=["node-tasks"])

# 战略管理模块
from app.api.v1.endpoints.strategy import router as strategy_router

api_router.include_router(strategy_router, prefix="/strategy", tags=["strategy"])

# 统一报告框架
from app.api.v1.endpoints.reports import router as reports_router

api_router.include_router(reports_router, tags=["reports"])

# === 项目模块整合：新增跨项目维度路由 ===
from app.api.v1.endpoints import my, departments, analytics

api_router.include_router(my.router, prefix="/my", tags=["my"])
api_router.include_router(
    departments.router, prefix="/departments", tags=["departments"]
)
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
