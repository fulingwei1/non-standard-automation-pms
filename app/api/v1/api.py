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
        api_router.include_router(acceptance_router, tags=["acceptance"])
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
    

    # ==================== 任务中心 ====================
    try:
        from app.api.v1.endpoints.task_center import router as task_center_router
        api_router.include_router(task_center_router, prefix="/task-center", tags=["task-center"])
        print("✓ 任务中心模块加载成功")
    except Exception as e:
        print(f"✗ 任务中心模块加载失败: {e}")
    
    # ==================== 阶段模板管理 ====================
    try:
        from app.api.v1.endpoints.stage_templates import router as stage_templates_router
        api_router.include_router(stage_templates_router, prefix="/stage-templates", tags=["stage-templates"])
        print("✓ 阶段模板管理模块加载成功")
    except Exception as e:
        print(f"✗ 阶段模板管理模块加载失败: {e}")
    
    # ==================== 节点子任务 ====================
    try:
        from app.api.v1.endpoints.node_tasks import router as node_tasks_router
        api_router.include_router(node_tasks_router, prefix="/node-tasks", tags=["node-tasks"])
        print("✓ 节点子任务模块加载成功")
    except Exception as e:
        print(f"✗ 节点子任务模块加载失败: {e}")
    
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
