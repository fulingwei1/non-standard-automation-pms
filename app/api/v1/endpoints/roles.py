# -*- coding: utf-8 -*-
"""角色管理 API。"""

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.schemas import success_response
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from app.schemas.role import (
    CreateRoleFromTemplate,
    RoleCreate,
    RoleTemplateCreate,
    RoleTemplateUpdate,
    RoleUpdate,
    SaveRoleAsTemplate,
)
from app.services.role_management.service import RoleManagementService
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["角色管理"])


def _role_to_dict(db: Session, role: Role) -> dict[str, Any]:
    return RoleService(db)._to_response(role).model_dump(mode="json")


def _ensure_role(db: Session, role_id: int) -> Role:
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return role


def _can_access_all_roles(user: User) -> bool:
    return bool(getattr(user, "is_superuser", False) or security.is_system_admin(user))


def _role_read_scope(current_user: User):
    if _can_access_all_roles(current_user):
        return None
    if current_user.tenant_id is None:
        return Role.tenant_id.is_(None)
    return or_(Role.tenant_id.is_(None), Role.tenant_id == current_user.tenant_id)


def _role_write_scope(current_user: User):
    if _can_access_all_roles(current_user):
        return None
    if current_user.tenant_id is None:
        return Role.tenant_id.is_(None)
    return Role.tenant_id == current_user.tenant_id


def _permission_read_scope(current_user: User):
    if _can_access_all_roles(current_user):
        return None
    if current_user.tenant_id is None:
        return ApiPermission.tenant_id.is_(None)
    return or_(ApiPermission.tenant_id.is_(None), ApiPermission.tenant_id == current_user.tenant_id)


def _scoped_role_query(db: Session, current_user: User, *, writable: bool = False):
    query = db.query(Role)
    scope = _role_write_scope(current_user) if writable else _role_read_scope(current_user)
    if scope is not None:
        query = query.filter(scope)
    return query


def _ensure_role_visible(db: Session, role_id: int, current_user: User) -> Role:
    role = _scoped_role_query(db, current_user).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return role


def _ensure_role_writable(db: Session, role_id: int, current_user: User) -> Role:
    role = _scoped_role_query(db, current_user, writable=True).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
    return role


def _ensure_parent_role_visible(
    db: Session,
    parent_id: int,
    current_user: User,
    *,
    child_role_id: int,
) -> Role:
    if parent_id == child_role_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父角色不能是自己")

    parent = _scoped_role_query(db, current_user).filter(Role.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="父角色不存在")
    return parent


def _replace_role_permissions(
    db: Session,
    role_id: int,
    permission_ids: list[int],
    current_user: User | None = None,
) -> None:
    db.query(RoleApiPermission).filter(RoleApiPermission.role_id == role_id).delete()
    if not permission_ids:
        return

    query = db.query(ApiPermission).filter(ApiPermission.id.in_(permission_ids))
    if current_user is not None:
        scope = _permission_read_scope(current_user)
        if scope is not None:
            query = query.filter(scope)
    permissions = query.all()
    found_ids = {permission.id for permission in permissions}
    missing_ids = sorted(set(permission_ids) - found_ids)
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"权限不存在: {missing_ids}",
        )

    for permission_id in sorted(found_ids):
        db.add(RoleApiPermission(role_id=role_id, permission_id=permission_id))


def _permission_codes_for_role(db: Session, role_id: int) -> list[str]:
    rows = (
        db.query(ApiPermission.perm_code)
        .join(RoleApiPermission, RoleApiPermission.permission_id == ApiPermission.id)
        .filter(RoleApiPermission.role_id == role_id, ApiPermission.is_active.is_(True))
        .order_by(ApiPermission.module.asc(), ApiPermission.perm_code.asc())
        .all()
    )
    return [row[0] for row in rows if row[0]]


def _role_user_ids(db: Session, role_id: int) -> list[int]:
    return [row[0] for row in db.query(UserRole.user_id).filter(UserRole.role_id == role_id).all()]


