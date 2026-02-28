# -*- coding: utf-8 -*-
"""
API路由聚合 - 中等版本（跳过有问题的模块）

基于api_lazy.py，但跳过导致递归错误的模块
"""

from fastapi import APIRouter

def create_api_router() -> APIRouter:
    """
    创建API路由（跳过有问题的模块）
    
    跳过的模块:
    - timesheet.analytics (Pydantic递归错误)
    - 其他可能有问题的模块
    """
    api_router = APIRouter()
    
    print("开始加载API路由...")
    
    # ==================== 核心认证模块 ====================
    try:
        from app.api.v1.endpoints import auth, sessions, two_factor
        api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
        api_router.include_router(sessions.router, prefix="/auth", tags=["sessions"])
        api_router.include_router(two_factor.router, prefix="/auth/2fa", tags=["2fa"])
        print("✓ 认证模块加载成功")
    except Exception as e:
        print(f"✗ 认证模块加载失败: {e}")
    
    # ==================== 用户和组织 ====================
    try:
        from app.api.v1.endpoints import users, organization
        api_router.include_router(users.router, prefix="/users", tags=["users"])
        api_router.include_router(organization.router, prefix="/org", tags=["organization"])
        print("✓ 用户组织模块加载成功")
    except Exception as e:
        print(f"✗ 用户组织模块加载失败: {e}")
    
    # ==================== 角色管理 ====================
    try:
        from app.api.v1.endpoints.roles import router as roles_router
        api_router.include_router(roles_router, tags=["roles"])  # 移除prefix（已在roles.py定义）
        print("✓ 角色管理模块加载成功")
    except Exception as e:
        print(f"✗ 角色管理模块加载失败: {e}")
    
    # ==================== 权限管理 ====================
    try:
        from app.api.v1.endpoints.permissions import router as permissions_router
        api_router.include_router(permissions_router, tags=["permissions"])
        print("✓ 权限管理模块加载成功")
    except Exception as e:
        print(f"✗ 权限管理模块加载失败: {e}")
    
    # ==================== 项目管理 ====================
    try:
        from app.api.v1.endpoints.projects import router as projects_router
        api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
        print("✓ 项目管理模块加载成功")
    except Exception as e:
        print(f"✗ 项目管理模块加载失败: {e}")
    
    # ==================== 生产管理 ====================
    try:
        from app.api.v1.endpoints.production import router as production_router
        api_router.include_router(production_router, prefix="/production", tags=["production"])
        print("✓ 生产管理模块加载成功")
    except Exception as e:
        print(f"✗ 生产管理模块加载失败: {e}")
    
    # ==================== 销售管理 ====================
    try:
        from app.api.v1.endpoints.sales import router as sales_router
        api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
        print("✓ 销售管理模块加载成功")
    except Exception as e:
        print(f"✗ 销售管理模块加载失败: {e}")
    
    # ==================== 工时管理 ====================
    try:
        from app.api.v1.endpoints.timesheet import router as timesheet_router
        api_router.include_router(timesheet_router, prefix="/timesheet", tags=["timesheet"])
        print("✓ 工时管理模块加载成功 (analytics已禁用)")
    except Exception as e:
        print(f"✗ 工时管理模块加载失败: {e}")
    
    # ==================== 研发项目 ====================
    try:
        from app.api.v1.endpoints.rd_project import router as rd_project_router
        api_router.include_router(rd_project_router, prefix="/rd-projects", tags=["rd-projects"])
        print("✓ 研发项目模块加载成功")
    except Exception as e:
        print(f"✗ 研发项目模块加载失败: {e}")
    
    # ==================== 审批流程 ====================
    try:
        from app.api.v1.endpoints.approvals import router as approvals_router
        api_router.include_router(approvals_router, prefix="/approvals", tags=["approvals"])
        print("✓ 审批流程模块加载成功")
    except Exception as e:
        print(f"✗ 审批流程模块加载失败: {e}")
    
    # ==================== 客户和供应商 ====================
    try:
        from app.api.v1.endpoints import customers
        from app.api.v1.endpoints.suppliers import router as suppliers_router
        api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
        api_router.include_router(suppliers_router, prefix="/suppliers", tags=["suppliers"])
        print("✓ 客户供应商模块加载成功")
    except Exception as e:
        print(f"✗ 客户供应商模块加载失败: {e}")
    
    # ==================== 物料和采购 ====================
    try:
        from app.api.v1.endpoints import materials, purchase, bom
        api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
        api_router.include_router(purchase.router, prefix="/purchase-orders", tags=["purchase"])
        api_router.include_router(bom.router, prefix="/bom", tags=["bom"])
        print("✓ 物料采购模块加载成功")
    except Exception as e:
        print(f"✗ 物料采购模块加载失败: {e}")
    
    # ==================== 采购智能管理 (暂时禁用 - 缺少MaterialShortage) ====================
    # try:
    #     from app.api.v1.endpoints.purchase_intelligence import router as purchase_intelligence_router
    #     api_router.include_router(purchase_intelligence_router, prefix="/purchase", tags=["purchase-intelligence"])
    #     print("✓ 采购智能管理模块加载成功")
    # except Exception as e:
    #     print(f"✗ 采购智能管理模块加载失败: {e}")
    
    # ==================== 库存管理 ====================
    try:
        from app.api.v1.endpoints.inventory.inventory_router import router as inventory_router
        api_router.include_router(inventory_router, tags=["inventory"])  # 移除prefix（已在inventory_router.py定义）
        print("✓ 库存管理模块加载成功")
    except Exception as e:
        print(f"✗ 库存管理模块加载失败: {e}")
    
    # ==================== 缺料管理 ====================
    try:
        from app.api.v1.endpoints.shortage import router as shortage_router
        api_router.include_router(shortage_router, prefix="/shortage", tags=["shortage"])
        print("✓ 缺料管理模块加载成功")
    except Exception as e:
        print(f"✗ 缺料管理模块加载失败: {e}")
    
    # ==================== 智能缺料预警 ====================
    try:
        from app.api.v1.endpoints.shortage.smart_alerts import router as smart_alerts_router
        api_router.include_router(smart_alerts_router, prefix="/shortage/smart-alerts", tags=["smart-alerts"])
        print("✓ 智能缺料预警模块加载成功")
    except Exception as e:
        print(f"✗ 智能缺料预警模块加载失败: {e}")
    
    # ==================== 预售管理 ====================
    try:
        from app.api.v1.endpoints.presale import router as presale_router
        api_router.include_router(presale_router, prefix="/presale", tags=["presale"])
        print("✓ 预售管理模块加载成功")
    except Exception as e:
        print(f"✗ 预售管理模块加载失败: {e}")
    
    # ==================== 预售AI ====================
    try:
        from app.api.v1.presale_ai_quotation import router as presale_ai_quotation_router
        from app.api.v1.presale_ai_win_rate import router as presale_ai_win_rate_router
        api_router.include_router(presale_ai_quotation_router, tags=["presale-ai"])
        api_router.include_router(presale_ai_win_rate_router, tags=["presale-ai"])
        print("✓ 预售AI模块加载成功")
    except Exception as e:
        print(f"✗ 预售AI模块加载失败: {e}")
    
    # ==================== 验收管理 ====================
    try:
        from app.api.v1.endpoints.acceptance import router as acceptance_router
        api_router.include_router(acceptance_router, prefix="/acceptance", tags=["acceptance"])
        print("✓ 验收管理模块加载成功")
    except Exception as e:
        print(f"✗ 验收管理模块加载失败: {e}")
    
    # ==================== 报表框架 ====================
    try:
        from app.api.v1.endpoints.reports.unified import router as reports_router
        api_router.include_router(reports_router, tags=["reports"])
        print("✓ 报表框架模块加载成功")
    except Exception as e:
        print(f"✗ 报表框架模块加载失败: {e}")
    

    # ==================== 仓储管理 ====================
    try:
        from app.api.v1.endpoints.warehouse import router as warehouse_router
        api_router.include_router(warehouse_router, prefix="/warehouse", tags=["warehouse"])
        print("✓ 仓储管理模块加载成功")
    except Exception as e:
        print(f"✗ 仓储管理模块加载失败: {e}")

    # 节点任务
    try:
        from app.api.v1.endpoints.node_tasks import router as node_tasks_router
        api_router.include_router(node_tasks_router, prefix="/node-tasks", tags=["node_tasks"])
        print("✓ 节点任务模块加载成功")
    except Exception as e:
        print(f"✗ 节点任务模块加载失败: {e}")

    # Dashboard 统计
    try:
        from app.api.v1.endpoints.dashboard_stats import router as dashboard_stats_router
        api_router.include_router(dashboard_stats_router, tags=["dashboard_stats"])
        print("✓ Dashboard统计模块加载成功")
    except Exception as e:
        print(f"✗ Dashboard统计模块加载失败: {e}")

    # Dashboard 统一入口
    try:
        from app.api.v1.endpoints.dashboard_unified import router as dashboard_unified_router
        api_router.include_router(dashboard_unified_router, tags=["dashboard_unified"])
        print("✓ Dashboard统一模块加载成功")
    except Exception as e:
        print(f"✗ Dashboard统一模块加载失败: {e}")

    # 通知中心
    try:
        from app.api.v1.endpoints.notifications import router as notifications_router
        api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
        print("✓ 通知中心模块加载成功")
    except Exception as e:
        print(f"✗ 通知中心模块加载失败: {e}")


    # ==================== 预警管理 ====================
    try:
        from app.api.v1.endpoints.alerts import router as alerts_router
        api_router.include_router(alerts_router, tags=["alerts"])
        print("✓ 预警管理模块加载成功")
    except Exception as e:
        print(f"✗ 预警管理模块加载失败: {e}")

    # ==================== 问题管理 ====================
    try:
        from app.api.v1.endpoints.issues import router as issues_router
        api_router.include_router(issues_router, prefix="/issues", tags=["issues"])
        print("✓ 问题管理模块加载成功")
    except Exception as e:
        print(f"✗ 问题管理模块加载失败: {e}")

    # ==================== 奖金管理 ====================
    try:
        from app.api.v1.endpoints.bonus import router as bonus_router
        api_router.include_router(bonus_router, tags=["bonus"])
        print("✓ 奖金管理模块加载成功")
    except Exception as e:
        print(f"✗ 奖金管理模块加载失败：{e}")

    # ==================== 工程师绩效 ====================
    try:
        from app.api.v1.endpoints.engineer_performance import router as engineer_performance_router
        api_router.include_router(engineer_performance_router, tags=["engineer-performance"])
        print("✓ 工程师绩效模块加载成功")
    except Exception as e:
        print(f"✗ 工程师绩效模块加载失败：{e}")

    # ==================== 绩效管理 ====================
    try:
        from app.api.v1.endpoints.performance import router as performance_router
        api_router.include_router(performance_router, tags=["performance"])
        print("✓ 绩效管理模块加载成功")
    except Exception as e:
        print(f"✗ 绩效管理模块加载失败：{e}")

    # ==================== 人事管理 ====================
    try:
        from app.api.v1.endpoints.hr_management import router as hr_management_router
        api_router.include_router(hr_management_router, prefix="/hr", tags=["hr-management"])
        print("✓ 人事管理模块加载成功")
    except Exception as e:
        print(f"✗ 人事管理模块加载失败：{e}")

    # ==================== 外包管理 ====================
    try:
        from app.api.v1.endpoints.outsourcing import router as outsourcing_router
        api_router.include_router(outsourcing_router, tags=["outsourcing"])
        print("✓ 外包管理模块加载成功")
    except Exception as e:
        print(f"✗ 外包管理模块加载失败：{e}")

    # ==================== PMO ====================
    try:
        from app.api.v1.endpoints.pmo import router as pmo_router
        api_router.include_router(pmo_router, tags=["pmo"])
        print("✓ PMO 模块加载成功")
    except Exception as e:
        print(f"✗ PMO 模块加载失败：{e}")

    # ==================== 人岗匹配 ====================
    try:
        from app.api.v1.endpoints.staff_matching import router as staff_matching_router
        api_router.include_router(staff_matching_router, prefix="/staff-matching", tags=["staff-matching"])
        print("✓ 人岗匹配模块加载成功")
    except Exception as e:
        print(f"✗ 人岗匹配模块加载失败：{e}")

    # ==================== 任务中心 ====================
    try:
        from app.api.v1.endpoints.task_center import router as task_center_router
        api_router.include_router(task_center_router, prefix="/task-center", tags=["task-center"])
        print("✓ 任务中心模块加载成功")
    except Exception as e:
        print(f"✗ 任务中心模块加载失败：{e}")

    # ==================== 技术评审 ====================
    try:
        from app.api.v1.endpoints.technical_review import router as technical_review_router
        api_router.include_router(technical_review_router, tags=["technical-reviews"])
        print("✓ 技术评审模块加载成功")
    except Exception as e:
        print(f"✗ 技术评审模块加载失败：{e}")

    # ==================== 任务调度 ====================
    try:
        from app.api.v1.endpoints.scheduler import router as scheduler_router
        api_router.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
        print("✓ 任务调度模块加载成功")
    except Exception as e:
        print(f"✗ 任务调度模块加载失败：{e}")

    # ==================== 资格认证 ====================
    try:
        from app.api.v1.endpoints.qualification import router as qualification_router
        api_router.include_router(qualification_router, prefix="/qualifications", tags=["qualifications"])
        print("✓ 资格认证模块加载成功")
    except Exception as e:
        print(f"✗ 资格认证模块加载失败：{e}")

    # ==================== 文档管理 ====================
    try:
        from app.api.v1.endpoints.documents import router as documents_router
        api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
        print("✓ 文档管理模块加载成功")
    except Exception as e:
        print(f"✗ 文档管理模块加载失败：{e}")

    # ==================== 工程师管理 ====================
    try:
        from app.api.v1.endpoints.engineers import router as engineers_router
        api_router.include_router(engineers_router, prefix="/engineers", tags=["engineers"])
        print("✓ 工程师管理模块加载成功")
    except Exception as e:
        print(f"✗ 工程师管理模块加载失败：{e}")

    # ==================== 工时费率 ====================
    try:
        from app.api.v1.endpoints.hourly_rate import router as hourly_rate_router
        api_router.include_router(hourly_rate_router, prefix="/hourly-rates", tags=["hourly-rates"])
        print("✓ 工时费率模块加载成功")
    except Exception as e:
        print(f"✗ 工时费率模块加载失败：{e}")

    # ==================== 成套率 ====================
    try:
        from app.api.v1.endpoints.kit_rate import router as kit_rate_router
        api_router.include_router(kit_rate_router, tags=["kit-rates"])
        print("✓ 成套率模块加载成功")
    except Exception as e:
        print(f"✗ 成套率模块加载失败：{e}")

    # ==================== 报表中心 ====================
    try:
        from app.api.v1.endpoints.report_center import router as report_center_router
        api_router.include_router(report_center_router, prefix="/report-center", tags=["report-center"])
        print("✓ 报表中心模块加载成功")
    except Exception as e:
        print(f"✗ 报表中心模块加载失败：{e}")

    # ==================== 管理统计 ====================
    try:
        from app.api.v1.endpoints.admin_stats import router as admin_stats_router
        api_router.include_router(admin_stats_router, prefix="/admin", tags=["admin-stats"])
        print("✓ 管理统计模块加载成功")
    except Exception as e:
        print(f"✗ 管理统计模块加载失败：{e}")

    # ==================== 采购分析 ====================
    try:
        from app.api.v1.endpoints.procurement_analysis import router as procurement_analysis_router
        api_router.include_router(procurement_analysis_router, prefix="/procurement-analysis", tags=["procurement-analysis"])
        print("✓ 采购分析模块加载成功")
    except Exception as e:
        print(f"✗ 采购分析模块加载失败：{e}")
    # ==================== ECN 工程变更 ====================
    try:
        from app.api.v1.endpoints.ecn import router as ecn_router
        api_router.include_router(ecn_router, prefix="", tags=["ecn"])
        print("✓ ECN模块加载成功")
    except Exception as e:
        print(f"✗ ECN模块加载失败：{e}")

    # ==================== 安装派工 ====================
    try:
        from app.api.v1.endpoints.installation_dispatch import router as installation_dispatch_router
        api_router.include_router(installation_dispatch_router, prefix="/installation-dispatch", tags=["installation-dispatch"])
        print("✓ 安装派工模块加载成功")
    except Exception as e:
        print(f"✗ 安装派工模块加载失败：{e}")

    # ==================== 阶段模板 ====================
    try:
        from app.api.v1.endpoints.stage_templates import router as stage_templates_router
        api_router.include_router(stage_templates_router, prefix="/stage-templates", tags=["stage-templates"])
        print("✓ 阶段模板模块加载成功")
    except Exception as e:
        print(f"✗ 阶段模板模块加载失败：{e}")

    # ==================== 优势产品 ====================
    try:
        from app.api.v1.endpoints.advantage_products import router as advantage_products_router
        api_router.include_router(advantage_products_router, prefix="/advantage-products", tags=["advantage-products"])
        print("✓ 优势产品模块加载成功")
    except Exception as e:
        print(f"✗ 优势产品模块加载失败：{e}")

    # ==================== 成套分析 ====================
    try:
        from app.api.v1.endpoints.assembly_kit import router as assembly_kit_router
        api_router.include_router(assembly_kit_router, tags=["assembly-kit"])
        print("✓ 成套分析模块加载成功")
    except Exception as e:
        print(f"✗ 成套分析模块加载失败：{e}")

    # ==================== 预算管理 ====================
    try:
        from app.api.v1.endpoints.budget import router as budget_router
        api_router.include_router(budget_router, prefix="/budget", tags=["budget"])
        print("✓ 预算管理模块加载成功")
    except Exception as e:
        print(f"✗ 预算管理模块加载失败：{e}")

    # ==================== 商务支持 ====================
    try:
        from app.api.v1.endpoints.business_support import router as business_support_router
        api_router.include_router(business_support_router, tags=["business-support"])
        print("✓ 商务支持模块加载成功")
    except Exception as e:
        print(f"✗ 商务支持模块加载失败：{e}")

    # ==================== 商务支持订单 ====================
    try:
        from app.api.v1.endpoints.business_support_orders import router as business_support_orders_router
        api_router.include_router(business_support_orders_router, prefix="/business-support-orders", tags=["business-support-orders"])
        print("✓ 商务支持订单模块加载成功")
    except Exception as e:
        print(f"✗ 商务支持订单模块加载失败：{e}")

    # ==================== 文化墙 ====================
    try:
        from app.api.v1.endpoints.culture_wall import router as culture_wall_router
        api_router.include_router(culture_wall_router, prefix="/culture-wall", tags=["culture-wall"])
        print("✓ 文化墙模块加载成功")
    except Exception as e:
        print(f"✗ 文化墙模块加载失败：{e}")

    # ==================== 数据导入导出 ====================
    try:
        from app.api.v1.endpoints.data_import_export import router as data_import_export_router
        api_router.include_router(data_import_export_router, prefix="/data-import-export", tags=["data-import-export"])
        print("✓ 数据导入导出模块加载成功")
    except Exception as e:
        print(f"✗ 数据导入导出模块加载失败：{e}")

    # ==================== 部门管理 ====================
    try:
        from app.api.v1.endpoints.departments import router as departments_router
        api_router.include_router(departments_router, prefix="/departments", tags=["departments"])
        print("✓ 部门管理模块加载成功")
    except Exception as e:
        print(f"✗ 部门管理模块加载失败：{e}")

    # ==================== 成套检查 ====================
    try:
        from app.api.v1.endpoints.kit_check import router as kit_check_router
        api_router.include_router(kit_check_router, prefix="/kit-check", tags=["kit-check"])
        print("✓ 成套检查模块加载成功")
    except Exception as e:
        print(f"✗ 成套检查模块加载失败：{e}")

    # ==================== 管理节奏 ====================
    try:
        from app.api.v1.endpoints.management_rhythm import router as management_rhythm_router
        api_router.include_router(management_rhythm_router, prefix="/management-rhythm", tags=["management-rhythm"])
        print("✓ 管理节奏模块加载成功")
    except Exception as e:
        print(f"✗ 管理节奏模块加载失败：{e}")

    # ==================== 物料需求 ====================
    try:
        from app.api.v1.endpoints.material_demands import router as material_demands_router
        api_router.include_router(material_demands_router, prefix="/material-demands", tags=["material-demands"])
        print("✓ 物料需求模块加载成功")
    except Exception as e:
        print(f"✗ 物料需求模块加载失败：{e}")

    # ==================== 我的 ====================
    try:
        from app.api.v1.endpoints.my import router as my_router
        api_router.include_router(my_router, prefix="/my", tags=["my"])
        print("✓ 我的模块加载成功")
    except Exception as e:
        print(f"✗ 我的模块加载失败：{e}")

    # ==================== 踩坑记录 ====================
    try:
        from app.api.v1.endpoints.pitfalls import router as pitfalls_router
        api_router.include_router(pitfalls_router, prefix="/pitfalls", tags=["pitfalls"])
        print("✓ 踩坑记录模块加载成功")
    except Exception as e:
        print(f"✗ 踩坑记录模块加载失败：{e}")

    # ==================== 预售分析 ====================
    try:
        from app.api.v1.endpoints.presale_analytics import router as presale_analytics_router
        api_router.include_router(presale_analytics_router, prefix="/presale-analytics", tags=["presale-analytics"])
        print("✓ 预售分析模块加载成功")
    except Exception as e:
        print(f"✗ 预售分析模块加载失败：{e}")

    # ==================== 项目评审 ====================
    try:
        from app.api.v1.endpoints.project_review import router as project_review_router
        api_router.include_router(project_review_router, prefix="/project-reviews", tags=["project-reviews"])
        print("✓ 项目评审模块加载成功")
    except Exception as e:
        print(f"✗ 项目评审模块加载失败：{e}")

    # ==================== 服务工单 ====================
    try:
        from app.api.v1.endpoints.service import router as service_router
        api_router.include_router(service_router, tags=["service"])
        print("✓ 服务工单模块加载成功")
    except Exception as e:
        print(f"✗ 服务工单模块加载失败：{e}")

    # ==================== SLA ====================
    try:
        from app.api.v1.endpoints.sla import router as sla_router
        api_router.include_router(sla_router, prefix="/sla", tags=["sla"])
        print("✓ SLA模块加载成功")
    except Exception as e:
        print(f"✗ SLA模块加载失败：{e}")

    # ==================== 方案学分 ====================
    try:
        from app.api.v1.endpoints.solution_credits import router as solution_credits_router
        api_router.include_router(solution_credits_router, prefix="/solution-credits", tags=["solution-credits"])
        print("✓ 方案学分模块加载成功")
    except Exception as e:
        print(f"✗ 方案学分模块加载失败：{e}")

    # ==================== 标准成本 ====================
    try:
        from app.api.v1.endpoints.standard_costs import router as standard_costs_router
        api_router.include_router(standard_costs_router, prefix="/standard-costs", tags=["standard-costs"])
        print("✓ 标准成本模块加载成功")
    except Exception as e:
        print(f"✗ 标准成本模块加载失败：{e}")

    # ==================== 技术规格 ====================
    try:
        from app.api.v1.endpoints.technical_spec import router as technical_spec_router
        api_router.include_router(technical_spec_router, prefix="/technical-specs", tags=["technical-specs"])
        print("✓ 技术规格模块加载成功")
    except Exception as e:
        print(f"✗ 技术规格模块加载失败：{e}")

    # ==================== 账号解锁 ====================
    try:
        from app.api.v1.endpoints.account_unlock import router as account_unlock_router
        api_router.include_router(account_unlock_router, prefix="/account-unlock", tags=["account-unlock"])
        print("✓ 账号解锁模块加载成功")
    except Exception as e:
        print(f"✗ 账号解锁模块加载失败：{e}")

    # ==================== 审计日志 ====================
    try:
        from app.api.v1.endpoints.audits import router as audits_router
        api_router.include_router(audits_router, prefix="/audits", tags=["audits"])
        print("✓ 审计日志模块加载成功")
    except Exception as e:
        print(f"✗ 审计日志模块加载失败：{e}")

    # ==================== 备份 ====================
    try:
        from app.api.v1.endpoints.backup import router as backup_router
        api_router.include_router(backup_router, prefix="/backup", tags=["backup"])
        print("✓ 备份模块加载成功")
    except Exception as e:
        print(f"✗ 备份模块加载失败：{e}")

    # ==================== 变更影响 ====================
    try:
        from app.api.v1.endpoints.change_impact import router as change_impact_router
        api_router.include_router(change_impact_router, prefix="/change-impact", tags=["change-impact"])
        print("✓ 变更影响模块加载成功")
    except Exception as e:
        print(f"✗ 变更影响模块加载失败：{e}")

    # ==================== 文化墙配置 ====================
    try:
        from app.api.v1.endpoints.culture_wall_config import router as culture_wall_config_router
        api_router.include_router(culture_wall_config_router, prefix="/culture-wall-config", tags=["culture-wall-config"])
        print("✓ 文化墙配置模块加载成功")
    except Exception as e:
        print(f"✗ 文化墙配置模块加载失败：{e}")

    # ==================== 库存分析 ====================
    try:
        from app.api.v1.endpoints.inventory_analysis import router as inventory_analysis_router
        api_router.include_router(inventory_analysis_router, prefix="/inventory-analysis", tags=["inventory-analysis"])
        print("✓ 库存分析模块加载成功")
    except Exception as e:
        print(f"✗ 库存分析模块加载失败：{e}")

    # ==================== ITR ====================
    try:
        from app.api.v1.endpoints.itr import router as itr_router
        api_router.include_router(itr_router, prefix="/itr", tags=["itr"])
        print("✓ ITR模块加载成功")
    except Exception as e:
        print(f"✗ ITR模块加载失败：{e}")

    # ==================== PM参与度 ====================
    try:
        from app.api.v1.endpoints.pm_involvement import router as pm_involvement_router
        api_router.include_router(pm_involvement_router, prefix="/pm-involvement", tags=["pm-involvement"])
        print("✓ PM参与度模块加载成功")
    except Exception as e:
        print(f"✗ PM参与度模块加载失败：{e}")

    # ==================== 预售AI需求 ====================
    try:
        from app.api.v1.endpoints.presale_ai_requirement import router as presale_ai_requirement_router
        api_router.include_router(presale_ai_requirement_router, tags=["presale-ai-requirement"])
        print("✓ 预售AI需求模块加载成功")
    except Exception as e:
        print(f"✗ 预售AI需求模块加载失败：{e}")

    # ==================== 预售移动端 ====================
    try:
        from app.api.v1.endpoints.presale_mobile import router as presale_mobile_router
        api_router.include_router(presale_mobile_router, prefix="/presale-mobile", tags=["presale-mobile"])
        print("✓ 预售移动端模块加载成功")
    except Exception as e:
        print(f"✗ 预售移动端模块加载失败：{e}")

    # ==================== 项目贡献 ====================
    try:
        from app.api.v1.endpoints.project_contributions import router as project_contributions_router
        api_router.include_router(project_contributions_router, prefix="/project-contributions", tags=["project-contributions"])
        print("✓ 项目贡献模块加载成功")
    except Exception as e:
        print(f"✗ 项目贡献模块加载失败：{e}")

    # ==================== 项目工作空间 ====================
    try:
        from app.api.v1.endpoints.project_workspace import router as project_workspace_router
        api_router.include_router(project_workspace_router, prefix="/project-workspace", tags=["project-workspace"])
        print("✓ 项目工作空间模块加载成功")
    except Exception as e:
        print(f"✗ 项目工作空间模块加载失败：{e}")

    # ==================== 质量风险 ====================
    try:
        from app.api.v1.endpoints.quality_risk import router as quality_risk_router
        api_router.include_router(quality_risk_router, prefix="/quality-risk", tags=["quality-risk"])
        print("✓ 质量风险模块加载成功")
    except Exception as e:
        print(f"✗ 质量风险模块加载失败：{e}")

    # ==================== 资源调度 ====================
    try:
        from app.api.v1.endpoints.resource_scheduling import router as resource_scheduling_router
        api_router.include_router(resource_scheduling_router, prefix="/resource-scheduling", tags=["resource-scheduling"])

        from app.api.v1.endpoints.resource_overview import router as resource_overview_router
        api_router.include_router(resource_overview_router, prefix="/resource-overview", tags=["resource-overview"])

        from app.api.v1.endpoints.margin_prediction import router as margin_prediction_router
        api_router.include_router(margin_prediction_router, prefix="/margin-prediction", tags=["margin-prediction"])

        from app.api.v1.endpoints.cost_collection import router as cost_collection_router
        api_router.include_router(cost_collection_router, prefix="/cost-collection", tags=["cost-collection"])

        from app.api.v1.endpoints.quote_actual_compare import router as quote_compare_router
        api_router.include_router(quote_compare_router, prefix="/quote-compare", tags=["quote-compare"])

        from app.api.v1.endpoints.cost_variance_analysis import router as cost_variance_router
        api_router.include_router(cost_variance_router, prefix="/cost-variance", tags=["cost-variance"])
        print("✓ 资源调度模块加载成功")
    except Exception as e:
        print(f"✗ 资源调度模块加载失败：{e}")

    # ==================== 经验教训库 ====================
    try:
        from app.api.v1.endpoints.lessons_learned import router as lessons_router
        api_router.include_router(lessons_router, prefix="/lessons", tags=["lessons-learned"])
        print("✓ 经验教训库模块加载成功")
    except Exception as e:
        print(f"✗ 经验教训库模块加载失败：{e}")

    # ==================== 销售区域 ====================
    try:
        from app.api.v1.endpoints.sales_regions import router as sales_regions_router
        api_router.include_router(sales_regions_router, prefix="/sales-regions", tags=["sales-regions"])
        print("✓ 销售区域模块加载成功")
    except Exception as e:
        print(f"✗ 销售区域模块加载失败：{e}")

    # ==================== 销售目标 ====================
    try:
        from app.api.v1.endpoints.sales_targets import router as sales_targets_router
        api_router.include_router(sales_targets_router, prefix="/sales-targets", tags=["sales-targets"])
        print("✓ 销售目标模块加载成功")
    except Exception as e:
        print(f"✗ 销售目标模块加载失败：{e}")

    # ==================== 销售团队 ====================
    try:
        from app.api.v1.endpoints.sales_teams import router as sales_teams_router
        api_router.include_router(sales_teams_router, prefix="/sales-teams", tags=["sales-teams"])
        print("✓ 销售团队模块加载成功")
    except Exception as e:
        print(f"✗ 销售团队模块加载失败：{e}")

    # ==================== 租户管理 ====================
    try:
        from app.api.v1.endpoints.tenants import router as tenants_router
        api_router.include_router(tenants_router, tags=["tenants"])
        print("✓ 租户管理模块加载成功")
    except Exception as e:
        print(f"✗ 租户管理模块加载失败：{e}")

    # ==================== 工时提醒 ====================
    try:
        from app.api.v1.endpoints.timesheet_reminders import router as timesheet_reminders_router
        api_router.include_router(timesheet_reminders_router, prefix="/timesheet-reminders", tags=["timesheet-reminders"])
        print("✓ 工时提醒模块加载成功")
    except Exception as e:
        print(f"✗ 工时提醒模块加载失败：{e}")

    # ==================== Dashboard ====================
    try:
        from app.api.v1.endpoints.dashboard import router as dashboard_router
        api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
        print("✓ Dashboard模块加载成功")
    except Exception as e:
        print(f"✗ Dashboard模块加载失败：{e}")

    # ==================== 报表 ====================
    try:
        from app.api.v1.endpoints.report import router as report_router
        api_router.include_router(report_router, prefix="/report", tags=["report"])
        print("✓ 报表模块加载成功")
    except Exception as e:
        print(f"✗ 报表模块加载失败：{e}")

    # ==================== Stub Endpoints (必须放最后作为fallback) ====================
    try:
        from app.api.v1.endpoints.stub_endpoints import router as stub_router
        api_router.include_router(stub_router, tags=["stub-未实现"])
        print("✓ Stub Endpoints加载成功（未实现API的兜底响应）")
    except Exception as e:
        print(f"✗ Stub模块加载失败：{e}")

    print(f"\n✓ API路由加载完成，共 {len(api_router.routes)} 个路由")
    return api_router

# 创建全局API路由实例
print("[DEBUG] app/api/v1/api.py: 准备调用 create_api_router()")
try:
    api_router = create_api_router()
    print(f"[DEBUG] app/api/v1/api.py: 成功创建api_router，路由数={len(api_router.routes)}")
except Exception as e:
    print(f"[ERROR] app/api/v1/api.py: create_api_router() 失败: {e}")
    import traceback
    traceback.print_exc()
    # 创建空路由器作为fallback
    api_router = APIRouter()
    print("[WARN] app/api/v1/api.py: 使用空路由器作为fallback")
