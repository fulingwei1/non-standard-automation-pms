# -*- coding: utf-8 -*-
"""
权限矩阵 API endpoints

提供权限矩阵结构、权限依赖关系等接口
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import ApiPermission, Role, RoleApiPermission, User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/matrix", response_model=ResponseModel)
def get_permission_matrix(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取权限矩阵结构（使用新的 ApiPermission 模型）

    返回按 模块 → 页面 → 操作 组织的权限树形结构
    """
    permissions = db.query(ApiPermission).filter(ApiPermission.is_active == True).all()

    # 构建矩阵结构: module → page → action
    matrix: Dict[str, Dict[str, List[Dict]]] = {}

    for perm in permissions:
        module = perm.module or "OTHER"
        page = perm.page_code or "general"
        action = perm.action or "OTHER"

        if module not in matrix:
            matrix[module] = {}
        if page not in matrix[module]:
            matrix[module][page] = []

        matrix[module][page].append(
            {
                "id": perm.id,
                "code": perm.perm_code,
                "name": perm.perm_name,
                "action": action,
                "description": perm.description,
            }
        )

    # 转换为前端友好的格式
    result = []
    for module_code, pages in matrix.items():
        module_item = {
            "module_code": module_code,
            "module_name": MODULE_NAMES.get(module_code, module_code),
            "pages": [],
        }
        for page_code, perms in pages.items():
            page_item = {
                "page_code": page_code,
                "page_name": PAGE_NAMES.get(page_code, page_code),
                "permissions": perms,
            }
            module_item["pages"].append(page_item)
        result.append(module_item)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "matrix": result,
            "action_types": ACTION_TYPES,
        },
    )


@router.get("/dependencies", response_model=ResponseModel)
def get_permission_dependencies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取权限依赖关系（新模型暂不支持 depends_on 字段，返回空列表）

    返回所有权限的依赖关系映射
    """
    # 新的 ApiPermission 模型暂无 depends_on 字段，返回空列表
    # 如果需要权限依赖，可以在后续版本中添加
    return ResponseModel(code=200, message="success", data={"dependencies": []})


@router.get("/by-role/{role_id}", response_model=ResponseModel)
def get_role_permissions(
    role_id: int,
    include_inherited: bool = Query(True, description="是否包含继承的权限"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取角色的权限列表（支持继承）- 使用新的 ApiPermission 模型
    """
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        return ResponseModel(code=404, message="角色不存在", data=None)

    # 获取直接分配的权限（使用新的关联表）
    direct_perms = (
        db.query(ApiPermission)
        .join(RoleApiPermission)
        .filter(RoleApiPermission.role_id == role_id, ApiPermission.is_active == True)
        .all()
    )

    direct_perm_ids = {p.id for p in direct_perms}

    # 获取继承的权限
    inherited_perm_ids = set()
    inherited_from = {}

    if include_inherited and role.parent_id:
        parent_roles = _get_parent_roles(db, role.parent_id)
        for parent_role in parent_roles:
            parent_perms = (
                db.query(ApiPermission)
                .join(RoleApiPermission)
                .filter(
                    RoleApiPermission.role_id == parent_role.id,
                    ApiPermission.is_active == True,
                )
                .all()
            )
            for p in parent_perms:
                if p.id not in direct_perm_ids:
                    inherited_perm_ids.add(p.id)
                    if p.id not in inherited_from:
                        inherited_from[p.id] = parent_role.role_name

    # 构建返回结果
    result = []
    for perm in direct_perms:
        result.append(
            {
                "id": perm.id,
                "code": perm.perm_code,
                "name": perm.perm_name,
                "module": perm.module,
                "page_code": perm.page_code,
                "action": perm.action,
                "is_inherited": False,
                "inherited_from": None,
            }
        )

    if inherited_perm_ids:
        inherited_perms = (
            db.query(ApiPermission)
            .filter(ApiPermission.id.in_(inherited_perm_ids))
            .all()
        )
        for perm in inherited_perms:
            result.append(
                {
                    "id": perm.id,
                    "code": perm.perm_code,
                    "name": perm.perm_name,
                    "module": perm.module,
                    "page_code": perm.page_code,
                    "action": perm.action,
                    "is_inherited": True,
                    "inherited_from": inherited_from.get(perm.id),
                }
            )

    return ResponseModel(
        code=200,
        message="success",
        data={
            "role_id": role_id,
            "role_name": role.role_name,
            "parent_id": role.parent_id,
            "permissions": result,
            "direct_count": len(direct_perm_ids),
            "inherited_count": len(inherited_perm_ids),
            "total_count": len(result),
        },
    )


def _get_parent_roles(db: Session, parent_id: int, visited: set = None) -> List[Role]:
    """递归获取所有父角色（防止循环引用）"""
    if visited is None:
        visited = set()

    if parent_id in visited:
        return []

    visited.add(parent_id)
    parent = db.query(Role).filter(Role.id == parent_id).first()
    if not parent:
        return []

    result = [parent]
    if parent.parent_id:
        result.extend(_get_parent_roles(db, parent.parent_id, visited))

    return result


# ============================================================
# 常量定义
# ============================================================

MODULE_NAMES = {
    "SALES": "销售管理",
    "PROJECT": "项目管理",
    "MATERIAL": "物料管理",
    "PURCHASE": "采购管理",
    "PRODUCTION": "生产管理",
    "FINANCE": "财务管理",
    "HR": "人力资源",
    "SYSTEM": "系统管理",
    "OTHER": "其他",
}

MODULE_ORDER = {
    "SALES": 1,
    "PROJECT": 2,
    "MATERIAL": 3,
    "PURCHASE": 4,
    "PRODUCTION": 5,
    "FINANCE": 6,
    "HR": 7,
    "SYSTEM": 8,
    "OTHER": 99,
}

PAGE_NAMES = {
    # 销售模块
    "leads": "线索管理",
    "opportunities": "商机管理",
    "quotes": "报价管理",
    "contracts": "合同管理",
    "invoices": "发票管理",
    "receivables": "应收管理",
    # 项目模块
    "projects": "项目列表",
    "tasks": "任务管理",
    "milestones": "里程碑",
    "progress": "进度跟踪",
    # 系统模块
    "users": "用户管理",
    "roles": "角色管理",
    "permissions": "权限管理",
    "departments": "部门管理",
    # 默认
    "general": "通用",
}

ACTION_TYPES = [
    {"code": "VIEW", "name": "查看", "description": "查看数据"},
    {"code": "CREATE", "name": "创建", "description": "创建新数据"},
    {"code": "EDIT", "name": "编辑", "description": "修改现有数据"},
    {"code": "DELETE", "name": "删除", "description": "删除数据"},
    {"code": "APPROVE", "name": "审批", "description": "审批流程"},
    {"code": "EXPORT", "name": "导出", "description": "导出数据"},
]
