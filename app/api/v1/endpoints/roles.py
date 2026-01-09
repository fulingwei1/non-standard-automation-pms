# -*- coding: utf-8 -*-
"""
角色管理 API endpoints
"""
import logging
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

logger = logging.getLogger(__name__)

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
        # 使用SQL查询，避免ORM关系错误
        from sqlalchemy import text
        
        # 构建基础查询
        where_clauses = []
        params = {}
        
        # 关键词搜索
        if keyword:
            where_clauses.append("(role_code LIKE :keyword OR role_name LIKE :keyword)")
            params['keyword'] = f"%{keyword}%"
        
        # 启用状态筛选（兼容status字段）
        if is_active is not None:
            # 尝试使用status字段，如果没有则不过滤
            where_clauses.append("(status = :status OR status IS NULL)")
            params['status'] = 'ACTIVE' if is_active else 'INACTIVE'
        
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # 计算总数
        count_sql = f"SELECT COUNT(*) FROM roles WHERE {where_sql}"
        count_result = db.execute(text(count_sql), params)
        total = count_result.scalar()
        
        # 分页查询
        offset = (page - 1) * page_size
        sql = f"""
            SELECT 
                id,
                role_code,
                role_name,
                description,
                data_scope,
                is_system,
                status,
                created_at,
                updated_at
            FROM roles
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """
        params['limit'] = page_size
        params['offset'] = offset
        
        result = db.execute(text(sql), params)
        rows = result.fetchall()
        
        # 转换为RoleResponse对象（避免创建Role对象触发ORM关系检查）
        roles = []
        for row in rows:
            role_id = row[0]
            
            # 查询角色的权限（使用SQL避免ORM关系错误）
            perm_sql = """
                SELECT p.perm_name
                FROM role_permissions rp
                JOIN permissions p ON rp.permission_id = p.id
                WHERE rp.role_id = :role_id
            """
            perm_result = db.execute(text(perm_sql), {"role_id": role_id})
            perm_rows = perm_result.fetchall()
            permissions = [row[0] for row in perm_rows if row[0] and row[0].strip()]
            
            # 直接构建RoleResponse（避免ORM关系错误）
            role_response = RoleResponse(
                id=row[0],
                role_code=row[1],
                role_name=row[2],
                description=row[3],
                data_scope=row[4] if row[4] else "OWN",
                is_system=bool(row[5]) if row[5] is not None else False,
                is_active=True,  # 默认启用
                permissions=permissions,
                created_at=row[7],
                updated_at=row[8],
            )
            roles.append(role_response)
        
        return RoleListResponse(
            items=roles,
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size
        )
        
    except Exception as e:
        logger.error(f"获取角色列表失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色列表失败: {str(e)}"
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
    try:
        logger.info(f"开始获取权限列表，用户: {current_user.username}, 模块筛选: {module}")
        # 使用SQL查询，避免其他模型关系定义错误影响
        # 表结构已统一，包含所有字段
        from sqlalchemy import text
        
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
            params['module'] = module
        
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
                        created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                    except Exception as dt_e:
                        logger.warning(f"created_at转换失败: {dt_e}, value={created_at}")
                        created_at = None
                
                if isinstance(updated_at, str) and updated_at:
                    try:
                        updated_at = datetime.strptime(updated_at, '%Y-%m-%d %H:%M:%S')
                    except Exception as dt_e:
                        logger.warning(f"updated_at转换失败: {dt_e}, value={updated_at}")
                        updated_at = None
                
                perm_dict = {
                    'id': row[0],
                    'permission_code': row[1] if row[1] else '',
                    'permission_name': row[2] if row[2] else '',
                    'module': row[3],
                    'resource': row[4],
                    'action': row[5],
                    'description': row[6],
                    'is_active': bool(row[7]) if row[7] is not None else True,
                    'created_at': created_at,
                    'updated_at': updated_at,
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
            detail=f"获取权限列表失败: {str(e)}"
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
        from sqlalchemy import text
        
        sql = """
            SELECT 
                id,
                role_code,
                role_name,
                description,
                data_scope,
                is_system,
                status,
                created_at,
                updated_at
            FROM roles
            WHERE id = :role_id
        """
        result = db.execute(text(sql), {"role_id": role_id})
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="角色不存在")
        
        # 查询角色的权限（使用SQL避免ORM关系错误）
        perm_sql = """
            SELECT p.perm_name
            FROM role_permissions rp
            JOIN permissions p ON rp.permission_id = p.id
            WHERE rp.role_id = :role_id
        """
        perm_result = db.execute(text(perm_sql), {"role_id": role_id})
        perm_rows = perm_result.fetchall()
        permissions = [row[0] for row in perm_rows if row[0] and row[0].strip()]
        
        # 直接构建RoleResponse（避免ORM关系错误）
        role_response = RoleResponse(
            id=row[0],
            role_code=row[1],
            role_name=row[2],
            description=row[3],
            data_scope=row[4] if row[4] else "OWN",
            is_system=bool(row[5]) if row[5] is not None else False,
            is_active=True,  # 默认启用
            permissions=permissions,
            created_at=row[7],
            updated_at=row[8],
        )
        
        return role_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取角色详情失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取角色详情失败: {str(e)}"
        )


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


