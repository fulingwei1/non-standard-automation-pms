# -*- coding: utf-8 -*-
"""
数据导入验证 routes
"""

from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.data_import_export import ImportValidateRequest, ImportValidateResponse

from .validators import _validate_row_data

router = APIRouter()


@router.post(
    "/validate", response_model=ImportValidateResponse, status_code=status.HTTP_200_OK
)
def validate_import_data(
    *,
    db: Session = Depends(deps.get_db),
    validate_in: ImportValidateRequest,
    current_user: User = Depends(
        security.require_permission("data_import_export:manage")
    ),
) -> Any:
    """
    验证导入数据（格式校验）
    验证数据格式和业务规则

    支持多种数据类型验证：
    - PROJECT: 项目导入
    - USER: 用户导入
    - TIMESHEET: 工时导入
    - TASK: 任务导入
    - MATERIAL: 物料导入
    - BOM: BOM导入
    """
    errors = []
    valid_count = 0
    template_type = validate_in.template_type.upper()

    for idx, row_data in enumerate(validate_in.data, start=1):
        row_errors = _validate_row_data(row_data, idx, db, template_type)

        if row_errors:
            errors.append({"row": idx, "errors": row_errors})
        else:
            valid_count += 1

    return ImportValidateResponse(
        is_valid=len(errors) == 0,
        valid_count=valid_count,
        invalid_count=len(validate_in.data) - valid_count,
        errors=errors,
    )
