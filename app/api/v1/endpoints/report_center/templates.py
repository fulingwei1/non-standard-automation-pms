# -*- coding: utf-8 -*-
"""
报表模板 - 自动生成
从 report_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
报表中心 API endpoints
核心功能：多角色视角报表、智能生成、导出分享
"""

import os
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.outsourcing import OutsourcingOrder
from app.models.vendor import Vendor
from app.models.project import Machine, Project, ProjectPaymentPlan
from app.models.rd_project import RdCost, RdCostType, RdProject
from app.models.report_center import (
    ReportDefinition,
    ReportGeneration,
    ReportSubscription,
    ReportTemplate,
)
from app.models.sales import Contract
from app.models.timesheet import Timesheet
from app.models.user import Role, User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.report_center import (
    ApplyTemplateRequest,
    ReportCompareRequest,
    ReportCompareResponse,
    ReportExportRequest,
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportPreviewResponse,
    ReportRoleResponse,
    ReportTemplateListResponse,
    ReportTemplateResponse,
    ReportTypeResponse,
    RoleReportMatrixResponse,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/report-center/templates",
    tags=["templates"]
)

# 共 2 个路由

# ==================== 报表模板 ====================

@router.get("/templates", response_model=ReportTemplateListResponse, status_code=status.HTTP_200_OK)
def get_report_templates(
    *,
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    report_type: Optional[str] = Query(None, description="报表类型筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取报表模板列表
    """
    query = db.query(ReportTemplate).filter(ReportTemplate.is_active == True)

    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)

    total = query.count()
    offset = (page - 1) * page_size
    templates = query.order_by(desc(ReportTemplate.use_count), desc(ReportTemplate.created_at)).offset(offset).limit(page_size).all()

    items = []
    for template in templates:
        items.append(ReportTemplateResponse(
            id=template.id,
            template_code=template.template_code,
            template_name=template.template_name,
            report_type=template.report_type,
            description=template.description,
            is_system=template.is_system or False,
            is_active=template.is_active or True,
            use_count=template.use_count or 0,
            created_at=template.created_at,
            updated_at=template.updated_at
        ))

    return ReportTemplateListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/templates/apply", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
def apply_report_template(
    *,
    db: Session = Depends(deps.get_db),
    apply_in: ApplyTemplateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    应用报表模板（套用模板）
    """
    from app.services.template_report_service import template_report_service

    template = db.query(ReportTemplate).filter(ReportTemplate.id == apply_in.template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已停用")

    # 更新使用次数
    template.use_count = (template.use_count or 0) + 1
    db.add(template)

    # 生成报表编码
    report_code = f"RPT-{datetime.now().strftime('%y%m%d%H%M%S')}"

    # 根据模板配置生成报表数据
    report_data = template_report_service.generate_from_template(
        db,
        template,
        apply_in.project_id,
        apply_in.department_id,
        apply_in.start_date,
        apply_in.end_date,
        apply_in.filters
    )

    # 如果有错误，返回错误信息
    if "error" in report_data:
        raise HTTPException(status_code=400, detail=report_data["error"])

    generation = ReportGeneration(
        template_id=template.id,
        report_type=template.report_type,
        report_title=apply_in.report_name,
        scope_type="PROJECT" if apply_in.project_id else ("DEPARTMENT" if apply_in.department_id else None),
        scope_id=apply_in.project_id or apply_in.department_id,
        period_start=apply_in.start_date,
        period_end=apply_in.end_date,
        report_data=report_data,
        status="GENERATED",
        generated_by=current_user.id
    )

    db.add(generation)
    db.commit()
    db.refresh(generation)

    return ReportGenerateResponse(
        report_id=generation.id,
        report_code=report_code,
        report_name=generation.report_title or f"{template.template_name}报表",
        report_type=generation.report_type,
        generated_at=generation.generated_at or datetime.now(),
        data=generation.report_data or {}
    )



