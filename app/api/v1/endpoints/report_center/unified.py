# -*- coding: utf-8 -*-
"""
统一报告 API - 基于 YAML 配置的报告引擎
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.api.deps import get_db
from app.api.v1.endpoints._shared.unified_reports import create_unified_report_router
from app.core.auth import get_current_user


class ReportMeta(BaseModel):
    """报告元数据"""

    code: str
    name: str
    description: Optional[str] = None
    version: Optional[str] = None

    class Config:
        from_attributes = True


class ReportParameter(BaseModel):
    """报告参数"""

    name: str
    type: str
    required: bool = True
    default: Optional[Any] = None
    description: Optional[str] = None


class ReportSchema(BaseModel):
    """报告 Schema"""

    report_code: str
    report_name: str
    description: Optional[str] = None
    parameters: List[ReportParameter]
    exports: Dict[str, bool]


def _map_reports(reports):
    return [
        ReportMeta(
            code=r.code,
            name=r.name,
            description=getattr(r, "description", None),
            version=getattr(r, "version", None),
        )
        for r in reports
    ]


def _map_schema(schema: Dict[str, Any]) -> ReportSchema:
    return ReportSchema(
        report_code=schema["report_code"],
        report_name=schema["report_name"],
        description=schema.get("description"),
        parameters=[ReportParameter(**p) for p in schema["parameters"]],
        exports=schema["exports"],
    )


router = create_unified_report_router(
    prefix="/unified",
    tags=["统一报告"],
    get_db=get_db,
    get_current_user=get_current_user,
    list_path="/reports",
    schema_path="/reports/{report_code}/schema",
    preview_path="/reports/{report_code}/preview",
    list_response_model=List[ReportMeta],
    schema_response_model=ReportSchema,
    list_mapper=_map_reports,
    schema_mapper=_map_schema,
)
