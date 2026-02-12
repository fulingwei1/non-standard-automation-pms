# -*- coding: utf-8 -*-
"""
报价模板管理 API endpoints

包含报价模板的CRUD、版本管理和应用功能
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.models.sales import QuoteTemplate, QuoteTemplateVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.schemas.sales import (
    CpqPricePreviewRequest,
    CpqPricePreviewResponse,
    QuoteTemplateApplyResponse,
    QuoteTemplateCreate,
    QuoteTemplateResponse,
    QuoteTemplateUpdate,
    QuoteTemplateVersionCreate,
    QuoteTemplateVersionResponse,
)
from app.services.cpq_pricing_service import CpqPricingService

from .common import (
    _build_template_history,
    _build_template_version_diff,
    _filter_template_visibility,
    _get_previous_version,
    _serialize_quote_template,
)

router = APIRouter()


@router.get("/quote-templates", response_model=PaginatedResponse[QuoteTemplateResponse])
def list_quote_templates(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取报价模板列表"""
    query = db.query(QuoteTemplate).options(joinedload(QuoteTemplate.versions))
    query = _filter_template_visibility(query, QuoteTemplate, current_user)

    query = apply_keyword_filter(query, QuoteTemplate, keyword, ["template_name", "template_code"])
    if status:
        query = query.filter(QuoteTemplate.status == status)

    total = query.count()
    templates = (
        query.order_by(desc(QuoteTemplate.created_at))
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )
    items = [_serialize_quote_template(t) for t in templates]
    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/quote-templates", response_model=QuoteTemplateResponse)
