# -*- coding: utf-8 -*-
"""
报价模板管理
包含：模板CRUD、版本管理、从模板创建报价
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_pagination
from app.core import security
from app.models.sales import QuoteTemplate, QuoteTemplateVersion
from app.models.user import User
from app.schemas.common import ResponseModel
from app.utils.db_helpers import delete_obj, get_or_404, save_obj

router = APIRouter()


PUBLIC_TEMPLATE_SCOPES = ("PUBLIC", "ALL")


def _json_value(value, default):
    if value is None:
        return default
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def _next_version_no(db: Session, template_id: int) -> str:
    version_count = (
        db.query(QuoteTemplateVersion)
        .filter(QuoteTemplateVersion.template_id == template_id)
        .count()
    )
    return f"V{version_count + 1}"


def _filter_visible_templates(query, current_user: User):
    if getattr(current_user, "is_superuser", False):
        return query
    return query.filter(
        or_(
            QuoteTemplate.visibility_scope.in_(PUBLIC_TEMPLATE_SCOPES),
            QuoteTemplate.owner_id == current_user.id,
        )
    )


def _can_access_template(template: QuoteTemplate, current_user: User) -> bool:
    return (
        getattr(current_user, "is_superuser", False)
        or template.visibility_scope in PUBLIC_TEMPLATE_SCOPES
        or template.owner_id == current_user.id
    )


def _can_manage_template(template: QuoteTemplate, current_user: User) -> bool:
    return getattr(current_user, "is_superuser", False) or template.owner_id == current_user.id


def _version_data(version: QuoteTemplateVersion) -> dict:
    return {
        "id": version.id,
        "version_no": version.version_no,
        "status": version.status,
        "sections": version.sections,
        "pricing_rules": version.pricing_rules,
        "config_schema": version.config_schema,
        "discount_rules": version.discount_rules,
        "release_notes": version.release_notes,
        "rule_set_id": version.rule_set_id,
        "content_json": version.sections,
        "created_by": version.created_by,
        "published_by": version.published_by,
        "published_at": version.published_at.isoformat() if version.published_at else None,
        "created_at": version.created_at.isoformat() if version.created_at else None,
    }


def _template_list_data(template: QuoteTemplate) -> dict:
    return {
        "id": template.id,
        "template_code": template.template_code,
        "template_name": template.template_name,
        "category": template.category,
        "description": template.description,
        "status": template.status,
        "visibility_scope": template.visibility_scope,
        "is_default": template.is_default,
        "current_version_id": template.current_version_id,
        "version_count": len(template.versions) if template.versions else 0,
        "owner_id": template.owner_id,
        "created_by": template.owner_id,
        "created_at": template.created_at.isoformat() if template.created_at else None,
    }


@router.get("/quotes/templates", response_model=ResponseModel)
def get_quote_templates(
    db: Session = Depends(get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    status: Optional[str] = Query(None, description="状态筛选"),
    visibility_scope: Optional[str] = Query(None, description="可见范围"),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取报价模板列表

    Args:
        db: 数据库会话
        skip: 跳过记录数
        limit: 返回记录数
        status: 状态筛选
        visibility_scope: 可见范围筛选
        current_user: 当前用户

    Returns:
        ResponseModel: 模板列表
    """
    query = db.query(QuoteTemplate).options(joinedload(QuoteTemplate.versions))

    if status:
        query = query.filter(QuoteTemplate.status == status)
    if visibility_scope:
        query = query.filter(QuoteTemplate.visibility_scope == visibility_scope)

    # 按可见范围过滤
    query = _filter_visible_templates(query, current_user)

    total = query.count()
    templates = apply_pagination(
        query.order_by(desc(QuoteTemplate.created_at)), pagination.offset, pagination.limit
    ).all()

    templates_data = [_template_list_data(t) for t in templates]

    return ResponseModel(
        code=200, message="获取模板列表成功", data={"total": total, "items": templates_data}
    )


