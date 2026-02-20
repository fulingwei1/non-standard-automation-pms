# -*- coding: utf-8 -*-
"""
角色管理 API 端点

提供角色的 CRUD 操作、权限分配和导航配置功能。
支持多租户数据隔离。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.security import get_current_active_user, require_permission
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.role_management import RoleManagementService
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["角色管理"])


@router.get("/", response_model=ResponseModel)
def list_roles(
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色列表（自动过滤当前租户）"""
    service = RoleManagementService(db)
    result = service.list_roles_by_tenant(
        tenant_id=current_user.tenant_id,
        page=pagination.page,
        page_size=pagination.page_size,
        keyword=keyword,
        is_active=is_active,
    )
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/permissions", response_model=ResponseModel)
def list_permissions(
    module: Optional[str] = Query(None, description="模块筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取权限列表（使用新的 ApiPermission 模型）"""
    service = RoleManagementService(db)
    result = service.get_permissions_list(module=module)
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/templates", response_model=ResponseModel)
def list_role_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色模板列表"""
    service = RoleManagementService(db)
    result = service.get_role_templates()
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/config/all", response_model=ResponseModel)
def get_all_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取所有角色配置（按租户隔离）"""
    service = RoleManagementService(db)
    result = service.get_all_role_configs(tenant_id=current_user.tenant_id)
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/my/nav-groups", response_model=ResponseModel)
def get_my_nav_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的导航组配置"""
    service = RoleManagementService(db)
    nav_groups = service.get_user_nav_groups(user_id=current_user.id)
    return ResponseModel(
        code=200,
        message="获取成功",
        data={"nav_groups": nav_groups}
    )


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:create")),
):
    """创建角色"""
    service = RoleManagementService(db)
    role = service.create_role(
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        tenant_id=current_user.tenant_id,
        description=role_in.description,
        data_scope=role_in.data_scope or "OWN",
    )
    
    # 使用旧的 RoleService 格式化响应（保持兼容性）
    role_service = RoleService(db)
    return ResponseModel(
        code=201,
        message="创建成功",
        data=role_service._to_response(role).model_dump()
    )


@router.get("/{role_id}", response_model=ResponseModel)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色详情"""
    service = RoleManagementService(db)
    role = service.get_role_by_id(role_id, tenant_id=current_user.tenant_id)
    
    # 使用旧的 RoleService 格式化响应（保持兼容性）
    role_service = RoleService(db)
    return ResponseModel(
        code=200,
        message="获取成功",
        data=role_service._to_response(role).model_dump()
    )


@router.put("/{role_id}", response_model=ResponseModel)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """更新角色"""
    service = RoleManagementService(db)
    update_data = role_in.model_dump(exclude_unset=True)
    
    role = service.update_role(
        role_id=role_id,
        **update_data
    )
    
    # 使用旧的 RoleService 格式化响应（保持兼容性）
    role_service = RoleService(db)
    return ResponseModel(
        code=200,
        message="更新成功",
        data=role_service._to_response(role).model_dump()
    )


@router.delete("/{role_id}", response_model=ResponseModel)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:delete")),
):
    """删除角色"""
    service = RoleManagementService(db)
    service.delete_role(role_id)
    return ResponseModel(code=200, message="删除成功")


@router.put("/{role_id}/permissions", response_model=ResponseModel)
def update_role_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """更新角色权限（使用新的 RoleApiPermission 模型）"""
    service = RoleManagementService(db)
    service.update_role_permissions(
        role_id=role_id,
        permission_ids=permission_ids,
        tenant_id=current_user.tenant_id
    )
    return ResponseModel(code=200, message="权限更新成功")


@router.get("/{role_id}/nav-groups", response_model=ResponseModel)
def get_role_nav_groups(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的导航组配置"""
    service = RoleManagementService(db)
    nav_groups = service.get_role_nav_groups(role_id)
    return ResponseModel(
        code=200,
        message="获取成功",
        data={"nav_groups": nav_groups}
    )


@router.put("/{role_id}/nav-groups", response_model=ResponseModel)
def update_role_nav_groups(
    role_id: int,
    nav_groups: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """更新角色的导航组配置"""
    service = RoleManagementService(db)
    service.update_role_nav_groups(role_id, nav_groups)
    return ResponseModel(code=200, message="导航配置更新成功")


# ============================================================
# 角色层级管理 API
# ============================================================


@router.get("/hierarchy/tree", response_model=ResponseModel)
def get_role_hierarchy_tree(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色层级树（按租户隔离）"""
    service = RoleManagementService(db)
    tree = service.get_role_hierarchy_tree(tenant_id=current_user.tenant_id)
    return ResponseModel(code=200, message="获取成功", data=tree)


@router.put("/{role_id}/parent", response_model=ResponseModel)
def update_role_parent(
    role_id: int,
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """
    修改角色的父角色（层级关系）

    - parent_id 为 null 时，将角色设为顶级角色
    - 不允许形成循环引用
    """
    service = RoleManagementService(db)
    role = service.update_role_parent(role_id, parent_id)
    
    return ResponseModel(
        code=200,
        message="角色层级更新成功",
        data={
            "role_id": role.id,
            "parent_id": role.parent_id,
            "role_code": role.role_code,
            "role_name": role.role_name,
        },
    )


@router.get("/{role_id}/ancestors", response_model=ResponseModel)
def get_role_ancestors(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的所有祖先角色（继承链）"""
    service = RoleManagementService(db)
    ancestors = service.get_role_ancestors(role_id)
    
    # 获取角色信息
    role = service.get_role_by_id(role_id)
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "role_id": role.id,
            "role_code": role.role_code,
            "ancestors": ancestors
        },
    )


@router.get("/{role_id}/descendants", response_model=ResponseModel)
def get_role_descendants(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的所有子孙角色"""
    service = RoleManagementService(db)
    descendants = service.get_role_descendants(role_id)
    
    # 获取角色信息
    role = service.get_role_by_id(role_id)
    
    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "role_id": role.id,
            "role_code": role.role_code,
            "descendants": descendants,
        },
    )
