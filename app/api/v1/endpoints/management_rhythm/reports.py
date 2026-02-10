# -*- coding: utf-8 -*-
"""
会议报告 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.core.config import settings
from app.models.management_rhythm import (
    MeetingReport,
    MeetingReportConfig,
)
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.management_rhythm import (
    MeetingReportGenerateRequest,
    MeetingReportResponse,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/management-rhythm/reports",
    tags=["reports"]
)

# 共 4 个路由

# ==================== 会议报告 ====================

@router.post("/meeting-reports/generate", response_model=MeetingReportResponse, status_code=status.HTTP_201_CREATED)
def generate_meeting_report(
    report_request: MeetingReportGenerateRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成会议报告（年度或月度）（使用统一报表框架）

    - **年度报告**：生成指定年份的年度会议报告
    - **月度报告**：生成指定年月的月度会议报告，包含与上月对比数据

    如果report_request中包含config_id，将使用该配置生成报告（包含业务指标）。
    如果没有config_id，将尝试使用默认配置。
    """
    from calendar import monthrange

    from app.services.report_framework import ConfigError
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    # 获取配置ID（优先使用请求中的，否则使用默认配置）
    config_id = report_request.config_id

    if not config_id:
        # 尝试获取默认配置
        default_config = db.query(MeetingReportConfig).filter(
            and_(
                MeetingReportConfig.report_type == report_request.report_type,
                MeetingReportConfig.is_default == True,
                MeetingReportConfig.is_active == True
            )
        ).first()
        if default_config:
            config_id = default_config.id

    try:
        # 使用统一报表框架生成报告
        engine = ReportEngine(db)

        if report_request.report_type == "ANNUAL":
            if report_request.period_month:
                raise HTTPException(status_code=400, detail="年度报告不需要指定月份")

            # 年度报告使用统一报表框架（如果YAML配置不存在，使用适配器）
            try:
                result = engine.generate(
                    report_code="MEETING_ANNUAL",
                    params={
                        "year": report_request.period_year,
                        "rhythm_level": report_request.rhythm_level,
                        "config_id": config_id,
                    },
                    format="json",
                    user=current_user,
                    skip_cache=False,
                )
                # 如果统一框架返回数据，需要转换为MeetingReport对象
                # 这里暂时使用适配器方法（待完善）
                from app.services.report_framework.adapters.meeting import MeetingReportAdapter
                adapter = MeetingReportAdapter(db)
                # 使用适配器生成数据，然后创建MeetingReport对象
                raise ConfigError("MEETING_ANNUAL YAML配置待创建")
            except ConfigError:
                # 如果YAML配置不存在，使用适配器（向后兼容）
                from app.services.report_framework.adapters.meeting import MeetingReportAdapter
                adapter = MeetingReportAdapter(db)
                # 暂时返回错误，提示需要创建YAML配置或完善适配器
                raise HTTPException(
                    status_code=501,
                    detail="年度会议报告功能待完善，请使用月度报告或联系管理员"
                )
        elif report_request.report_type == "MONTHLY":
            if not report_request.period_month:
                raise HTTPException(status_code=400, detail="月度报告必须指定月份")

            if not (1 <= report_request.period_month <= 12):
                raise HTTPException(status_code=400, detail="月份必须在1-12之间")

            # 使用统一报表框架生成月度报告
            from datetime import date
            period_start = date(report_request.period_year, report_request.period_month, 1)
            period_end = date(report_request.period_year, report_request.period_month,
                            monthrange(report_request.period_year, report_request.period_month)[1])

            try:
                result = engine.generate(
                    report_code="MEETING_MONTHLY",
                    params={
                        "year": report_request.period_year,
                        "month": report_request.period_month,
                        "start_date": period_start.isoformat(),
                        "end_date": period_end.isoformat(),
                        "rhythm_level": report_request.rhythm_level,
                        "config_id": config_id,
                    },
                    format="json",
                    user=current_user,
                    skip_cache=False,
                )
                # 统一框架返回JSON数据，需要转换为MeetingReport对象
                # 这里暂时使用适配器方法（待完善）
                raise ConfigError("MEETING_MONTHLY需要返回MeetingReport对象")
            except ConfigError:
                # 如果YAML配置不存在或需要返回MeetingReport对象，使用适配器
                from app.services.report_framework.adapters.meeting import MeetingReportAdapter
                adapter = MeetingReportAdapter(db)
                # 暂时返回错误，提示需要完善适配器
                raise HTTPException(
                    status_code=501,
                    detail="月度会议报告功能待完善，请使用统一报表框架端点或联系管理员"
                )
        else:
            raise HTTPException(status_code=400, detail="报告类型必须是ANNUAL或MONTHLY")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成会议报告失败: {str(e)}")

    return MeetingReportResponse(
        id=report.id,
        report_no=report.report_no,
        report_type=report.report_type,
        report_title=report.report_title,
        period_year=report.period_year,
        period_month=report.period_month,
        period_start=report.period_start,
        period_end=report.period_end,
        rhythm_level=report.rhythm_level,
        report_data=report.report_data,
        comparison_data=report.comparison_data,
        file_path=report.file_path,
        file_size=report.file_size,
        status=report.status,
        generated_by=report.generated_by,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/meeting-reports", response_model=PaginatedResponse)
def read_meeting_reports(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    report_type: Optional[str] = Query(None, description="报告类型筛选:ANNUAL/MONTHLY"),
    period_year: Optional[int] = Query(None, description="年份筛选"),
    rhythm_level: Optional[str] = Query(None, description="节律层级筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议报告列表
    """
    query = db.query(MeetingReport)

    if report_type:
        query = query.filter(MeetingReport.report_type == report_type)

    if period_year:
        query = query.filter(MeetingReport.period_year == period_year)

    if rhythm_level:
        query = query.filter(MeetingReport.rhythm_level == rhythm_level)

    total = query.count()
    reports = query.order_by(desc(MeetingReport.period_start), desc(MeetingReport.created_at)).offset(pagination.offset).limit(pagination.limit).all()

    items = []
    for report in reports:
        items.append(MeetingReportResponse(
            id=report.id,
            report_no=report.report_no,
            report_type=report.report_type,
            report_title=report.report_title,
            period_year=report.period_year,
            period_month=report.period_month,
            period_start=report.period_start,
            period_end=report.period_end,
            rhythm_level=report.rhythm_level,
            report_data=report.report_data,
            comparison_data=report.comparison_data,
            file_path=report.file_path,
            file_size=report.file_size,
            status=report.status,
            generated_by=report.generated_by,
            generated_at=report.generated_at,
            published_at=report.published_at,
            created_at=report.created_at,
            updated_at=report.updated_at,
        ))

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.get("/meeting-reports/{report_id}", response_model=MeetingReportResponse)
def read_meeting_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议报告详情
    """
    report = db.query(MeetingReport).filter(MeetingReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    return MeetingReportResponse(
        id=report.id,
        report_no=report.report_no,
        report_type=report.report_type,
        report_title=report.report_title,
        period_year=report.period_year,
        period_month=report.period_month,
        period_start=report.period_start,
        period_end=report.period_end,
        rhythm_level=report.rhythm_level,
        report_data=report.report_data,
        comparison_data=report.comparison_data,
        file_path=report.file_path,
        file_size=report.file_size,
        status=report.status,
        generated_by=report.generated_by,
        generated_at=report.generated_at,
        published_at=report.published_at,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.get("/meeting-reports/{report_id}/export-docx")
def export_meeting_report_docx(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    导出会议报告为Word文档
    """
    import os

    from fastapi.responses import StreamingResponse

    from app.services.meeting_report_docx_service import MeetingReportDocxService

    report = db.query(MeetingReport).filter(MeetingReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    try:
        docx_service = MeetingReportDocxService()

        if report.report_type == "ANNUAL":
            # 生成年度报告Word文档
            buffer = docx_service.generate_annual_report_docx(
                report_data=report.report_data or {},
                report_title=report.report_title,
                period_year=report.period_year,
                rhythm_level=report.rhythm_level if report.rhythm_level != "ALL" else None
            )
        else:
            # 生成月度报告Word文档
            buffer = docx_service.generate_monthly_report_docx(
                report_data=report.report_data or {},
                comparison_data=report.comparison_data or {},
                report_title=report.report_title,
                period_year=report.period_year,
                period_month=report.period_month or 1,
                rhythm_level=report.rhythm_level if report.rhythm_level != "ALL" else None
            )

        # 保存文件
        report_dir = os.path.join(settings.UPLOAD_DIR, "reports")
        os.makedirs(report_dir, exist_ok=True)

        file_rel_path = f"reports/{report.report_no}.docx"
        file_full_path = os.path.join(settings.UPLOAD_DIR, file_rel_path)

        with open(file_full_path, "wb") as f:
            f.write(buffer.read())

        file_size = os.path.getsize(file_full_path)

        # 更新报告记录
        report.file_path = file_rel_path
        report.file_size = file_size
        db.commit()

        # 返回文件
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={report.report_no}.docx"
            }
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="Word文档生成功能不可用，请安装python-docx库")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成Word文档失败: {str(e)}")

