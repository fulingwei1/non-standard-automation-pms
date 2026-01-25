# -*- coding: utf-8 -*-
"""
工时报表 - 统一报表框架版本

使用统一报表框架生成工时报表
"""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.report_framework import ConfigError
from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

router = APIRouter(prefix="/timesheet/reports-unified", tags=["timesheet-reports-unified"])
logger = logging.getLogger(__name__)


@router.get("/hr", response_model=ResponseModel)
def get_hr_report_unified(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份（1-12）"),
    department_id: Optional[int] = Query(None, description="部门ID（可选）"),
    format: str = Query("json", description="格式：json/pdf/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取HR加班工资报表（使用统一报表框架）

    支持多种导出格式：json、pdf、excel
    """
    try:
        engine = ReportEngine(db)
        result = engine.generate(
            report_code="TIMESHEET_HR_MONTHLY",
            params={
                "year": year,
                "month": month,
                "department_id": department_id,
            },
            format=format,
            user=current_user,
            skip_cache=False,
        )

        if format == "excel":
            # Excel格式返回文件流
            filename = f"HR加班工资表_{year}年{month}月.xlsx"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            # JSON或PDF格式返回数据
            return ResponseModel(
                code=200,
                message="success",
                data=result.data,
            )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"生成HR报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成HR报表失败: {str(e)}")


@router.get("/finance", response_model=ResponseModel)
def get_finance_report_unified(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份（1-12）"),
    project_id: Optional[int] = Query(None, description="项目ID（可选）"),
    format: str = Query("json", description="格式：json/pdf/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取财务报表（项目成本核算）（使用统一报表框架）

    支持多种导出格式：json、pdf、excel
    """
    try:
        engine = ReportEngine(db)
        result = engine.generate(
            report_code="TIMESHEET_FINANCE_MONTHLY",
            params={
                "year": year,
                "month": month,
                "project_id": project_id,
            },
            format=format,
            user=current_user,
            skip_cache=False,
        )

        if format == "excel":
            filename = f"项目成本核算表_{year}年{month}月.xlsx"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            return ResponseModel(
                code=200,
                message="success",
                data=result.data,
            )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"生成财务报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成财务报表失败: {str(e)}")


@router.get("/rd", response_model=ResponseModel)
def get_rd_report_unified(
    *,
    db: Session = Depends(deps.get_db),
    year: int = Query(..., description="年份"),
    month: int = Query(..., ge=1, le=12, description="月份（1-12）"),
    rd_project_id: Optional[int] = Query(None, description="研发项目ID（可选）"),
    format: str = Query("json", description="格式：json/pdf/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取研发报表（研发费用核算）（使用统一报表框架）

    支持多种导出格式：json、pdf、excel
    """
    try:
        engine = ReportEngine(db)
        result = engine.generate(
            report_code="TIMESHEET_RD_MONTHLY",
            params={
                "year": year,
                "month": month,
                "rd_project_id": rd_project_id,
            },
            format=format,
            user=current_user,
            skip_cache=False,
        )

        if format == "excel":
            filename = f"研发费用核算表_{year}年{month}月.xlsx"
            return StreamingResponse(
                result.data.get("file_stream"),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            return ResponseModel(
                code=200,
                message="success",
                data=result.data,
            )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"生成研发报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成研发报表失败: {str(e)}")


@router.get("/project", response_model=ResponseModel)
def get_project_report_unified(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int = Query(..., description="项目ID"),
    start_date: Optional[str] = Query(None, description="开始日期（可选，格式：YYYY-MM-DD）"),
    end_date: Optional[str] = Query(None, description="结束日期（可选，格式：YYYY-MM-DD）"),
    format: str = Query("json", description="格式：json/pdf/excel"),
    current_user: User = Depends(security.require_permission("timesheet:read")),
) -> Any:
    """
    获取项目工时统计报表（使用统一报表框架）

    支持多种导出格式：json、pdf、excel
    """
    from datetime import date as date_type

    try:
        # 解析日期参数
        start_date_parsed = None
        end_date_parsed = None
        if start_date:
            start_date_parsed = date_type.fromisoformat(start_date)
        if end_date:
            end_date_parsed = date_type.fromisoformat(end_date)

        engine = ReportEngine(db)
        result = engine.generate(
            report_code="TIMESHEET_PROJECT",
            params={
                "project_id": project_id,
                "start_date": start_date_parsed.isoformat() if start_date_parsed else None,
                "end_date": end_date_parsed.isoformat() if end_date_parsed else None,
            },
            format=format,
            user=current_user,
            skip_cache=False,
        )

        if format == "excel":
            from app.models.project import Project

            project = db.query(Project).filter(Project.id == project_id).first()
            project_name = project.project_name if project else f"项目{project_id}"
            filename = f"{project_name}_工时报表.xlsx"

            return StreamingResponse(
                result.data.get("file_stream"),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename={filename}"},
            )
        else:
            return ResponseModel(
                code=200,
                message="success",
                data=result.data,
            )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"生成项目报表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"生成项目报表失败: {str(e)}")
