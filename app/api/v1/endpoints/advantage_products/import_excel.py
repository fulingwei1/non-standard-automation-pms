# -*- coding: utf-8 -*-
"""
优势产品Excel导入端点
"""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.services.import_export_engine import ImportExportEngine
from app.models.user import User
from app.schemas.advantage_product import AdvantageProductImportResult

router = APIRouter()


@router.post("/import", response_model=AdvantageProductImportResult)
async def import_from_excel(
    file: UploadFile = File(..., description="Excel 文件"),
    clear_existing: bool = Query(True, description="是否先清空现有数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("advantage_product:create"))
):
    """从 Excel 文件导入优势产品"""
    from app.services.advantage_product_import_service import (
        ensure_categories_exist,
        parse_product_from_cell,
        process_product_row,
    )

    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器未安装 pandas 库"
        )

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请上传 Excel 文件 (.xlsx 或 .xls)"
        )

    errors = []
    categories_created = 0
    products_created = 0
    products_updated = 0
    products_skipped = 0

    try:
        # 读取 Excel 文件
        content = await file.read()
        df = ImportExportEngine.parse_excel(content, header=None)

        # 确保类别存在
        category_id_map, categories_created = ensure_categories_exist(db, clear_existing)

        # 处理每一列（每列是一个类别）
        for col_idx in range(min(len(df.columns), 8)):
            category_id = category_id_map.get(col_idx)
            if not category_id:
                continue

            current_series = None

            for row_idx, cell_value in enumerate(df.iloc[:, col_idx]):
                if pd.isna(cell_value) or str(cell_value).strip() == "":
                    continue

                cell_str = str(cell_value).strip()

                # 检查是否是系列编号
                product_code, product_name = parse_product_from_cell(cell_str, current_series, row_idx, col_idx)

                if product_code is None:
                    current_series = product_name
                    continue

                # 处理产品行
                is_created, is_updated, is_skipped = process_product_row(
                    db, product_code, product_name, category_id, current_series, clear_existing
                )

                if is_created:
                    products_created += 1
                elif is_updated:
                    products_updated += 1
                elif is_skipped:
                    products_skipped += 1

        db.commit()

        return AdvantageProductImportResult(
            success=True,
            categories_created=categories_created,
            products_created=products_created,
            products_updated=products_updated,
            products_skipped=products_skipped,
            errors=errors,
            message=f"导入成功：创建 {categories_created} 个类别，{products_created} 个产品"
        )

    except Exception as e:
        db.rollback()
        errors.append(str(e))
        return AdvantageProductImportResult(
            success=False,
            categories_created=0,
            products_created=0,
            products_updated=0,
            products_skipped=0,
            errors=errors,
            message=f"导入失败：{str(e)}"
        )
