# -*- coding: utf-8 -*-
"""
数据导入预览 routes
"""

from typing import Any

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.data_import_export import ImportPreviewResponse
from app.services.import_export_engine import ImportExportEngine

from .validators import _validate_import_row

router = APIRouter()


@router.post(
    "/preview", response_model=ImportPreviewResponse, status_code=status.HTTP_200_OK
)
def preview_import_data(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(...),
    template_type: str = Query(..., description="模板类型"),
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    预览导入数据（上传预览）

    支持多种数据类型预览：
    - PROJECT: 项目导入
    - USER: 用户导入
    - TIMESHEET: 工时导入
    - TASK: 任务导入
    - MATERIAL: 物料导入
    - BOM: BOM导入
    """
    try:
        file_content = file.file.read()
        df = ImportExportEngine.parse_excel(file_content)
        total_rows = len(df)

        if total_rows == 0:
            return ImportPreviewResponse(
                total_rows=0,
                valid_rows=0,
                invalid_rows=0,
                preview_data=[],
                errors=[{"row": 0, "field": "", "message": "文件中没有数据"}],
            )

        template_type_upper = template_type.upper()

        required_columns = ImportExportEngine.get_required_columns(template_type_upper)
        missing_columns = ImportExportEngine.find_missing_columns(df, required_columns)

        if missing_columns:
            return ImportPreviewResponse(
                total_rows=total_rows,
                valid_rows=0,
                invalid_rows=total_rows,
                preview_data=[],
                errors=[
                    {
                        "row": 0,
                        "field": "",
                        "message": f"缺少必需的列：{', '.join(missing_columns)}",
                    }
                ],
            )

        preview_rows = min(10, total_rows)
        preview_data = df.head(preview_rows).to_dict("records")

        errors = []
        valid_rows = 0

        import pandas as pd
        for idx, row in df.iterrows():
            row_num = idx + 2
            is_valid = _validate_import_row(
                row, row_num, template_type_upper, errors, pd
            )
            if is_valid:
                valid_rows += 1

        return ImportPreviewResponse(
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=total_rows - valid_rows,
            preview_data=preview_data[:preview_rows],
            errors=errors[:20],
        )

    except Exception as e:
        return ImportPreviewResponse(
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            preview_data=[],
            errors=[{"row": 0, "field": "", "message": f"文件解析失败: {str(e)}"}],
        )
