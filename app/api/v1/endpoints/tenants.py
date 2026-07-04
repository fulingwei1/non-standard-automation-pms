# -*- coding: utf-8 -*-
"""Tenant management API endpoints."""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.tenant import (
    TenantCreate,
    TenantInitRequest,
    TenantListResponse,
    TenantResponse,
    TenantStatsResponse,
    TenantUpdate,
)
from app.services.tenant_service import TenantService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants", tags=["tenants"])


def _ensure_super_admin(current_user: User) -> None:
    if not getattr(current_user, "is_superuser", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要超级管理员权限")


def _tenant_response(tenant: Any) -> TenantResponse:
    return TenantResponse.model_validate(tenant)


@router.get("/", response_model=TenantListResponse, status_code=status.HTTP_200_OK)
def list_tenants(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    status: Optional[str] = Query(None, description="租户状态"),
    keyword: Optional[str] = Query(None, description="关键词"),
    current_user: User = Depends(deps.require_super_admin),
) -> TenantListResponse:
    """List tenants."""

    _ensure_super_admin(current_user)
    result = TenantService(db).list_tenants(
        page=page,
        page_size=page_size,
        status=status,
        keyword=keyword,
    )
    return TenantListResponse(
        items=[_tenant_response(item) for item in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        pages=result["pages"],
    )


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
def create_tenant(
    *,
    tenant_in: TenantCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> TenantResponse:
    """Create a tenant."""

    _ensure_super_admin(current_user)
    try:
        tenant = TenantService(db).create_tenant(tenant_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return _tenant_response(tenant)


@router.get("/{tenant_id}", response_model=TenantResponse, status_code=status.HTTP_200_OK)
def get_tenant(
    *,
    tenant_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> TenantResponse:
    """Get a tenant by id."""

    _ensure_super_admin(current_user)
    tenant = TenantService(db).get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")
    return _tenant_response(tenant)


@router.put("/{tenant_id}", response_model=TenantResponse, status_code=status.HTTP_200_OK)
def update_tenant(
    *,
    tenant_id: int,
    tenant_in: TenantUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> TenantResponse:
    """Update a tenant."""

    _ensure_super_admin(current_user)
    tenant = TenantService(db).update_tenant(tenant_id, tenant_in)
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")
    return _tenant_response(tenant)


@router.delete(
    "/{tenant_id}", response_model=ResponseModel[dict], status_code=status.HTTP_200_OK
)
def delete_tenant(
    *,
    tenant_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> ResponseModel[dict]:
    """Soft-delete a tenant."""

    _ensure_super_admin(current_user)
    deleted = TenantService(db).delete_tenant(tenant_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")
    return ResponseModel(code=200, message="租户已删除", data={"id": tenant_id})


@router.post(
    "/{tenant_id}/init",
    response_model=ResponseModel[dict],
    status_code=status.HTTP_200_OK,
)
def init_tenant(
    *,
    tenant_id: int,
    init_data: TenantInitRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> ResponseModel[dict]:
    """Initialize tenant roles and administrator."""

    _ensure_super_admin(current_user)
    try:
        result = TenantService(db).init_tenant(tenant_id, init_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ResponseModel(code=200, message="租户初始化成功", data=result)


@router.get(
    "/{tenant_id}/stats",
    response_model=TenantStatsResponse,
    status_code=status.HTTP_200_OK,
)
def get_tenant_stats(
    *,
    tenant_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_super_admin),
) -> TenantStatsResponse:
    """Get tenant statistics."""

    _ensure_super_admin(current_user)
    stats = TenantService(db).get_tenant_stats(tenant_id)
    if not stats:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="租户不存在")
    return TenantStatsResponse(**stats)