@router.put("/{role_id}/nav-groups", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def update_role_nav_groups(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    nav_groups: List[Dict[str, Any]],
    request: Request,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    更新角色的导航菜单配置

    - **role_id**: 角色ID
    - **nav_groups**: 导航组配置（JSON数组）

    nav_groups 格式示例：
    [
        {
            "label": "概览",
            "items": [
                {"name": "工作台", "path": "/workstation", "icon": "LayoutDashboard"}
            ]
        }
    ]
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 更新导航组配置
    role.nav_groups = nav_groups
    db.add(role)
    db.commit()

    # 记录审计日志
    try:
        PermissionAuditService.log_role_operation(
            db=db,
            operator_id=current_user.id,
            role_id=role.id,
            action="NAV_GROUPS_UPDATED",
            changes={"nav_groups": nav_groups},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
    except Exception:
        pass  # 审计日志记录失败不影响主流程

    return ResponseModel(
        code=200,
        message="角色菜单配置更新成功"
    )


@router.get("/my/nav-groups", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_my_nav_groups(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的导航菜单组
    
    返回当前用户所属角色的导航菜单配置
    """
    try:
        logger.info(f"获取用户 {current_user.username} 的导航菜单")
        from sqlalchemy import text
        
        # 查询用户的角色（使用SQL避免ORM关系错误）
        user_roles_sql = """
            SELECT r.id, r.role_code, r.role_name
            FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = :user_id
        """
        result = db.execute(text(user_roles_sql), {"user_id": current_user.id})
        roles = result.fetchall()
        
        if not roles:
            logger.warning(f"用户 {current_user.username} 没有分配角色")
            return {
                "nav_groups": [],
                "ui_config": {}
            }
        
        # 返回空菜单（前端使用默认菜单）
        # 如果需要从数据库读取，可以在这里添加逻辑
        logger.info(f"用户 {current_user.username} 有 {len(roles)} 个角色")
        return {
            "nav_groups": [],
            "ui_config": {}
        }
        
    except Exception as e:
        logger.error(f"获取导航菜单失败: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取导航菜单失败: {str(e)}"
        )


@router.get("/{role_id}/nav-groups", response_model=Dict[str, Any], status_code=status.HTTP_200_OK)
def get_role_nav_groups(
    role_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取角色的导航菜单配置

    - **role_id**: 角色ID
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    return {
        "role_id": role.id,
        "role_code": role.role_code,
        "role_name": role.role_name,
        "nav_groups": role.nav_groups or []
    }
