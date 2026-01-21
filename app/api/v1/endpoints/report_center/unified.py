# -*- coding: utf-8 -*-
"""
统一报告 API - 基于 YAML 配置的报告引擎

提供统一的报告生成接口，支持所有 YAML 配置的报告类型
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.auth import get_current_user
from app.models.user import User


router = APIRouter(prefix="/unified", tags=["统一报告"])


# ============== Schemas ==============

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


# ============== API Endpoints ==============

@router.get("/reports", response_model=List[ReportMeta])
async def list_available_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    列出当前用户可用的报告

    根据用户角色过滤可访问的报告列表
    """
    from app.services.report_framework import ReportEngine

    engine = ReportEngine(db)
    reports = engine.list_available(user=current_user)

    return [
        ReportMeta(
            code=r.code,
            name=r.name,
            description=r.description,
            version=r.version
        )
        for r in reports
    ]


@router.get("/reports/{report_code}/schema", response_model=ReportSchema)
async def get_report_schema(
    report_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取报告参数 Schema

    返回报告所需的参数定义，供前端动态生成表单
    """
    from app.services.report_framework import ReportEngine
    from app.services.report_framework.config_loader import ConfigError

    engine = ReportEngine(db)

    try:
        schema = engine.get_schema(report_code)
        return ReportSchema(
            report_code=schema["report_code"],
            report_name=schema["report_name"],
            description=schema.get("description"),
            parameters=[
                ReportParameter(**p) for p in schema["parameters"]
            ],
            exports=schema["exports"]
        )
    except ConfigError:
        raise HTTPException(status_code=404, detail=f"报告不存在: {report_code}")


@router.post("/generate", response_model=GenerateResponse)
async def generate_report(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成报告（JSON 格式）

    根据报告代码和参数生成报告数据
    """
    from app.services.report_framework import ReportEngine
    from app.services.report_framework.config_loader import ConfigError
    from app.services.report_framework.engine import ParameterError, PermissionError

    engine = ReportEngine(db)

    try:
        result = engine.generate(
            report_code=request.report_code,
            params=request.params,
            format="json",
            user=current_user,
            skip_cache=request.skip_cache
        )

        return GenerateResponse(
            success=True,
            report_code=request.report_code,
            format="json",
            data=result.data
        )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@router.post("/generate/download")
async def generate_and_download(
    request: GenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成并下载报告（支持 PDF/Excel/Word 格式）

    返回二进制文件流供下载
    """
    from app.services.report_framework import ReportEngine
    from app.services.report_framework.config_loader import ConfigError
    from app.services.report_framework.engine import ParameterError, PermissionError

    engine = ReportEngine(db)

    # 验证格式
    format_map = {
        "json": ("application/json", ".json"),
        "pdf": ("application/pdf", ".pdf"),
        "excel": ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".xlsx"),
        "word": ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", ".docx"),
    }

    if request.format not in format_map:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式: {request.format}，支持: {list(format_map.keys())}"
        )

    try:
        result = engine.generate(
            report_code=request.report_code,
            params=request.params,
            format=request.format,
            user=current_user,
            skip_cache=request.skip_cache
        )

        content_type, extension = format_map[request.format]

        # JSON 格式返回文本
        if request.format == "json":
            import json
            content = json.dumps(result.data, ensure_ascii=False, indent=2).encode("utf-8")
        else:
            # 其他格式返回二进制
            content = result.data if isinstance(result.data, bytes) else str(result.data).encode("utf-8")

        filename = f"{request.report_code}{extension}"

        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@router.get("/reports/{report_code}/preview")
async def preview_report(
    report_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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

    便于快速测试和预览报告
    """
    from app.services.report_framework import ReportEngine
    from app.services.report_framework.config_loader import ConfigError
    from app.services.report_framework.engine import ParameterError, PermissionError

    # 构建参数字典
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

    engine = ReportEngine(db)

    try:
        result = engine.generate(
            report_code=report_code,
            params=params,
            format="json",
            user=current_user,
            skip_cache=True
        )

        return {
            "success": True,
            "report_code": report_code,
            "params": params,
            "data": result.data
        }

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")
