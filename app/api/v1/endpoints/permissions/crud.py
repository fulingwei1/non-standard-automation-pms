# -*- coding: utf-8 -*-
"""
权限管理 API 端点

提供权限的 CRUD 操作、角色权限关联和用户权限查询功能。
支持多租户数据隔离。
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.security import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.common import ResponseModel, PaginatedResponse
from app.services.permission_management import PermissionManagementService

router = APIRouter(prefix="/permissions", tags=["权限管理"])
logger = logging.getLogger(__name__)


# ============================================================
# 权限 CRUD API
# ============================================================


@router.get("/", response_model=ResponseModel)
def list_permissions(
    pagination: PaginationParams = Depends(get_pagination_query),
    module: Optional[str] = Query(None, description="模块筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:read")),
):
    """
    获取权限列表（支持多租户隔离）
    
    - 系统级权限（tenant_id=NULL）：所有租户可见
    - 租户级权限（tenant_id=N）：仅该租户可见
    """
    service = PermissionManagementService(db)
    result = service.list_permissions(
        tenant_id=current_user.tenant_id,
        page=pagination.page,
        page_size=pagination.page_size,
        module=module,
        action=action,
        keyword=keyword,
        is_active=is_active,
    )
    
    # 构建响应
    items = [
        {
            "id": p.id,
            "permission_code": p.perm_code,
            "permission_name": p.perm_name,
            "module": p.module,
            "page_code": p.page_code,
            "action": p.action,
            "description": p.description,
            "permission_type": p.permission_type,
            "is_active": p.is_active,
            "is_system": p.is_system,
            "tenant_id": p.tenant_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in result["items"]
    ]
    
    paginated_result = PaginatedResponse(
        items=items,
        total=result["total"],
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(result["total"] + pagination.page_size - 1) // pagination.page_size,
    )
    
    return ResponseModel(code=200, message="获取成功", data=paginated_result.model_dump())


@router.get("/modules", response_model=ResponseModel)
def list_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:read")),
):
    """获取所有权限模块列表（去重）"""
    service = PermissionManagementService(db)
    modules = service.list_modules(tenant_id=current_user.tenant_id)
    
    return ResponseModel(code=200, message="获取成功", data=modules)


@router.get("/{permission_id}", response_model=ResponseModel)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:read")),
):
    """获取权限详情"""
    service = PermissionManagementService(db)
    permission = service.get_permission(
        permission_id=permission_id,
        tenant_id=current_user.tenant_id,
    )
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在或无访问权限"
        )
    
    result = {
        "id": permission.id,
        "permission_code": permission.perm_code,
        "permission_name": permission.perm_name,
        "module": permission.module,
        "page_code": permission.page_code,
        "action": permission.action,
        "description": permission.description,
        "permission_type": permission.permission_type,
        "is_active": permission.is_active,
        "is_system": permission.is_system,
        "tenant_id": permission.tenant_id,
        "created_at": permission.created_at.isoformat() if permission.created_at else None,
        "updated_at": permission.updated_at.isoformat() if permission.updated_at else None,
    }
    
    return ResponseModel(code=200, message="获取成功", data=result)


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_permission(
    perm_code: str = Query(..., description="权限编码"),
    perm_name: str = Query(..., description="权限名称"),
    module: Optional[str] = Query(None, description="所属模块"),
    page_code: Optional[str] = Query(None, description="所属页面"),
    action: Optional[str] = Query(None, description="操作类型"),
    description: Optional[str] = Query(None, description="权限描述"),
    permission_type: str = Query("API", description="权限类型"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:create")),
):
    """
    创建权限（租户级）
    
    - 普通用户只能创建租户级权限
    - 超级管理员可以创建系统级权限（通过设置 tenant_id=NULL）
    """
    service = PermissionManagementService(db)
    
    # 检查权限编码是否已存在
    if service.check_permission_code_exists(perm_code, current_user.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"权限编码 {perm_code} 已存在"
        )
    
    # 创建权限
    permission = service.create_permission(
        tenant_id=current_user.tenant_id,
        perm_code=perm_code,
        perm_name=perm_name,
        module=module,
        page_code=page_code,
        action=action,
        description=description,
        permission_type=permission_type,
    )
    
    result = {
        "id": permission.id,
        "permission_code": permission.perm_code,
        "permission_name": permission.perm_name,
        "module": permission.module,
    }
    
    return ResponseModel(code=201, message="创建成功", data=result)


@router.put("/{permission_id}", response_model=ResponseModel)
def update_permission(
    permission_id: int,
    perm_name: Optional[str] = Query(None, description="权限名称"),
    module: Optional[str] = Query(None, description="所属模块"),
    page_code: Optional[str] = Query(None, description="所属页面"),
    action: Optional[str] = Query(None, description="操作类型"),
    description: Optional[str] = Query(None, description="权限描述"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:update")),
):
    """更新权限（不允许修改系统预置权限）"""
    service = PermissionManagementService(db)
    
    permission = service.get_permission(
        permission_id=permission_id,
        tenant_id=current_user.tenant_id,
    )
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在或无访问权限"
        )
    
    if permission.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统预置权限不允许修改"
        )
    
    # 更新权限
    permission = service.update_permission(
        permission=permission,
        perm_name=perm_name,
        module=module,
        page_code=page_code,
        action=action,
        description=description,
        is_active=is_active,
    )
    
    result = {
        "id": permission.id,
        "permission_code": permission.perm_code,
        "permission_name": permission.perm_name,
        "module": permission.module,
    }
    
    return ResponseModel(code=200, message="更新成功", data=result)


@router.delete("/{permission_id}", response_model=ResponseModel)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:delete")),
):
    """删除权限（不允许删除系统预置权限）"""
    service = PermissionManagementService(db)
    
    permission = service.get_permission(
        permission_id=permission_id,
        tenant_id=current_user.tenant_id,
    )
    
    # 注意：删除时需要严格限制只能删除自己租户的权限
    if not permission or permission.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在或无删除权限"
        )
    
    if permission.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统预置权限不允许删除"
        )
    
    # 检查是否有角色使用此权限
    role_count = service.count_roles_using_permission(permission_id)
    if role_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该权限被 {role_count} 个角色使用，无法删除"
        )
    
    service.delete_permission(permission)
    
    return ResponseModel(code=200, message="删除成功")


# ============================================================
# 角色权限关联 API
# ============================================================


@router.get("/roles/{role_id}", response_model=ResponseModel)
def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的所有权限"""
    service = PermissionManagementService(db)
    
    # 检查角色是否存在且可访问
    role = service.get_role(role_id=role_id, tenant_id=current_user.tenant_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在或无访问权限"
        )
    
    # 获取角色权限
    permissions = service.get_role_permissions(role_id)
    
    result = {
        "role_id": role_id,
        "role_code": role.role_code,
        "role_name": role.role_name,
        "permissions": [
            {
                "id": p.id,
                "permission_code": p.perm_code,
                "permission_name": p.perm_name,
                "module": p.module,
                "action": p.action,
            }
            for p in permissions
        ]
    }
    
    return ResponseModel(code=200, message="获取成功", data=result)


