# -*- coding: utf-8 -*-
"""
验收报告 - 报告生成和下载

包含报告生成、下载功能
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder, AcceptanceReport
from app.models.user import User
from app.schemas.acceptance import (
    AcceptanceReportGenerateRequest,
    AcceptanceReportResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# 辅助函数已移至 app.services.acceptance_report_service
# 这里保留导入以便向后兼容（如果需要）


@router.post("/acceptance-orders/{order_id}/report", response_model=AcceptanceReportResponse, status_code=status.HTTP_201_CREATED)
def generate_acceptance_report(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int,
    report_in: AcceptanceReportGenerateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成验收报告（使用统一报表框架）
    """
    from datetime import datetime

    from app.services.report_framework import ConfigError
    from app.services.report_framework.adapters.acceptance import AcceptanceReportAdapter
    from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    if order.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="只有已完成的验收单才能生成报告")

    try:
        # 使用统一报表框架生成报告
        engine = ReportEngine(db)
        result = engine.generate(
            report_code="ACCEPTANCE_REPORT",
            params={
                "order_id": order_id,
                "report_type": report_in.report_type,
            },
            format="json",
            user=current_user,
            skip_cache=False,
        )

        # 生成报告编号和版本（保留原有逻辑）
        from app.services.acceptance.report_utils import (
            generate_report_no,
            get_report_version,
            save_report_file,
        )

        report_no = generate_report_no(db, report_in.report_type)
        version = get_report_version(db, order_id, report_in.report_type)

        # 构建报告内容（从统一框架结果中提取）
        report_content = result.data.get("content", "")
        if not report_content:
            # 如果没有内容，使用工具函数生成
            from app.services.acceptance.report_utils import build_report_content
            report_content = build_report_content(
                db, order, report_no, version, current_user
            )

        # 保存报告文件
        file_rel_path, file_size, file_hash = save_report_file(
            report_content,
            report_no,
            report_in.report_type,
            report_in.include_signatures,
            order,
            db,
            current_user,
        )

        # 创建报告记录
        report = AcceptanceReport(
            order_id=order_id,
            report_no=report_no,
            report_type=report_in.report_type,
            version=version,
            report_content=report_content,
            file_path=file_rel_path,
            file_size=file_size,
            file_hash=file_hash,
            generated_at=datetime.now(),
            generated_by=current_user.id,
        )

        db.add(report)

        # 更新验收单的报告文件路径（如果有最新报告）
        if not order.report_file_path or report_in.report_type == "FINAL":
            order.report_file_path = file_rel_path
            db.add(order)

        db.commit()
        db.refresh(report)

        return AcceptanceReportResponse(
            id=report.id,
            order_id=report.order_id,
            report_no=report.report_no,
            report_type=report.report_type,
            version=report.version,
            report_content=report.report_content,
            file_path=report.file_path,
            file_size=report.file_size,
            file_hash=report.file_hash,
            generated_at=report.generated_at,
            generated_by=report.generated_by,
            generated_by_name=current_user.real_name or current_user.username,
            created_at=report.created_at,
            updated_at=report.updated_at,
        )

    except ConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ParameterError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"生成验收报告失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"报告生成失败: {str(e)}")


@router.get("/acceptance-reports/{report_id}/download", response_class=FileResponse)
def download_acceptance_report(
    report_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载验收报告（支持PDF和文本格式）
    """
    import os
    from fastapi.responses import Response
    from app.core.config import settings

    report = db.query(AcceptanceReport).filter(AcceptanceReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="验收报告不存在")

    if not report.file_path:
        raise HTTPException(status_code=404, detail="报告文件不存在")

    # 安全检查：解析为规范路径，防止路径遍历攻击
    upload_dir = os.path.abspath(settings.UPLOAD_DIR)
    file_path = os.path.abspath(os.path.join(settings.UPLOAD_DIR, report.file_path))

    if not file_path.startswith(upload_dir + os.sep):
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not os.path.exists(file_path):
        # 如果文件不存在，返回报告内容作为文本
        content = report.report_content or "报告内容为空"
        return Response(
            content=content.encode('utf-8'),
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={report.report_no}.txt"
            }
        )

    filename = os.path.basename(file_path)
    # 根据文件扩展名设置媒体类型
    if filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".txt"):
        media_type = "text/plain"
    else:
        media_type = "application/octet-stream"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )


@router.get("/acceptance-orders/{order_id}/report", response_model=List[AcceptanceReportResponse], status_code=status.HTTP_200_OK)
def read_acceptance_reports(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取验收报告列表
    """
    order = db.query(AcceptanceOrder).filter(AcceptanceOrder.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="验收单不存在")

    reports = db.query(AcceptanceReport).filter(AcceptanceReport.order_id == order_id).order_by(desc(AcceptanceReport.created_at)).all()

    items = []
    for report in reports:
        items.append(AcceptanceReportResponse(
            id=report.id,
            order_id=report.order_id,
            report_no=report.report_no,
            report_type=report.report_type,
            version=report.version,
            generated_by=report.generated_by,
            file_size=report.file_size,
            include_signatures=report.include_signatures,
            created_at=report.created_at,
            updated_at=report.updated_at
        ))

    return items
