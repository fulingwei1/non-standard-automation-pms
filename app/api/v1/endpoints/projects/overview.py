# -*- coding: utf-8 -*-
"""
项目总览 API

提供项目与各模块关联数据的总览视图
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.services.project_relation_service import get_project_relation_service

router = APIRouter()


@router.get("/projects/{project_id}/overview", summary="项目总览")
def get_project_overview(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取项目总览（包含生产/采购/交付/售后各模块数据）
    """
    service = get_project_relation_service(db)
    overview = service.get_project_overview(project_id)
    
    if not overview:
        raise HTTPException(status_code=404, detail="项目不存在")
    
    return overview


@router.get("/projects/{project_id}/production-status", summary="项目生产状态")
def get_project_production_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目生产状态"""
    service = get_project_relation_service(db)
    return service.get_production_status(project_id)


@router.get("/projects/{project_id}/procurement-status", summary="项目采购状态")
def get_project_procurement_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目采购状态"""
    service = get_project_relation_service(db)
    return service.get_procurement_status(project_id)


@router.get("/projects/{project_id}/delivery-status", summary="项目交付状态")
def get_project_delivery_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目交付状态"""
    service = get_project_relation_service(db)
    return service.get_delivery_status(project_id)


@router.get("/projects/{project_id}/after-sales-status", summary="项目售后状态")
def get_project_after_sales_status(
    project_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取项目售后状态"""
    service = get_project_relation_service(db)
    return service.get_after_sales_status(project_id)