def _invalidate_role_permission_cache(
    *,
    db: Session,
    role_id: int,
    tenant_id: int | None,
    user_ids: list[int],
) -> None:
    try:
        from app.core.permission_engine import bump_permission_cache_revision
        from app.services.permission_cache_service import get_permission_cache_service

        bump_permission_cache_revision(db, tenant_id)
        get_permission_cache_service().invalidate_role_and_users(
            role_id,
            user_ids=user_ids,
            tenant_id=tenant_id,
        )
    except Exception:
        # Cache invalidation must not roll back the role update itself.
        pass


def _require_role_assign_permission(current_user: User, db: Session) -> None:
    if security.check_permission(current_user, "role:assign", db):
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="权限不足: role:assign",
    )


@router.get("/", status_code=status.HTTP_200_OK)
def list_roles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    keyword: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    service = RoleService(db)
    result = service.list_roles(
        page=page,
        page_size=page_size,
        keyword=keyword,
        is_active=is_active,
        tenant_id=current_user.tenant_id,
        include_all_tenants=_can_access_all_roles(current_user),
    )
    result["items"] = [item.model_dump(mode="json") for item in result["items"]]
    return success_response(data=result, message="获取角色列表成功")


@router.get("/permissions", status_code=status.HTTP_200_OK)
def list_role_permissions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    query = db.query(ApiPermission)
    scope = _permission_read_scope(current_user)
    if scope is not None:
        query = query.filter(scope)
    permissions = query.order_by(ApiPermission.module.asc(), ApiPermission.perm_code.asc()).all()
    items = [
        {
            "id": permission.id,
            "permission_code": permission.perm_code,
            "permission_name": permission.perm_name,
            "perm_code": permission.perm_code,
            "perm_name": permission.perm_name,
            "module": permission.module,
            "action": permission.action,
            "description": permission.description,
            "is_active": bool(permission.is_active),
            "is_system": bool(permission.is_system),
        }
        for permission in permissions
    ]
    return success_response(data=items, message="获取权限列表成功")


