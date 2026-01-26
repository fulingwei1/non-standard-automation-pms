# -*- coding: utf-8 -*-
"""
角色管理 API 端点

提供角色的 CRUD 操作、权限分配和导航配置功能。
支持多租户数据隔离。
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.user import Permission, Role, RolePermission, RoleTemplate, User, UserRole
from app.schemas.common import ResponseModel
from app.schemas.auth import RoleCreate, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["角色管理"])


def get_current_tenant_id(current_user: User) -> Optional[int]:
    """获取当前用户的租户ID"""
    return current_user.tenant_id


def require_role_management_permission(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """要求角色管理权限（超级管理员或租户管理员）"""
    if current_user.is_superuser or current_user.is_tenant_admin:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="需要角色管理权限"
    )


@router.get("/", response_model=ResponseModel)
def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取角色列表（自动过滤当前租户）"""
    service = RoleService(db)
    result = service.list_roles(
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active,
    )
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/permissions", response_model=ResponseModel)
def list_permissions(
    module: Optional[str] = Query(None, description="模块筛选"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取权限列表"""
    query = db.query(Permission)
    if module:
        query = query.filter(Permission.module == module)

    permissions = query.order_by(Permission.module, Permission.permission_code).all()

    result = [
        {
            "id": p.id,
            "permission_code": p.permission_code,
            "permission_name": p.permission_name,
            "module": p.module,
            "action": p.action,
        }
        for p in permissions
    ]
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/templates", response_model=ResponseModel)
def list_role_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management_permission),
):
    """获取角色模板列表"""
    templates = db.query(RoleTemplate).filter(RoleTemplate.is_active == True).order_by(RoleTemplate.sort_order).all()

    result = [
        {
            "id": t.id,
            "role_code": t.role_code,
            "role_name": t.role_name,
            "description": t.description,
            "data_scope": t.data_scope,
            "permission_codes": t.permission_codes,
        }
        for t in templates
    ]
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/config/all", response_model=ResponseModel)
def get_all_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取所有角色配置"""
    roles = db.query(Role).filter(Role.is_active == True).order_by(Role.sort_order).all()

    result = []
    for role in roles:
        result.append({
            "id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "data_scope": role.data_scope,
            "nav_groups": role.nav_groups,
            "ui_config": role.ui_config,
        })

    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/my/nav-groups", response_model=ResponseModel)
def get_my_nav_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的导航组配置"""
    # 获取用户的所有角色
    user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    role_ids = [ur.role_id for ur in user_roles]

    if not role_ids:
        return ResponseModel(code=200, message="获取成功", data={"nav_groups": []})

    # 获取角色的导航配置
    roles = db.query(Role).filter(Role.id.in_(role_ids), Role.is_active == True).all()

    # 合并导航组
    merged_nav_groups = []
    seen_labels = set()

    for role in roles:
        if role.nav_groups:
            for group in role.nav_groups:
                label = group.get("label", "")
                if label not in seen_labels:
                    merged_nav_groups.append(group)
                    seen_labels.add(label)

    return ResponseModel(code=200, message="获取成功", data={"nav_groups": merged_nav_groups})


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management_permission),
):
    """创建角色"""
    # 检查角色编码是否已存在
    existing = db.query(Role).filter(Role.role_code == role_in.role_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色编码 {role_in.role_code} 已存在"
        )

    role = Role(
        tenant_id=current_user.tenant_id,
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        description=role_in.description,
        data_scope=role_in.data_scope or "OWN",
        is_active=True,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    service = RoleService(db)
    return ResponseModel(
        code=201,
        message="创建成功",
        data=service._to_response(role).model_dump()
    )


@router.get("/{role_id}", response_model=ResponseModel)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    service = RoleService(db)
    return ResponseModel(code=200, message="获取成功", data=service._to_response(role).model_dump())


@router.put("/{role_id}", response_model=ResponseModel)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management_permission),
):
    """更新角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 系统预置角色不允许修改编码
    if role.is_system and role_in.role_code and role_in.role_code != role.role_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统预置角色不允许修改编码"
        )

    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    service = RoleService(db)
    return ResponseModel(code=200, message="更新成功", data=service._to_response(role).model_dump())


@router.delete("/{role_id}", response_model=ResponseModel)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management_permission),
):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="系统预置角色不允许删除"
        )

    # 检查是否有用户使用此角色
    user_count = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该角色下有 {user_count} 个用户，无法删除"
        )

    db.delete(role)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


@router.put("/{role_id}/permissions", response_model=ResponseModel)
def update_role_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management_permission),
):
    """更新角色权限"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 删除现有权限
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()

    # 添加新权限
    for perm_id in permission_ids:
        perm = db.query(Permission).filter(Permission.id == perm_id).first()
        if perm:
            db.add(RolePermission(role_id=role_id, permission_id=perm_id))

    db.commit()

    return ResponseModel(code=200, message="权限更新成功")


@router.get("/{role_id}/nav-groups", response_model=ResponseModel)
def get_role_nav_groups(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取角色的导航组配置"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    return ResponseModel(
        code=200,
        message="获取成功",
        data={"nav_groups": role.nav_groups or []}
    )


@router.put("/{role_id}/nav-groups", response_model=ResponseModel)
def update_role_nav_groups(
    role_id: int,
    nav_groups: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management_permission),
):
    """更新角色的导航组配置"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    role.nav_groups = nav_groups
    db.commit()

    return ResponseModel(code=200, message="导航配置更新成功")
