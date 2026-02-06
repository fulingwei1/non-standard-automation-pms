# -*- coding: utf-8 -*-
"""
角色管理 API 端点

提供角色的 CRUD 操作、权限分配和导航配置功能。
支持多租户数据隔离。
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.security import get_current_active_user, require_permission
from app.models.user import (
    ApiPermission,
    Role,
    RoleApiPermission,
    RoleTemplate,
    User,
    UserRole,
)
from app.schemas.common import ResponseModel
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.role_service import RoleService

router = APIRouter(prefix="/roles", tags=["角色管理"])

# 系统预置角色编码，禁止通过 API 创建同名角色（防止权限提升）
_RESERVED_ROLE_CODES = {
 # 超级管理员相关
 "ADMIN", "admin", "SUPERUSER", "superuser", "ROOT", "root",
 "super_admin", "system_admin", "sysadmin", "administrator",
  "Administrator", "ADMINISTRATOR",
  # 高管角色
 "GM", "CFO", "CTO", "CEO", "COO", "SALES_DIR",
  "gm", "cfo", "cto", "ceo", "coo", "sales_dir",
 # 系统角色
 "SYSTEM", "system", "internal", "INTERNAL",
  # 租户管理员
 "TENANT_ADMIN", "tenant_admin", "TenantAdmin",
 # 其他敏感角色
 "SECURITY", "security", "AUDIT", "audit",
}


def get_current_tenant_id(current_user: User) -> Optional[int]:
    """获取当前用户的租户ID"""
    return current_user.tenant_id


@router.get("/", response_model=ResponseModel)
def list_roles(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
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
    current_user: User = Depends(require_permission("role:read")),
):
    """获取权限列表（使用新的 ApiPermission 模型）"""
    if hasattr(db, "bind") and db.bind is not None and db.bind.dialect.name == "sqlite":
        pragma_columns = db.execute(text("PRAGMA table_info(api_permissions)")).fetchall()
        logging.getLogger(__name__).warning(
            "api_permissions schema snapshot: %s",
            [row[1] for row in pragma_columns],
        )

    query = (
        db.query(
            ApiPermission.id.label("id"),
            ApiPermission.perm_code.label("perm_code"),
            ApiPermission.perm_name.label("perm_name"),
            ApiPermission.module.label("module"),
            ApiPermission.action.label("action"),
        )
        .filter(ApiPermission.is_active == True)
    )
    if module:
        query = query.filter(ApiPermission.module == module)

    try:
        permissions = query.order_by(ApiPermission.module, ApiPermission.perm_code).all()
    except OperationalError as exc:
        logging.getLogger(__name__).error(
            "Failed to load ApiPermission records (falling back to empty list): %s",
            exc,
        )
        db.rollback()
        permissions = []

    result = [
        {
            "id": p.id,
            "permission_code": p.perm_code,
            "permission_name": p.perm_name,
            "module": p.module,
            "action": p.action,
        }
        for p in permissions
    ]
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/templates", response_model=ResponseModel)
def list_role_templates(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色模板列表"""
    templates = (
        db.query(RoleTemplate)
        .filter(RoleTemplate.is_active == True)
        .order_by(RoleTemplate.template_name)
        .all()
    )

    result = [
        {
            "id": t.id,
            "role_code": t.template_code,
            "role_name": t.template_name,
            "description": t.description,
            "data_scope": t.data_scope,
            "permission_codes": t.permission_snapshot,
        }
        for t in templates
    ]
    return ResponseModel(code=200, message="获取成功", data=result)


@router.get("/config/all", response_model=ResponseModel)
def get_all_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取所有角色配置（按租户隔离）"""
    from sqlalchemy import or_
    tenant_id = current_user.tenant_id
    roles = (
        db.query(Role)
        .filter(
            Role.is_active == True,
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
        )
        .order_by(Role.sort_order)
        .all()
    )

    result = []
    for role in roles:
        result.append(
            {
                "id": role.id,
                "role_code": role.role_code,
                "role_name": role.role_name,
                "data_scope": role.data_scope,
                "nav_groups": role.nav_groups,
                "ui_config": role.ui_config,
            }
        )

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

    return ResponseModel(
        code=200, message="获取成功", data={"nav_groups": merged_nav_groups}
    )


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_role(
    role_in: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:create")),
):
    """创建角色"""
    # 安全检查：禁止创建与系统预置角色同名的角色（防止权限提升）
    if role_in.role_code in _RESERVED_ROLE_CODES or role_in.role_code.upper() in _RESERVED_ROLE_CODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色编码 {role_in.role_code} 为系统保留编码，不允许使用",
        )

    # 检查角色编码是否已存在（在当前租户或全局范围内）
    from sqlalchemy import or_
    tenant_id = current_user.tenant_id
    existing = db.query(Role).filter(
        Role.role_code == role_in.role_code,
        or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None))
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色编码 {role_in.role_code} 已存在",
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
        code=201, message="创建成功", data=service._to_response(role).model_dump()
    )


@router.get("/{role_id}", response_model=ResponseModel)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    service = RoleService(db)
    return ResponseModel(
        code=200, message="获取成功", data=service._to_response(role).model_dump()
    )


@router.put("/{role_id}", response_model=ResponseModel)
def update_role(
    role_id: int,
    role_in: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """更新角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 系统预置角色不允许修改编码
    if role.is_system and role_in.role_code and role_in.role_code != role.role_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="系统预置角色不允许修改编码"
        )

    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)

    db.commit()
    db.refresh(role)

    service = RoleService(db)
    return ResponseModel(
        code=200, message="更新成功", data=service._to_response(role).model_dump()
    )


