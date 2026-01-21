# -*- coding: utf-8 -*-
"""
数据权限规则管理

提供 DataScopeRule 和 RoleDataScope 的 CRUD 操作
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.permission_v2 import DataScopeRule, RoleDataScope, ResourceType
from app.models.user import Role, User
from app.schemas.common import PaginatedResponse, ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# Schemas
# ============================================================

class DataScopeRuleCreate(BaseModel):
    """创建数据权限规则"""
    rule_code: str = Field(..., min_length=1, max_length=50, description="规则编码")
    rule_name: str = Field(..., min_length=1, max_length=100, description="规则名称")
    scope_type: str = Field(..., description="范围类型: ALL/DEPARTMENT/TEAM/PROJECT/OWN/CUSTOM")
    scope_config: Optional[dict] = Field(None, description="自定义规则配置")
    description: Optional[str] = Field(None, description="规则描述")


class DataScopeRuleUpdate(BaseModel):
    """更新数据权限规则"""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=100)
    scope_type: Optional[str] = None
    scope_config: Optional[dict] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class RoleDataScopeAssign(BaseModel):
    """分配角色数据权限"""
    resource_type: str = Field(..., description="资源类型")
    scope_rule_id: int = Field(..., description="数据权限规则ID")


# ============================================================
# DataScopeRule CRUD
# ============================================================

@router.get("/data-scope-rules", response_model=PaginatedResponse)
def list_data_scope_rules(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    scope_type: Optional[str] = Query(None, description="范围类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用筛选"),
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """获取数据权限规则列表"""
    query = db.query(DataScopeRule)

    if scope_type:
        query = query.filter(DataScopeRule.scope_type == scope_type)
    if is_active is not None:
        query = query.filter(DataScopeRule.is_active == is_active)

    total = query.count()
    offset = (page - 1) * page_size
    rules = query.order_by(DataScopeRule.id).offset(offset).limit(page_size).all()

    items = [
        {
            "id": rule.id,
            "rule_code": rule.rule_code,
            "rule_name": rule.rule_name,
            "scope_type": rule.scope_type,
            "scope_config": rule.scope_config,
            "description": rule.description,
            "is_active": rule.is_active,
            "created_at": rule.created_at.isoformat() if rule.created_at else None,
        }
        for rule in rules
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size if page_size > 0 else 0
    )


@router.post("/data-scope-rules", response_model=ResponseModel)
def create_data_scope_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_in: DataScopeRuleCreate,
    current_user: User = Depends(security.require_permission("ROLE_CREATE")),
) -> Any:
    """创建数据权限规则"""
    # 检查编码是否已存在
    existing = db.query(DataScopeRule).filter(
        DataScopeRule.rule_code == rule_in.rule_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="规则编码已存在")

    # 验证 scope_type
    valid_types = ["ALL", "BUSINESS_UNIT", "DEPARTMENT", "TEAM", "PROJECT", "OWN", "CUSTOM"]
    if rule_in.scope_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"无效的范围类型，有效值: {valid_types}")

    # CUSTOM 类型必须提供 scope_config
    if rule_in.scope_type == "CUSTOM" and not rule_in.scope_config:
        raise HTTPException(status_code=400, detail="自定义规则必须提供 scope_config")

    # 验证 scope_config 格式
    if rule_in.scope_type == "CUSTOM" and rule_in.scope_config:
        from app.services.data_scope import CustomRuleService
        errors = CustomRuleService.validate_scope_config(rule_in.scope_config)
        if errors:
            raise HTTPException(
                status_code=400,
                detail=f"scope_config 配置无效: {'; '.join(errors)}"
            )

    rule = DataScopeRule(
        rule_code=rule_in.rule_code,
        rule_name=rule_in.rule_name,
        scope_type=rule_in.scope_type,
        scope_config=rule_in.scope_config,
        description=rule_in.description,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return ResponseModel(
        code=200,
        message="创建成功",
        data={
            "id": rule.id,
            "rule_code": rule.rule_code,
            "rule_name": rule.rule_name,
            "scope_type": rule.scope_type,
        }
    )


@router.put("/data-scope-rules/{rule_id}", response_model=ResponseModel)
def update_data_scope_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    rule_in: DataScopeRuleUpdate,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """更新数据权限规则"""
    rule = db.query(DataScopeRule).filter(DataScopeRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    update_data = rule_in.model_dump(exclude_unset=True)

    # 验证 scope_type
    if "scope_type" in update_data:
        valid_types = ["ALL", "BUSINESS_UNIT", "DEPARTMENT", "TEAM", "PROJECT", "OWN", "CUSTOM"]
        if update_data["scope_type"] not in valid_types:
            raise HTTPException(status_code=400, detail="无效的范围类型")

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.add(rule)
    db.commit()

    return ResponseModel(code=200, message="更新成功")


@router.delete("/data-scope-rules/{rule_id}", response_model=ResponseModel)
def delete_data_scope_rule(
    *,
    db: Session = Depends(deps.get_db),
    rule_id: int,
    current_user: User = Depends(security.require_permission("ROLE_DELETE")),
) -> Any:
    """删除数据权限规则"""
    rule = db.query(DataScopeRule).filter(DataScopeRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    # 检查是否有角色在使用
    usage_count = db.query(RoleDataScope).filter(
        RoleDataScope.scope_rule_id == rule_id
    ).count()
    if usage_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"该规则正在被 {usage_count} 个角色使用，无法删除"
        )

    db.delete(rule)
    db.commit()

    return ResponseModel(code=200, message="删除成功")


# ============================================================
# RoleDataScope 管理
# ============================================================

@router.get("/{role_id}/data-scopes", response_model=ResponseModel)
def get_role_data_scopes(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """获取角色的数据权限配置"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    scopes = db.query(RoleDataScope).filter(
        RoleDataScope.role_id == role_id,
        RoleDataScope.is_active == True
    ).all()

    items = []
    for scope in scopes:
        rule = scope.scope_rule
        items.append({
            "id": scope.id,
            "resource_type": scope.resource_type,
            "scope_rule_id": scope.scope_rule_id,
            "scope_rule_code": rule.rule_code if rule else None,
            "scope_rule_name": rule.rule_name if rule else None,
            "scope_type": rule.scope_type if rule else None,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "role_id": role_id,
            "role_name": role.role_name,
            "default_data_scope": role.data_scope,
            "resource_scopes": items,
            "available_resource_types": [
                {"code": ResourceType.PROJECT, "name": "项目"},
                {"code": ResourceType.CUSTOMER, "name": "客户"},
                {"code": ResourceType.OPPORTUNITY, "name": "商机"},
                {"code": ResourceType.CONTRACT, "name": "合同"},
                {"code": ResourceType.EMPLOYEE, "name": "员工"},
                {"code": ResourceType.MATERIAL, "name": "物料"},
                {"code": ResourceType.SUPPLIER, "name": "供应商"},
            ]
        }
    )


