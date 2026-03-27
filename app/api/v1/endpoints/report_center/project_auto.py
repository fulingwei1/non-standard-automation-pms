# -*- coding: utf-8 -*-
"""
项目报告自动生成 API

提供周报/月报自动生成、手动编辑、导出、推送接口。
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.project_report_auto import (
    MonthlyReportGenerateRequest,
    MonthlyReportResponse,
    ReportEditRequest,
    ReportEditResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportPushRequest,
    ReportPushResponse,
    WeeklyReportGenerateRequest,
    WeeklyReportResponse,
)

router = APIRouter(prefix="/project-auto", tags=["project-report-auto"])


# ==================== 周报 ====================


@router.post(
    "/weekly/generate",
    response_model=WeeklyReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="自动生成项目周报",
)
def generate_weekly_report(
    *,
    db: Session = Depends(deps.get_db),
    req: WeeklyReportGenerateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    基于本周数据自动生成项目周报，包含：
    - 本周完成（里程碑 + 工时汇总）
    - 下周计划
    - 风险/问题汇总
    - 资源负荷情况
    - 成本执行情况
    """
    from app.services.project_report_auto import WeeklyReportService

    try:
        service = WeeklyReportService(db)
        data = service.generate(
            project_id=req.project_id,
            report_date=req.report_date,
            template_id=req.template_id,
            generated_by=current_user.id,
        )
        return WeeklyReportResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成周报失败: {str(e)}")


# ==================== 月报 ====================


@router.post(
    "/monthly/generate",
    response_model=MonthlyReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="自动生成项目月报",
)
def generate_monthly_report(
    *,
    db: Session = Depends(deps.get_db),
    req: MonthlyReportGenerateRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    基于本月数据自动生成项目月报，包含：
    - 里程碑进度
    - 成本偏差分析（CV / CPI / EAC）
    - 质量指标（问题统计）
    - 干系人变更
    - 周度趋势
    """
    from app.services.project_report_auto import MonthlyReportService

    try:
        service = MonthlyReportService(db)
        data = service.generate(
            project_id=req.project_id,
            year=req.year,
            month=req.month,
            template_id=req.template_id,
            generated_by=current_user.id,
        )
        return MonthlyReportResponse(**data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成月报失败: {str(e)}")


# ==================== 编辑 ====================


@router.put(
    "/edit",
    response_model=ReportEditResponse,
    summary="编辑报告（手动修改后再发送）",
)
def edit_report(
    *,
    db: Session = Depends(deps.get_db),
    req: ReportEditRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    手动编辑自动生成的报告内容。
    支持合并式更新 summary 和 sections。
    编辑后状态变为 REVIEWED，可继续推送。
    """
    from app.services.project_report_auto import ReportPushService

    try:
        service = ReportPushService(db)
        updated_data = {}
        if req.summary:
            updated_data["summary"] = req.summary
        if req.sections:
            updated_data["sections"] = req.sections
        if req.extra:
            updated_data.update(req.extra)

        result = service.update_report_data(
            report_id=req.report_id,
            updated_data=updated_data,
            editor_id=current_user.id,
        )
        return ReportEditResponse(
            report_id=req.report_id,
            status="REVIEWED",
            updated_data=result,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编辑报告失败: {str(e)}")


# ==================== 推送 ====================


@router.post(
    "/push",
    response_model=ReportPushResponse,
    summary="推送报告（通知 + 导出）",
)
def push_report(
    *,
    db: Session = Depends(deps.get_db),
    req: ReportPushRequest,
    current_user: User = Depends(security.require_permission("report:create")),
) -> Any:
    """
    推送报告：
    - 发送通知给项目负责人和干系人
    - 支持导出 PDF / Excel 附件
    - 支持指定额外接收人和通知渠道
    """
    from app.services.project_report_auto import ReportPushService

    try:
        service = ReportPushService(db)
        result = service.push_report(
            report_id=req.report_id,
            recipient_user_ids=req.recipient_user_ids,
            channels=req.channels,
            export_formats=req.export_formats,
            send_to_pm=req.send_to_pm,
            send_to_stakeholders=req.send_to_stakeholders,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"推送报告失败: {str(e)}")


# ==================== 仅导出 ====================


@router.post(
    "/export",
    response_model=ReportExportResponse,
    summary="仅导出报告（不推送）",
)
def export_report(
    *,
    db: Session = Depends(deps.get_db),
    req: ReportExportRequest,
    current_user: User = Depends(security.require_permission("report:read")),
) -> Any:
    """仅导出报告为 PDF/Excel，不发送通知。"""
    from app.services.project_report_auto import ReportPushService

    try:
        service = ReportPushService(db)
        exports = service.export_only(
            report_id=req.report_id,
            formats=req.formats,
        )
        return ReportExportResponse(exports=exports)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
