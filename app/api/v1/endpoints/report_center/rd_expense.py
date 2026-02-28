# -*- coding: utf-8 -*-
"""
研发费用报表 - 自动生成
从 report_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
报表中心 API endpoints
核心功能：多角色视角报表、智能生成、导出分享
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/rd-expense",
    tags=["rd_expense"]
)

# 共 6 个路由

# ==================== 研发费用报表 ====================

@router.get("/rd-auxiliary-ledger", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_auxiliary_ledger(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    project_id: Optional[int] = Query(None, description="研发项目ID（不提供则查询所有项目）"),
    format: str = Query("json", description="导出格式：json/excel/pdf"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发费用辅助账（使用统一报表框架）
    税务要求的研发费用辅助账格式
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    try:
        # 优先使用统一报表框架（如果存在YAML配置）
        engine = ReportEngine(db)
        try:
            result = engine.generate(
                report_code="RD_AUXILIARY_LEDGER",
                params={
                    "year": year,
                    "project_id": project_id,
                },
                format=format,
                user=current_user,
                skip_cache=False,
            )
            
            if format in ["excel", "pdf"]:
                filename = f"研发费用辅助账_{year}年.xlsx" if format == "excel" else f"研发费用辅助账_{year}年.pdf"
                return StreamingResponse(
                    result.data.get("file_stream"),
                    media_type=result.content_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
            else:
                return ResponseModel(code=200, message="success", data=result.data)
        except (ConfigError, ParameterError):
            # 如果YAML配置不存在，使用适配器（向后兼容）
            adapter = RdExpenseReportAdapter(db, "RD_AUXILIARY_LEDGER")
            result = adapter.generate(
                params={"year": year, "project_id": project_id},
                format=format,
                user=current_user,
            )
            data = result.data if hasattr(result, 'data') else result
            return ResponseModel(code=200, message="success", data=data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研发费用辅助账失败: {str(e)}")


@router.get("/rd-deduction-detail", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_deduction_detail(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    project_id: Optional[int] = Query(None, description="研发项目ID"),
    format: str = Query("json", description="导出格式：json/excel/pdf"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发费用加计扣除明细（使用统一报表框架）
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    try:
        # 优先使用统一报表框架（如果存在YAML配置）
        engine = ReportEngine(db)
        try:
            result = engine.generate(
                report_code="RD_DEDUCTION_DETAIL",
                params={
                    "year": year,
                    "project_id": project_id,
                },
                format=format,
                user=current_user,
                skip_cache=False,
            )
            
            if format in ["excel", "pdf"]:
                filename = f"研发费用加计扣除明细_{year}年.xlsx" if format == "excel" else f"研发费用加计扣除明细_{year}年.pdf"
                return StreamingResponse(
                    result.data.get("file_stream"),
                    media_type=result.content_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
            else:
                return ResponseModel(code=200, message="success", data=result.data)
        except (ConfigError, ParameterError):
            # 如果YAML配置不存在，使用适配器（向后兼容）
            adapter = RdExpenseReportAdapter(db, "RD_DEDUCTION_DETAIL")
            result = adapter.generate(
                params={"year": year, "project_id": project_id},
                format=format,
                user=current_user,
            )
            data = result.data if hasattr(result, 'data') else result
            return ResponseModel(code=200, message="success", data=data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研发费用加计扣除明细失败: {str(e)}")


@router.get("/rd-high-tech", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_high_tech_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    format: str = Query("json", description="导出格式：json/excel/pdf"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    高新企业研发费用表（使用统一报表框架）
    用于高新技术企业认定
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    try:
        # 优先使用统一报表框架（如果存在YAML配置）
        engine = ReportEngine(db)
        try:
            result = engine.generate(
                report_code="RD_HIGH_TECH",
                params={"year": year},
                format=format,
                user=current_user,
                skip_cache=False,
            )
            
            if format in ["excel", "pdf"]:
                filename = f"高新企业研发费用表_{year}年.xlsx" if format == "excel" else f"高新企业研发费用表_{year}年.pdf"
                return StreamingResponse(
                    result.data.get("file_stream"),
                    media_type=result.content_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
            else:
                return ResponseModel(code=200, message="success", data=result.data)
        except (ConfigError, ParameterError):
            # 如果YAML配置不存在，使用适配器（向后兼容）
            adapter = RdExpenseReportAdapter(db, "RD_HIGH_TECH")
            result = adapter.generate(
                params={"year": year},
                format=format,
                user=current_user,
            )
            data = result.data if hasattr(result, 'data') else result
            return ResponseModel(code=200, message="success", data=data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成高新企业研发费用表失败: {str(e)}")


@router.get("/rd-intensity", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_intensity_report(
    *,
    db: Session = Depends(deps.get_db),
    start_year: int = Query(..., description="开始年度"),
    end_year: int = Query(..., description="结束年度"),
    format: str = Query("json", description="导出格式：json/excel/pdf"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发投入强度报表（使用统一报表框架）
    研发费用/营业收入
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    try:
        # 优先使用统一报表框架（如果存在YAML配置）
        engine = ReportEngine(db)
        try:
            result = engine.generate(
                report_code="RD_INTENSITY",
                params={
                    "start_year": start_year,
                    "end_year": end_year,
                },
                format=format,
                user=current_user,
                skip_cache=False,
            )
            
            if format in ["excel", "pdf"]:
                filename = f"研发投入强度报表_{start_year}-{end_year}年.xlsx" if format == "excel" else f"研发投入强度报表_{start_year}-{end_year}年.pdf"
                return StreamingResponse(
                    result.data.get("file_stream"),
                    media_type=result.content_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
            else:
                return ResponseModel(code=200, message="success", data=result.data)
        except (ConfigError, ParameterError):
            # 如果YAML配置不存在，使用适配器（向后兼容）
            adapter = RdExpenseReportAdapter(db, "RD_INTENSITY")
            result = adapter.generate(
                params={"start_year": start_year, "end_year": end_year},
                format=format,
                user=current_user,
            )
            data = result.data if hasattr(result, 'data') else result
            return ResponseModel(code=200, message="success", data=data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研发投入强度报表失败: {str(e)}")


@router.get("/rd-personnel", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def get_rd_personnel_report(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年度"),
    format: str = Query("json", description="导出格式：json/excel/pdf"),
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """
    研发人员统计（使用统一报表框架）
    研发人员占比统计
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    try:
        # 优先使用统一报表框架（如果存在YAML配置）
        engine = ReportEngine(db)
        try:
            result = engine.generate(
                report_code="RD_PERSONNEL",
                params={"year": year},
                format=format,
                user=current_user,
                skip_cache=False,
            )
            
            if format in ["excel", "pdf"]:
                filename = f"研发人员统计_{year}年.xlsx" if format == "excel" else f"研发人员统计_{year}年.pdf"
                return StreamingResponse(
                    result.data.get("file_stream"),
                    media_type=result.content_type,
                    headers={"Content-Disposition": f"attachment; filename={filename}"},
                )
            else:
                return ResponseModel(code=200, message="success", data=result.data)
        except (ConfigError, ParameterError):
            # 如果YAML配置不存在，使用适配器（向后兼容）
            adapter = RdExpenseReportAdapter(db, "RD_PERSONNEL")
            result = adapter.generate(
                params={"year": year},
                format=format,
                user=current_user,
            )
            data = result.data if hasattr(result, 'data') else result
            return ResponseModel(code=200, message="success", data=data)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成研发人员统计失败: {str(e)}")


