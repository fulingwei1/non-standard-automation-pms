# -*- coding: utf-8 -*-
"""
角色列表与详情端点
"""

import logging
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, or_, text
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import Role, User
from app.schemas.auth import PermissionResponse, RoleResponse
from app.schemas.common import PaginatedResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class RoleListResponse(PaginatedResponse):
    """角色列表响应"""

    items: List[RoleResponse]


@router.get("/", response_model=RoleListResponse, status_code=status.HTTP_200_OK)
def read_roles(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(
        settings.DEFAULT_PAGE_SIZE,
        ge=1,
        le=settings.MAX_PAGE_SIZE,
        description="每页数量",
    ),
    keyword: Optional[str] = Query(None, description="关键词搜索（角色编码/名称）"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取角色列表（支持分页和筛选）

    - **page**: 页码，从1开始
    - **page_size**: 每页数量，默认20，最大100
    - **keyword**: 关键词搜索（角色编码/名称）
    - **is_active**: 是否启用筛选
    """
    try:
        # 使用ORM查询构建器，更安全且易于维护
        query = db.query(Role)

        # 关键词搜索
        if keyword:
            search_pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Role.role_code.like(search_pattern),
                    Role.role_name.like(search_pattern),
                )
            )

        # 启用状态筛选（使用 is_active 字段）
        if is_active is not None:
            # 使用 is_active 字段进行筛选
            query = query.filter(
                or_(Role.is_active == is_active, Role.is_active.is_(None))
            )

        # 计算总数
        total = query.count()

        # 分页查询
        offset = (page - 1) * page_size
        query = query.order_by(desc(Role.created_at)).offset(offset).limit(page_size)

        # 执行查询
        roles_db = query.all()

        # 转换为RoleResponse对象
        roles = []
        for role in roles_db:
            try:
                # 查询角色的权限（使用SQL避免ORM关系错误）
                perm_sql = """
                    SELECT p.perm_name
                    FROM role_permissions rp
                    JOIN permissions p ON rp.permission_id = p.id
                    WHERE rp.role_id = :role_id
                """
                perm_result = db.execute(text(perm_sql), {"role_id": role.id})
                perm_rows = perm_result.fetchall()
                # 安全地处理权限数据
                permissions = []
                for perm_row in perm_rows:
                    if perm_row and len(perm_row) > 0 and perm_row[0]:
                        perm_name = (
                            perm_row[0].strip()
                            if isinstance(perm_row[0], str)
                            else str(perm_row[0]).strip()
                        )
                        if perm_name:
                            permissions.append(perm_name)

                # 直接构建RoleResponse（避免ORM关系错误）
                role_response = RoleResponse(
                    id=role.id,
                    role_code=role.role_code or "",
                    role_name=role.role_name or "",
                    description=role.description or None,
                    data_scope=role.data_scope or "OWN",
                    is_system=bool(role.is_system)
                    if role.is_system is not None
                    else False,
                    is_active=bool(role.is_active)
                    if role.is_active is not None
                    else True,
                    permissions=permissions,
                    permission_count=len(permissions),  # 添加权限计数
                    created_at=role.created_at,
                    updated_at=role.updated_at,
                )
                roles.append(role_response)
            except Exception as row_error:
                logger.error(
                    f"处理角色数据行失败: {row_error}, role_id={getattr(role, 'id', None)}",
                    exc_info=True,
                )
                continue

        return RoleListResponse(
            items=roles,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    except Exception as e:
        logger.error(f"获取角色列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}",
        )


@router.get(
    "/permissions",
    response_model=List[PermissionResponse],
    status_code=status.HTTP_200_OK,
)
def read_permissions(
    db: Session = Depends(deps.get_db),
    module: Optional[str] = Query(None, description="模块筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取所有可用权限列表

    - **module**: 模块筛选（可选）
    """
    try:
        logger.info(
            f"开始获取权限列表，用户: {current_user.username}, 模块筛选: {module}"
        )
        # 使用SQL查询，避免其他模型关系定义错误影响
        # 表结构已统一，包含所有字段

        # 构建SQL查询
        sql = """
            SELECT
                id,
                perm_code as permission_code,
                perm_name as permission_name,
                module,
                resource,
                action,
                description,
                is_active,
                created_at,
                updated_at
            FROM permissions
            WHERE is_active = 1
        """
        params = {}

        # 模块筛选
        if module:
            sql += " AND module = :module"
            params["module"] = module

        # 排序
        sql += " ORDER BY module ASC, perm_code ASC"

        # 执行查询
        result = db.execute(text(sql), params)
        rows = result.fetchall()

        logger.info(f"查询到 {len(rows)} 条权限数据")

        # 转换为字典列表
        permissions = []
        for row in rows:
            try:
                # 处理datetime字段（SQLite返回字符串，需要转换）
                created_at = row[8]
                updated_at = row[9]

                # 如果是字符串，尝试转换为datetime
                if isinstance(created_at, str) and created_at:
                    try:
                        # SQLite datetime格式: 'YYYY-MM-DD HH:MM:SS'
                        created_at = datetime.strptime(created_at, "%Y-%m-%d %H:%M:%S")
                    except Exception as dt_e:
                        logger.warning(
                            f"created_at转换失败: {dt_e}, value={created_at}"
                        )
                        created_at = None

                if isinstance(updated_at, str) and updated_at:
                    try:
                        updated_at = datetime.strptime(updated_at, "%Y-%m-%d %H:%M:%S")
                    except Exception as dt_e:
                        logger.warning(
                            f"updated_at转换失败: {dt_e}, value={updated_at}"
                        )
                        updated_at = None

                perm_dict = {
                    "id": row[0],
                    "permission_code": row[1] if row[1] else "",
                    "permission_name": row[2] if row[2] else "",
                    "module": row[3],
                    "resource": row[4],
                    "action": row[5],
                    "description": row[6],
                    "is_active": bool(row[7]) if row[7] is not None else True,
                    "created_at": created_at,
                    "updated_at": updated_at,
                }
                permissions.append(perm_dict)
            except Exception as e:
                logger.error(f"转换权限数据失败: {e}, row={row}", exc_info=True)
                continue

        # 转换为响应模型
        result_list = []
        for perm in permissions:
            try:
                perm_response = PermissionResponse(**perm)
                result_list.append(perm_response)
            except Exception as e:
                logger.error(f"创建PermissionResponse失败: {e}, perm={perm}")
                continue

        logger.info(f"成功返回 {len(result_list)} 条权限")
        return result_list

    except Exception as e:
        logger.error(f"获取权限列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取权限列表失败: {str(e)}",
        )


@router.get("/{role_id}", response_model=RoleResponse, status_code=status.HTTP_200_OK)
def read_role(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取角色详情

    - **role_id**: 角色ID
    """
    try:
        # 使用SQL查询，避免ORM关系错误

        sql = """
            SELECT
                id,
                role_code,
                role_name,
                description,
                data_scope,
                is_system,
                COALESCE(is_active, 1) as is_active,
                created_at,
                updated_at
            FROM roles
            WHERE id = :role_id
        """
        result = db.execute(text(sql), {"role_id": role_id})
        row = result.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="角色不存在")

        # 检查行数据完整性
        if len(row) < 9:
            raise HTTPException(
                status_code=500, detail=f"角色数据不完整: 期望9列，实际{len(row)}列"
            )

        # 查询角色的权限（使用SQL避免ORM关系错误）
        perm_sql = """
            SELECT p.perm_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = :role_id
        """
        perm_result = db.execute(text(perm_sql), {"role_id": role_id})
        perm_rows = perm_result.fetchall()
        # 安全地处理权限数据
        permissions = []
        for perm_row in perm_rows:
            if perm_row and len(perm_row) > 0 and perm_row[0]:
                perm_name = (
                    perm_row[0].strip()
                    if isinstance(perm_row[0], str)
                    else str(perm_row[0]).strip()
                )
                if perm_name:
                    permissions.append(perm_name)

        # 直接构建RoleResponse（避免ORM关系错误）
        role_response = RoleResponse(
            id=row[0],
            role_code=row[1] if row[1] else "",
            role_name=row[2] if row[2] else "",
            description=row[3] if len(row) > 3 and row[3] else None,
            data_scope=row[4] if len(row) > 4 and row[4] else "OWN",
            is_system=bool(row[5]) if len(row) > 5 and row[5] is not None else False,
            is_active=bool(row[6]) if len(row) > 6 and row[6] is not None else True,
            permissions=permissions,
            created_at=row[7] if len(row) > 7 else None,
            updated_at=row[8] if len(row) > 8 else None,
        )

        return role_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详情失败: {str(e)}",
        )
