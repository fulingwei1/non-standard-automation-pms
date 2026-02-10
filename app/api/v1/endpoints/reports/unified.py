# -*- coding: utf-8 -*-
"""
统一报告 API 端点
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.api import deps
from app.api.v1.endpoints._shared.unified_reports import create_unified_report_router


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


def _map_reports(reports):
    return [
        ReportMetaResponse(
            code=r.code,
            name=r.name,
            description=getattr(r, "description", None),
        )
        for r in reports
    ]


def _map_schema(schema: Dict[str, Any]) -> ReportSchemaResponse:
    return ReportSchemaResponse(**schema)


router = create_unified_report_router(
    prefix="/reports",
    tags=["reports"],
    get_db=deps.get_db,
    get_current_user=deps.get_current_user,
    list_path="/available",
    schema_path="/{report_code}/schema",
    preview_path="/{report_code}/preview",
    list_response_model=List[ReportMetaResponse],
    schema_response_model=ReportSchemaResponse,
    list_mapper=_map_reports,
    schema_mapper=_map_schema,
)
