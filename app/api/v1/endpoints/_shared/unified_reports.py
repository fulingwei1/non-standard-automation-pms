# -*- coding: utf-8 -*-
"""
Shared unified report routes for report_center and reports modules.
"""

from typing import Any, Dict, List, Optional, Callable

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """生成报告请求"""
    report_code: str = Field(..., description="报告代码")
    params: Dict[str, Any] = Field(default_factory=dict, description="报告参数")
    format: str = Field(default="json", description="导出格式: json/pdf/excel/word")
    skip_cache: bool = Field(default=False, description="是否跳过缓存")


class GenerateResponse(BaseModel):
    """生成报告响应"""
    success: bool
    report_code: str
    format: str
    data: Optional[Any] = None
    message: Optional[str] = None


def create_unified_report_router(
    *,
    prefix: str,
    tags: List[str],
    get_db,
    get_current_user,
    list_path: str,
    schema_path: str,
    preview_path: str,
    list_response_model,
    schema_response_model,
    list_mapper: Callable[[List[Any]], Any],
    schema_mapper: Callable[[Dict[str, Any]], Any],
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=tags)

    @router.get(list_path, response_model=list_response_model)
    async def list_available_reports(
        db=Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        """
        获取当前用户可访问的报告列表
        """
        from app.services.report_framework import ReportEngine

        engine = ReportEngine(db)
        reports = engine.list_available(user=current_user)
        return list_mapper(reports)

    @router.get(schema_path, response_model=schema_response_model)
    async def get_report_schema(
        report_code: str,
        db=Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        """
        获取报告配置 Schema（前端用于动态渲染表单）
        """
        from app.services.report_framework import ConfigError, ReportEngine

        try:
            engine = ReportEngine(db)
            schema = engine.get_schema(report_code)
            return schema_mapper(schema)
        except ConfigError as exc:
            raise HTTPException(status_code=404, detail=str(exc))

    @router.post("/generate", response_model=GenerateResponse)
    async def generate_report(
        request: GenerateRequest,
        db=Depends(get_db),
        current_user=Depends(get_current_user),
    ):
        """
        生成报告（JSON 格式）
        """
        from app.services.report_framework import ConfigError, ReportEngine
        from app.services.report_framework.engine import ParameterError, PermissionError

        try:
            engine = ReportEngine(db)
            result = engine.generate(
                report_code=request.report_code,
                params=request.params,
                format="json",
                user=current_user,
                skip_cache=request.skip_cache,
            )
            return GenerateResponse(
                success=True,
                report_code=request.report_code,
                format="json",
                data=result.data,
            )
        except ConfigError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ParameterError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"报告生成失败: {str(exc)}")

    @router.post("/generate/download")
    async def generate_and_download(
        request: GenerateRequest,
        db=Depends(get_db),
        current_user=Depends(get_current_user),
    ) -> Response:
        """
        生成并下载报告（支持 PDF/Excel/Word 格式）
        """
        from app.services.report_framework import ConfigError, ReportEngine
        from app.services.report_framework.engine import ParameterError, PermissionError

        # 验证格式
        format_map = {
            "json": ("application/json", ".json"),
            "pdf": ("application/pdf", ".pdf"),
            "excel": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                ".xlsx",
            ),
            "word": (
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ".docx",
            ),
        }

        if request.format not in format_map:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的格式: {request.format}，支持: {list(format_map.keys())}",
            )

        try:
            engine = ReportEngine(db)
            result = engine.generate(
                report_code=request.report_code,
                params=request.params,
                format=request.format,
                user=current_user,
                skip_cache=request.skip_cache,
            )

            content_type, extension = format_map[request.format]

            if request.format == "json":
                import json

                content = json.dumps(result.data, ensure_ascii=False, indent=2).encode("utf-8")
            else:
                content = result.data if isinstance(result.data, bytes) else str(result.data).encode("utf-8")

            filename = f"{request.report_code}{extension}"

            return Response(
                content=content,
                media_type=content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )

        except ConfigError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ParameterError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"报告生成失败: {str(exc)}")

    @router.get(preview_path)
    async def preview_report(
        report_code: str,
        db=Depends(get_db),
        current_user=Depends(get_current_user),
        project_id: Optional[int] = Query(None, description="项目ID"),
        department_id: Optional[int] = Query(None, description="部门ID"),
        order_id: Optional[int] = Query(None, description="验收单ID"),
        start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
        end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)"),
        target_date: Optional[str] = Query(None, description="目标日期 (YYYY-MM-DD)"),
        year: Optional[int] = Query(None, description="年份"),
        month: Optional[int] = Query(None, description="月份"),
    ):
        """
        预览报告（通过 Query 参数）
        """
        from app.services.report_framework import ConfigError, ReportEngine
        from app.services.report_framework.engine import ParameterError, PermissionError

        params = {}
        if project_id is not None:
            params["project_id"] = project_id
        if department_id is not None:
            params["department_id"] = department_id
        if order_id is not None:
            params["order_id"] = order_id
        if start_date is not None:
            params["start_date"] = start_date
        if end_date is not None:
            params["end_date"] = end_date
        if target_date is not None:
            params["target_date"] = target_date
        if year is not None:
            params["year"] = year
        if month is not None:
            params["month"] = month

        try:
            engine = ReportEngine(db)
            result = engine.generate(
                report_code=report_code,
                params=params,
                format="json",
                user=current_user,
                skip_cache=True,
            )

            return {
                "success": True,
                "report_code": report_code,
                "params": params,
                "data": result.data,
            }

        except ConfigError as exc:
            raise HTTPException(status_code=404, detail=str(exc))
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc))
        except ParameterError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"报告生成失败: {str(exc)}")

    return router
