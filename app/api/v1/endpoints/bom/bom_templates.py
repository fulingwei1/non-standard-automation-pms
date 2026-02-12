# -*- coding: utf-8 -*-
"""
BOM模板下载 - 从 bom.py 拆分
"""

from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.core import security
from app.services.import_export_engine import ExcelExportEngine
from app.models.user import User

router = APIRouter()


@router.get("/template/download")
def download_bom_import_template(
    current_user: User = Depends(security.get_current_active_user),
):
    """下载BOM导入模板"""
    # 创建模板DataFrame
    template_rows = [
        {
            "物料编码": "MAT-001",
            "物料名称": "示例物料1",
            "规格型号": "规格1",
            "单位": "件",
            "数量": 10,
            "单价": 1.5,
            "来源类型": "PURCHASE",
            "是否关键": False,
            "备注": "",
        },
        {
            "物料编码": "MAT-002",
            "物料名称": "示例物料2",
            "规格型号": "规格2",
            "单位": "件",
            "数量": 20,
            "单价": 2.5,
            "来源类型": "PURCHASE",
            "是否关键": False,
            "备注": "",
        },
        {
            "物料编码": "MAT-003",
            "物料名称": "示例物料3",
            "规格型号": "规格3",
            "单位": "件",
            "数量": 30,
            "单价": 3.5,
            "来源类型": "PURCHASE",
            "是否关键": True,
            "备注": "",
        },
    ]

    labels = ["物料编码", "物料名称", "规格型号", "单位", "数量", "单价", "来源类型", "是否关键", "备注"]
    widths = [15, 30, 20, 8, 10, 12, 12, 8, 30]
    columns = ExcelExportEngine.build_columns(labels, widths=widths)

    output = ExcelExportEngine.export_table(
        data=template_rows,
        columns=columns,
        sheet_name="BOM明细",
    )

    # 生成文件名
    filename = "BOM导入模板.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        },
    )
