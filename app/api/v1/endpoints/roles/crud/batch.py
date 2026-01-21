# -*- coding: utf-8 -*-
"""
角色批量操作 API

提供角色和权限的批量操作功能
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Permission, Role, RolePermission, User
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class BatchPermissionAssign(BaseModel):
    """批量分配权限"""
    role_ids: List[int] = Field(..., min_length=1, description="角色ID列表")
    permission_ids: List[int] = Field(..., min_length=1, description="权限ID列表")


class BatchPermissionRemove(BaseModel):
    """批量移除权限"""
    role_ids: List[int] = Field(..., min_length=1, description="角色ID列表")
    permission_ids: List[int] = Field(..., min_length=1, description="权限ID列表")


class BatchRoleStatusUpdate(BaseModel):
    """批量更新角色状态"""
    role_ids: List[int] = Field(..., min_length=1, description="角色ID列表")
    is_active: bool = Field(..., description="是否启用")


class BatchDataScopeUpdate(BaseModel):
    """批量更新数据权限"""
    role_ids: List[int] = Field(..., min_length=1, description="角色ID列表")
    data_scope: str = Field(..., description="数据权限范围")


class BatchRoleDelete(BaseModel):
    """批量删除角色"""
    role_ids: List[int] = Field(..., min_length=1, description="角色ID列表")
    force: bool = Field(False, description="是否强制删除（包括有用户的角色）")


# ============================================================
# Batch Operations
# ============================================================

@router.post("/batch/assign-permissions", response_model=ResponseModel)
def batch_assign_permissions(
    *,
    db: Session = Depends(deps.get_db),
    data: BatchPermissionAssign,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    批量为多个角色分配权限

    - 跳过已存在的权限关联
    - 返回成功分配的数量
    """
    # 验证角色存在
    roles = db.query(Role).filter(Role.id.in_(data.role_ids)).all()
    valid_role_ids = {r.id for r in roles}
    invalid_role_ids = set(data.role_ids) - valid_role_ids

    # 验证权限存在
    permissions = db.query(Permission).filter(Permission.id.in_(data.permission_ids)).all()
    valid_perm_ids = {p.id for p in permissions}
    invalid_perm_ids = set(data.permission_ids) - valid_perm_ids

    if invalid_role_ids or invalid_perm_ids:
        detail = []
        if invalid_role_ids:
            detail.append(f"无效的角色ID: {list(invalid_role_ids)}")
        if invalid_perm_ids:
            detail.append(f"无效的权限ID: {list(invalid_perm_ids)}")
        raise HTTPException(status_code=400, detail="; ".join(detail))

    # 获取已存在的关联
    existing = db.query(RolePermission).filter(
        RolePermission.role_id.in_(valid_role_ids),
        RolePermission.permission_id.in_(valid_perm_ids)
    ).all()
    existing_pairs = {(rp.role_id, rp.permission_id) for rp in existing}

    # 创建新的关联
    created_count = 0
    for role_id in valid_role_ids:
        for perm_id in valid_perm_ids:
            if (role_id, perm_id) not in existing_pairs:
                db.add(RolePermission(role_id=role_id, permission_id=perm_id))
                created_count += 1

    db.commit()

    # 清除缓存
    _invalidate_roles_cache(db, list(valid_role_ids))

    return ResponseModel(
        code=200,
        message=f"批量分配完成，新增 {created_count} 条权限关联",
        data={
            "roles_count": len(valid_role_ids),
            "permissions_count": len(valid_perm_ids),
            "created_count": created_count,
            "skipped_count": len(valid_role_ids) * len(valid_perm_ids) - created_count,
        }
    )


