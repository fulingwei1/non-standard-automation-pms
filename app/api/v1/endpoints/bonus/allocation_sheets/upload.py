# -*- coding: utf-8 -*-
"""
奖金分配明细表 - 上传功能
"""
import os
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.bonus import BonusAllocationSheet
from app.models.user import User
from app.schemas.bonus import BonusAllocationSheetResponse
from app.schemas.common import ResponseModel

from ..allocation_helpers import generate_sheet_code

router = APIRouter()


@router.post("/allocation-sheets/upload", response_model=ResponseModel[BonusAllocationSheetResponse], status_code=status.HTTP_201_CREATED)
async def upload_allocation_sheet(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(..., description="分配明细表Excel文件"),
    sheet_name: str = Form(..., description="明细表名称"),
    project_id: Optional[int] = Form(None, description="项目ID（可选）"),
    period_id: Optional[int] = Form(None, description="考核周期ID（可选）"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传奖金分配明细表

    上传后会自动解析Excel文件，验证数据格式
    """
    try:
        import pandas as pd
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Excel处理库未安装，请安装pandas和openpyxl"
        )

    from app.services.bonus_allocation_parser import (
        parse_allocation_sheet,
        parse_excel_file,
        read_and_save_file,
        save_uploaded_file,
        validate_file_type,
        validate_required_columns,
    )

    file_path = None
    try:
        # 验证文件类型
        validate_file_type(file.filename)

        # 保存文件
        file_path, relative_path, _ = save_uploaded_file(file)
        file_content, file_size = await read_and_save_file(file, file_path)

        # 解析Excel
        df = parse_excel_file(file_content)
        validate_required_columns(df)

        # 解析数据
        valid_rows, parse_errors = parse_allocation_sheet(df, db)
        invalid_rows = list(parse_errors.keys())

        # 创建上传记录
        sheet_code = generate_sheet_code()
        allocation_sheet = BonusAllocationSheet(
            sheet_code=sheet_code,
            sheet_name=sheet_name,
            file_path=relative_path,
            file_name=file.filename,
            file_size=file_size,
            project_id=project_id,
            period_id=period_id,
            total_rows=len(df),
            valid_rows=len(valid_rows),
            invalid_rows=len(invalid_rows),
            status='PARSED' if len(invalid_rows) == 0 else 'UPLOADED',
            parse_result={'valid_rows': valid_rows},
            parse_errors=parse_errors if parse_errors else None,
            uploaded_by=current_user.id
        )

        db.add(allocation_sheet)
        db.commit()
        db.refresh(allocation_sheet)

        return ResponseModel(
            code=201,
            message=f"上传成功，有效行数：{len(valid_rows)}，无效行数：{len(invalid_rows)}",
            data=BonusAllocationSheetResponse.model_validate(allocation_sheet)
        )

    except HTTPException:
        raise
    except Exception as e:
        # 删除已上传的文件
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"解析Excel文件失败: {str(e)}")
