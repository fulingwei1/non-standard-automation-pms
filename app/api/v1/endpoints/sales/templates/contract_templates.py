# -*- coding: utf-8 -*-
"""
合同模板管理 API endpoints

包含合同模板的CRUD、版本管理和应用功能
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.sales import ContractTemplate, ContractTemplateVersion
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.sales import (
    ContractTemplateApplyResponse,
    ContractTemplateCreate,
    ContractTemplateResponse,
    ContractTemplateUpdate,
    ContractTemplateVersionCreate,
    ContractTemplateVersionResponse,
)

from .common import (
    _build_template_history,
    _build_template_version_diff,
    _filter_template_visibility,
    _get_previous_version,
    _serialize_contract_template,
)

router = APIRouter()


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
    """获取合同模板列表"""
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
    """创建合同模板"""
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
    """更新合同模板"""
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
    """创建合同模板版本"""
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
    """发布合同模板版本"""
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
    version.published_at = datetime.now(timezone.utc)
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
    """应用合同模板"""
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
