# -*- coding: utf-8 -*-
"""
统一数据导入服务 - 物料数据导入
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.vendor import Vendor

from .base import ImportBase


class MaterialImporter(ImportBase):
    """物料数据导入器"""

    @classmethod
    def import_material_data(
        cls,
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入物料数据
        """
        required_columns = ['物料编码*', '物料名称*']
        missing_columns = []
        for col in required_columns:
            if col not in df.columns and col.replace('*', '') not in df.columns:
                missing_columns.append(col)

        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Excel文件缺少必需的列：{', '.join(missing_columns)}"
            )

        imported_count = 0
        updated_count = 0
        failed_rows = []

        for index, row in df.iterrows():
            try:
                # 解析必需字段
                material_code = str(row.get('物料编码*', '') or row.get('物料编码', '')).strip()
                material_name = str(row.get('物料名称*', '') or row.get('物料名称', '')).strip()

                if not material_code or not material_name:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "物料编码和物料名称为必填项"
                    })
                    continue

                # 解析可选字段
                specification = str(row.get('规格型号', '') or '').strip()
                unit = str(row.get('单位', '件') or '件').strip()
                material_type = str(row.get('物料类型', '') or '').strip()
                supplier_name = str(row.get('默认供应商', '') or '').strip()

                # 解析价格和库存
                standard_price = Decimal('0')
                if pd.notna(row.get('参考价格')):
                    try:
                        standard_price = Decimal(str(row.get('参考价格')))
                    except (ValueError, TypeError, InvalidOperation):
                        pass

                safety_stock = Decimal('0')
                if pd.notna(row.get('安全库存')):
                    try:
                        safety_stock = Decimal(str(row.get('安全库存')))
                    except (ValueError, TypeError, InvalidOperation):
                        pass

                # 查找或创建供应商
                default_supplier_id = None
                if supplier_name:
                    supplier = db.query(Vendor).filter(
                        Vendor.supplier_name == supplier_name,
                        Vendor.vendor_type == 'MATERIAL'
                    ).first()
                    if not supplier:
                        # 自动创建供应商
                        supplier_code = f"SUP{datetime.now().strftime('%Y%m%d%H%M%S')}{index:03d}"
                        supplier = Vendor(
                            supplier_code=supplier_code,
                            supplier_name=supplier_name,
                            vendor_type='MATERIAL',
                            status='ACTIVE'
                        )
                        db.add(supplier)
                        db.flush()
                    default_supplier_id = supplier.id

                # 检查是否已存在
                existing = db.query(Material).filter(Material.material_code == material_code).first()

                if existing:
                    if update_existing:
                        existing.material_name = material_name
                        if specification:
                            existing.specification = specification
                        existing.unit = unit
                        if material_type:
                            existing.material_type = material_type
                        existing.standard_price = standard_price
                        existing.safety_stock = safety_stock
                        if default_supplier_id:
                            existing.default_supplier_id = default_supplier_id
                        updated_count += 1
                    else:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": f"物料编码 {material_code} 已存在"
                        })
                        continue
                else:
                    # 创建物料
                    material = Material(
                        material_code=material_code,
                        material_name=material_name,
                        specification=specification,
                        unit=unit,
                        material_type=material_type,
                        standard_price=standard_price,
                        safety_stock=safety_stock,
                        default_supplier_id=default_supplier_id,
                        is_active=True,
                        created_by=current_user_id
                    )
                    db.add(material)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": str(e)
                })

        return imported_count, updated_count, failed_rows
