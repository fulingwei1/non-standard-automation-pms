# -*- coding: utf-8 -*-
"""
统一工作台数据 API

提供统一的dashboard入口，聚合各模块数据。
支持两种模式：
1. 简化模式：仅返回统计卡片和widget配置
2. 详细模式：返回完整的业务数据
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.dashboard import (
    DashboardModuleInfo,
    DetailedDashboardResponse,
    UnifiedDashboardResponse,
)
from app.services.dashboard_adapter import dashboard_registry

# 导入所有适配器（触发自动注册）
import app.services.dashboard_adapters  # noqa: F401

router = APIRouter()


@router.get("/dashboard/unified/{role_code}", response_model=ResponseModel[UnifiedDashboardResponse])
def get_unified_dashboard(
    role_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[UnifiedDashboardResponse]:
    """
    获取统一工作台数据（简化模式）

    Args:
        role_code: 角色代码（sales/engineer/procurement/production/pmo/admin等）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统一格式的dashboard数据，包含统计卡片和widget列表
    """
    # 获取该角色的所有适配器
    adapters = dashboard_registry.get_adapters_for_role(role_code, db, current_user)

    # 汇总所有统计卡片
    all_stats = []
    all_widgets = []

    for adapter in adapters:
        try:
            stats = adapter.get_stats()
            all_stats.extend(stats)

            widgets = adapter.get_widgets()
            all_widgets.extend(widgets)
        except Exception as e:
            # 单个模块失败不影响整体
            print(f"Error loading dashboard for {adapter.module_id}: {e}")
            continue

    # 按order排序widgets
    all_widgets.sort(key=lambda w: w.order)

    return ResponseModel(
        data=UnifiedDashboardResponse(
            role_code=role_code,
            role_name=_get_role_name(role_code),
            stats=all_stats,
            widgets=all_widgets,
            last_updated=datetime.now(),
            refresh_interval=300,  # 5分钟刷新
        )
    )


@router.get("/dashboard/unified/{role_code}/detailed", response_model=ResponseModel[List[DetailedDashboardResponse]])
def get_unified_dashboard_detailed(
    role_code: str,
    module_id: Optional[str] = Query(None, description="指定模块ID，不指定则返回所有模块"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[List[DetailedDashboardResponse]]:
    """
    获取统一工作台详细数据

    Args:
        role_code: 角色代码
        module_id: 可选的模块ID过滤
        db: 数据库会话
        current_user: 当前用户

    Returns:
        详细的dashboard数据列表
    """
    if module_id:
        # 获取指定模块
        adapter = dashboard_registry.get_adapter(module_id, db, current_user)
        if not adapter:
            raise HTTPException(status_code=404, detail=f"Dashboard module '{module_id}' not found")

        if not adapter.supports_role(role_code):
            raise HTTPException(
                status_code=403,
                detail=f"Module '{module_id}' does not support role '{role_code}'"
            )

        adapters = [adapter]
    else:
        # 获取该角色的所有适配器
        adapters = dashboard_registry.get_adapters_for_role(role_code, db, current_user)

    # 获取详细数据
    detailed_data = []
    for adapter in adapters:
        try:
            data = adapter.get_detailed_data()
            detailed_data.append(data)
        except NotImplementedError:
            # 如果模块未实现详细数据接口，跳过
            continue
        except Exception as e:
            # 单个模块失败不影响整体
            print(f"Error loading detailed dashboard for {adapter.module_id}: {e}")
            continue

    return ResponseModel(data=detailed_data)


@router.get("/dashboard/modules", response_model=ResponseModel[List[DashboardModuleInfo]])
def list_dashboard_modules(
    role_code: Optional[str] = Query(None, description="按角色过滤"),
    current_user: User = Depends(security.get_current_active_user),
) -> ResponseModel[List[DashboardModuleInfo]]:
    """
    列出所有可用的dashboard模块

    Args:
        role_code: 可选的角色过滤
        current_user: 当前用户

    Returns:
        模块信息列表
    """
    modules = dashboard_registry.list_modules()

    if role_code:
        # 按角色过滤
        modules = [m for m in modules if role_code in m["supported_roles"]]

    # 转换为response格式
    module_infos = [
        DashboardModuleInfo(
            module_id=m["module_id"],
            module_name=m["module_name"],
            description=None,
            roles=m["supported_roles"],
            endpoint=f"/dashboard/unified/{{role_code}}/detailed?module_id={m['module_id']}",
            widgets=[],
            is_active=True,
        )
        for m in modules
    ]

    return ResponseModel(data=module_infos)


def _get_role_name(role_code: str) -> str:
    """获取角色中文名称"""
    role_names = {
        "sales": "销售",
        "engineer": "工程师",
        "procurement": "采购",
        "production": "生产",
        "pmo": "项目管理",
        "admin": "管理员",
        "business_support": "商务支持",
        "hr": "人事",
        "presales": "售前",
    }
    return role_names.get(role_code, role_code)