@router.post("/batch/remove-permissions", response_model=ResponseModel)
def batch_remove_permissions(
    *,
    db: Session = Depends(deps.get_db),
    data: BatchPermissionRemove,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    批量从多个角色移除权限
    """
    # 删除匹配的关联
    result = db.query(RolePermission).filter(
        RolePermission.role_id.in_(data.role_ids),
        RolePermission.permission_id.in_(data.permission_ids)
    ).delete(synchronize_session=False)

    db.commit()

    # 清除缓存
    _invalidate_roles_cache(db, data.role_ids)

    return ResponseModel(
        code=200,
        message=f"批量移除完成，删除 {result} 条权限关联",
        data={"removed_count": result}
    )


@router.post("/batch/update-status", response_model=ResponseModel)
def batch_update_role_status(
    *,
    db: Session = Depends(deps.get_db),
    data: BatchRoleStatusUpdate,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    批量启用/禁用角色
    """
    # 不允许禁用系统管理员角色
    if not data.is_active:
        admin_roles = db.query(Role).filter(
            Role.id.in_(data.role_ids),
            Role.role_code == "ADMIN"
        ).all()
        if admin_roles:
            raise HTTPException(
                status_code=400,
                detail="不能禁用系统管理员角色"
            )

    result = db.query(Role).filter(
        Role.id.in_(data.role_ids)
    ).update({"is_active": data.is_active}, synchronize_session=False)

    db.commit()

    # 清除缓存
    _invalidate_roles_cache(db, data.role_ids)

    status_text = "启用" if data.is_active else "禁用"
    return ResponseModel(
        code=200,
        message=f"批量{status_text}完成，更新 {result} 个角色",
        data={"updated_count": result}
    )


@router.post("/batch/update-data-scope", response_model=ResponseModel)
def batch_update_data_scope(
    *,
    db: Session = Depends(deps.get_db),
    data: BatchDataScopeUpdate,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    批量更新角色的数据权限范围
    """
    valid_scopes = ["ALL", "BUSINESS_UNIT", "DEPARTMENT", "TEAM", "PROJECT", "OWN"]
    if data.data_scope not in valid_scopes:
        raise HTTPException(
            status_code=400,
            detail=f"无效的数据权限范围，有效值: {valid_scopes}"
        )

    result = db.query(Role).filter(
        Role.id.in_(data.role_ids)
    ).update({"data_scope": data.data_scope}, synchronize_session=False)

    db.commit()

    # 清除缓存
    _invalidate_roles_cache(db, data.role_ids)

    return ResponseModel(
        code=200,
        message=f"批量更新数据权限完成，更新 {result} 个角色",
        data={"updated_count": result, "new_data_scope": data.data_scope}
    )


@router.post("/batch/delete", response_model=ResponseModel)
def batch_delete_roles(
    *,
    db: Session = Depends(deps.get_db),
    data: BatchRoleDelete,
    current_user: User = Depends(security.require_permission("ROLE_DELETE")),
) -> Any:
    """
    批量删除角色（软删除）

    - 默认不删除有用户关联的角色
    - force=True 时强制删除
    """
    from app.models.user import UserRole

    # 不允许删除系统管理员角色
    admin_roles = db.query(Role).filter(
        Role.id.in_(data.role_ids),
        Role.role_code == "ADMIN"
    ).all()
    if admin_roles:
        raise HTTPException(
            status_code=400,
            detail="不能删除系统管理员角色"
        )

    roles_to_delete = data.role_ids.copy()

    if not data.force:
        # 检查哪些角色有用户关联
        roles_with_users = db.query(UserRole.role_id).filter(
            UserRole.role_id.in_(data.role_ids)
        ).distinct().all()
        roles_with_users_ids = {r[0] for r in roles_with_users}

        if roles_with_users_ids:
            # 从删除列表中排除有用户的角色
            roles_to_delete = [r for r in data.role_ids if r not in roles_with_users_ids]

            if not roles_to_delete:
                raise HTTPException(
                    status_code=400,
                    detail="所有角色都有用户关联，无法删除。使用 force=true 强制删除"
                )

    # 软删除角色
    result = db.query(Role).filter(
        Role.id.in_(roles_to_delete)
    ).update({"is_active": False}, synchronize_session=False)

    db.commit()

    # 清除缓存
    _invalidate_roles_cache(db, roles_to_delete)

    skipped_count = len(data.role_ids) - len(roles_to_delete)
    return ResponseModel(
        code=200,
        message=f"批量删除完成，删除 {result} 个角色" +
                (f"，跳过 {skipped_count} 个有用户关联的角色" if skipped_count > 0 else ""),
        data={
            "deleted_count": result,
            "skipped_count": skipped_count,
        }
    )


@router.post("/batch/copy-permissions", response_model=ResponseModel)
def batch_copy_permissions(
    *,
    db: Session = Depends(deps.get_db),
    source_role_id: int,
    target_role_ids: List[int],
    replace: bool = False,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    将一个角色的权限复制到多个目标角色

    - replace=False: 追加权限（默认）
    - replace=True: 替换权限（先删除目标角色的现有权限）
    """
    # 验证源角色
    source_role = db.query(Role).filter(Role.id == source_role_id).first()
    if not source_role:
        raise HTTPException(status_code=404, detail="源角色不存在")

    # 验证目标角色
    target_roles = db.query(Role).filter(Role.id.in_(target_role_ids)).all()
    valid_target_ids = {r.id for r in target_roles}
    invalid_ids = set(target_role_ids) - valid_target_ids

    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"无效的目标角色ID: {list(invalid_ids)}"
        )

    # 获取源角色的权限
    source_perms = db.query(RolePermission.permission_id).filter(
        RolePermission.role_id == source_role_id
    ).all()
    source_perm_ids = [p[0] for p in source_perms]

    if not source_perm_ids:
        return ResponseModel(
            code=200,
            message="源角色没有权限可复制",
            data={"copied_count": 0}
        )

    # 如果是替换模式，先删除目标角色的权限
    if replace:
        db.query(RolePermission).filter(
            RolePermission.role_id.in_(valid_target_ids)
        ).delete(synchronize_session=False)

    # 获取已存在的关联（追加模式时需要）
    if not replace:
        existing = db.query(RolePermission).filter(
            RolePermission.role_id.in_(valid_target_ids),
            RolePermission.permission_id.in_(source_perm_ids)
        ).all()
        existing_pairs = {(rp.role_id, rp.permission_id) for rp in existing}
    else:
        existing_pairs = set()

    # 复制权限
    created_count = 0
    for target_id in valid_target_ids:
        for perm_id in source_perm_ids:
            if (target_id, perm_id) not in existing_pairs:
                db.add(RolePermission(role_id=target_id, permission_id=perm_id))
                created_count += 1

    db.commit()

    # 清除缓存
    _invalidate_roles_cache(db, list(valid_target_ids))

    return ResponseModel(
        code=200,
        message=f"权限复制完成，{'替换' if replace else '新增'} {created_count} 条权限关联",
        data={
            "source_role": source_role.role_name,
            "target_count": len(valid_target_ids),
            "permissions_count": len(source_perm_ids),
            "created_count": created_count,
        }
    )


# ============================================================
# Helper Functions
# ============================================================

def _invalidate_roles_cache(db: Session, role_ids: List[int]) -> None:
    """清除多个角色的缓存"""
    try:
        from .utils import _invalidate_role_cache
        for role_id in role_ids:
            _invalidate_role_cache(db, role_id, include_children=True)
    except Exception as e:
        logger.warning(f"批量清除缓存失败: {e}")
