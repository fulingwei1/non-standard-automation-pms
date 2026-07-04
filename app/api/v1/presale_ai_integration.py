"""
售前AI系统集成 - API路由
Team 10: 售前AI系统集成与前端UI
"""

import csv
import logging
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.schemas.presale_ai import (
    AIAuditLogResponse,
    AIConfigResponse,
    AIConfigUpdate,
    AIFeedbackCreate,
    AIFeedbackResponse,
    AIUsageStatsResponse,
    AIWorkflowLogResponse,
    BatchProcessRequest,
    BatchProcessResponse,
    DashboardStatsResponse,
    ExportReportRequest,
    ExportReportResponse,
    HealthCheckResponse,
    WorkflowStartRequest,
    WorkflowStatusResponse,
)
from app.services.presale.presale_ai_integration import PresaleAIIntegrationService

logger = logging.getLogger(__name__)

router = APIRouter()

EXPORT_COLUMNS = [
    ("date", "日期"),
    ("ai_function", "AI功能"),
    ("user_id", "用户ID"),
    ("usage_count", "使用次数"),
    ("success_count", "成功次数"),
    ("success_rate", "成功率"),
    ("avg_response_time", "平均响应时间(ms)"),
]

EXPORT_MEDIA_TYPES = {
    "csv": "text/csv; charset=utf-8",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pdf": "application/pdf",
}


def _report_export_dir() -> Path:
    export_dir = Path(settings.UPLOAD_DIR).expanduser().resolve() / "presale_ai_reports"
    export_dir.mkdir(parents=True, exist_ok=True)
    return export_dir


def _normalize_export_format(format_name: str) -> tuple[str, str]:
    normalized = (format_name or "excel").strip().lower()
    if normalized in {"excel", "xlsx"}:
        return "xlsx", "xlsx"
    if normalized in {"csv"}:
        return "csv", "csv"
    if normalized in {"pdf"}:
        return "pdf", "pdf"
    raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format_name}")


def _report_rows(stats: list[dict]) -> list[dict]:
    rows = []
    for item in stats:
        usage_count = int(item.get("usage_count") or 0)
        success_count = int(item.get("success_count") or 0)
        success_rate = round(success_count / usage_count * 100, 2) if usage_count else 0
        report_date = item.get("date")
        ai_function = str(item.get("ai_function") or "")
        if ai_function.isupper():
            ai_function = ai_function.lower()
        rows.append(
            {
                "date": report_date.isoformat() if hasattr(report_date, "isoformat") else report_date,
                "ai_function": ai_function,
                "user_id": item.get("user_id") or "",
                "usage_count": usage_count,
                "success_count": success_count,
                "success_rate": f"{success_rate}%",
                "avg_response_time": item.get("avg_response_time") or "",
            }
        )
    return rows


def _write_csv_report(file_path: Path, rows: list[dict]) -> None:
    with file_path.open("w", encoding="utf-8-sig", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=[column for column, _ in EXPORT_COLUMNS])
        writer.writerow({column: label for column, label in EXPORT_COLUMNS})
        writer.writerows(rows)


def _write_xlsx_report(file_path: Path, rows: list[dict]) -> None:
    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise HTTPException(status_code=500, detail="Excel 导出功能需要安装 openpyxl") from exc

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "AI使用统计"
    sheet.append([label for _, label in EXPORT_COLUMNS])
    for row in rows:
        sheet.append([row.get(column, "") for column, _ in EXPORT_COLUMNS])
    for column_cells in sheet.columns:
        max_length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max_length + 2, 32)
    workbook.save(file_path)


def _write_pdf_report(file_path: Path, rows: list[dict], title: str) -> None:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise HTTPException(status_code=500, detail="PDF 导出功能需要安装 reportlab") from exc

    styles = getSampleStyleSheet()
    document = SimpleDocTemplate(str(file_path), pagesize=A4)
    table_data = [[label for _, label in EXPORT_COLUMNS]]
    table_data.extend([[row.get(column, "") for column, _ in EXPORT_COLUMNS] for row in rows])
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    document.build([Paragraph(title, styles["Title"]), Spacer(1, 12), table])


