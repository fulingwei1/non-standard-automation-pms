# -*- coding: utf-8 -*-
"""
模板管理 API endpoints

包含报价模板、合同模板和CPQ规则集管理
"""

from typing import Any, List, Optional, Dict
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, aliased
from sqlalchemy import desc, or_, and_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.sales import (
    QuoteTemplate, QuoteTemplateVersion,
    ContractTemplate, ContractTemplateVersion,
    CpqRuleSet
)
from app.schemas.sales import (
    QuoteTemplateCreate, QuoteTemplateUpdate, QuoteTemplateResponse,
    QuoteTemplateVersionCreate, QuoteTemplateVersionResponse,
    QuoteTemplateApplyResponse,
    ContractTemplateCreate, ContractTemplateUpdate, ContractTemplateResponse,
    ContractTemplateVersionCreate, ContractTemplateVersionResponse,
    ContractTemplateApplyResponse,
    CpqRuleSetCreate, CpqRuleSetUpdate, CpqRuleSetResponse,
    CpqPricePreviewRequest, CpqPricePreviewResponse,
    TemplateVersionDiff, TemplateApprovalHistoryRecord
)
from app.schemas.common import PaginatedResponse
from app.services.cpq_pricing_service import CpqPricingService

router = APIRouter()


# ==================== 辅助函数 ====================


def _flatten_structure(data: Any, prefix: str = "") -> Dict[str, Any]:
    """将嵌套结构展开便于比较"""
    entries: Dict[str, Any] = {}
    if data is None:
        return entries
    if isinstance(data, dict):
        for key, value in data.items():
            sub_prefix = f"{prefix}.{key}" if prefix else str(key)
            entries.update(_flatten_structure(value, sub_prefix))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            sub_prefix = f"{prefix}[{index}]" if prefix else f"[{index}]"
            entries.update(_flatten_structure(value, sub_prefix))
    else:
        entries[prefix or "value"] = data
    return entries


def _build_diff_section(current: Any, previous: Any) -> Dict[str, Any]:
    current_flat = _flatten_structure(current)
    previous_flat = _flatten_structure(previous)

    added = sorted(list(set(current_flat.keys()) - set(previous_flat.keys())))
    removed = sorted(list(set(previous_flat.keys()) - set(current_flat.keys())))
    changed = []
    for key in current_flat.keys() & previous_flat.keys():
        if current_flat[key] != previous_flat[key]:
            changed.append(
                {
                    "path": key,
                    "old": previous_flat[key],
                    "new": current_flat[key],
                }
            )
    return {
        "added": added,
        "removed": removed,
        "changed": changed,
    }


