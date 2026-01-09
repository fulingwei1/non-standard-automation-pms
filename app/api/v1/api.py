from fastapi import APIRouter
from app.api.v1.endpoints import (
    projects,
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
    progress,
    kit_rate,
    kit_check,
    shortage_alerts,
    shortage,
    notifications,
    sales,
    production,
    alerts,
    ecn,
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
    business_support_orders,
    service,
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
)

api_router = APIRouter()
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
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
api_router.include_router(progress.router, prefix="", tags=["progress"])
api_router.include_router(shortage_alerts.router, prefix="/shortage-alerts", tags=["shortage-alerts"])
api_router.include_router(shortage.router, prefix="", tags=["shortage"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(production.router, prefix="", tags=["production"])
api_router.include_router(alerts.router, prefix="", tags=["alerts"])
api_router.include_router(ecn.router, prefix="", tags=["ecn"])
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
api_router.include_router(business_support_orders.router, prefix="/business-support", tags=["business-support"])
api_router.include_router(installation_dispatch.router, prefix="/installation-dispatch", tags=["installation-dispatch"])
api_router.include_router(service.router, prefix="/service", tags=["service"])
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