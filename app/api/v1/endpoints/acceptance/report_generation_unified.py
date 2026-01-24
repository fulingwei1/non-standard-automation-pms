# -*- coding: utf-8 -*-
"""
验收报告 - 统一报表框架版本

使用统一报表框架生成验收报告
"""

import logging
from datetime import datetime
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.acceptance import AcceptanceOrder, AcceptanceReport
from app.models.user import User
from app.schemas.acceptance import AcceptanceReportResponse
from app.services.report_framework import ConfigError
from app.services.report_framework.adapters.acceptance import AcceptanceReportAdapter
from app.services.report_framework.engine import ParameterError, PermissionError, ReportEngine

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/acceptance-orders/{order_id}/report-unified",
    response_model=AcceptanceReportResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_acceptance_report_unified(
    *,
    db: Session = Depends(deps.get_db),
    order_id: int = Path(..., description="验收单ID"),
    report_type: str = Query(default="FAT", description="报告类型（FAT/SAT/FINAL）"),
    format: str = Query(default="json", description="导出格式（json/pdf/excel/word）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    生成验收报告（使用统一报表框架）

    使用统一报表框架生成验收报告，支持多种导出格式
    """
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
                "report_type": report_type,
            },
            format=format,
            user=current_user,
            skip_cache=False,
        )

        # 生成报告编号和版本（保留原有逻辑）
        from app.services.acceptance_report_service import (
            generate_report_no,
            get_report_version,
            save_report_file,
        )

        report_no = generate_report_no(db, report_type)
        version = get_report_version(db, order_id, report_type)

        # 构建报告内容（从统一框架结果中提取）
        report_content = result.data.get("content", "")
        if not report_content:
            # 如果没有内容，使用适配器生成
            adapter = AcceptanceReportAdapter(db)
            data = adapter.generate_data(
                {"order_id": order_id, "report_type": report_type},
                current_user,
            )
            report_content = f"验收报告\n\n报告编号：{report_no}\n验收单号：{order.order_no}\n\n{data}"

        # 保存报告文件
        file_rel_path, file_size, file_hash = save_report_file(
            report_content,
            report_no,
            report_type,
            True,  # include_signatures
            order,
            db,
            current_user,
        )

        # 创建报告记录
        report = AcceptanceReport(
            order_id=order_id,
            report_no=report_no,
            report_type=report_type,
            version=version,
            report_content=report_content,
            file_path=file_rel_path,
            file_size=file_size,
            file_hash=file_hash,
            generated_at=datetime.now(),
            generated_by=current_user.id,
        )

        db.add(report)

        # 更新验收单的报告文件路径
        if not order.report_file_path or report_type == "FINAL":
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
        raise HTTPException(status_code=500, detail=f"报告生成失败: {e}")
