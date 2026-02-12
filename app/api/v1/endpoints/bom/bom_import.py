# -*- coding: utf-8 -*-
"""
BOM导入 - 从 bom.py 拆分
"""

from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.import_export_engine import ImportExportEngine
from app.models.material import BomHeader, BomItem, Material
from app.models.user import User
from app.schemas.common import ResponseModel

# 尝试导入Excel处理库
try:
    import pandas as pd

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

router = APIRouter()


@router.post("/{bom_id}/import", response_model=ResponseModel)
async def import_bom_from_excel(
    *,
    db: Session = Depends(deps.get_db),
    bom_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """从Excel导入BOM明细
    支持格式：物料编码、物料名称、规格型号、数量、单价、单位等
    """
    if not EXCEL_AVAILABLE:
        raise HTTPException(
            status_code=500, detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    bom = db.query(BomHeader).filter(BomHeader.id == bom_id).first()
    if not bom:
        raise HTTPException(status_code=404, detail="BOM不存在")

    # 只有草稿状态才能导入
    if bom.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只有草稿状态的BOM才能导入")

    try:
        # 读取Excel文件
        file_content = await file.read()
        df = ImportExportEngine.parse_excel(file_content)

        # 验证必需的列
        required_columns = ["物料编码", "物料名称", "数量"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}",
            )

        # 导入明细
        imported_count = 0
        error_count = 0
        errors = []

        for idx, row in df.iterrows():
            try:
                material_code = str(row.get("物料编码", "")).strip()
                material_name = str(row.get("物料名称", "")).strip()
                quantity = float(row.get("数量", 0))

                if not material_code or not material_name or quantity <= 0:
                    error_count += 1
                    errors.append(f"第{idx + 2}行：数据不完整或数量无效")
                    continue

                # 尝试查找物料
                material = (
                    db.query(Material)
                    .filter(Material.material_code == material_code)
                    .first()
                )
                material_id = material.id if material else None

                # 获取其他字段
                specification = (
                    str(row.get("规格型号", "")).strip()
                    if pd.notna(row.get("规格型号"))
                    else None
                )
                unit = (
                    str(row.get("单位", "件")).strip()
                    if pd.notna(row.get("单位"))
                    else "件"
                )
                unit_price = (
                    float(row.get("单价", 0)) if pd.notna(row.get("单价")) else 0
                )
                amount = quantity * unit_price
                source_type = (
                    row.get("来源类型", "PURCHASE")
                    if pd.notna(row.get("来源类型"))
                    else "PURCHASE"
                )
                is_key_item = (
                    bool(row.get("是否关键", False))
                    if pd.notna(row.get("是否关键"))
                    else False
                )

                # 获取当前最大行号
                max_item = (
                    db.query(BomItem)
                    .filter(BomItem.bom_id == bom_id)
                    .order_by(BomItem.item_no.desc())
                    .first()
                )
                item_no = (max_item.item_no + 1) if max_item else imported_count + 1

                # 创建BOM明细
                item = BomItem(
                    bom_id=bom_id,
                    item_no=item_no,
                    material_id=material_id,
                    material_code=material_code,
                    material_name=material_name,
                    specification=specification,
                    unit=unit,
                    quantity=quantity,
                    unit_price=unit_price,
                    amount=amount,
                    source_type=source_type,
                    is_key_item=is_key_item,
                )
                db.add(item)
                imported_count += 1

            except Exception as e:
                error_count += 1
                errors.append(f"第{idx + 2}行：{str(e)}")

        # 更新BOM统计
        bom.total_items = bom.items.count()
        total_amount = (
            db.query(func.sum(BomItem.amount)).filter(BomItem.bom_id == bom_id).scalar()
            or 0
        )
        bom.total_amount = total_amount

        db.commit()

        return ResponseModel(
            code=200,
            message=f"导入完成：成功{imported_count}条，失败{error_count}条",
            data={
                "imported_count": imported_count,
                "error_count": error_count,
                "errors": errors[:10] if errors else [],
            },
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"导入失败：{str(e)}")