@router.get("/templates", status_code=status.HTTP_200_OK)
def list_role_templates(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    include_all = _can_access_all_roles(current_user)
    data = RoleManagementService(db).get_role_templates(
        tenant_id=current_user.tenant_id,
        include_all_tenants=include_all,
    )
    return success_response(data=data, message="获取角色模板成功")


@router.post("/templates/", status_code=status.HTTP_201_CREATED)
def create_role_template(
    template_in: RoleTemplateCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:create")),
) -> Any:
    if template_in.permission_codes:
        _require_role_assign_permission(current_user, db)
    include_all = _can_access_all_roles(current_user)
    payload = template_in.model_dump()
    if not include_all:
        payload["tenant_id"] = current_user.tenant_id
    data = RoleManagementService(db).create_template(**payload)
    return success_response(data=data, message="创建角色模板成功", code=201)


@router.get("/templates/{template_id}", status_code=status.HTTP_200_OK)
def get_role_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    include_all = _can_access_all_roles(current_user)
    data = RoleManagementService(db).get_template_detail(
        template_id,
        tenant_id=current_user.tenant_id,
        include_all_tenants=include_all,
    )
    return success_response(data=data, message="获取角色模板成功")


@router.put("/templates/{template_id}", status_code=status.HTTP_200_OK)
def update_role_template(
    template_id: int,
    template_in: RoleTemplateUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:update")),
) -> Any:
    payload = template_in.model_dump(exclude_unset=True)
    if "permission_codes" in payload:
        _require_role_assign_permission(current_user, db)
    include_all = _can_access_all_roles(current_user)
    data = RoleManagementService(db).update_template(
        template_id,
        tenant_id=current_user.tenant_id,
        include_all_tenants=include_all,
        **payload,
    )
    return success_response(data=data, message="更新角色模板成功")


@router.delete("/templates/{template_id}", status_code=status.HTTP_200_OK)
def delete_role_template(
    template_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:delete")),
) -> Any:
    include_all = _can_access_all_roles(current_user)
    RoleManagementService(db).delete_template(
        template_id,
        tenant_id=current_user.tenant_id,
        include_all_tenants=include_all,
    )
    return success_response(data={"id": template_id}, message="删除角色模板成功")


@router.post("/templates/{template_id}/create-role", status_code=status.HTTP_201_CREATED)
def create_role_from_template(
    template_id: int,
    role_in: CreateRoleFromTemplate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:create")),
) -> Any:
    service = RoleManagementService(db)
    include_all = _can_access_all_roles(current_user)
    template = service.get_template_detail(
        template_id,
        tenant_id=current_user.tenant_id,
        include_all_tenants=include_all,
    )
    if template.get("permission_codes"):
        _require_role_assign_permission(current_user, db)
    role = service.create_role_from_template(
        template_id,
        role_code=role_in.role_code,
        role_name=role_in.role_name,
        tenant_id=current_user.tenant_id,
        description=role_in.description,
        include_all_tenants=include_all,
    )
    return success_response(data=_role_to_dict(db, role), message="从模板创建角色成功", code=201)


@router.get("/config/all", status_code=status.HTTP_200_OK)
def get_all_role_config(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    roles = _scoped_role_query(db, current_user).order_by(Role.sort_order.asc(), Role.id.asc()).all()
    return success_response(
        data={"roles": [_role_to_dict(db, role) for role in roles]},
        message="获取角色配置成功",
    )


@router.get("/my/nav-groups", status_code=status.HTTP_200_OK)
def get_my_nav_groups(
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    groups: list[dict[str, Any]] = []
    try:
        user_roles = current_user.roles.all() if hasattr(current_user.roles, "all") else []
        for user_role in user_roles:
            nav_groups = getattr(user_role.role, "nav_groups", None) or []
            if isinstance(nav_groups, list):
                groups.extend(nav_groups)
    except Exception:
        groups = []
    return success_response(data=groups, message="获取导航组成功")


@router.get("/hierarchy/tree", status_code=status.HTTP_200_OK)
def get_role_hierarchy_tree(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    roles = _scoped_role_query(db, current_user).order_by(Role.sort_order.asc(), Role.id.asc()).all()
    by_parent: dict[int | None, list[Role]] = {}
    for role in roles:
        by_parent.setdefault(role.parent_id, []).append(role)

    def build_nodes(parent_id: int | None = None) -> list[dict[str, Any]]:
        return [
            {
                **_role_to_dict(db, role),
                "children": build_nodes(role.id),
            }
            for role in by_parent.get(parent_id, [])
        ]

    return success_response(data=build_nodes(), message="获取角色层级成功")


@router.post("/compare", status_code=status.HTTP_200_OK)
def compare_roles(
    role_ids: list[int] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    unique_role_ids = list(dict.fromkeys(role_ids))
    if len(unique_role_ids) < 2:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="至少选择两个角色比较")

    roles = [_ensure_role_visible(db, role_id, current_user) for role_id in unique_role_ids]
    role_permissions = {
        role.id: _permission_codes_for_role(db, role.id)
        for role in roles
    }
    permission_sets = [set(codes) for codes in role_permissions.values()]
    common_permissions = sorted(set.intersection(*permission_sets)) if permission_sets else []
    common_set = set(common_permissions)

    data = {
        "roles": [
            {
                "role_id": role.id,
                "role_code": role.role_code,
                "role_name": role.role_name,
                "permissions": role_permissions[role.id],
            }
            for role in roles
        ],
        "common_permissions": common_permissions,
        "diff_permissions": {
            str(role.id): sorted(set(role_permissions[role.id]) - common_set)
            for role in roles
        },
    }
    return success_response(data=data, message="角色权限比较成功")


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:create")),
) -> Any:
    exists = db.query(Role).filter(Role.role_code == role_in.role_code).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色编码已存在")
    if role_in.permission_ids:
        _require_role_assign_permission(current_user, db)

    payload = role_in.model_dump(exclude={"permission_ids"}, exclude_unset=True)
    if not _can_access_all_roles(current_user):
        payload["tenant_id"] = current_user.tenant_id
    if payload.get("parent_id") is not None:
        _ensure_parent_role_visible(
            db,
            payload["parent_id"],
            current_user,
            child_role_id=0,
        )
    role = Role(**payload)
    db.add(role)
    db.flush()
    _replace_role_permissions(db, role.id, role_in.permission_ids or [], current_user)
    db.commit()
    db.refresh(role)
    return success_response(data=_role_to_dict(db, role), message="创建角色成功", code=201)


@router.post("/{role_id}/save-as-template", status_code=status.HTTP_201_CREATED)
def save_role_as_template(
    role_id: int,
    template_in: SaveRoleAsTemplate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:create")),
) -> Any:
    include_all = _can_access_all_roles(current_user)
    _ensure_role_visible(db, role_id, current_user)
    if _permission_codes_for_role(db, role_id):
        _require_role_assign_permission(current_user, db)
    data = RoleManagementService(db).save_role_as_template(
        role_id,
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        description=template_in.description,
        tenant_id=current_user.tenant_id,
        include_all_tenants=include_all,
    )
    return success_response(data=data, message="角色另存模板成功", code=201)


@router.get("/{role_id}", status_code=status.HTTP_200_OK)
def get_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    role = _ensure_role_visible(db, role_id, current_user)
    return success_response(data=_role_to_dict(db, role), message="获取角色成功")


@router.put("/{role_id}", status_code=status.HTTP_200_OK)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:update")),
) -> Any:
    role = _ensure_role_writable(db, role_id, current_user)
    payload = role_in.model_dump(exclude={"permission_ids"}, exclude_unset=True)
    permissions_changed = role_in.permission_ids is not None
    if permissions_changed:
        _require_role_assign_permission(current_user, db)
    affected_user_ids = _role_user_ids(db, role_id) if permissions_changed else []
    if "role_code" in payload:
        exists = (
            db.query(Role)
            .filter(Role.role_code == payload["role_code"], Role.id != role_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="角色编码已存在")
    if "parent_id" in payload and payload["parent_id"] is not None:
        _ensure_parent_role_visible(
            db,
            payload["parent_id"],
            current_user,
            child_role_id=role_id,
        )

    for field, value in payload.items():
        setattr(role, field, value)
    if permissions_changed:
        _replace_role_permissions(db, role.id, role_in.permission_ids, current_user)
    db.commit()
    db.refresh(role)
    if permissions_changed:
        _invalidate_role_permission_cache(
            db=db,
            role_id=role.id,
            tenant_id=role.tenant_id,
            user_ids=affected_user_ids,
        )
    return success_response(data=_role_to_dict(db, role), message="更新角色成功")


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
def delete_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:delete")),
) -> Any:
    from app.services.session_service import SessionService

    role = _ensure_role_writable(db, role_id, current_user)
    role_tenant_id = role.tenant_id
    affected_user_ids = _role_user_ids(db, role.id)
    db.query(RoleApiPermission).filter(RoleApiPermission.role_id == role.id).delete(
        synchronize_session=False
    )
    db.query(UserRole).filter(UserRole.role_id == role.id).delete(synchronize_session=False)
    db.query(Role).filter(Role.id == role.id).delete(synchronize_session=False)
    db.commit()

    _invalidate_role_permission_cache(
        db=db,
        role_id=role_id,
        tenant_id=role_tenant_id,
        user_ids=affected_user_ids,
    )
    revoked_session_count = 0
    for user_id in affected_user_ids:
        revoked_session_count += SessionService.revoke_all_sessions(db, user_id)

    return success_response(
        data={
            "id": role_id,
            "affected_user_count": len(affected_user_ids),
            "revoked_session_count": revoked_session_count,
        },
        message="删除角色成功",
    )


@router.put("/{role_id}/permissions", status_code=status.HTTP_200_OK)
def update_role_permissions(
    role_id: int,
    payload: dict[str, list[int]],
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:assign")),
) -> Any:
    role = _ensure_role_writable(db, role_id, current_user)
    affected_user_ids = _role_user_ids(db, role_id)
    permission_ids = payload.get("permission_ids") or []
    _replace_role_permissions(db, role_id, permission_ids, current_user)
    db.commit()
    role = _ensure_role_visible(db, role_id, current_user)
    _invalidate_role_permission_cache(
        db=db,
        role_id=role.id,
        tenant_id=role.tenant_id,
        user_ids=affected_user_ids,
    )
    return success_response(data=_role_to_dict(db, role), message="更新角色权限成功")


@router.get("/{role_id}/nav-groups", status_code=status.HTTP_200_OK)
def get_role_nav_groups(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    role = _ensure_role_visible(db, role_id, current_user)
    return success_response(data=role.nav_groups or [], message="获取角色导航组成功")


@router.put("/{role_id}/nav-groups", status_code=status.HTTP_200_OK)
def update_role_nav_groups(
    role_id: int,
    nav_groups: list[dict[str, Any]] | None = Body(default=None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:update")),
) -> Any:
    role = _ensure_role_writable(db, role_id, current_user)
    role.nav_groups = nav_groups or []
    db.commit()
    db.refresh(role)
    return success_response(data=role.nav_groups or [], message="更新角色导航组成功")


@router.get("/{role_id}/ancestors", status_code=status.HTTP_200_OK)
def get_role_ancestors(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    role = _ensure_role_visible(db, role_id, current_user)
    ancestors = []
    parent_id = role.parent_id
    parent = (
        _scoped_role_query(db, current_user).filter(Role.id == parent_id).first()
        if parent_id is not None
        else None
    )
    while parent:
        ancestors.append(_role_to_dict(db, parent))
        parent_id = parent.parent_id
        parent = (
            _scoped_role_query(db, current_user).filter(Role.id == parent_id).first()
            if parent_id is not None
            else None
        )
    return success_response(data={"role_id": role_id, "ancestors": ancestors}, message="获取成功")


@router.get("/{role_id}/descendants", status_code=status.HTTP_200_OK)
def get_role_descendants(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:read")),
) -> Any:
    _ensure_role_visible(db, role_id, current_user)
    roles = _scoped_role_query(db, current_user).order_by(Role.sort_order.asc(), Role.id.asc()).all()
    by_parent: dict[int | None, list[Role]] = {}
    for role in roles:
        by_parent.setdefault(role.parent_id, []).append(role)

    def collect(parent_id: int) -> list[dict[str, Any]]:
        descendants = []
        for child in by_parent.get(parent_id, []):
            child_data = _role_to_dict(db, child)
            child_descendants = collect(child.id)
            child_data["children"] = child_descendants
            descendants.append(child_data)
        return descendants

    return success_response(
        data={"role_id": role_id, "descendants": collect(role_id)},
        message="获取成功",
    )


@router.put("/{role_id}/parent", status_code=status.HTTP_200_OK)
def update_role_parent(
    role_id: int,
    parent_id: Optional[int] = Query(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("role:update")),
) -> Any:
    role = _ensure_role_writable(db, role_id, current_user)
    if parent_id is not None:
        _ensure_parent_role_visible(
            db,
            parent_id,
            current_user,
            child_role_id=role_id,
        )
    role.parent_id = parent_id
    db.commit()
    return success_response(
        data={"role_id": role_id, "parent_id": parent_id},
        message="更新角色父级成功",
    )


__all__ = ["router"]
