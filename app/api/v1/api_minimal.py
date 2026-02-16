# -*- coding: utf-8 -*-
"""
API路由聚合 - 最小版本（用于测试）

只导入核心模块，逐步添加
"""

from fastapi import APIRouter

def create_api_router() -> APIRouter:
    """创建最小API路由"""
    api_router = APIRouter()
    
    # ==================== 核心认证模块 ====================
    from app.api.v1.endpoints import auth
    api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
    print("✓ auth 已加载")
    
    # ==================== 用户管理 ====================
    from app.api.v1.endpoints import users
    api_router.include_router(users.router, prefix="/users", tags=["users"])
    print("✓ users 已加载")
    
    # ==================== 项目管理 ====================
    from app.api.v1.endpoints.projects import router as projects_router
    api_router.include_router(projects_router, prefix="/projects", tags=["projects"])
    print("✓ projects 已加载")
    
    # ==================== 生产管理 ====================
    from app.api.v1.endpoints.production import router as production_router
    api_router.include_router(production_router, prefix="/production", tags=["production"])
    print("✓ production 已加载")
    
    # ==================== 销售管理 ====================
    from app.api.v1.endpoints.sales import router as sales_router
    api_router.include_router(sales_router, prefix="/sales", tags=["sales"])
    print("✓ sales 已加载")
    
    print(f"\n✓ 最小路由加载完成，共 {len(api_router.routes)} 个路由")
    return api_router

# 创建全局API路由实例
api_router = create_api_router()