def _get_previous_version(template, current_version):
    if not template or not template.versions:
        return None
    versions = sorted(
        template.versions,
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    for idx, version in enumerate(versions):
        if version.id == current_version.id and idx + 1 < len(versions):
            return versions[idx + 1]
    return None


def _build_template_version_diff(current_version, previous_version) -> TemplateVersionDiff:
    sections_diff = _build_diff_section(
        getattr(current_version, "sections", None),
        getattr(previous_version, "sections", None) if previous_version else None,
    )
    pricing_diff = _build_diff_section(
        getattr(current_version, "pricing_rules", None),
        getattr(previous_version, "pricing_rules", None) if previous_version else None,
    )
    clause_diff = _build_diff_section(
        getattr(current_version, "clause_sections", None),
        getattr(previous_version, "clause_sections", None) if previous_version else None,
    )
    return TemplateVersionDiff(
        sections=sections_diff,
        pricing_rules=pricing_diff,
        clause_sections=clause_diff,
    )


def _build_template_history(template) -> List[TemplateApprovalHistoryRecord]:
    if not template or not template.versions:
        return []
    versions = sorted(
        template.versions,
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    history = []
    for version in versions[:10]:
        history.append(
            TemplateApprovalHistoryRecord(
                version_id=version.id,
                version_no=version.version_no,
                status=version.status,
                published_by=version.published_by,
                published_at=version.published_at,
                release_notes=version.release_notes,
            )
        )
    return history


def _filter_template_visibility(query, model, user: User):
    """根据可见范围过滤模板"""
    if user.is_superuser:
        return query
    owner_alias = aliased(User)
    query = query.outerjoin(owner_alias, model.owner)
    conditions = [
        model.visibility_scope == "ALL",
        model.owner_id == user.id,
    ]
    if user.department:
        conditions.append(
            and_(
                model.visibility_scope.in_(["TEAM", "DEPT"]),
                owner_alias.department == user.department,
            )
        )
    return query.filter(or_(*conditions))


def _serialize_quote_template(template: QuoteTemplate) -> QuoteTemplateResponse:
    versions = sorted(
        template.versions or [],
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    version_responses = [
        QuoteTemplateVersionResponse(
            id=v.id,
            template_id=v.template_id,
            version_no=v.version_no,
            status=v.status,
            sections=v.sections,
            pricing_rules=v.pricing_rules,
            config_schema=v.config_schema,
            discount_rules=v.discount_rules,
            release_notes=v.release_notes,
            rule_set_id=v.rule_set_id,
            created_by=v.created_by,
            published_by=v.published_by,
            published_at=v.published_at,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in versions
    ]
    return QuoteTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        category=template.category,
        description=template.description,
        status=template.status,
        visibility_scope=template.visibility_scope,
        is_default=template.is_default,
        current_version_id=template.current_version_id,
        owner_id=template.owner_id,
        versions=version_responses,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _serialize_contract_template(template: ContractTemplate) -> ContractTemplateResponse:
    versions = sorted(
        template.versions or [],
        key=lambda v: v.created_at or datetime.min,
        reverse=True,
    )
    version_responses = [
        ContractTemplateVersionResponse(
            id=v.id,
            template_id=v.template_id,
            version_no=v.version_no,
            status=v.status,
            clause_sections=v.clause_sections,
            clause_library=v.clause_library,
            attachment_refs=v.attachment_refs,
            approval_flow=v.approval_flow,
            release_notes=v.release_notes,
            created_by=v.created_by,
            published_by=v.published_by,
            published_at=v.published_at,
            created_at=v.created_at,
            updated_at=v.updated_at,
        )
        for v in versions
    ]
    return ContractTemplateResponse(
        id=template.id,
        template_code=template.template_code,
        template_name=template.template_name,
        contract_type=template.contract_type,
        description=template.description,
        status=template.status,
        visibility_scope=template.visibility_scope,
        is_default=template.is_default,
        current_version_id=template.current_version_id,
        owner_id=template.owner_id,
        versions=version_responses,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def _serialize_rule_set(rule_set: CpqRuleSet) -> CpqRuleSetResponse:
    return CpqRuleSetResponse(
        id=rule_set.id,
        rule_code=rule_set.rule_code,
        rule_name=rule_set.rule_name,
        description=rule_set.description,
        status=rule_set.status,
        base_price=rule_set.base_price or Decimal("0"),
        currency=rule_set.currency or "CNY",
        config_schema=rule_set.config_schema,
        pricing_matrix=rule_set.pricing_matrix,
        approval_threshold=rule_set.approval_threshold,
        visibility_scope=rule_set.visibility_scope or "ALL",
        is_default=rule_set.is_default or False,
        owner_role=rule_set.owner_role,
        created_at=rule_set.created_at,
        updated_at=rule_set.updated_at,
    )


# ==================== 报价模板端点 ====================


@router.get("/quote-templates", response_model=PaginatedResponse[QuoteTemplateResponse])
def list_quote_templates(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(QuoteTemplate).options(joinedload(QuoteTemplate.versions))
    query = _filter_template_visibility(query, QuoteTemplate, current_user)

    if keyword:
        query = query.filter(
            or_(
                QuoteTemplate.template_name.contains(keyword),
                QuoteTemplate.template_code.contains(keyword),
            )
        )
    if status:
        query = query.filter(QuoteTemplate.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    templates = (
        query.order_by(desc(QuoteTemplate.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )
    items = [_serialize_quote_template(t) for t in templates]
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/quote-templates", response_model=QuoteTemplateResponse)
def create_quote_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: QuoteTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
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
    version.published_at = datetime.utcnow()
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


# ==================== 合同模板端点 ====================


@router.get("/contract-templates", response_model=PaginatedResponse[ContractTemplateResponse])
def list_contract_templates(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(ContractTemplate).options(joinedload(ContractTemplate.versions))
    query = _filter_template_visibility(query, ContractTemplate, current_user)

    if keyword:
        query = query.filter(
            or_(
                ContractTemplate.template_name.contains(keyword),
                ContractTemplate.template_code.contains(keyword),
            )
        )
    if status:
        query = query.filter(ContractTemplate.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    templates = (
        query.order_by(desc(ContractTemplate.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse(
        items=[_serialize_contract_template(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/contract-templates", response_model=ContractTemplateResponse)
def create_contract_template(
    *,
    db: Session = Depends(deps.get_db),
    template_in: ContractTemplateCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    existing = (
        db.query(ContractTemplate)
        .filter(ContractTemplate.template_code == template_in.template_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="模板编码已存在")

    template = ContractTemplate(
        template_code=template_in.template_code,
        template_name=template_in.template_name,
        contract_type=template_in.contract_type,
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
        version = ContractTemplateVersion(
            template_id=template.id,
            version_no=version_data.version_no,
            clause_sections=version_data.clause_sections,
            clause_library=version_data.clause_library,
            attachment_refs=version_data.attachment_refs,
            approval_flow=version_data.approval_flow,
            release_notes=version_data.release_notes,
            status="DRAFT",
            created_by=current_user.id,
        )
        db.add(version)
        db.flush()
        template.current_version_id = version.id

    db.commit()
    template = (
        db.query(ContractTemplate)
        .options(joinedload(ContractTemplate.versions))
        .filter(ContractTemplate.id == template.id)
        .first()
    )
    return _serialize_contract_template(template)


@router.put("/contract-templates/{template_id}", response_model=ContractTemplateResponse)
def update_contract_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_in: ContractTemplateUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = (
        _filter_template_visibility(
            db.query(ContractTemplate).options(joinedload(ContractTemplate.versions)),
            ContractTemplate,
            current_user,
        )
        .filter(ContractTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权访问")

    update_data = template_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    template = (
        db.query(ContractTemplate)
        .options(joinedload(ContractTemplate.versions))
        .filter(ContractTemplate.id == template_id)
        .first()
    )
    return _serialize_contract_template(template)


@router.post("/contract-templates/{template_id}/versions", response_model=ContractTemplateVersionResponse)
def create_contract_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_in: ContractTemplateVersionCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = (
        _filter_template_visibility(
            db.query(ContractTemplate),
            ContractTemplate,
            current_user,
        )
        .filter(ContractTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权访问")

    version = ContractTemplateVersion(
        template_id=template_id,
        version_no=version_in.version_no,
        clause_sections=version_in.clause_sections,
        clause_library=version_in.clause_library,
        attachment_refs=version_in.attachment_refs,
        approval_flow=version_in.approval_flow,
        release_notes=version_in.release_notes,
        status="DRAFT",
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return ContractTemplateVersionResponse(
        id=version.id,
        template_id=version.template_id,
        version_no=version.version_no,
        status=version.status,
        clause_sections=version.clause_sections,
        clause_library=version.clause_library,
        attachment_refs=version.attachment_refs,
        approval_flow=version.approval_flow,
        release_notes=version.release_notes,
        created_by=version.created_by,
        published_by=version.published_by,
        published_at=version.published_at,
        created_at=version.created_at,
        updated_at=version.updated_at,
    )


@router.post("/contract-templates/{template_id}/versions/{version_id}/publish", response_model=ContractTemplateResponse)
def publish_contract_template_version(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    version_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = (
        db.query(ContractTemplate)
        .options(joinedload(ContractTemplate.versions))
        .filter(ContractTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    version = next((v for v in template.versions if v.id == version_id), None)
    if not version:
        raise HTTPException(status_code=404, detail="模板版本不存在")

    version.status = "PUBLISHED"
    version.published_by = current_user.id
    version.published_at = datetime.utcnow()
    template.current_version_id = version.id
    template.status = "ACTIVE"
    db.query(ContractTemplateVersion).filter(
        ContractTemplateVersion.template_id == template_id,
        ContractTemplateVersion.id != version_id,
        ContractTemplateVersion.status == "PUBLISHED",
    ).update({"status": "ARCHIVED"}, synchronize_session=False)

    db.commit()
    template = (
        db.query(ContractTemplate)
        .options(joinedload(ContractTemplate.versions))
        .filter(ContractTemplate.id == template_id)
        .first()
    )
    return _serialize_contract_template(template)


@router.get("/contract-templates/{template_id}/apply", response_model=ContractTemplateApplyResponse)
def apply_contract_template(
    *,
    db: Session = Depends(deps.get_db),
    template_id: int,
    template_version_id: Optional[int] = Query(None, description="指定模板版本ID"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    template = (
        _filter_template_visibility(
            db.query(ContractTemplate).options(joinedload(ContractTemplate.versions)),
            ContractTemplate,
            current_user,
        )
        .filter(ContractTemplate.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在或无权访问")

    version = None
    if template_version_id:
        version = next((v for v in template.versions if v.id == template_version_id), None)
    if not version:
        version = template.current_version or (template.versions[0] if template.versions else None)
    if not version:
        raise HTTPException(status_code=400, detail="模板尚未创建版本")

    previous_version = _get_previous_version(template, version)
    version_diff = _build_template_version_diff(version, previous_version)
    history = _build_template_history(template)

    return ContractTemplateApplyResponse(
        template=_serialize_contract_template(template),
        version=ContractTemplateVersionResponse(
            id=version.id,
            template_id=version.template_id,
            version_no=version.version_no,
            status=version.status,
            clause_sections=version.clause_sections,
            clause_library=version.clause_library,
            attachment_refs=version.attachment_refs,
            approval_flow=version.approval_flow,
            release_notes=version.release_notes,
            created_by=version.created_by,
            published_by=version.published_by,
            published_at=version.published_at,
            created_at=version.created_at,
            updated_at=version.updated_at,
        ),
        version_diff=version_diff,
        approval_history=history,
    )


# ==================== CPQ规则集端点 ====================


@router.get("/cpq/rule-sets", response_model=PaginatedResponse[CpqRuleSetResponse])
def list_cpq_rule_sets(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    query = db.query(CpqRuleSet)
    if keyword:
        query = query.filter(
            or_(
                CpqRuleSet.rule_name.contains(keyword),
                CpqRuleSet.rule_code.contains(keyword),
            )
        )
    if status:
        query = query.filter(CpqRuleSet.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    rule_sets = (
        query.order_by(desc(CpqRuleSet.created_at))
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return PaginatedResponse(
        items=[_serialize_rule_set(r) for r in rule_sets],
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )


@router.post("/cpq/rule-sets", response_model=CpqRuleSetResponse)
def create_cpq_rule_set(
    *,
    db: Session = Depends(deps.get_db),
    rule_set_in: CpqRuleSetCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    existing = (
        db.query(CpqRuleSet)
        .filter(CpqRuleSet.rule_code == rule_set_in.rule_code)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="规则集编码已存在")

    rule_set = CpqRuleSet(
        rule_code=rule_set_in.rule_code,
        rule_name=rule_set_in.rule_name,
        description=rule_set_in.description,
        status=rule_set_in.status or "ACTIVE",
        base_price=rule_set_in.base_price or Decimal("0"),
        currency=rule_set_in.currency or "CNY",
        config_schema=rule_set_in.config_schema,
        pricing_matrix=rule_set_in.pricing_matrix,
        approval_threshold=rule_set_in.approval_threshold,
        visibility_scope=rule_set_in.visibility_scope or "ALL",
        is_default=rule_set_in.is_default or False,
        owner_role=rule_set_in.owner_role or (current_user.department or "SALES"),
    )
    db.add(rule_set)
    db.commit()
    db.refresh(rule_set)
    return _serialize_rule_set(rule_set)


@router.put("/cpq/rule-sets/{rule_set_id}", response_model=CpqRuleSetResponse)
def update_cpq_rule_set(
    *,
    db: Session = Depends(deps.get_db),
    rule_set_id: int,
    rule_set_in: CpqRuleSetUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    rule_set = db.query(CpqRuleSet).filter(CpqRuleSet.id == rule_set_id).first()
    if not rule_set:
        raise HTTPException(status_code=404, detail="规则集不存在")

    update_data = rule_set_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule_set, field, value)
    db.commit()
    db.refresh(rule_set)
    return _serialize_rule_set(rule_set)


@router.post("/cpq/price-preview", response_model=CpqPricePreviewResponse)
def preview_cpq_price(
    *,
    db: Session = Depends(deps.get_db),
    preview_request: CpqPricePreviewRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    service = CpqPricingService(db)
    preview_data = service.preview_price(
        rule_set_id=preview_request.rule_set_id,
        template_version_id=preview_request.template_version_id,
        selections=preview_request.selections,
        manual_discount_pct=preview_request.manual_discount_pct,
        manual_markup_pct=preview_request.manual_markup_pct,
    )
    return CpqPricePreviewResponse(**preview_data)
