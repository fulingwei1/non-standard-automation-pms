# -*- coding: utf-8 -*-
"""
统一权限引擎 (Unified Permission Engine)

收敛 auth.py 和 permission_service.py 中重复的权限加载逻辑（缓存 + SQL）。

职责（仅限数据层）：
1. 缓存读取（带租户隔离）
2. 数据库查询（递归角色继承 + 多租户过滤）
3. 缓存回写

不负责：超管/管理员快速放行（由各调用方自行判断，保持原有语义差异）。
"""

import logging
from typing import List, Optional, Set

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.permission_codes import canonicalize_permission_code, canonicalize_permission_codes

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 权限缓存修订号：Redis 不可用时用于跨 worker 识别陈旧内存缓存
# ---------------------------------------------------------------------------

def _permission_revision_scope(tenant_id: Optional[int]) -> str:
    return f"tenant:{tenant_id}" if tenant_id is not None else "system"


def _ensure_permission_cache_revision_table(db: Session) -> None:
    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS permission_cache_revisions (
                scope VARCHAR(64) PRIMARY KEY,
                revision INTEGER NOT NULL DEFAULT 0,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


def _current_permission_cache_revision(
    db: Session,
    tenant_id: Optional[int],
) -> Optional[int]:
    """读取当前权限缓存修订号；失败时返回 None，保持旧缓存逻辑可用。"""
    try:
        _ensure_permission_cache_revision_table(db)
        row = db.execute(
            text("SELECT revision FROM permission_cache_revisions WHERE scope = :scope"),
            {"scope": _permission_revision_scope(tenant_id)},
        ).fetchone()
        if row is None:
            return 0
        return int(row[0])
    except Exception as exc:
        logger.warning("Permission cache revision read failed: %s", exc)
        return None


def bump_permission_cache_revision(
    db: Session,
    tenant_id: Optional[int],
    *,
    commit: bool = True,
) -> Optional[int]:
    """权限/角色关系变更后递增修订号，让其他 worker 丢弃旧内存缓存。"""
    try:
        _ensure_permission_cache_revision_table(db)
        scope = _permission_revision_scope(tenant_id)
        row = db.execute(
            text("SELECT revision FROM permission_cache_revisions WHERE scope = :scope"),
            {"scope": scope},
        ).fetchone()
        next_revision = int(row[0]) + 1 if row is not None else 1
        if row is None:
            db.execute(
                text(
                    """
                    INSERT INTO permission_cache_revisions (scope, revision, updated_at)
                    VALUES (:scope, :revision, CURRENT_TIMESTAMP)
                    """
                ),
                {"scope": scope, "revision": next_revision},
            )
        else:
            db.execute(
                text(
                    """
                    UPDATE permission_cache_revisions
                    SET revision = :revision, updated_at = CURRENT_TIMESTAMP
                    WHERE scope = :scope
                    """
                ),
                {"scope": scope, "revision": next_revision},
            )
        if commit:
            db.commit()
        return next_revision
    except Exception as exc:
        logger.warning("Permission cache revision bump failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# 核心：从数据库加载用户权限（唯一实现）
# ---------------------------------------------------------------------------

def _load_permissions_from_db(
    user_id: int,
    db: Session,
    tenant_id: Optional[int] = None,
) -> Set[str]:
    """从数据库加载用户权限（含递归角色继承 + 多租户隔离）

    多租户规则：
    - tenant_id 不为 None 时：系统级权限(tenant_id IS NULL) + 该租户权限
    - tenant_id 为 None（超管场景）：仅系统级权限

    Returns:
        权限编码集合
    """
    if tenant_id is not None:
        tenant_filter = "AND (ap.tenant_id IS NULL OR ap.tenant_id = :tenant_id)"
        params = {"user_id": user_id, "tenant_id": tenant_id}
    else:
        tenant_filter = "AND ap.tenant_id IS NULL"
        params = {"user_id": user_id}

    sql = f"""
        WITH RECURSIVE role_tree AS (
            SELECT r.id, r.parent_id, r.inherit_permissions
            FROM roles r
            JOIN user_roles ur ON ur.role_id = r.id
            WHERE ur.user_id = :user_id

            UNION ALL

            SELECT r.id, r.parent_id, r.inherit_permissions
            FROM roles r
            JOIN role_tree rt ON r.id = rt.parent_id
            WHERE rt.inherit_permissions = 1
        )
        SELECT DISTINCT ap.perm_code, ap.is_active
        FROM role_tree rt
        JOIN role_api_permissions rap ON rt.id = rap.role_id
        JOIN api_permissions ap ON rap.permission_id = ap.id
        WHERE 1 = 1
        {tenant_filter}
    """
    result = db.execute(text(sql), params)
    permissions: Set[str] = set()
    inactive_permissions: Set[str] = set()
    for perm_code, is_active in result.fetchall():
        if not perm_code:
            continue
        if is_active:
            permissions.add(perm_code)
        else:
            inactive_permissions.add(perm_code)

    if inactive_permissions:
        logger.warning(
            "Inactive API permissions assigned to user: user=%s tenant=%s permissions=%s",
            user_id,
            tenant_id,
            sorted(inactive_permissions),
        )

    return permissions


# ---------------------------------------------------------------------------
# 公开 API
# ---------------------------------------------------------------------------

def load_permissions(
    user_id: int,
    db: Session,
    tenant_id: Optional[int] = None,
) -> Set[str]:
    """加载用户的全部权限编码（带缓存）。

    这是获取用户权限列表的唯一入口。缓存命中时直接返回，
    缓存未命中时从数据库查询并回写缓存。

    注意：此函数不做超管/管理员判断，调用方需自行处理快速放行逻辑。

    Args:
        user_id: 用户 ID
        db: 数据库会话
        tenant_id: 租户 ID（None 表示系统级）

    Returns:
        权限编码集合
    """
    revision = _current_permission_cache_revision(db, tenant_id)

    # 1. 尝试缓存
    try:
        from app.services.permission_management.permission_cache_service import get_permission_cache_service
        cache_svc = get_permission_cache_service()
        cached = cache_svc.get_user_permissions(user_id, tenant_id, revision=revision)
        if cached is not None:
            logger.debug(
                "PermEngine cache HIT: user=%s tenant=%s revision=%s count=%d",
                user_id, tenant_id, revision, len(cached),
            )
            return cached
    except Exception as e:
        logger.warning("PermEngine cache read failed, fallback to DB: %s", e)
        cache_svc = None

    # 2. 数据库查询
    try:
        permissions = _load_permissions_from_db(user_id, db, tenant_id)
    except Exception as e:
        logger.error("PermEngine DB query failed: user=%s tenant=%s error=%s", user_id, tenant_id, e)
        return set()

    logger.debug(
        "PermEngine cache MISS → DB: user=%s tenant=%s loaded=%d",
        user_id, tenant_id, len(permissions),
    )

    # 3. 回写缓存
    if cache_svc is not None:
        try:
            cache_svc.set_user_permissions(user_id, permissions, tenant_id, revision=revision)
        except Exception as e:
            logger.warning("PermEngine cache write failed: %s", e)

    return permissions


def check_permission_for_user(
    user_id: int,
    permission_code: str,
    db: Session,
    tenant_id: Optional[int] = None,
) -> bool:
    """检查指定用户是否拥有某权限（纯数据层，不含管理员放行）。

    Args:
        user_id: 用户 ID
        permission_code: 权限编码，如 "sales:read"
        db: 数据库会话
        tenant_id: 租户 ID

    Returns:
        bool
    """
    permissions = load_permissions(user_id, db, tenant_id)
    return canonicalize_permission_code(permission_code) in canonicalize_permission_codes(
        permissions
    )


def check_any_permission_for_user(
    user_id: int,
    permission_codes: List[str],
    db: Session,
    tenant_id: Optional[int] = None,
) -> bool:
    """检查用户是否拥有任一权限（纯数据层）。"""
    permissions = load_permissions(user_id, db, tenant_id)
    normalized_permissions = canonicalize_permission_codes(permissions)
    return any(
        canonicalize_permission_code(code) in normalized_permissions
        for code in permission_codes
    )


def check_all_permissions_for_user(
    user_id: int,
    permission_codes: List[str],
    db: Session,
    tenant_id: Optional[int] = None,
) -> bool:
    """检查用户是否拥有所有权限（纯数据层）。"""
    permissions = load_permissions(user_id, db, tenant_id)
    normalized_permissions = canonicalize_permission_codes(permissions)
    return all(
        canonicalize_permission_code(code) in normalized_permissions
        for code in permission_codes
    )