def create_quote_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: QuoteTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建报价模板"""
    existing = (
        db.query(QuoteTemplate)
        .filter(QuoteTemplate.template_code == template_in.template_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = QuoteTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        category=template_in.category,
        description=template_in.description,
        visibility_scope=template_in.visibility_scope or "TEAM",
        is_default=template_in.is_default or False,
        owner_id=template_in.owner_id or current_user.id,
        status="DRAFT",
    )
    db.add(template)
    db.flush()

    if template_in.initial_version:
        version_data = template_in.initial_version
        version = QuoteTemplateVersion(
            template_id=template.id,
            version_no=version_data.version_no,
            sections=version_data.sections,
            pricing_rules=version_data.pricing_rules,
            config_schema=version_data.config_schema,
            discount_rules=version_data.discount_rules,
            release_notes=version_data.release_notes,
            rule_set_id=version_data.rule_set_id,
            status="DRAFT",
            created_by=current_user.id,
        )
        db.add(version)
        db.flush()
        template.current_version_id = version.id

    db.commit()
    db.refresh(template)
    template = (
        db.query(QuoteTemplate)
        .options(joinedload(QuoteTemplate.versions))
        .filter(QuoteTemplate.id == template.id)
        .first()
    )
    return _serialize_quote_template(template)


@router.put("/quote-templates/{template_id}", response_model=QuoteTemplateResponse)
def update_quote_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: QuoteTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新报价模板"""
    template = (
        _filter_template_visibility(
            db.query(QuoteTemplate).options(joinedload(QuoteTemplate.versions)),
            QuoteTemplate,
            current_user,
        )
        .filter(QuoteTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权访问")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    db.commit()
    db.refresh(template)
    template = (
        db.query(QuoteTemplate)
        .options(joinedload(QuoteTemplate.versions))
        .filter(QuoteTemplate.id == template_id)
        .first()
    )
    return _serialize_quote_template(template)


@router.post("/quote-templates/{template_id}/versions", response_model=QuoteTemplateVersionResponse)
def create_quote_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_in: QuoteTemplateVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建报价模板版本"""
    template = (
        _filter_template_visibility(
            db.query(QuoteTemplate),
            QuoteTemplate,
            current_user,
        )
        .filter(QuoteTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权访问")

    version = QuoteTemplateVersion(
        template_id=template_id,
        version_no=version_in.version_no,
        sections=version_in.sections,
        pricing_rules=version_in.pricing_rules,
        config_schema=version_in.config_schema,
        discount_rules=version_in.discount_rules,
        release_notes=version_in.release_notes,
        rule_set_id=version_in.rule_set_id,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return QuoteTemplateVersionResponse(
        id=version.id,
        template_id=version.template_id,
        version_no=version.version_no,
        status=version.status,
        sections=version.sections,
        pricing_rules=version.pricing_rules,
        config_schema=version.config_schema,
        discount_rules=version.discount_rules,
        release_notes=version.release_notes,
        rule_set_id=version.rule_set_id,
        created_by=version.created_by,
        published_by=version.published_by,
        published_at=version.published_at,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.post("/quote-templates/{template_id}/versions/{version_id}/publish", response_model=QuoteTemplateResponse)
def publish_quote_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """发布报价模板版本"""
    template = (
        db.query(QuoteTemplate)
        .options(joinedload(QuoteTemplate.versions))
        .filter(QuoteTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    version = next((v for v in template.versions if v.id == version_id), None)
    if not version:
        raise HTTPException(status_code=404, detail="模板版本不存在")

    version.status = "PUBLISHED"
    version.published_by = current_user.id
    version.published_at = datetime.now(timezone.utc)
    template.current_version_id = version.id
    template.status = "ACTIVE"
    db.query(QuoteTemplateVersion).filter(
        QuoteTemplateVersion.template_id == template_id,
        QuoteTemplateVersion.id != version_id,
        QuoteTemplateVersion.status == "PUBLISHED",
    ).update({"status": "ARCHIVED"}, synchronize_session=False)

    db.commit()
    template = (
        db.query(QuoteTemplate)
        .options(joinedload(QuoteTemplate.versions))
        .filter(QuoteTemplate.id == template_id)
        .first()
    )
    return _serialize_quote_template(template)


@router.post("/quote-templates/{template_id}/apply", response_model=QuoteTemplateApplyResponse)
def apply_quote_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    preview_request: Optional[CpqPricePreviewRequest] = None,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """应用报价模板并预览价格"""
    template = (
        _filter_template_visibility(
            db.query(QuoteTemplate).options(joinedload(QuoteTemplate.versions)),
            QuoteTemplate,
            current_user,
        )
        .filter(QuoteTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权访问")

    version = None
    if preview_request and preview_request.template_version_id:
        version = next(
            (v for v in template.versions if v.id == preview_request.template_version_id),
            None,
        )
    if not version:
        version = template.current_version or (template.versions[0] if template.versions else None)

    if not version:
        raise HTTPException(status_code=400, detail="模板尚未创建版本")

    preview = preview_request or CpqPricePreviewRequest()
    service = CpqPricingService(db)
    preview_data = service.preview_price(
        rule_set_id=preview.rule_set_id or version.rule_set_id,
        template_version_id=version.id,
        selections=preview.selections,
        manual_discount_pct=preview.manual_discount_pct,
        manual_markup_pct=preview.manual_markup_pct,
    )

    previous_version = _get_previous_version(template, version)
    version_diff = _build_template_version_diff(version, previous_version)
    history = _build_template_history(template)

    return QuoteTemplateApplyResponse(
        template=_serialize_quote_template(template),
        version=QuoteTemplateVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_no=version.version_no,
            status=version.status,
            sections=version.sections,
            pricing_rules=version.pricing_rules,
            config_schema=version.config_schema,
            discount_rules=version.discount_rules,
            release_notes=version.release_notes,
            rule_set_id=version.rule_set_id,
            created_by=version.created_by,
            published_by=version.published_by,
            published_at=version.published_at,
            created_at=version.created_at,
            updated_at=version.updated_at,
        ),
        cpq_preview=CpqPricePreviewResponse(**preview_data),
        version_diff=version_diff,
        approval_history=history,
    )