@router.post("/roles/{role_id}", response_model=ResponseModel)
def assign_role_permissions(
    role_id: int,
    permission_ids: List[int] = Query(..., description="权限ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """
    为角色分配权限（覆盖式更新）
    
    - 删除现有权限关联
    - 添加新的权限关联
    """
    service = PermissionManagementService(db)
    
    # 检查角色是否存在且可访问
    role = service.get_role(role_id=role_id, tenant_id=current_user.tenant_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在或无访问权限"
        )
    
    # 分配权限
    valid_count = service.assign_role_permissions(
        role_id=role_id,
        permission_ids=permission_ids,
        tenant_id=current_user.tenant_id,
    )
    
    # 清除权限缓存
    service.invalidate_permission_cache(role_id, current_user.tenant_id)
    
    return ResponseModel(
        code=200,
        message=f"权限分配成功，共分配 {valid_count} 个权限",
        data={"role_id": role_id, "assigned_count": valid_count}
    )


# ============================================================
# 用户权限查询 API
# ============================================================


@router.get("/users/{user_id}", response_model=ResponseModel)
def get_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user:read")),
):
    """
    获取用户的所有权限（通过角色继承）
    
    - 包含直接分配的角色权限
    - 支持角色继承（如果启用）
    - 返回去重后的权限列表
    """
    service = PermissionManagementService(db)
    
    # 检查用户是否存在
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 数据隔离：只能查询同租户的用户
    if not current_user.is_superuser and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查询其他租户的用户权限"
        )
    
    # 获取用户权限
    permissions = service.get_user_permissions(user_id, user.tenant_id)
    
    result = {
        "user_id": user_id,
        "username": user.username,
        "real_name": user.real_name,
        "permissions": [
            {
                "id": p.id,
                "permission_code": p.perm_code,
                "permission_name": p.perm_name,
                "module": p.module,
                "action": p.action,
            }
            for p in permissions
        ],
        "permission_count": len(permissions)
    }
    
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/users/{user_id}/check", response_model=ResponseModel)
def check_user_permission(
    user_id: int,
    permission_code: str = Query(..., description="权限编码"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user:read")),
):
    """
    检查用户是否有指定权限
    
    返回: { "has_permission": true/false }
    """
    service = PermissionManagementService(db)
    
    # 检查用户是否存在
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 数据隔离
    if not current_user.is_superuser and user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查询其他租户的用户权限"
        )
    
    # 检查权限
    has_permission = service.check_user_permission(
        user_id, permission_code, user, user.tenant_id
    )
    
    result = {
        "user_id": user_id,
        "permission_code": permission_code,
        "has_permission": has_permission
    }
    
    return ResponseModel(code=200, message="检查完成", data=result)
