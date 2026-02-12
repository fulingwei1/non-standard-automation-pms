# -*- coding: utf-8 -*-
"""
BOM导出 - 从 bom.py 拆分
"""

from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.import_export_engine import ExcelExportEngine
from app.models.material import BomHeader, BomItem
from app.models.user import User

router = APIRouter()


@router.get("/{bom_id}/export")
def export_bom_to_excel(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    current_user: User = Depends(security.get_current_active_user),
):
    """导出BOM明细到Excel"""
    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 获取BOM明细
    items = bom.items.order_by(BomItem.item_no).all()

    # 构建导出数据
    data = []
    for item in items:
        data.append(
            {
                "行号": item.item_no,
                "物料编码": item.material_code,
                "物料名称": item.material_name,
                "规格型号": item.specification or "",
                "图号": item.drawing_no or "",
                "单位": item.unit,
                "数量": float(item.quantity),
                "单价": float(item.unit_price) if item.unit_price else 0,
                "金额": float(item.amount) if item.amount else 0,
                "来源类型": item.source_type,
                "需求日期": item.required_date.strftime("%Y-%m-%d")
                if item.required_date
                else "",
                "已采购数量": float(item.purchased_qty or 0),
                "已到货数量": float(item.received_qty or 0),
                "是否关键": "是" if item.is_key_item else "否",
                "备注": item.remark or "",
            }
        )

    labels = [
        "行号",
        "物料编码",
        "物料名称",
        "规格型号",
        "图号",
        "单位",
        "数量",
        "单价",
        "金额",
        "来源类型",
        "需求日期",
        "已采购数量",
        "已到货数量",
        "是否关键",
        "备注",
    ]
    widths = [10, 15, 30, 20, 10, 8, 10, 12, 12, 12, 12, 12, 12, 8, 30]
    columns = ExcelExportEngine.build_columns(labels, widths=widths)

    output = ExcelExportEngine.export_table(
        data=data,
        columns=columns,
        sheet_name="BOM明细",
    )

    # 生成文件名
    filename = f"BOM_{bom.bom_no}_v{bom.version}_{datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        },
    )
