# -*- coding: utf-8 -*-
"""
报价导出功能
包含：导出为Excel、导出为PDF
"""

import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db
from app.core import security
from app.models.sales import Quote, QuoteVersion, QuoteItem
from app.models.user import User
from app.schemas.common import ResponseModel
from app.services.import_export_engine import ExcelExportEngine

router = APIRouter()


@router.get("/quotes/{quote_id}/export/excel")
def export_quote_to_excel(
    quote_id: int,
    version_id: Optional[int] = Query(None, description="指定版本ID，不指定则使用当前版本"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    导出报价为Excel

    Args:
        quote_id: 报价ID
        version_id: 版本ID（可选）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        StreamingResponse: Excel文件流
    """
    quote = db.query(Quote).options(
        joinedload(Quote.customer),
        joinedload(Quote.opportunity)
    ).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取版本
    if version_id:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == version_id,
            QuoteVersion.quote_id == quote_id
        ).first()
    else:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == quote.current_version_id
        ).first() if quote.current_version_id else None

    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    # 获取明细
    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == version.id
    ).all()

    # 构建数据
    header_rows = [{
        "报价编码": quote.quote_code,
        "客户名称": quote.customer.customer_name if quote.customer else "",
        "版本号": version.version_no,
        "总价": float(version.total_price) if version.total_price else 0,
        "成本合计": float(version.cost_total) if version.cost_total else 0,
        "毛利率": f"{float(version.gross_margin)}%" if version.gross_margin else "",
        "交期(天)": version.lead_time_days or "",
    }]

    items_data = []
    for i, item in enumerate(items, 1):
        items_data.append({
            "序号": i,
            "类型": item.item_type or "",
            "名称": item.item_name or "",
            "数量": float(item.qty) if item.qty else 0,
            "单价": float(item.unit_price) if item.unit_price else 0,
            "成本": float(item.cost) if item.cost else 0,
            "小计": float(item.qty * item.unit_price) if item.qty and item.unit_price else 0,
            "备注": item.remark or "",
        })

    sheets = [
        {"name": "报价概要", "data": header_rows},
    ]
    if items_data:
        sheets.append({"name": "报价明细", "data": items_data})

    output = ExcelExportEngine.export_multi_sheet(sheets)

    filename = f"报价_{quote.quote_code}_{version.version_no}_{datetime.now().strftime('%Y%m%d')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    )


@router.get("/quotes/{quote_id}/export/pdf")
def export_quote_to_pdf(
    quote_id: int,
    version_id: Optional[int] = Query(None, description="指定版本ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    导出报价为PDF

    Args:
        quote_id: 报价ID
        version_id: 版本ID（可选）
        db: 数据库会话
        current_user: 当前用户

    Returns:
        StreamingResponse: PDF文件流
    """
    quote = db.query(Quote).options(
        joinedload(Quote.customer),
        joinedload(Quote.opportunity)
    ).filter(Quote.id == quote_id).first()

    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    # 获取版本
    if version_id:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == version_id,
            QuoteVersion.quote_id == quote_id
        ).first()
    else:
        version = db.query(QuoteVersion).filter(
            QuoteVersion.id == quote.current_version_id
        ).first() if quote.current_version_id else None

    if not version:
        raise HTTPException(status_code=404, detail="报价版本不存在")

    items = db.query(QuoteItem).filter(
        QuoteItem.quote_version_id == version.id
    ).all()

    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        # 标题
        elements.append(Paragraph(f"Quote: {quote.quote_code}", styles['Title']))
        elements.append(Spacer(1, 0.5 * cm))

        # 基本信息表格
        info_data = [
            ["Customer", quote.customer.customer_name if quote.customer else "-"],
            ["Version", version.version_no],
            ["Total Price", f"{float(version.total_price):,.2f}" if version.total_price else "-"],
            ["Cost Total", f"{float(version.cost_total):,.2f}" if version.cost_total else "-"],
            ["Gross Margin", f"{float(version.gross_margin)}%" if version.gross_margin else "-"],
            ["Lead Time", f"{version.lead_time_days} days" if version.lead_time_days else "-"],
        ]
        info_table = Table(info_data, colWidths=[4 * cm, 10 * cm])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(info_table)
        elements.append(Spacer(1, 1 * cm))

        # 明细表格
        if items:
            elements.append(Paragraph("Line Items", styles['Heading2']))
            elements.append(Spacer(1, 0.3 * cm))

            item_data = [["#", "Type", "Name", "Qty", "Unit Price", "Cost"]]
            for i, item in enumerate(items, 1):
                item_data.append([
                    str(i),
                    item.item_type or "-",
                    (item.item_name or "-")[:30],
                    str(float(item.qty)) if item.qty else "-",
                    f"{float(item.unit_price):,.2f}" if item.unit_price else "-",
                    f"{float(item.cost):,.2f}" if item.cost else "-",
                ])

            item_table = Table(item_data, colWidths=[1 * cm, 2 * cm, 5 * cm, 2 * cm, 3 * cm, 3 * cm])
            item_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            elements.append(item_table)

        doc.build(elements)
        output.seek(0)

        filename = f"Quote_{quote.quote_code}_{version.version_no}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return StreamingResponse(
            output,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="PDF导出功能需要安装reportlab")


@router.get("/quotes/export/batch", response_model=ResponseModel)
def batch_export_quotes(
    quote_ids: str = Query(..., description="报价ID列表，逗号分隔"),
    format: str = Query("excel", description="导出格式: excel"),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    批量导出报价（返回下载任务ID）

    Args:
        quote_ids: 报价ID列表
        format: 导出格式
        db: 数据库会话
        current_user: 当前用户

    Returns:
        ResponseModel: 导出任务信息
    """
    ids = [int(id.strip()) for id in quote_ids.split(",") if id.strip().isdigit()]

    if not ids:
        raise HTTPException(status_code=400, detail="请提供有效的报价ID")

    if len(ids) > 50:
        raise HTTPException(status_code=400, detail="单次最多导出50个报价")

    # 验证报价存在
    quotes = db.query(Quote).filter(Quote.id.in_(ids)).all()
    if len(quotes) != len(ids):
        raise HTTPException(status_code=404, detail="部分报价不存在")

    # 实际项目中这里应该创建异步任务
    return ResponseModel(
        code=200,
        message="批量导出任务已创建",
        data={
            "task_id": f"export_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "quote_count": len(ids),
            "format": format,
            "status": "PROCESSING"
        }
    )
