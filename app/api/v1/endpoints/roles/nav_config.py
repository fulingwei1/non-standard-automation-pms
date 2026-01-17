# -*- coding: utf-8 -*-
"""
角色导航配置端点
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Role, User
from app.schemas.common import ResponseModel
from app.services.permission_audit_service import PermissionAuditService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/config/all", response_model=Dict[str, Any], status_code=status.HTTP_200_OK
)
def get_all_roles_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取所有角色的配置信息（供前端使用）

    返回格式：
    {
        "roles": {
            "role_code": {
                "name": "...",
                "dataScope": "...",
                "navGroups": [...],
                "uiConfig": {...}
            }
        }
    }
    """

    roles = db.query(Role).filter(Role.is_active == True).all()

    roles_config = {}
    for role in roles:
        # 构建角色配置
        role_config = {
            "name": role.role_name,
            "dataScope": role.data_scope,
            "description": role.description,
        }

        # 添加导航组配置
        if role.nav_groups:
            role_config["navGroups"] = role.nav_groups
        else:
            role_config["navGroups"] = []

        # 添加UI配置
        if role.ui_config:
            role_config["uiConfig"] = role.ui_config
        else:
            role_config["uiConfig"] = {}

        roles_config[role.role_code] = role_config

    return {"roles": roles_config}


@router.put(
    "/{role_id}/nav-groups",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def update_role_nav_groups(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    nav_groups: List[Dict[str, Any]],
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    更新角色的导航菜单配置

    - **role_id**: 角色ID
    - **nav_groups**: 导航组配置（JSON数组）

    nav_groups 格式示例：
    [
        {
            "label": "概览",
            "items": [
                {"name": "工作台", "path": "/workstation", "icon": "LayoutDashboard"}
            ]
        }
    ]
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 更新导航组配置
    role.nav_groups = nav_groups
    db.add(role)
    db.commit()

    # 记录审计日志
    try:
        PermissionAuditService.log_role_operation(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            action="NAV_GROUPS_UPDATED",
            changes={"nav_groups": nav_groups},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except Exception:
        logger.warning("审计日志记录失败（update_nav_groups），不影响主流程", exc_info=True)

    return ResponseModel(code=200, message="角色菜单配置更新成功")


@router.get(
    "/my/nav-groups", response_model=Dict[str, Any], status_code=status.HTTP_200_OK
)
def get_my_nav_groups(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的导航菜单组

    返回当前用户所属角色的导航菜单配置
    """
    try:
        logger.info(f"获取用户 {current_user.username} 的导航菜单")

        # 查询用户的角色（使用SQL避免ORM关系错误）
        user_roles_sql = """
            SELECT r.id, r.role_code, r.role_name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id
        """
        result = db.execute(text(user_roles_sql), {"user_id": current_user.id})
        roles = result.fetchall()

        if not roles:
            logger.warning(f"用户 {current_user.username} 没有分配角色")
            return {"nav_groups": [], "ui_config": {}}

        # 返回空菜单（前端使用默认菜单）
        # 如果需要从数据库读取，可以在这里添加逻辑
        logger.info(f"用户 {current_user.username} 有 {len(roles)} 个角色")
        return {"nav_groups": [], "ui_config": {}}

    except Exception as e:
        logger.error(f"获取导航菜单失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导航菜单失败: {str(e)}",
        )


@router.get(
    "/{role_id}/nav-groups",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
)
def get_role_nav_groups(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取角色的导航菜单配置

    - **role_id**: 角色ID
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    return {
        "role_id": role.id,
        "role_code": role.role_code,
        "role_name": role.role_name,
        "nav_groups": role.nav_groups or [],
    }