@router.post("/{role_id}/data-scopes", response_model=ResponseModel)
def assign_role_data_scope(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    scope_in: RoleDataScopeAssign,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """为角色分配资源级数据权限"""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    rule = db.query(DataScopeRule).filter(
        DataScopeRule.id == scope_in.scope_rule_id
    ).first()
    if not rule:
        raise HTTPException(status_code=404, detail="数据权限规则不存在")

    # 检查是否已存在
    existing = db.query(RoleDataScope).filter(
        RoleDataScope.role_id == role_id,
        RoleDataScope.resource_type == scope_in.resource_type
    ).first()

    if existing:
        # 更新现有配置
        existing.scope_rule_id = scope_in.scope_rule_id
        existing.is_active = True
        db.add(existing)
    else:
        # 创建新配置
        role_scope = RoleDataScope(
            role_id=role_id,
            resource_type=scope_in.resource_type,
            scope_rule_id=scope_in.scope_rule_id,
        )
        db.add(role_scope)

    db.commit()

    # 清除缓存
    try:
        from .utils import _invalidate_role_cache
        _invalidate_role_cache(db, role_id, include_children=True)
    except Exception as e:
        logger.warning(f"缓存清除失败: {e}")

    return ResponseModel(code=200, message="分配成功")


@router.delete("/{role_id}/data-scopes/{resource_type}", response_model=ResponseModel)
def remove_role_data_scope(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    resource_type: str,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """移除角色的资源级数据权限"""
    scope = db.query(RoleDataScope).filter(
        RoleDataScope.role_id == role_id,
        RoleDataScope.resource_type == resource_type
    ).first()

    if not scope:
        raise HTTPException(status_code=404, detail="数据权限配置不存在")

    db.delete(scope)
    db.commit()

    # 清除缓存
    try:
        from .utils import _invalidate_role_cache
        _invalidate_role_cache(db, role_id, include_children=True)
    except Exception as e:
        logger.warning(f"缓存清除失败: {e}")

    return ResponseModel(code=200, message="移除成功")
