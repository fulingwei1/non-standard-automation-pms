from fastapi import APIRouter
from app.api.v1.endpoints import (
    # projects,  # 已拆分为projects包
    customers,
    machines,
    milestones,
    members,
    stages,
    organization,
    auth,
    costs,
    budget,
    documents,
    users,
    roles,
    audits,
    issues,
    technical_spec,
    suppliers,
    materials,
    purchase,
    bom,
    # progress,  # 已拆分为progress包
    kit_rate,
    kit_check,
    shortage_alerts,
    shortage,
    notifications,
    # sales,  # 已拆分为sales包
    # production,  # 已拆分为production包
    alerts,
    # ecn,  # 已拆分为ecn包
    outsourcing,
    acceptance,
    material_demands,
    task_center,
    workload,
    pmo,
    presale,
    timesheet,
    data_import_export,
    report_center,
    performance,
    business_support,
    # business_support_orders,  # 已拆分为business_support_orders包
    service,
    sla,
    itr,
    installation_dispatch,
    rd_project,
    engineers,
    technical_review,
    bonus,
    project_evaluation,
    hourly_rate,
    qualification,
    scheduler,
    assembly_kit,
    staff_matching,
    project_roles,
    management_rhythm,
    culture_wall,
    work_log,
    project_workspace,
    project_contributions,
    admin_stats,
    hr_management,
    presales_integration,
    advantage_products,
    procurement_analysis,
    inventory_analysis,
)

api_router = APIRouter()
# 项目模块已拆分为子模块，从projects包导入
from app.api.v1.endpoints.projects import router as projects_router
api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(milestones.router, prefix="/milestones", tags=["milestones"])
api_router.include_router(members.router, prefix="/members", tags=["members"])
api_router.include_router(stages.router, prefix="/stages", tags=["stages"])
api_router.include_router(organization.router, prefix="/org", tags=["organization"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(costs.router, prefix="/costs", tags=["costs"])
api_router.include_router(budget.router, prefix="/budgets", tags=["budgets"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
api_router.include_router(issues.template_router, prefix="/issue-templates", tags=["issue-templates"])
api_router.include_router(technical_spec.router, prefix="/technical-spec", tags=["technical-spec"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(purchase.router, prefix="/purchase-orders", tags=["purchase"])
api_router.include_router(bom.router, prefix="/bom", tags=["bom"])
api_router.include_router(kit_rate.router, prefix="", tags=["kit-rate"])
api_router.include_router(kit_check.router, prefix="", tags=["kit-check"])
# 进度模块已拆分为子模块，从progress包导入
from app.api.v1.endpoints.progress import router as progress_router
api_router.include_router(progress_router, prefix="/progress", tags=["progress"])
api_router.include_router(shortage_alerts.router, prefix="/shortage-alerts", tags=["shortage-alerts"])
api_router.include_router(shortage.router, prefix="", tags=["shortage"])
# 销售模块已拆分为子模块，从sales包导入
from app.api.v1.endpoints.sales import router as sales_router
api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
# 生产模块已拆分为子模块，从production包导入
from app.api.v1.endpoints.production import router as production_router
api_router.include_router(production_router, prefix="", tags=["production"])
api_router.include_router(alerts.router, prefix="", tags=["alerts"])
# ECN模块已拆分为子模块，从ecn包导入
from app.api.v1.endpoints.ecn import router as ecn_router
api_router.include_router(ecn_router, prefix="", tags=["ecn"])
api_router.include_router(outsourcing.router, prefix="", tags=["outsourcing"])
api_router.include_router(acceptance.router, prefix="", tags=["acceptance"])
api_router.include_router(material_demands.router, prefix="", tags=["material-demands"])
api_router.include_router(task_center.router, prefix="/task-center", tags=["task-center"])
api_router.include_router(workload.router, prefix="", tags=["workload"])
api_router.include_router(timesheet.router, prefix="/timesheets", tags=["timesheets"])
api_router.include_router(pmo.router, prefix="", tags=["pmo"])
api_router.include_router(presale.router, prefix="", tags=["presale"])
api_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_router.include_router(report_center.router, prefix="/reports", tags=["reports"])
api_router.include_router(data_import_export.router, prefix="/import", tags=["data-import-export"])
api_router.include_router(business_support.router, prefix="/business-support", tags=["business-support"])
# 商务支持订单模块已拆分为子模块，从business_support_orders包导入
from app.api.v1.endpoints.business_support_orders import router as business_support_orders_router
api_router.include_router(business_support_orders_router, prefix="/business-support", tags=["business-support"])
api_router.include_router(installation_dispatch.router, prefix="/installation-dispatch", tags=["installation-dispatch"])
api_router.include_router(service.router, prefix="/service", tags=["service"])
api_router.include_router(sla.router, prefix="/sla", tags=["sla"])
api_router.include_router(itr.router, prefix="/itr", tags=["itr"])
api_router.include_router(rd_project.router, prefix="", tags=["rd-project"])
api_router.include_router(engineers.router, prefix="/engineers", tags=["engineers"])
api_router.include_router(technical_review.router, prefix="", tags=["technical-review"])
api_router.include_router(bonus.router, prefix="/bonus", tags=["bonus"])
api_router.include_router(project_evaluation.router, prefix="/project-evaluation", tags=["project-evaluation"])
api_router.include_router(hourly_rate.router, prefix="/hourly-rates", tags=["hourly-rates"])
api_router.include_router(qualification.router, prefix="/qualifications", tags=["qualifications"])
api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
api_router.include_router(assembly_kit.router, prefix="/assembly", tags=["assembly-kit"])
api_router.include_router(staff_matching.router, prefix="/staff-matching", tags=["staff-matching"])
api_router.include_router(project_roles.router, prefix="/project-roles", tags=["project-roles"])
api_router.include_router(management_rhythm.router, prefix="", tags=["management-rhythm"])
api_router.include_router(culture_wall.router, prefix="", tags=["culture-wall"])
from app.api.v1.endpoints import culture_wall_config
api_router.include_router(culture_wall_config.router, prefix="", tags=["culture-wall-config"])
api_router.include_router(work_log.router, prefix="", tags=["work-log"])
api_router.include_router(project_workspace.router, prefix="", tags=["project-workspace"])
api_router.include_router(project_contributions.router, prefix="", tags=["project-contributions"])
api_router.include_router(admin_stats.router, prefix="", tags=["admin-stats"])
api_router.include_router(hr_management.router, prefix="/hr", tags=["hr-management"])
api_router.include_router(presales_integration.router, prefix="/presales", tags=["presales-integration"])
api_router.include_router(advantage_products.router, prefix="/advantage-products", tags=["advantage-products"])
api_router.include_router(procurement_analysis.router, prefix="/procurement-analysis", tags=["procurement-analysis"])
api_router.include_router(inventory_analysis.router, prefix="/inventory-analysis", tags=["inventory-analysis"])

# 工程师绩效评价模块
from app.api.v1.endpoints.engineer_performance import router as engineer_performance_router
api_router.include_router(engineer_performance_router, prefix="", tags=["engineer-performance"])