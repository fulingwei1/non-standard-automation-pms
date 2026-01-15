# -*- coding: utf-8 -*-
"""
导出 - 自动生成
从 sales/quotes.py 拆分
"""

from typing import Any, List, Optional

from datetime import datetime

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session, joinedload

from sqlalchemy import desc, or_

from app.api import deps

from app.core.config import settings

from app.core import security

from app.models.user import User

from app.models.sales import (

from app.schemas.sales import (


from fastapi import APIRouter

router = APIRouter(
    prefix="/quotes",
    tags=["exports"]
)

# 共 2 个路由

# ==================== 导出 ====================


@router.get("/quotes/export")
def export_quotes(
    *,
    db: Session = Depends(deps.get_db),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status: Optional[str] = Query(None, description="状态筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    owner_id: Optional[int] = Query(None, description="负责人ID筛选"),
    include_items: bool = Query(False, description="是否包含明细"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.3: 导出报价列表（Excel）
    支持导出报价主表和明细（多 Sheet）
    """
    from app.services.excel_export_service import ExcelExportService, create_excel_response

    query = db.query(Quote)
    if keyword:
        query = query.filter(or_(Quote.quote_code.contains(keyword), Quote.opportunity.has(Opportunity.opp_name.contains(keyword))))
    if status:
        query = query.filter(Quote.status == status)
    if customer_id:
        query = query.filter(Quote.customer_id == customer_id)
    if owner_id:
        query = query.filter(Quote.owner_id == owner_id)

    quotes = query.order_by(Quote.created_at.desc()).all()
    export_service = ExcelExportService()

    if include_items:
        sheets = []
        quote_data = []
        for quote in quotes:
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            quote_data.append({
                "quote_code": quote.quote_code,
                "opp_code": quote.opportunity.opp_code if quote.opportunity else '',
                "customer_name": quote.customer.customer_name if quote.customer else '',
                "status": quote.status,
                "total_price": float(version.total_price) if version and version.total_price else 0,
                "total_cost": float(version.total_cost) if version and version.total_cost else 0,
                "gross_margin": float(version.gross_margin) if version and version.gross_margin else 0,
                "valid_until": version.valid_until if version and version.valid_until else None,
                "owner_name": quote.owner.real_name if quote.owner else '',
                "created_at": quote.created_at,
            })
        sheets.append({
            "name": "报价列表",
            "data": quote_data,
            "columns": [
                {"key": "quote_code", "label": "报价编码", "width": 15},
                {"key": "opp_code", "label": "商机编码", "width": 15},
                {"key": "customer_name", "label": "客户名称", "width": 25},
                {"key": "status", "label": "状态", "width": 12},
                {"key": "total_price", "label": "报价金额", "width": 15, "format": export_service.format_currency},
                {"key": "total_cost", "label": "成本金额", "width": 15, "format": export_service.format_currency},
                {"key": "gross_margin", "label": "毛利率", "width": 12, "format": export_service.format_percentage},
                {"key": "valid_until", "label": "有效期至", "width": 12, "format": export_service.format_date},
                {"key": "owner_name", "label": "负责人", "width": 12},
                {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
            ],
            "title": "报价列表"
        })
        item_data = []
        for quote in quotes:
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            if version:
                items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()
                for item in items:
                    item_data.append({
                        "quote_code": quote.quote_code,
                        "item_name": item.item_name or '',
                        "specification": item.specification or '',
                        "qty": float(item.qty) if item.qty else 0,
                        "unit": item.unit or '',
                        "unit_price": float(item.unit_price) if item.unit_price else 0,
                        "total_price": float(item.total_price) if item.total_price else 0,
                        "cost": float(item.cost) if item.cost else 0,
                        "item_type": item.item_type or '',
                    })
        sheets.append({
            "name": "报价明细",
            "data": item_data,
            "columns": [
                {"key": "quote_code", "label": "报价编码", "width": 15},
                {"key": "item_name", "label": "物料名称", "width": 30},
                {"key": "specification", "label": "规格型号", "width": 25},
                {"key": "qty", "label": "数量", "width": 10},
                {"key": "unit", "label": "单位", "width": 8},
                {"key": "unit_price", "label": "单价", "width": 12, "format": export_service.format_currency},
                {"key": "total_price", "label": "总价", "width": 12, "format": export_service.format_currency},
                {"key": "cost", "label": "成本", "width": 12, "format": export_service.format_currency},
                {"key": "item_type", "label": "类型", "width": 12},
            ],
            "title": "报价明细"
        })
        excel_data = export_service.export_multisheet(sheets)
    else:
        quote_data = []
        for quote in quotes:
            version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
            quote_data.append({
                "quote_code": quote.quote_code,
                "opp_code": quote.opportunity.opp_code if quote.opportunity else '',
                "customer_name": quote.customer.customer_name if quote.customer else '',
                "status": quote.status,
                "total_price": float(version.total_price) if version and version.total_price else 0,
                "total_cost": float(version.total_cost) if version and version.total_cost else 0,
                "gross_margin": float(version.gross_margin) if version and version.gross_margin else 0,
                "valid_until": version.valid_until if version and version.valid_until else None,
                "owner_name": quote.owner.real_name if quote.owner else '',
                "created_at": quote.created_at,
            })
        columns = [
            {"key": "quote_code", "label": "报价编码", "width": 15},
            {"key": "opp_code", "label": "商机编码", "width": 15},
            {"key": "customer_name", "label": "客户名称", "width": 25},
            {"key": "status", "label": "状态", "width": 12},
            {"key": "total_price", "label": "报价金额", "width": 15, "format": export_service.format_currency},
            {"key": "total_cost", "label": "成本金额", "width": 15, "format": export_service.format_currency},
            {"key": "gross_margin", "label": "毛利率", "width": 12, "format": export_service.format_percentage},
            {"key": "valid_until", "label": "有效期至", "width": 12, "format": export_service.format_date},
            {"key": "owner_name", "label": "负责人", "width": 12},
            {"key": "created_at", "label": "创建时间", "width": 18, "format": export_service.format_date},
        ]
        excel_data = export_service.export_to_excel(data=quote_data, columns=columns, sheet_name="报价列表", title="报价列表")

    filename = f"报价列表_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return create_excel_response(excel_data, filename)


@router.get("/quotes/{quote_id}/pdf")
def export_quote_pdf(
    *,
    db: Session = Depends(deps.get_db),
    quote_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    Issue 4.5: 导出报价单 PDF
    """
    from app.services.pdf_export_service import PDFExportService, create_pdf_response

    quote = db.query(Quote).filter(Quote.id == quote_id).first()
    if not quote:
        raise HTTPException(status_code=404, detail="报价不存在")

    version = db.query(QuoteVersion).filter(QuoteVersion.id == quote.current_version_id).first()
    if not version:
        raise HTTPException(status_code=400, detail="报价没有当前版本")

    items = db.query(QuoteItem).filter(QuoteItem.quote_version_id == version.id).all()

    # 准备数据
    quote_data = {
        "quote_code": quote.quote_code,
        "customer_name": quote.customer.customer_name if quote.customer else '',
        "created_at": quote.created_at,
        "valid_until": version.valid_until,
        "total_price": float(version.total_price) if version.total_price else 0,
        "status": quote.status,
    }

    quote_items = [{
        "item_name": item.item_name or '',
        "specification": item.specification or '',
        "qty": float(item.qty) if item.qty else 0,
        "unit": item.unit or '',
        "unit_price": float(item.unit_price) if item.unit_price else 0,
        "total_price": float(item.total_price) if item.total_price else 0,
        "remark": item.remark or '',
    } for item in items]

    pdf_service = PDFExportService()
    pdf_data = pdf_service.export_quote_to_pdf(quote_data, quote_items)

    filename = f"报价单_{quote.quote_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return create_pdf_response(pdf_data, filename)

