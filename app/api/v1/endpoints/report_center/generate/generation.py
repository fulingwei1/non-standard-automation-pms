# -*- coding: utf-8 -*-
"""
报表生成 - 生成和预览
"""
from datetime import date, datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.report_center import ReportGeneration
from app.models.user import User
from app.schemas.report_center import (
    ReportGenerateRequest,
    ReportGenerateResponse,
    ReportPreviewResponse,
)

router = APIRouter()


@router.post("/generate", response_model=ReportGenerateResponse, status_code=status.HTTP_201_CREATED)
def generate_report(
    *,
    db: Session = Depends(deps.get_db),
    generate_in: ReportGenerateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    生成报表（按角色/类型）
    """
    from app.services.report_data_generation_service import report_data_service

    # 检查权限
    if not report_data_service.check_permission(db, current_user, generate_in.report_type, generate_in.role):
        raise HTTPException(
            status_code=403,
            detail=f"您没有权限生成 {generate_in.report_type} 类型的报表"
        )

    # 生成报表编码
    report_code = f"RPT-{datetime.now().strftime('%y%m%d%H%M%S')}"

    # 根据报表类型和角色生成数据
    report_data = report_data_service.generate_report_by_type(
        db,
        generate_in.report_type,
        generate_in.project_id,
        generate_in.department_id,
        generate_in.start_date,
        generate_in.end_date
    )

    # 如果有错误，返回错误信息
    if "error" in report_data:
        raise HTTPException(status_code=400, detail=report_data["error"])

    # 创建报表生成记录
    generation = ReportGeneration(
        report_type=generate_in.report_type,
        report_title=f"{generate_in.report_type}报表",
        viewer_role=generate_in.role,
        scope_type="PROJECT" if generate_in.project_id else ("DEPARTMENT" if generate_in.department_id else None),
        scope_id=generate_in.project_id or generate_in.department_id,
        period_start=generate_in.start_date,
        period_end=generate_in.end_date,
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
        report_name=generation.report_title or f"{generate_in.report_type}报表",
        report_type=generation.report_type,
        generated_at=generation.generated_at or datetime.now(),
        data=generation.report_data or {}
    )


@router.get("/preview/{report_type}", response_model=ReportPreviewResponse, status_code=status.HTTP_200_OK)
def preview_report(
    *,
    db: Session = Depends(deps.get_db),
    report_type: str,
    project_id: Optional[int] = Query(None, description="项目ID"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    预览报表（简化版预览）
    """
    from app.services.report_data_generation_service import report_data_service

    # 生成预览数据（使用默认时间范围）
    end_date = date.today()
    start_date = end_date - timedelta(days=7)

    preview_data = report_data_service.generate_report_by_type(
        db,
        report_type,
        project_id,
        None,  # department_id
        start_date,
        end_date
    )

    # 添加可用的字段列表
    preview_data["available_fields"] = list(preview_data.get("summary", {}).keys())
    preview_data["sections"] = [k for k in preview_data.keys() if k not in ["summary", "available_fields", "error"]]

    return ReportPreviewResponse(
        report_type=report_type,
        preview_data=preview_data
    )