@router.get("/rd-export", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def export_rd_report(
    *,
    db: Session = Depends(deps.get_db),
    report_type: str = Query(..., description="报表类型：auxiliary-ledger/deduction-detail/high-tech/intensity/personnel"),
    year: int = Query(..., description="年度"),
    format: str = Query("xlsx", description="导出格式：xlsx/pdf"),
    project_id: Optional[int] = Query(None, description="研发项目ID"),
    current_user: User = Depends(security.require_permission("report:export")),
) -> Any:
    """
    导出研发费用报表（使用统一报表框架）
    """
    from fastapi.responses import StreamingResponse

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.rd_expense import RdExpenseReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    # 报表类型映射
    report_type_map = {
        "auxiliary-ledger": "RD_AUXILIARY_LEDGER",
        "deduction-detail": "RD_DEDUCTION_DETAIL",
        "high-tech": "RD_HIGH_TECH",
        "intensity": "RD_INTENSITY",
        "personnel": "RD_PERSONNEL",
    }
    
    mapped_report_type = report_type_map.get(report_type)
    if not mapped_report_type:
        raise HTTPException(status_code=400, detail=f"不支持的报表类型: {report_type}")

    try:
        # 优先使用统一报表框架（如果存在YAML配置）
        engine = ReportEngine(db)
        try:
            params = {"year": year}
            if project_id:
                params["project_id"] = project_id
            
            result = engine.generate(
                report_code=mapped_report_type,
                params=params,
                format=format.lower(),
                user=current_user,
                skip_cache=False,
            )
            
            filename = f"rd-{report_type}-{year}.{format.lower()}"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type=result.content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        except (ConfigError, ParameterError):
            # 如果YAML配置不存在，使用适配器（向后兼容）
            adapter = RdExpenseReportAdapter(db, mapped_report_type)
            result = adapter.generate(
                params={"year": year, "project_id": project_id},
                format=format.lower(),
                user=current_user,
            )
            
            # 使用统一报表框架的渲染器导出
            from app.services.report_framework.renderers import ExcelRenderer, PdfRenderer
            
            if format.lower() == "xlsx":
                renderer = ExcelRenderer()
            elif format.lower() == "pdf":
                renderer = PdfRenderer()
            else:
                raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")
            
            data = result.data if hasattr(result, 'data') else result
            render_result = renderer.render(
                sections=[{"id": "summary", "title": "汇总", "type": "metrics", "items": []}],
                metadata={"code": mapped_report_type, "name": data.get("title", "研发费用报表")}
            )
            
            filename = f"rd-{report_type}-{year}.{format.lower()}"
            return StreamingResponse(
                render_result.data.get("file_stream"),
                media_type=render_result.content_type,
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")



