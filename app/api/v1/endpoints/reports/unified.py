# -*- coding: utf-8 -*-
"""
统一报告 API 端点

提供报告生成、查询、下载等功能
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User
from app.services.report_framework import ConfigError
from app.services.report_framework.engine import ReportEngine, PermissionError, ParameterError


router = APIRouter(prefix="/reports", tags=["reports"])


# === 请求/响应模型 ===

class ReportMetaResponse(BaseModel):
    """报告元数据响应"""
    code: str
    name: str
    description: Optional[str] = None


class ReportSchemaResponse(BaseModel):
    """报告 Schema 响应"""
    report_code: str
    report_name: str
    description: Optional[str] = None
    parameters: List[Dict[str, Any]]
    exports: Dict[str, bool]


class GenerateReportRequest(BaseModel):
    """生成报告请求"""
    parameters: Dict[str, Any] = {}


class ReportDataResponse(BaseModel):
    """报告数据响应"""
    meta: Dict[str, Any]
    sections: List[Dict[str, Any]]


# === API 端点 ===

@router.get("/available", response_model=List[ReportMetaResponse])
def list_available_reports(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> List[ReportMetaResponse]:
    """
    获取当前用户可访问的报告列表
    """
    engine = ReportEngine(db)
    reports = engine.list_available(current_user)

    return [
        ReportMetaResponse(
            code=r.code,
            name=r.name,
            description=r.description,
        )
        for r in reports
    ]


@router.get("/{report_code}/schema", response_model=ReportSchemaResponse)
def get_report_schema(
    report_code: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> ReportSchemaResponse:
    """
    获取报告配置 Schema（前端用于动态渲染表单）
    """
    try:
        engine = ReportEngine(db)
        schema = engine.get_schema(report_code)

        return ReportSchemaResponse(**schema)

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{report_code}/generate", response_model=ReportDataResponse)
def generate_report(
    report_code: str,
    request: GenerateReportRequest,
    format: str = Query(default="json", description="导出格式: json, pdf, excel, word"),
    skip_cache: bool = Query(default=False, description="是否跳过缓存"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> ReportDataResponse:
    """
    生成报告

    - **report_code**: 报告代码，如 PROJECT_WEEKLY
    - **format**: 导出格式（当前仅支持 json）
    - **skip_cache**: 是否跳过缓存
    """
    try:
        engine = ReportEngine(db)
        result = engine.generate(
            report_code=report_code,
            params=request.parameters,
            format=format,
            user=current_user,
            skip_cache=skip_cache,
        )

        return ReportDataResponse(
            meta=result.data.get("meta", {}),
            sections=result.data.get("sections", []),
        )

    except ConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {e}")


@router.get("/{report_code}/preview")
def preview_report(
    report_code: str,
    limit: int = Query(default=10, description="预览数据条数"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Dict[str, Any]:
    """
    预览报告（返回部分数据，用于快速预览）
    """
    try:
        engine = ReportEngine(db)
        schema = engine.get_schema(report_code)

        return {
            "report_code": report_code,
            "schema": schema,
            "preview_note": "使用 /generate 端点生成完整报告",
        }

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
