# -*- coding: utf-8 -*-
"""
角色模板 API endpoints
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import Role, RolePermission, RoleTemplate, User
from app.schemas.auth import RoleTemplateCreate, RoleTemplateUpdate
from app.schemas.common import ResponseModel

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=ResponseModel)
def list_role_templates(
    *,
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取角色模板列表
    """
    templates = (
        db.query(RoleTemplate)
        .filter(RoleTemplate.is_active == True)
        .order_by(RoleTemplate.sort_order)
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = db.query(RoleTemplate).filter(RoleTemplate.is_active == True).count()

    return ResponseModel(
        code=200,
        message="success",
        data={
            "items": [
                {
                    "id": t.id,
                    "template_code": t.template_code,
                    "template_name": t.template_name,
                    "description": t.description,
                    "data_scope": t.data_scope,
                    "permission_ids": t.permission_ids or [],
                    "is_active": t.is_active,
                    "sort_order": t.sort_order,
                }
                for t in templates
            ],
            "total": total,
        }
    )


@router.get("/{template_id}", response_model=ResponseModel)
def get_role_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.require_permission("ROLE_VIEW")),
) -> Any:
    """
    获取单个角色模板详情
    """
    template = db.query(RoleTemplate).filter(RoleTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="角色模板不存在")

    return ResponseModel(
        code=200,
        message="success",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "description": template.description,
            "data_scope": template.data_scope,
            "permission_ids": template.permission_ids or [],
            "is_active": template.is_active,
            "sort_order": template.sort_order,
        }
    )


@router.post("/", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_role_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: RoleTemplateCreate,
    current_user: User = Depends(security.require_permission("ROLE_CREATE")),
) -> Any:
    """
    创建角色模板
    """
    existing = db.query(RoleTemplate).filter(
        RoleTemplate.template_code == template_in.template_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = RoleTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        description=template_in.description,
        data_scope=template_in.data_scope,
        permission_ids=template_in.permission_ids,
        sort_order=template_in.sort_order,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(
        code=200,
        message="角色模板创建成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
        }
    )


@router.put("/{template_id}", response_model=ResponseModel)
def update_role_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: RoleTemplateUpdate,
    current_user: User = Depends(security.require_permission("ROLE_UPDATE")),
) -> Any:
    """
    更新角色模板
    """
    template = db.query(RoleTemplate).filter(RoleTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="角色模板不存在")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.add(template)
    db.commit()
    db.refresh(template)

    return ResponseModel(
        code=200,
        message="角色模板更新成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
        }
    )


@router.delete("/{template_id}", response_model=ResponseModel)
def delete_role_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    current_user: User = Depends(security.require_permission("ROLE_DELETE")),
) -> Any:
    """
    删除角色模板（软删除）
    """
    template = db.query(RoleTemplate).filter(RoleTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="角色模板不存在")

    template.is_active = False
    db.add(template)
    db.commit()

    return ResponseModel(code=200, message="角色模板删除成功")


@router.post("/{template_id}/create-role", response_model=ResponseModel)
def create_role_from_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    role_code: str,
    role_name: str,
    description: str = None,
    current_user: User = Depends(security.require_permission("ROLE_CREATE")),
) -> Any:
    """
    从模板创建角色

    - 使用模板的数据权限范围和权限配置
    - 需要提供新角色的编码和名称
    """
    template = db.query(RoleTemplate).filter(
        RoleTemplate.id == template_id,
        RoleTemplate.is_active == True
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="角色模板不存在或已禁用")

    # 检查角色编码是否已存在
    existing_role = db.query(Role).filter(Role.role_code == role_code).first()
    if existing_role:
        raise HTTPException(status_code=400, detail="角色编码已存在")

    # 创建角色
    role = Role(
        role_code=role_code,
        role_name=role_name,
        description=description or template.description,
        data_scope=template.data_scope,
    )
    db.add(role)
    db.commit()
    db.refresh(role)

    # 分配模板中的权限
    if template.permission_ids:
        for perm_id in template.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=perm_id))
        db.commit()

    return ResponseModel(
        code=200,
        message="角色创建成功",
        data={
            "id": role.id,
            "role_code": role.role_code,
            "role_name": role.role_name,
            "data_scope": role.data_scope,
            "template_used": template.template_name,
            "permission_count": len(template.permission_ids) if template.permission_ids else 0,
        }
    )
