# -*- coding: utf-8 -*-
"""
BOM模板下载 - 从 bom.py 拆分
"""

import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core import security
from app.models.user import User

router = APIRouter()


@router.get("/template/download")
def download_bom_import_template(
    current_user: User = Depends(security.get_current_active_user),
):
    """下载BOM导入模板"""
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    # 创建模板DataFrame
    template_data = {
        "物料编码": ["MAT-001", "MAT-002", "MAT-003"],
        "物料名称": ["示例物料1", "示例物料2", "示例物料3"],
        "规格型号": ["规格1", "规格2", "规格3"],
        "单位": ["件", "件", "件"],
        "数量": [10, 20, 30],
        "单价": [1.5, 2.5, 3.5],
        "来源类型": ["PURCHASE", "PURCHASE", "PURCHASE"],
        "是否关键": [False, False, True],
        "备注": ["", "", ""],
    }

    df = pd.DataFrame(template_data)

    # 创建Excel文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="BOM明细", index=False)

        # 设置列宽
        worksheet = writer.sheets["BOM明细"]
        column_widths = {
            "A": 15,  # 物料编码
            "B": 30,  # 物料名称
            "C": 20,  # 规格型号
            "D": 10,  # 图号
            "E": 8,  # 单位
            "F": 10,  # 数量
            "G": 12,  # 单价
            "H": 12,  # 金额
            "I": 12,  # 来源类型
            "J": 10,  # 需求日期
            "K": 8,  # 是否关键
            "L": 30,  # 备注
        }
        for col, width in column_widths.items():
            worksheet.column_dimensions[col].width = width

    output.seek(0)

    # 生成文件名
    filename = "BOM导入模板.xlsx"
    encoded_filename = quote(filename)

    return StreamingResponse(
        io.BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        },
    )
