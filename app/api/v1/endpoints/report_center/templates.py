# -*- coding: utf-8 -*-
"""
报表模板
"""

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.models.report_center import (
    ReportGeneration,
    ReportTemplate,
)
from app.models.user import User
from app.schemas.report_center import (
    ApplyTemplateRequest,
    ReportGenerateResponse,
    ReportTemplateListResponse,
    ReportTemplateResponse,
)
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404

router = APIRouter(
    prefix="/templates",
    tags=["templates"]
)

# 共 2 个路由

# ==================== 报表模板 ====================

@router.get("", response_model=ReportTemplateListResponse, status_code=status.HTTP_200_OK)
def get_report_templates(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    report_type: Optional[str] = Query(None, description="报表类型筛选"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    获取报表模板列表
    """
    query = db.query(ReportTemplate).filter(ReportTemplate.is_active)

    if report_type:
        query = query.filter(ReportTemplate.report_type == report_type)

    total = query.count()
    templates = apply_pagination(query.order_by(desc(ReportTemplate.use_count), desc(ReportTemplate.created_at)), pagination.offset, pagination.limit).all()

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
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/apply", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
def apply_report_template(
    *,
    db: Session = Depends(deps.get_db),
    apply_in: ApplyTemplateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    应用报表模板（套用模板）
    """
    template = get_or_404(db, ReportTemplate, apply_in.template_id, "模板不存在")

    if not template.is_active:
        raise HTTPException(status_code=400, detail="模板已停用")

    # 更新使用次数
    template.use_count = (template.use_count or 0) + 1
    db.add(template)

    # 生成报表编码
    report_code = f"RPT-{datetime.now().strftime('%y%m%d%H%M%S')}"

    filters_payload = apply_in.filters or apply_in.customizations or {}

    # 使用模板报表适配器生成报表
    from app.services.report_framework.adapters.template import TemplateReportAdapter
    
    adapter = TemplateReportAdapter(db)
    
    try:
        result = adapter.generate(
            params={
                "template_id": template.id,
                "project_id": apply_in.project_id,
                "department_id": apply_in.department_id,
                "start_date": apply_in.start_date,
                "end_date": apply_in.end_date,
                "filters": filters_payload,
            },
            format="json",
            user=current_user,
            skip_cache=False,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成报表失败: {e}")

    # 提取报表数据
    report_data = result.data if hasattr(result, "data") else result
    
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


