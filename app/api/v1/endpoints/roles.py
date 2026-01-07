# -*- coding: utf-8 -*-
"""
角色管理 API endpoints
"""
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import Role, Permission, RolePermission, User
from app.schemas.auth import RoleCreate, RoleUpdate, RoleResponse, PermissionResponse
from app.schemas.common import ResponseModel, PaginatedResponse
from app.services.permission_audit_service import PermissionAuditService
from fastapi import Request

router = APIRouter()


class RoleListResponse(PaginatedResponse):
    """角色列表响应"""
    items: List[RoleResponse]


@router.get("/", response_model=RoleListResponse, status_code=status.HTTP_200_OK)
def read_roles(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索（角色编码/名称）"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取角色列表（支持分页和筛选）
    
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，默认20，最大100
    - **keyword**: 关键词搜索（角色编码/名称）
    - **is_active**: 是否启用筛选
    """
    query = db.query(Role)
    
    # 关键词搜索
    if keyword:
        query = query.filter(
            or_(
                Role.role_code.like(f"%{keyword}%"),
                Role.role_name.like(f"%{keyword}%"),
            )
        )
    
    # 启用状态筛选
    if is_active is not None:
        query = query.filter(Role.is_active == is_active)
    
    # 计算总数
    total = query.count()
    
    # 分页
    offset = (page - 1) * page_size
    roles = query.order_by(Role.sort_order.asc(), Role.created_at.desc()).offset(offset).limit(page_size).all()
    
    # 设置权限列表
    for r in roles:
        r.permissions = [rp.permission.permission_name for rp in r.permissions]
    
    return RoleListResponse(
        items=roles,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
def read_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取角色详情
    
    - **role_id**: 角色ID
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    # 设置权限列表
    role.permissions = [rp.permission.permission_name for rp in role.permissions]
    
    return role


@router.post("/", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_CREATE")),
) -> Any:
    """
    创建新角色
    
    - **role_in**: 角色创建数据
    """
    role = db.query(Role).filter(Role.role_code == role_in.role_code).first()
    if role:
        raise HTTPException(
            status_code=400,
            detail="该角色编码已存在",
        )

    role = Role(
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        description=role_in.description,
        data_scope=role_in.data_scope,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    if role_in.permission_ids:
        for p_id in role_in.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))
        db.commit()
        db.refresh(role)
    
    # 设置权限列表
    role.permissions = [rp.permission.permission_name for rp in role.permissions]

    # 记录审计日志
    try:
        PermissionAuditService.log_role_operation(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            action=PermissionAuditService.ACTION_ROLE_CREATED,
            changes={
                "role_code": role.role_code,
                "role_name": role.role_name,
                "data_scope": role.data_scope,
                "permission_ids": role_in.permission_ids
            },
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程

    return role


@router.put("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    role_in: RoleUpdate,
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    更新角色信息
    
    - **role_id**: 角色ID
    - **role_in**: 角色更新数据
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统预置角色不允许修改")

    # 记录变更前的状态
    old_is_active = role.is_active
    old_data = {
        "role_name": role.role_name,
        "description": role.description,
        "data_scope": role.data_scope,
        "is_active": role.is_active
    }

    update_data = role_in.model_dump(exclude_unset=True)
    permission_ids = None
    
    # 处理权限分配
    if "permission_ids" in update_data:
        permission_ids = update_data.pop("permission_ids")
        # 删除原有权限关联
        db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
        # 添加新权限关联
        for p_id in permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=p_id))

    # 更新其他字段
    for field, value in update_data.items():
        setattr(role, field, value)

    db.add(role)
    db.commit()
    db.refresh(role)
    
    # 设置权限列表
    role.permissions = [rp.permission.permission_name for rp in role.permissions]

    # 记录审计日志
    try:
        changes = {k: v for k, v in update_data.items() if k in old_data and old_data[k] != v}
        if permission_ids is not None:
            changes["permission_ids"] = permission_ids
        
        # 检查状态变更
        if old_is_active != role.is_active:
            action = PermissionAuditService.ACTION_ROLE_ACTIVATED if role.is_active else PermissionAuditService.ACTION_ROLE_DEACTIVATED
        else:
            action = PermissionAuditService.ACTION_ROLE_UPDATED
        
        PermissionAuditService.log_role_operation(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            action=action,
            changes=changes,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程
    
    return role


@router.put("/{role_id}/permissions", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def assign_role_permissions(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    permission_ids: List[int],
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    分配角色权限
    
    - **role_id**: 角色ID
    - **permission_ids**: 权限ID列表
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    if role.is_system:
        raise HTTPException(status_code=400, detail="系统预置角色不允许修改权限")
    
    # 验证权限是否存在
    permissions = db.query(Permission).filter(Permission.id.in_(permission_ids)).all()
    if len(permissions) != len(permission_ids):
        raise HTTPException(status_code=400, detail="部分权限不存在")
    
    # 删除原有权限关联
    db.query(RolePermission).filter(RolePermission.role_id == role.id).delete()
    
    # 添加新权限关联
    for permission_id in permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=permission_id))
    
    db.commit()
    
    # 记录审计日志
    try:
        PermissionAuditService.log_role_permission_assignment(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            permission_ids=permission_ids,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程
    
    return ResponseModel(
        code=200,
        message="角色权限分配成功"
    )


@router.get("/permissions", response_model=List[PermissionResponse], status_code=status.HTTP_200_OK)
def read_permissions(
    db: Session = Depends(deps.get_db),
    module: Optional[str] = Query(None, description="模块筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取所有可用权限列表
    
    - **module**: 模块筛选（可选）
    """
    query = db.query(Permission).filter(Permission.is_active == True)
    
    if module:
        query = query.filter(Permission.module == module)
    
    return query.order_by(Permission.module.asc(), Permission.permission_code.asc()).all()


@router.get("/config/all", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
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
    from typing import Dict, Any
    
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
