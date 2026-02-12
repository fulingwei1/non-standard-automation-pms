# -*- coding: utf-8 -*-
"""
统一数据导入服务 - BOM数据导入
"""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Tuple

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.material import Material
from app.models.project import Project
from app.models.material import BomHeader, BomItem

from .base import ImportBase


class BomImporter(ImportBase):
    """BOM数据导入器"""

    @classmethod
    def import_bom_data(
        cls,
        db: Session,
        df: pd.DataFrame,
        current_user_id: int,
        update_existing: bool = False
    ) -> Tuple[int, int, List[Dict[str, Any]]]:
        """
        导入BOM数据
        """
        required_columns = ['BOM编码*', '项目编码*', '物料编码*', '用量*']
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
        bom_cache = {}  # 缓存BOM头

        for index, row in df.iterrows():
            try:
                # 解析必需字段
                bom_code = str(row.get('BOM编码*', '') or row.get('BOM编码', '')).strip()
                project_code = str(row.get('项目编码*', '') or row.get('项目编码', '')).strip()
                material_code = str(row.get('物料编码*', '') or row.get('物料编码', '')).strip()

                # 解析用量
                quantity_val = row.get('用量*') or row.get('用量')
                if pd.isna(quantity_val):
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "用量为必填项"
                    })
                    continue

                try:
                    quantity = Decimal(str(quantity_val))
                    if quantity <= 0:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": "用量必须大于0"
                        })
                        continue
                except (ValueError, TypeError, InvalidOperation):
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": "用量格式错误"
                    })
                    continue

                # 查找项目
                project = db.query(Project).filter(Project.project_code == project_code).first()
                if not project:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"未找到项目: {project_code}"
                    })
                    continue

                # 查找物料
                material = db.query(Material).filter(Material.material_code == material_code).first()
                if not material:
                    failed_rows.append({
                        "row_index": index + 2,
                        "error": f"未找到物料: {material_code}"
                    })
                    continue

                # 解析可选字段
                str(row.get('机台编号', '') or '').strip()
                unit = str(row.get('单位', '件') or '件').strip()
                remark = str(row.get('备注', '') or '').strip()

                # 获取或创建BOM头
                bom_key = (bom_code, project.id)
                if bom_key not in bom_cache:
                    bom_header = db.query(BomHeader).filter(
                        BomHeader.bom_no == bom_code
                    ).first()
                    if not bom_header:
                        bom_header = BomHeader(
                            bom_no=bom_code,
                            bom_name=f"{project.project_name}-BOM",
                            project_id=project.id,
                            version='1.0',
                            status='DRAFT',
                            created_by=current_user_id
                        )
                        db.add(bom_header)
                        db.flush()
                    bom_cache[bom_key] = bom_header
                else:
                    bom_header = bom_cache[bom_key]

                # 检查BOM明细是否已存在
                existing = db.query(BomItem).filter(
                    BomItem.bom_id == bom_header.id,
                    BomItem.material_id == material.id
                ).first()

                if existing:
                    if update_existing:
                        existing.quantity = quantity
                        existing.unit = unit
                        existing.remark = remark
                        updated_count += 1
                    else:
                        failed_rows.append({
                            "row_index": index + 2,
                            "error": "该BOM明细已存在"
                        })
                        continue
                else:
                    # 获取下一行号
                    max_item_no = db.query(BomItem).filter(
                        BomItem.bom_id == bom_header.id
                    ).count()
                    item_no = max_item_no + 1

                    # 创建BOM明细
                    bom_item = BomItem(
                        bom_id=bom_header.id,
                        item_no=item_no,
                        material_id=material.id,
                        material_code=material_code,
                        material_name=material.material_name,
                        specification=material.specification,
                        unit=unit,
                        quantity=quantity,
                        source_type=material.source_type or 'PURCHASE',
                        remark=remark
                    )
                    db.add(bom_item)
                    imported_count += 1

            except Exception as e:
                failed_rows.append({
                    "row_index": index + 2,
                    "error": str(e)
                })

        return imported_count, updated_count, failed_rows
