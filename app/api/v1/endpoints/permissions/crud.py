# -*- coding: utf-8 -*-
"""
权限管理 API 端点

提供权限的 CRUD 操作、角色权限关联和用户权限查询功能。
支持多租户数据隔离。
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.security import get_current_active_user, require_permission
from app.models.user import (
    ApiPermission,
    Role,
    RoleApiPermission,
    User,
    UserRole,
)
from app.schemas.common import ResponseModel, PaginatedResponse
from app.services.permission_crud_service import PermissionCRUDService

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
    tenant_id = current_user.tenant_id
    
    query = db.query(ApiPermission).filter(
        or_(
            ApiPermission.tenant_id.is_(None),  # 系统级权限
            ApiPermission.tenant_id == tenant_id  # 租户级权限
        )
    )
    
    # 筛选条件
    if module:
        query = query.filter(ApiPermission.module == module)
    if action:
        query = query.filter(ApiPermission.action == action)
    if is_active is not None:
        query = query.filter(ApiPermission.is_active == is_active)
    if keyword:
        query = query.filter(
            or_(
                ApiPermission.perm_code.contains(keyword),
                ApiPermission.perm_name.contains(keyword),
                ApiPermission.description.contains(keyword),
            )
        )
    
    # 分页查询
    total = query.count()
    permissions = (
        query.order_by(ApiPermission.module, ApiPermission.perm_code)
        .offset((pagination.page - 1) * pagination.page_size)
        .limit(pagination.page_size)
        .all()
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
        for p in permissions
    ]
    
    result = PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=(total + pagination.page_size - 1) // pagination.page_size,
    )
    
    return ResponseModel(code=200, message="获取成功", data=result.model_dump())


@router.get("/modules", response_model=ResponseModel)
def list_modules(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:read")),
):
    """获取所有权限模块列表（去重）"""
    tenant_id = current_user.tenant_id
    
    modules = (
        db.query(ApiPermission.module)
        .filter(
            ApiPermission.module.isnot(None),
            or_(
                ApiPermission.tenant_id.is_(None),
                ApiPermission.tenant_id == tenant_id
            )
        )
        .distinct()
        .order_by(ApiPermission.module)
        .all()
    )
    
    result = [m[0] for m in modules if m[0]]
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/{permission_id}", response_model=ResponseModel)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("permission:read")),
):
    """获取权限详情"""
    tenant_id = current_user.tenant_id
    
    permission = db.query(ApiPermission).filter(
        ApiPermission.id == permission_id,
        or_(
            ApiPermission.tenant_id.is_(None),
            ApiPermission.tenant_id == tenant_id
        )
    ).first()
    
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
    tenant_id = current_user.tenant_id
    
    # 检查权限编码是否已存在（在当前租户或系统级）
    existing = db.query(ApiPermission).filter(
        ApiPermission.perm_code == perm_code,
        or_(
            ApiPermission.tenant_id.is_(None),
            ApiPermission.tenant_id == tenant_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"权限编码 {perm_code} 已存在"
        )
    
    # 创建权限
    permission = ApiPermission(
        tenant_id=tenant_id,  # 租户级权限
        perm_code=perm_code,
        perm_name=perm_name,
        module=module,
        page_code=page_code,
        action=action,
        description=description,
        permission_type=permission_type,
        is_active=True,
        is_system=False,
    )
    
    db.add(permission)
    db.commit()
    db.refresh(permission)
    
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
    tenant_id = current_user.tenant_id
    
    permission = db.query(ApiPermission).filter(
        ApiPermission.id == permission_id,
        or_(
            ApiPermission.tenant_id.is_(None),
            ApiPermission.tenant_id == tenant_id
        )
    ).first()
    
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
    
    # 更新字段
    if perm_name is not None:
        permission.perm_name = perm_name
    if module is not None:
        permission.module = module
    if page_code is not None:
        permission.page_code = page_code
    if action is not None:
        permission.action = action
    if description is not None:
        permission.description = description
    if is_active is not None:
        permission.is_active = is_active
    
    db.commit()
    db.refresh(permission)
    
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
    tenant_id = current_user.tenant_id
    
    permission = db.query(ApiPermission).filter(
        ApiPermission.id == permission_id,
        ApiPermission.tenant_id == tenant_id  # 只能删除自己租户的权限
    ).first()
    
    if not permission:
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
    role_count = db.query(RoleApiPermission).filter(
        RoleApiPermission.permission_id == permission_id
    ).count()
    
    if role_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该权限被 {role_count} 个角色使用，无法删除"
        )
    
    db.delete(permission)
    db.commit()
    
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
    tenant_id = current_user.tenant_id
    
    # 检查角色是否存在且可访问
    role = db.query(Role).filter(
        Role.id == role_id,
        or_(
            Role.tenant_id.is_(None),
            Role.tenant_id == tenant_id
        )
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在或无访问权限"
        )
    
    # 获取角色权限
    permissions = (
        db.query(ApiPermission)
        .join(RoleApiPermission, RoleApiPermission.permission_id == ApiPermission.id)
        .filter(RoleApiPermission.role_id == role_id)
        .filter(ApiPermission.is_active)
        .order_by(ApiPermission.module, ApiPermission.perm_code)
        .all()
    )
    
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
    tenant_id = current_user.tenant_id
    
    # 检查角色是否存在且可访问
    role = db.query(Role).filter(
        Role.id == role_id,
        or_(
            Role.tenant_id.is_(None),
            Role.tenant_id == tenant_id
        )
    ).first()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在或无访问权限"
        )
    
    # 删除现有权限关联
    db.query(RoleApiPermission).filter(
        RoleApiPermission.role_id == role_id
    ).delete()
    
    # 验证权限ID并添加新的关联
    valid_count = 0
    for perm_id in permission_ids:
        permission = db.query(ApiPermission).filter(
            ApiPermission.id == perm_id,
            or_(
                ApiPermission.tenant_id.is_(None),
                ApiPermission.tenant_id == tenant_id
            )
        ).first()
        
        if permission:
            db.add(RoleApiPermission(role_id=role_id, permission_id=perm_id))
            valid_count += 1
    
    db.commit()
    
    # 清除权限缓存
    try:
        from app.services.permission_cache_service import get_permission_cache_service
        cache_service = get_permission_cache_service()
        cache_service.invalidate_role_and_users(role_id, tenant_id=tenant_id)
    except Exception as e:
        logger.warning(f"清除权限缓存失败: {e}")
    
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
    tenant_id = current_user.tenant_id
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 数据隔离：只能查询同租户的用户
    if not current_user.is_superuser and user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查询其他租户的用户权限"
        )
    
    # 使用 PermissionService 获取用户权限
    from app.services.permission_service import PermissionService
    
    permission_codes = PermissionService.get_user_permissions(
        db, user_id, user.tenant_id
    )
    
    # 获取权限详情
    permissions = (
        db.query(ApiPermission)
        .filter(
            ApiPermission.perm_code.in_(permission_codes),
            ApiPermission.is_active
        )
        .order_by(ApiPermission.module, ApiPermission.perm_code)
        .all()
    )
    
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
    tenant_id = current_user.tenant_id
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 数据隔离
    if not current_user.is_superuser and user.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查询其他租户的用户权限"
        )
    
    # 使用 PermissionService 检查权限
    from app.services.permission_service import PermissionService
    
    has_permission = PermissionService.check_permission(
        db, user_id, permission_code, user, user.tenant_id
    )
    
    result = {
        "user_id": user_id,
        "permission_code": permission_code,
        "has_permission": has_permission
    }
    
    return ResponseModel(code=200, message="检查完成", data=result)