@router.get("/quotes/templates/{template_id}", response_model=ResponseModel)
def get_template_detail(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取模板详情

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 模板详情
    """
    template = (
        db.query(QuoteTemplate)
        .options(joinedload(QuoteTemplate.versions))
        .filter(QuoteTemplate.id == template_id)
        .first()
    )

    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 权限检查
    if not _can_access_template(template, current_user):
        raise HTTPException(status_code=403, detail="无权限查看此模板")

    versions_data = (
        [_version_data(v) for v in template.versions]
        if template.versions
        else []
    )

    return ResponseModel(
        code=200,
        message="获取模板详情成功",
        data={
            "id": template.id,
            "template_code": template.template_code,
            "template_name": template.template_name,
            "category": template.category,
            "description": template.description,
            "status": template.status,
            "visibility_scope": template.visibility_scope,
            "is_default": template.is_default,
            "current_version_id": template.current_version_id,
            "owner_id": template.owner_id,
            "created_by": template.owner_id,
            "versions": versions_data,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        },
    )


@router.post("/quotes/templates", response_model=ResponseModel)
def create_quote_template(
    template_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建报价模板

    Args:
        template_data: 模板数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    # 生成模板编码
    count = db.query(QuoteTemplate).count()
    template_code = f"QT{datetime.now().strftime('%y%m%d')}{count + 1:03d}"

    template = QuoteTemplate(
        template_code=template_code,
        template_name=template_data.get("template_name", "新模板"),
        category=template_data.get("category"),
        description=template_data.get("description"),
        status="DRAFT",
        visibility_scope=template_data.get("visibility_scope", "PRIVATE"),
        is_default=template_data.get("is_default", False),
        owner_id=current_user.id,
    )
    db.add(template)
    db.flush()

    # 创建初始版本
    version = QuoteTemplateVersion(
        template_id=template.id,
        version_no=template_data.get("version_no", "V1"),
        status="DRAFT",
        sections=_json_value(
            template_data.get("sections", template_data.get("content_json")), {}
        ),
        pricing_rules=_json_value(template_data.get("pricing_rules"), None),
        config_schema=_json_value(template_data.get("config_schema"), None),
        discount_rules=_json_value(template_data.get("discount_rules"), None),
        release_notes=template_data.get("release_notes"),
        rule_set_id=template_data.get("rule_set_id"),
        created_by=current_user.id,
    )
    db.add(version)
    db.flush()

    template.current_version_id = version.id
    db.commit()

    return ResponseModel(
        code=200, message="模板创建成功", data={"id": template.id, "template_code": template_code}
    )


@router.put("/quotes/templates/{template_id}", response_model=ResponseModel)
def update_quote_template(
    template_id: int,
    template_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新报价模板

    Args:
        template_id: 模板ID
        template_data: 模板数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 更新结果
    """
    template = get_or_404(db, QuoteTemplate, template_id, detail="模板不存在")

    if not _can_manage_template(template, current_user):
        raise HTTPException(status_code=403, detail="无权限修改此模板")

    updatable = [
        "template_name",
        "category",
        "description",
        "visibility_scope",
        "is_default",
        "status",
    ]
    for field in updatable:
        if field in template_data:
            setattr(template, field, template_data[field])

    db.commit()

    return ResponseModel(code=200, message="模板更新成功", data={"id": template.id})


@router.delete("/quotes/templates/{template_id}", response_model=ResponseModel)
def delete_quote_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除报价模板

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 删除结果
    """
    template = get_or_404(db, QuoteTemplate, template_id, detail="模板不存在")

    if not _can_manage_template(template, current_user):
        raise HTTPException(status_code=403, detail="无权限删除此模板")

    if template.status == "PUBLISHED":
        raise HTTPException(status_code=400, detail="已发布的模板不能删除")

    delete_obj(db, template)

    return ResponseModel(code=200, message="模板删除成功", data={"id": template_id})


@router.post("/quotes/templates/{template_id}/versions", response_model=ResponseModel)
def create_template_version(
    template_id: int,
    version_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建模板新版本

    Args:
        template_id: 模板ID
        version_data: 版本数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 创建结果
    """
    template = get_or_404(db, QuoteTemplate, template_id, detail="模板不存在")

    if not _can_manage_template(template, current_user):
        raise HTTPException(status_code=403, detail="无权限操作此模板")

    new_version_no = version_data.get("version_no") or _next_version_no(db, template_id)

    version = QuoteTemplateVersion(
        template_id=template_id,
        version_no=new_version_no,
        status="DRAFT",
        sections=_json_value(
            version_data.get("sections", version_data.get("content_json")), {}
        ),
        pricing_rules=_json_value(version_data.get("pricing_rules"), None),
        config_schema=_json_value(version_data.get("config_schema"), None),
        discount_rules=_json_value(version_data.get("discount_rules"), None),
        release_notes=version_data.get("release_notes"),
        rule_set_id=version_data.get("rule_set_id"),
        created_by=current_user.id,
    )
    save_obj(db, version)

    return ResponseModel(
        code=200, message="版本创建成功", data={"id": version.id, "version_no": new_version_no}
    )


@router.post("/quotes/templates/{template_id}/publish", response_model=ResponseModel)
def publish_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    发布模板

    Args:
        template_id: 模板ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 发布结果
    """
    template = get_or_404(db, QuoteTemplate, template_id, detail="模板不存在")

    if not _can_manage_template(template, current_user):
        raise HTTPException(status_code=403, detail="无权限操作此模板")

    if not template.current_version_id:
        raise HTTPException(status_code=400, detail="模板没有版本，无法发布")

    # 更新当前版本状态
    version = (
        db.query(QuoteTemplateVersion)
        .filter(QuoteTemplateVersion.id == template.current_version_id)
        .first()
    )
    if version:
        version.status = "PUBLISHED"
        version.published_at = datetime.now()
        version.published_by = current_user.id

    template.status = "PUBLISHED"
    db.commit()

    return ResponseModel(code=200, message="模板发布成功", data={"id": template.id})
