# -*- coding: utf-8 -*-
"""
API路由聚合 - 延迟导入版本

使用延迟导入避免循环依赖：
- 不在模块顶层导入所有endpoint
- 在函数内部按需导入
- 避免一次性加载所有模块
"""

from fastapi import APIRouter

def create_api_router() -> APIRouter:
    """
    使用延迟导入创建API路由
    
    优点:
    - 避免顶层导入导致的循环依赖
    - 模块按需加载，减少启动时间
    - 便于调试和测试
    
    Returns:
        APIRouter: 配置好的API路由
    """
    api_router = APIRouter()
    
    # ==================== 核心认证模块 ====================
    from app.api.v1.endpoints import auth, sessions, two_factor
    api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
    api_router.include_router(sessions.router, prefix="/auth", tags=["sessions"])
    api_router.include_router(two_factor.router, prefix="/auth/2fa", tags=["2fa"])
    
    # ==================== 用户和组织 ====================
    from app.api.v1.endpoints import users, organization
    api_router.include_router(users.router, prefix="/users", tags=["users"])
    api_router.include_router(organization.router, prefix="/org", tags=["organization"])
    
    # ==================== 权限管理 ====================
    from app.api.v1.endpoints.roles import router as roles_router
    from app.api.v1.endpoints.permissions import router as permissions_router
    api_router.include_router(roles_router, prefix="/roles", tags=["roles"])
    api_router.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
    
    # ==================== 项目管理 ====================
    from app.api.v1.endpoints.projects import router as projects_router
    api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
    
    # ==================== 生产管理 ====================
    from app.api.v1.endpoints.production import router as production_router
    api_router.include_router(production_router, prefix="/production", tags=["production"])
    
    # ==================== 销售管理 ====================
    from app.api.v1.endpoints.sales import router as sales_router
    api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
    
    # ==================== 工时管理 ====================
    from app.api.v1.endpoints.timesheet import router as timesheet_router
    api_router.include_router(timesheet_router, prefix="/timesheet", tags=["timesheet"])
    
    # ==================== 研发项目 ====================
    from app.api.v1.endpoints.rd_project import router as rd_project_router
    api_router.include_router(rd_project_router, prefix="/rd-projects", tags=["rd-projects"])
    
    # ==================== 审批流程 ====================
    from app.api.v1.endpoints.approvals import router as approvals_router
    api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
    
    # ==================== 客户和供应商 ====================
    from app.api.v1.endpoints import customers
    from app.api.v1.endpoints.suppliers import router as suppliers_router
    api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
    api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
    
    # ==================== 物料和采购 ====================
    from app.api.v1.endpoints import materials, purchase, bom
    api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
    api_router.include_router(purchase.router, prefix="/purchase-orders", tags=["purchase"])
    api_router.include_router(bom.router, prefix="/bom", tags=["bom"])
    
    # ==================== 缺料管理 ====================
    from app.api.v1.endpoints.shortage import router as shortage_router
    api_router.include_router(shortage_router, prefix="/shortage", tags=["shortage"])
    
    # ==================== 智能缺料预警 ====================
    from app.api.v1.endpoints.shortage.smart_alerts import router as smart_alerts_router
    api_router.include_router(smart_alerts_router, prefix="/shortage/smart-alerts", tags=["smart-alerts"])
    
    # ==================== 预售AI ====================
    try:
        from app.api.v1.presale_ai_quotation import router as presale_ai_quotation_router
        from app.api.v1.presale_ai_win_rate import router as presale_ai_win_rate_router
        from app.api.v1.endpoints.presale import router as presale_router
        api_router.include_router(presale_ai_quotation_router, tags=["presale-ai"])
        api_router.include_router(presale_ai_win_rate_router, tags=["presale-ai"])
        api_router.include_router(presale_router, prefix="/presale", tags=["presale"])
    except ImportError as e:
        print(f"⚠️  预售AI模块导入失败: {e}")
    
    # ==================== 通知和告警 ====================
    try:
        from app.api.v1.endpoints import notifications, alerts
        api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
        api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
    except ImportError as e:
        print(f"⚠️  通知模块导入失败（循环依赖）: {e}")
    
    # ==================== 仪表盘 ====================
    from app.api.v1.endpoints import dashboard_unified, dashboard_stats
    api_router.include_router(dashboard_unified.router, prefix="/dashboard", tags=["dashboard"])
    api_router.include_router(dashboard_stats.router, prefix="/dashboard-stats", tags=["dashboard-stats"])
    
    # ==================== 其他业务模块 ====================
    from app.api.v1.endpoints import (
        audits, issues, documents, budget,
        kit_rate, kit_check, engineers, hourly_rate,
        technical_spec, acceptance, admin_stats,
        advantage_products, culture_wall, hr_management,
        installation_dispatch, inventory_analysis, itr,
        material_demands, procurement_analysis, project_contributions,
        project_workspace, qualification, scheduler, sla,
        solution_credits, staff_matching, technical_review,
    )
    
    api_router.include_router(audits.router, prefix="/audits", tags=["audits"])
    api_router.include_router(issues.router, prefix="/issues", tags=["issues"])
    api_router.include_router(issues.template_router, prefix="/issue-templates", tags=["issue-templates"])
    api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
    api_router.include_router(budget.router, prefix="/budgets", tags=["budgets"])
    api_router.include_router(kit_rate.router, prefix="", tags=["kit-rate"])
    api_router.include_router(kit_check.router, prefix="", tags=["kit-check"])
    api_router.include_router(engineers.router, prefix="/engineers", tags=["engineers"])
    api_router.include_router(hourly_rate.router, prefix="/hourly-rates", tags=["hourly-rates"])
    api_router.include_router(technical_spec.router, prefix="/technical-spec", tags=["technical-spec"])
    api_router.include_router(acceptance.router, prefix="/acceptance", tags=["acceptance"])
    api_router.include_router(admin_stats.router, prefix="/admin-stats", tags=["admin-stats"])
    api_router.include_router(advantage_products.router, prefix="/advantage-products", tags=["advantage-products"])
    api_router.include_router(culture_wall.router, prefix="/culture-wall", tags=["culture-wall"])
    api_router.include_router(hr_management.router, prefix="/hr", tags=["hr-management"])
    api_router.include_router(installation_dispatch.router, prefix="/installation-dispatch", tags=["installation-dispatch"])
    api_router.include_router(inventory_analysis.router, prefix="/inventory-analysis", tags=["inventory-analysis"])
    api_router.include_router(itr.router, prefix="/itr", tags=["itr"])
    api_router.include_router(material_demands.router, prefix="/material-demands", tags=["material-demands"])
    api_router.include_router(procurement_analysis.router, prefix="/procurement-analysis", tags=["procurement-analysis"])
    api_router.include_router(project_contributions.router, prefix="/project-contributions", tags=["project-contributions"])
    api_router.include_router(project_workspace.router, prefix="/project-workspace", tags=["project-workspace"])
    api_router.include_router(qualification.router, prefix="/qualification", tags=["qualification"])
    api_router.include_router(scheduler.router, prefix="/scheduler", tags=["scheduler"])
    api_router.include_router(sla.router, prefix="/sla", tags=["sla"])
    api_router.include_router(solution_credits.router, prefix="/solution-credits", tags=["solution-credits"])
    api_router.include_router(staff_matching.router, prefix="/staff-matching", tags=["staff-matching"])
    api_router.include_router(technical_review.router, prefix="/technical-review", tags=["technical-review"])
    
    # ==================== 更多端点 ====================
    from app.api.v1.endpoints.pitfalls import router as pitfalls_router
    from app.api.v1.endpoints.account_unlock import router as account_unlock_router
    from app.api.v1.endpoints.standard_costs import router as standard_costs_router
    
    api_router.include_router(pitfalls_router, prefix="/pitfalls", tags=["pitfalls"])
    api_router.include_router(account_unlock_router, prefix="/admin/account-lockout", tags=["admin", "security"])
    api_router.include_router(standard_costs_router, prefix="/standard-costs", tags=["standard-costs"])
    
    # ==================== 高级功能模块 ====================
    try:
        from app.api.v1.endpoints.ecn import router as ecn_router
        from app.api.v1.endpoints.outsourcing import router as outsourcing_router
        from app.api.v1.endpoints.task_center import router as task_center_router
        from app.api.v1.endpoints.pmo import router as pmo_router
        from app.api.v1.endpoints.data_import_export import router as data_import_export_router
        from app.api.v1.endpoints.report_center import router as report_center_router
        from app.api.v1.endpoints.performance import router as performance_router
        from app.api.v1.endpoints.business_support import router as business_support_router
        from app.api.v1.endpoints.service import router as service_router
        from app.api.v1.endpoints.bonus import router as bonus_router
        from app.api.v1.endpoints.assembly_kit import router as assembly_kit_router
        from app.api.v1.endpoints.management_rhythm import router as management_rhythm_router
        
        api_router.include_router(ecn_router, prefix="/ecn", tags=["ecn"])
        api_router.include_router(outsourcing_router, prefix="/outsourcing", tags=["outsourcing"])
        api_router.include_router(task_center_router, prefix="/task-center", tags=["task-center"])
        api_router.include_router(pmo_router, prefix="/pmo", tags=["pmo"])
        api_router.include_router(data_import_export_router, prefix="/data", tags=["data-import-export"])
        api_router.include_router(report_center_router, prefix="/reports", tags=["report-center"])
        api_router.include_router(performance_router, prefix="/performance", tags=["performance"])
        api_router.include_router(business_support_router, prefix="/business-support", tags=["business-support"])
        api_router.include_router(service_router, prefix="/service", tags=["service"])
        api_router.include_router(bonus_router, prefix="/bonus", tags=["bonus"])
        api_router.include_router(assembly_kit_router, prefix="/assembly-kit", tags=["assembly-kit"])
        api_router.include_router(management_rhythm_router, prefix="/management-rhythm", tags=["management-rhythm"])
    except ImportError as e:
        print(f"⚠️  部分高级功能模块导入失败: {e}")
    
    # ==================== 采购库存系统 ====================
    try:
        from app.api.v1.endpoints.purchase_intelligence import router as purchase_intelligence_router
        from app.api.v1.endpoints.material_tracking import router as material_tracking_router
        from app.api.v1.endpoints.shortage_alert import router as shortage_alert_router
        
        api_router.include_router(purchase_intelligence_router, prefix="/purchase-intelligence", tags=["purchase-intelligence"])
        api_router.include_router(material_tracking_router, prefix="/material-tracking", tags=["material-tracking"])
        api_router.include_router(shortage_alert_router, prefix="/shortage-alert", tags=["shortage-alert"])
    except ImportError as e:
        print(f"⚠️  采购库存系统导入失败: {e}")
    
    # ==================== 项目复盘系统 ====================
    try:
        from app.api.v1.endpoints.project_review import router as project_review_router
        api_router.include_router(project_review_router, prefix="/project-review", tags=["project-review"])
    except ImportError as e:
        print(f"⚠️  项目复盘系统导入失败: {e}")
    
    # ==================== 工程师绩效系统 ====================
    try:
        from app.api.v1.endpoints.engineer_performance import router as engineer_performance_router
        api_router.include_router(engineer_performance_router, prefix="/engineer-performance", tags=["engineer-performance"])
    except ImportError as e:
        print(f"⚠️  工程师绩效系统导入失败: {e}")
    
    # ==================== 统一报告框架 ====================
    try:
        from app.api.v1.endpoints.reports import router as reports_router
        api_router.include_router(reports_router, tags=["reports"])
    except ImportError as e:
        print(f"⚠️  统一报告框架导入失败: {e}")
    
    # 战略管理模块 (Temporarily disabled due to circular import)
    # from app.api.v1.endpoints.strategy import router as strategy_router
    # api_router.include_router(strategy_router, prefix="/strategy", tags=["strategy"])
    
    return api_router


# 创建全局API路由实例
api_router = create_api_router()