@router.delete("/{role_id}", response_model=ResponseModel)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:delete")),
):
    """删除角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="系统预置角色不允许删除"
        )

    # 检查是否有用户使用此角色
    user_count = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该角色下有 {user_count} 个用户，无法删除",
        )

    db.delete(role)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


@router.put("/{role_id}/permissions", response_model=ResponseModel)
def update_role_permissions(
    role_id: int,
    permission_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """更新角色权限（使用新的 RoleApiPermission 模型）"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    # 删除现有权限（使用新的关联表）
    db.query(RoleApiPermission).filter(RoleApiPermission.role_id == role_id).delete()

    # 添加新权限
    for perm_id in permission_ids:
        perm = db.query(ApiPermission).filter(ApiPermission.id == perm_id).first()
        if perm:
            db.add(RoleApiPermission(role_id=role_id, permission_id=perm_id))

    db.commit()
    
    # 清除角色和相关用户的权限缓存
    try:
        from app.services.permission_cache_service import get_permission_cache_service
        cache_service = get_permission_cache_service()
        cache_service.invalidate_role_and_users(role_id, tenant_id=current_user.tenant_id)
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"清除权限缓存失败: {e}")

    return ResponseModel(code=200, message="权限更新成功")


@router.get("/{role_id}/nav-groups", response_model=ResponseModel)
def get_role_nav_groups(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的导航组配置"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    return ResponseModel(
        code=200, message="获取成功", data={"nav_groups": role.nav_groups or []}
    )


@router.put("/{role_id}/nav-groups", response_model=ResponseModel)
def update_role_nav_groups(
    role_id: int,
    nav_groups: List[dict],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:update")),
):
    """更新角色的导航组配置"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    role.nav_groups = nav_groups
    db.commit()

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
    from sqlalchemy import or_
    tenant_id = current_user.tenant_id
    roles = (
        db.query(Role)
        .filter(
            Role.is_active == True,
            or_(Role.tenant_id == tenant_id, Role.tenant_id.is_(None)),
        )
        .order_by(Role.sort_order)
        .all()
    )

    # 构建树形结构
    role_map = {
        r.id: {
            "id": r.id,
            "role_code": r.role_code,
            "role_name": r.role_name,
            "parent_id": r.parent_id,
            "data_scope": r.data_scope,
            "children": [],
        }
        for r in roles
    }

    tree = []
    for role in roles:
        node = role_map[role.id]
        if role.parent_id and role.parent_id in role_map:
            role_map[role.parent_id]["children"].append(node)
        else:
            tree.append(node)

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
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="系统预置角色不允许修改层级"
        )

    # 检查父角色是否存在
    if parent_id is not None:
        parent_role = db.query(Role).filter(Role.id == parent_id).first()
        if not parent_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="父角色不存在"
            )

        # 检查是否形成循环引用
        if _would_create_cycle(db, role_id, parent_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能将子角色设为父角色（会形成循环引用）",
            )

    role.parent_id = parent_id
    db.commit()

    return ResponseModel(
        code=200,
        message="角色层级更新成功",
        data={
            "role_id": role_id,
            "parent_id": parent_id,
            "role_code": role.role_code,
            "role_name": role.role_name,
        },
    )


def _would_create_cycle(db: Session, role_id: int, new_parent_id: int) -> bool:
    """检查设置新父角色是否会形成循环引用"""
    current_id = new_parent_id
    visited = {role_id}  # 包含当前角色

    while current_id is not None:
        if current_id in visited:
            return True
        visited.add(current_id)

        parent_role = db.query(Role).filter(Role.id == current_id).first()
        if parent_role:
            current_id = parent_role.parent_id
        else:
            break

    return False


@router.get("/{role_id}/ancestors", response_model=ResponseModel)
def get_role_ancestors(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的所有祖先角色（继承链）"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    ancestors = []
    current = role

    while current.parent_id is not None:
        parent = db.query(Role).filter(Role.id == current.parent_id).first()
        if parent:
            ancestors.append(
                {
                    "id": parent.id,
                    "role_code": parent.role_code,
                    "role_name": parent.role_name,
                    "data_scope": parent.data_scope,
                }
            )
            current = parent
        else:
            break

    return ResponseModel(
        code=200,
        message="获取成功",
        data={"role_id": role_id, "role_code": role.role_code, "ancestors": ancestors},
    )


@router.get("/{role_id}/descendants", response_model=ResponseModel)
def get_role_descendants(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role:read")),
):
    """获取角色的所有子孙角色"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")

    descendants = []
    _collect_descendants(db, role_id, descendants)

    return ResponseModel(
        code=200,
        message="获取成功",
        data={
            "role_id": role_id,
            "role_code": role.role_code,
            "descendants": descendants,
        },
    )


def _collect_descendants(db: Session, parent_id: int, result: list):
    """递归收集所有子孙角色"""
    children = (
        db.query(Role).filter(Role.parent_id == parent_id, Role.is_active == True).all()
    )
    for child in children:
        result.append(
            {
                "id": child.id,
                "role_code": child.role_code,
                "role_name": child.role_name,
                "parent_id": child.parent_id,
                "data_scope": child.data_scope,
            }
        )
        _collect_descendants(db, child.id, result)