def _generate_usage_report_file(
    export_request: ExportReportRequest,
    stats: list[dict],
) -> Path:
    _, extension = _normalize_export_format(export_request.format)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"ai_report_{export_request.start_date}_{export_request.end_date}_{timestamp}.{extension}"
    file_path = _report_export_dir() / file_name
    rows = _report_rows(stats)

    if extension == "csv":
        _write_csv_report(file_path, rows)
    elif extension == "xlsx":
        _write_xlsx_report(file_path, rows)
    else:
        _write_pdf_report(
            file_path,
            rows,
            f"AI Usage Report {export_request.start_date} to {export_request.end_date}",
        )
    return file_path


# ============ 仪表盘统计 ============


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    days: int = Query(default=30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI仪表盘统计数据

    - 总使用次数
    - 总成功次数
    - 成功率
    - 平均响应时间
    - Top AI功能
    - 使用趋势
    - 用户统计
    """
    service = PresaleAIIntegrationService(db)
    return service.get_dashboard_stats(days=days)


# ============ 使用统计 ============


@router.get("/usage-stats", response_model=List[AIUsageStatsResponse])
async def get_usage_stats(
    start_date: Optional[date] = Query(None, description="开始日期"),
    end_date: Optional[date] = Query(None, description="结束日期"),
    ai_functions: Optional[List[str]] = Query(None, description="AI功能列表"),
    user_ids: Optional[List[int]] = Query(None, description="用户ID列表"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取AI使用统计

    支持多维度查询：日期范围、AI功能、用户等
    """
    service = PresaleAIIntegrationService(db)
    stats = service.get_usage_stats(
        start_date=start_date, end_date=end_date, ai_functions=ai_functions, user_ids=user_ids
    )
    return stats


# ============ 反馈管理 ============


@router.post("/feedback", response_model=AIFeedbackResponse)
async def submit_feedback(
    feedback_data: AIFeedbackCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    提交AI反馈

    - 评分1-5星
    - 反馈文本
    - 关联售前工单
    """
    service = PresaleAIIntegrationService(db)

    # 创建反馈
    feedback = service.create_feedback(user_id=current_user.id, feedback_data=feedback_data)

    # 记录审计日志
    service.create_audit_log(
        user_id=current_user.id,
        action="submit_feedback",
        ai_function=feedback_data.ai_function,
        resource_type="feedback",
        resource_id=feedback.id,
        details={"rating": feedback_data.rating},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return feedback


@router.get("/feedback/{function}", response_model=List[AIFeedbackResponse])
async def get_feedback_by_function(
    function: str,
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    max_rating: Optional[int] = Query(None, ge=1, le=5),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定AI功能的反馈

    支持评分过滤、日期范围等
    """
    service = PresaleAIIntegrationService(db)
    feedbacks = service.get_feedbacks(
        ai_function=function,
        min_rating=min_rating,
        max_rating=max_rating,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )
    return feedbacks


# ============ 工作流管理 ============


@router.post("/workflow/start", response_model=List[AIWorkflowLogResponse])
async def start_workflow(
    workflow_request: WorkflowStartRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    启动AI工作流

    自动创建：需求理解 → 方案生成 → 成本估算 → 赢率预测 → 报价生成
    """
    service = PresaleAIIntegrationService(db)

    try:
        logs = service.start_workflow(
            presale_ticket_id=workflow_request.presale_ticket_id,
            initial_data=workflow_request.initial_data,
            auto_run=workflow_request.auto_run,
        )

        # 记录审计日志
        service.create_audit_log(
            user_id=current_user.id,
            action="start_workflow",
            resource_type="workflow",
            resource_id=workflow_request.presale_ticket_id,
            details={"auto_run": workflow_request.auto_run},
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return logs
    except ValueError as e:
        raise HTTPException(status_code=501, detail=str(e)) from e
    except Exception as e:
        logger.error(f"Failed to start workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start workflow: {str(e)}")


@router.get("/workflow/status/{ticket_id}", response_model=WorkflowStatusResponse)
async def get_workflow_status(
    ticket_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取工作流状态

    返回：
    - 当前步骤
    - 整体状态
    - 所有步骤详情
    - 进度百分比
    """
    service = PresaleAIIntegrationService(db)
    status = service.get_workflow_status(ticket_id)

    if not status:
        raise HTTPException(status_code=404, detail=f"Workflow not found for ticket {ticket_id}")

    return status


# ============ 批量处理 ============


@router.post("/batch-process", response_model=BatchProcessResponse)
async def batch_process(
    batch_request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    批量AI处理

    支持批量处理多个工单的指定AI功能
    """
    import uuid

    job_id = str(uuid.uuid4())

    # 记录审计日志
    service = PresaleAIIntegrationService(db)
    service.create_audit_log(
        user_id=current_user.id,
        action="batch_process",
        ai_function=batch_request.ai_function,
        details={
            "job_id": job_id,
            "ticket_count": len(batch_request.ticket_ids),
            "options": batch_request.options,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    # TODO: 实际的批量处理逻辑（异步处理）
    # background_tasks.add_task(process_batch, batch_request, job_id)

    return BatchProcessResponse(
        job_id=job_id,
        total_count=len(batch_request.ticket_ids),
        status="started",
        started_at=datetime.now(),
    )


# ============ 健康检查 ============


@router.get("/health-check", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """
    AI服务健康检查

    检查：
    - 数据库连接
    - AI功能配置
    - 最近活动情况
    """
    service = PresaleAIIntegrationService(db)
    return service.health_check()


# ============ 配置管理 ============


@router.post("/config/update", response_model=AIConfigResponse)
async def update_config(
    ai_function: str,
    config_data: AIConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新AI配置

    可配置：
    - 是否启用
    - 模型名称
    - 温度参数
    - 最大tokens
    - 超时时间
    """
    service = PresaleAIIntegrationService(db)

    try:
        config = service.update_config(ai_function, config_data)

        # 记录审计日志
        service.create_audit_log(
            user_id=current_user.id,
            action="update_config",
            ai_function=ai_function,
            resource_type="config",
            resource_id=config.id,
            details=config_data.dict(exclude_unset=True),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        return config
    except Exception as e:
        logger.error(f"Failed to update config: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")


@router.get("/config", response_model=List[AIConfigResponse])
async def get_all_configs(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    获取所有AI配置
    """
    service = PresaleAIIntegrationService(db)
    return service.get_all_configs()


# ============ 审计日志 ============


@router.get("/audit-log", response_model=List[AIAuditLogResponse])
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取操作审计日志

    记录所有AI相关操作
    """
    service = PresaleAIIntegrationService(db)
    return service.get_audit_logs(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset,
    )


# ============ 报告导出 ============


@router.post("/export-report", response_model=ExportReportResponse)
async def export_report(
    export_request: ExportReportRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    导出AI使用报告

    支持格式：
    - Excel
    - PDF
    - CSV
    """

    service = PresaleAIIntegrationService(db)

    # 记录审计日志
    service.create_audit_log(
        user_id=current_user.id,
        action="export_report",
        details={
            "start_date": export_request.start_date.isoformat(),
            "end_date": export_request.end_date.isoformat(),
            "format": export_request.format,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    stats = service.get_usage_stats(
        start_date=export_request.start_date,
        end_date=export_request.end_date,
        ai_functions=export_request.ai_functions,
        user_ids=export_request.user_ids,
    )
    file_path = _generate_usage_report_file(export_request, stats)

    return ExportReportResponse(
        file_url=f"/api/v1/presale/ai/downloads/{file_path.name}",
        file_name=file_path.name,
        file_size=file_path.stat().st_size,
        generated_at=datetime.now(),
    )


@router.get("/downloads/{file_name}", response_class=FileResponse)
async def download_exported_report(
    file_name: str,
    current_user: User = Depends(get_current_user),
):
    """下载 AI 使用报告导出文件。"""
    safe_name = Path(file_name).name
    if safe_name != file_name:
        raise HTTPException(status_code=400, detail="非法文件名")

    file_path = _report_export_dir() / safe_name
    try:
        file_path.resolve().relative_to(_report_export_dir())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="非法文件路径") from exc
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="导出文件不存在")

    extension = file_path.suffix.lstrip(".").lower()
    media_type = EXPORT_MEDIA_TYPES.get(extension, "application/octet-stream")
    return FileResponse(path=file_path, media_type=media_type, filename=safe_name)
